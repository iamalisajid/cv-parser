"""Ingestion endpoints: trigger from Google Sheet, upload CSV, refresh."""

from __future__ import annotations

import io
import logging
import sys
import threading
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.api_schemas import IngestResponse, JobStatus
from backend.database import Worker, get_db
from backend.tasks import (
    create_job_id,
    get_job,
    list_jobs,
    process_workers_background,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["ingest"])


def _ensure_importable() -> None:
    root = str(Path(__file__).resolve().parent.parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)


@router.post("/ingest", response_model=IngestResponse)
def ingest_from_sheet(db: Session = Depends(get_db)) -> IngestResponse:
    """Read the worker list from the configured Google Sheet and queue processing."""
    _ensure_importable()
    import config
    import google_auth

    gs_client, _ = google_auth.get_google_clients()

    if config.google_enabled and gs_client:
        try:
            sheet = gs_client.open_by_key(config.INPUT_SHEET_ID)
            wks = sheet.get_worksheet_by_id(int(config.INPUT_SHEET_GID))
            if wks is None:
                wks = sheet.sheet1
            rows = wks.get_all_values()
            if len(rows) < 2:
                return IngestResponse(job_id="", message="Sheet is empty", workers_queued=0)
            headers = rows[1]
            data = rows[2:]
            df = pd.DataFrame(data, columns=headers)
        except Exception as e:
            logger.exception("Failed to read Google Sheet")
            return IngestResponse(job_id="", message=f"Sheet error: {e}", workers_queued=0)
    else:
        csv_path = config.LOCAL_INPUT_CSV
        if not Path(csv_path).is_file():
            return IngestResponse(job_id="", message="No input CSV found", workers_queued=0)
        df = pd.read_csv(csv_path, header=1)

    existing_emails = {
        r[0] for r in db.query(Worker.email).filter(Worker.status == "completed").all()
    }

    workers_data = []
    for _, row in df.iterrows():
        email = str(row.get("Email", "")).strip()
        if not email or email.lower() in {e.lower() for e in existing_emails}:
            continue
        workers_data.append({
            "name": str(row.get("Name", "")).strip(),
            "email": email,
            "location": str(row.get("Location", "")).strip(),
            "cv_url": str(row.get("CV", "")).strip(),
        })

    if not workers_data:
        return IngestResponse(
            job_id="", message="All workers already processed", workers_queued=0
        )

    job_id = create_job_id()
    thread = threading.Thread(
        target=process_workers_background,
        args=(job_id, workers_data),
        daemon=True,
    )
    thread.start()

    return IngestResponse(
        job_id=job_id,
        message=f"Queued {len(workers_data)} workers for processing",
        workers_queued=len(workers_data),
    )


@router.post("/upload-csv", response_model=IngestResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> IngestResponse:
    """Upload a worker-list CSV and queue processing."""
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content), header=1)

    existing_emails = {
        r[0] for r in db.query(Worker.email).filter(Worker.status == "completed").all()
    }

    workers_data = []
    for _, row in df.iterrows():
        email = str(row.get("Email", "")).strip()
        if not email or email.lower() in {e.lower() for e in existing_emails}:
            continue
        workers_data.append({
            "name": str(row.get("Name", "")).strip(),
            "email": email,
            "location": str(row.get("Location", "")).strip(),
            "cv_url": str(row.get("CV", "")).strip(),
        })

    if not workers_data:
        return IngestResponse(
            job_id="", message="No new workers in CSV", workers_queued=0
        )

    job_id = create_job_id()
    thread = threading.Thread(
        target=process_workers_background,
        args=(job_id, workers_data),
        daemon=True,
    )
    thread.start()

    return IngestResponse(
        job_id=job_id,
        message=f"Queued {len(workers_data)} workers from uploaded CSV",
        workers_queued=len(workers_data),
    )


@router.post("/refresh", response_model=IngestResponse)
def refresh(db: Session = Depends(get_db)) -> IngestResponse:
    """Re-ingest from source, processing only new workers."""
    return ingest_from_sheet(db=db)


@router.get("/jobs", response_model=list[JobStatus])
def get_jobs() -> list[JobStatus]:
    return [JobStatus(**j) for j in list_jobs()]


@router.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str) -> JobStatus:
    job = get_job(job_id)
    if not job:
        return JobStatus(job_id=job_id, status="not_found", message="Job not found")
    return JobStatus(**job)
