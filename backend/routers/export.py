"""Export endpoints: CSV, JSON, and Google Sheets."""

from __future__ import annotations

import io
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from backend.api_schemas import PROFICIENCY_ORDER, SkillCondition
from backend.database import Skill, Worker, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/export", tags=["export"])


def _filtered_workers(
    db: Session,
    worker_ids: list[int] | None = None,
    skill_filters: list[SkillCondition] | None = None,
) -> list[Worker]:
    q = db.query(Worker).filter(Worker.status == "completed")

    if worker_ids:
        q = q.filter(Worker.id.in_(worker_ids))

    if skill_filters:
        for cond in skill_filters:
            min_ord = PROFICIENCY_ORDER.get(cond.min_proficiency, 1)
            valid_levels = [k for k, v in PROFICIENCY_ORDER.items() if v >= min_ord]
            sub = (
                db.query(Skill.worker_id)
                .filter(
                    Skill.skill_name.ilike(f"%{cond.skill_name}%"),
                    Skill.proficiency.in_(valid_levels),
                )
                .distinct()
            )
            ids = [r[0] for r in sub.all()]
            q = q.filter(Worker.id.in_(ids)) if ids else q.filter(False)

    return q.order_by(Worker.overall_score.desc().nullslast()).all()


def _build_export_rows(
    db: Session, workers: list[Worker]
) -> tuple[list[str], list[dict[str, Any]]]:
    """Build wide-format rows matching the original results.csv layout."""
    all_skill_cols: set[str] = set()
    worker_skills: dict[int, dict[str, str]] = {}

    for w in workers:
        skills = db.query(Skill).filter(Skill.worker_id == w.id).all()
        flat: dict[str, str] = {}
        for s in skills:
            col = f"{s.category} | {s.skill_name}"
            flat[col] = s.proficiency
            all_skill_cols.add(col)
        worker_skills[w.id] = flat

    fixed = [
        "Name", "Email", "Location", "Education Level", "Education Field",
        "Years of Experience", "Domain Expertise Rating", "Overall Score",
        "Summary", "Reasoning",
    ]
    skill_cols_sorted = sorted(all_skill_cols)
    headers = fixed + skill_cols_sorted

    rows = []
    for w in workers:
        row: dict[str, Any] = {
            "Name": w.name,
            "Email": w.email,
            "Location": w.location,
            "Education Level": w.education_level or "",
            "Education Field": w.education_field or "",
            "Years of Experience": w.years_of_experience or "",
            "Domain Expertise Rating": w.domain_expertise_rating or "",
            "Overall Score": w.overall_score or "",
            "Summary": w.summary or "",
            "Reasoning": w.reasoning or "",
        }
        sk = worker_skills.get(w.id, {})
        for col in skill_cols_sorted:
            row[col] = sk.get(col, "N/A")
        rows.append(row)

    return headers, rows


@router.get("/csv")
def export_csv(
    worker_ids: str = Query("", description="Comma-separated worker IDs"),
    db: Session = Depends(get_db),
):
    ids = [int(x) for x in worker_ids.split(",") if x.strip().isdigit()] or None
    workers = _filtered_workers(db, worker_ids=ids)
    headers, rows = _build_export_rows(db, workers)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cv_parser_export.csv"},
    )


@router.get("/json")
def export_json(
    worker_ids: str = Query("", description="Comma-separated worker IDs"),
    db: Session = Depends(get_db),
):
    ids = [int(x) for x in worker_ids.split(",") if x.strip().isdigit()] or None
    workers = _filtered_workers(db, worker_ids=ids)

    result = []
    for w in workers:
        skills = db.query(Skill).filter(Skill.worker_id == w.id).all()
        skills_grouped: dict[str, list[dict]] = {}
        for s in skills:
            skills_grouped.setdefault(s.category, []).append({
                "skill_name": s.skill_name,
                "proficiency": s.proficiency,
                "context": s.context,
            })
        result.append({
            "name": w.name,
            "email": w.email,
            "location": w.location,
            "education_level": w.education_level,
            "education_field": w.education_field,
            "years_of_experience": w.years_of_experience,
            "domain_expertise_rating": w.domain_expertise_rating,
            "overall_score": w.overall_score,
            "summary": w.summary,
            "reasoning": w.reasoning,
            "skills": skills_grouped,
        })

    return Response(
        content=json.dumps(result, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=cv_parser_export.json"},
    )


@router.post("/sheets")
def export_to_sheets(
    sheet_url: str = Query("", description="Optional target Google Sheets URL"),
    worker_ids: str = Query("", description="Comma-separated worker IDs"),
    db: Session = Depends(get_db),
):
    """Push results to the configured or a user-specified Google Sheet."""
    root = str(Path(__file__).resolve().parent.parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)

    try:
        import google_auth
        import output_writer

        gs_client, _ = google_auth.get_google_clients()
        if not gs_client:
            return {"error": "Google Sheets not configured"}

        ids = [int(x) for x in worker_ids.split(",") if x.strip().isdigit()] or None
        workers = _filtered_workers(db, worker_ids=ids)
        headers, rows = _build_export_rows(db, workers)

        import pandas as pd
        df = pd.DataFrame(rows, columns=headers)

        if sheet_url.strip():
            import re
            m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", sheet_url)
            if not m:
                return {"error": "Invalid Google Sheets URL"}
            target_id = m.group(1)
            try:
                spreadsheet = gs_client.open_by_key(target_id)
                ws = spreadsheet.sheet1
                ws.clear()
                ws.update(
                    [df.columns.tolist()] + df.values.tolist(),
                    value_input_option="USER_ENTERED",
                )
                return {
                    "message": f"Exported {len(workers)} workers to {spreadsheet.title}",
                    "path": sheet_url,
                }
            except Exception as e:
                logger.exception("Export to custom sheet failed")
                return {"error": str(e)}

        path = output_writer.write_results(df, gs_client)
        output_writer.write_extra_sheets(df, gs_client)

        return {"message": f"Exported {len(workers)} workers to Google Sheets", "path": str(path)}
    except Exception as e:
        logger.exception("Sheets export failed")
        return {"error": str(e)}
