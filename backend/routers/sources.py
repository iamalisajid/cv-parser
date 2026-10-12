"""Data source CRUD, tab listing, and per-source ingestion."""

from __future__ import annotations

import logging
import re
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api_schemas import (
    DataSourceCreate,
    DataSourceOut,
    IngestResponse,
    JobStatus,
    SheetTabOut,
)
from backend.database import DataSource, Worker, get_db
from backend.tasks import create_job_id, get_job, list_jobs, process_workers_background

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sources", tags=["sources"])

_SHEET_URL_RE = re.compile(
    r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)"
)
_GID_RE = re.compile(r"[#&]gid=(\d+)")


def _ensure_importable() -> None:
    root = str(Path(__file__).resolve().parent.parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)


def _extract_sheet_id(url: str) -> str:
    m = _SHEET_URL_RE.search(url)
    if not m:
        raise ValueError("Invalid Google Sheets URL")
    return m.group(1)


def _extract_gid(url: str) -> str | None:
    m = _GID_RE.search(url)
    return m.group(1) if m else None


def _get_gs_client():
    _ensure_importable()
    import google_auth
    gs_client, _ = google_auth.get_google_clients()
    if not gs_client:
        raise HTTPException(status_code=503, detail="Google Sheets not configured")
    return gs_client


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[DataSourceOut])
def list_sources(db: Session = Depends(get_db)) -> list[DataSourceOut]:
    sources = db.query(DataSource).order_by(DataSource.created_at.desc()).all()
    return [DataSourceOut.model_validate(s) for s in sources]


@router.post("", response_model=DataSourceOut, status_code=201)
def create_source(
    body: DataSourceCreate,
    db: Session = Depends(get_db),
) -> DataSourceOut:
    try:
        sheet_id = _extract_sheet_id(body.sheet_url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google Sheets URL")

    gid = body.gid
    if gid == "0":
        url_gid = _extract_gid(body.sheet_url)
        if url_gid:
            gid = url_gid

    source = DataSource(
        name=body.name,
        sheet_url=body.sheet_url,
        sheet_id=sheet_id,
        gid=gid,
        tab_name=body.tab_name,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return DataSourceOut.model_validate(source)


@router.get("/{source_id}", response_model=DataSourceOut)
def get_source(source_id: int, db: Session = Depends(get_db)) -> DataSourceOut:
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return DataSourceOut.model_validate(source)


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    db.delete(source)
    db.commit()


# ── Tab Listing ──────────────────────────────────────────────────────────────

@router.get("/{source_id}/tabs", response_model=list[SheetTabOut])
def list_tabs(source_id: int, db: Session = Depends(get_db)) -> list[SheetTabOut]:
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    gs_client = _get_gs_client()
    try:
        spreadsheet = gs_client.open_by_key(source.sheet_id)
        tabs = []
        for ws in spreadsheet.worksheets():
            tabs.append(SheetTabOut(
                gid=str(ws.id),
                title=ws.title,
                row_count=ws.row_count,
            ))
        return tabs
    except Exception as e:
        logger.exception("Failed to list tabs for source %d", source_id)
        raise HTTPException(status_code=502, detail=f"Google Sheets error: {e}")


@router.post("/from-url/tabs", response_model=list[SheetTabOut])
def list_tabs_from_url(
    sheet_url: str = Query(..., description="Full Google Sheets URL"),
) -> list[SheetTabOut]:
    """List tabs without creating a source first (for the add-source flow)."""
    try:
        sheet_id = _extract_sheet_id(sheet_url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google Sheets URL")

    gs_client = _get_gs_client()
    try:
        spreadsheet = gs_client.open_by_key(sheet_id)
        tabs = []
        for ws in spreadsheet.worksheets():
            tabs.append(SheetTabOut(
                gid=str(ws.id),
                title=ws.title,
                row_count=ws.row_count,
            ))
        return tabs
    except Exception as e:
        logger.exception("Failed to list tabs from URL")
        raise HTTPException(status_code=502, detail=f"Google Sheets error: {e}")


# ── Ingest ───────────────────────────────────────────────────────────────────

@router.patch("/{source_id}", response_model=DataSourceOut)
def update_source_tab(
    source_id: int,
    gid: str = Query(...),
    tab_name: str = Query(""),
    db: Session = Depends(get_db),
) -> DataSourceOut:
    """Update which tab is selected for a source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    source.gid = gid
    source.tab_name = tab_name
    db.commit()
    db.refresh(source)
    return DataSourceOut.model_validate(source)


@router.post("/{source_id}/ingest", response_model=IngestResponse)
def ingest_from_source(source_id: int, db: Session = Depends(get_db)) -> IngestResponse:
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    gs_client = _get_gs_client()

    try:
        sheet = gs_client.open_by_key(source.sheet_id)
        wks = sheet.get_worksheet_by_id(int(source.gid))
        if wks is None:
            wks = sheet.sheet1
        rows = wks.get_all_values()
        if len(rows) < 2:
            return IngestResponse(job_id="", message="Sheet is empty", workers_queued=0)
        headers = rows[1]
        data = rows[2:]
        df = pd.DataFrame(data, columns=headers)
    except Exception as e:
        logger.exception("Failed to read source %d", source_id)
        return IngestResponse(job_id="", message=f"Sheet error: {e}", workers_queued=0)

    existing_emails = {
        r[0] for r in db.query(Worker.email).filter(Worker.status == "completed").all()
    }

    workers_data: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        email = str(row.get("Email", "")).strip()
        if not email or email.lower() in {e.lower() for e in existing_emails}:
            continue
        workers_data.append({
            "name": str(row.get("Name", "")).strip(),
            "email": email,
            "location": str(row.get("Location", "")).strip(),
            "cv_url": str(row.get("CV", "")).strip(),
            "source_id": source_id,
        })

    if not workers_data:
        return IngestResponse(
            job_id="", message="All workers already processed", workers_queued=0
        )

    job_id = create_job_id()
    thread = threading.Thread(
        target=_ingest_and_update_source,
        args=(job_id, workers_data, source_id),
        daemon=True,
    )
    thread.start()

    return IngestResponse(
        job_id=job_id,
        message=f"Queued {len(workers_data)} workers for processing",
        workers_queued=len(workers_data),
    )


def _ingest_and_update_source(
    job_id: str,
    workers_data: list[dict[str, str]],
    source_id: int,
) -> None:
    """Run ingestion then update source metadata."""
    process_workers_background(job_id, workers_data)

    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        source = db.query(DataSource).filter(DataSource.id == source_id).first()
        if source:
            source.last_synced_at = datetime.now(timezone.utc)
            source.worker_count = (
                db.query(Worker)
                .filter(Worker.source_id == source_id, Worker.status == "completed")
                .count()
            )
            db.commit()
    finally:
        db.close()
