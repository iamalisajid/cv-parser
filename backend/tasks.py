"""Background task runner for CV processing pipeline."""

from __future__ import annotations

import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.database import SessionLocal, Skill, Worker

logger = logging.getLogger(__name__)

# In-memory job tracker
_jobs: dict[str, dict[str, Any]] = {}


def _ensure_importable() -> None:
    """Add the project root to sys.path so the existing modules are importable."""
    root = str(Path(__file__).resolve().parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)


def get_job(job_id: str) -> dict[str, Any] | None:
    return _jobs.get(job_id)


def list_jobs() -> list[dict[str, Any]]:
    return list(_jobs.values())


def _upsert_worker_from_extraction(
    db: Session,
    name: str,
    email: str,
    location: str,
    cv_url: str,
    extraction: dict[str, Any],
    source_id: int | None = None,
) -> Worker:
    """Insert or update a worker and their skills from an LLM extraction result."""
    worker = db.query(Worker).filter(Worker.email == email).first()
    if worker:
        db.query(Skill).filter(Skill.worker_id == worker.id).delete()
    else:
        worker = Worker(email=email)
        db.add(worker)

    worker.name = name
    worker.location = location
    worker.cv_url = cv_url
    if source_id is not None:
        worker.source_id = source_id
    worker.education_level = str(extraction.get("education_level", "") or "")
    worker.education_field = str(extraction.get("education_field", "") or "")
    worker.years_of_experience = extraction.get("years_of_experience")
    worker.domain_expertise_rating = extraction.get("domain_expertise_rating")
    worker.overall_score = extraction.get("overall_score")
    worker.summary = str(extraction.get("summary", ""))
    worker.reasoning = str(extraction.get("reasoning", ""))
    worker.status = "completed"
    worker.processed_at = datetime.now(timezone.utc)

    db.flush()

    skills = extraction.get("skills", {})
    for category, items in skills.items():
        if isinstance(items, dict):
            for skill_name, value in items.items():
                if isinstance(value, dict):
                    level = value.get("level", "Intermediate")
                    context = value.get("context", "professional")
                else:
                    level = str(value) if value else "Intermediate"
                    context = "professional"
                db.add(Skill(
                    worker_id=worker.id,
                    category=category,
                    skill_name=skill_name,
                    proficiency=level,
                    context=context,
                ))

    return worker


def process_workers_background(
    job_id: str,
    workers_data: list[dict[str, str]],
) -> None:
    """Process a batch of workers in the background.

    Each entry in workers_data should have: name, email, location, cv_url.
    """
    _ensure_importable()
    import cv_downloader
    import google_auth
    import pdf_parser
    import skill_extractor

    _jobs[job_id] = {
        "job_id": job_id,
        "status": "running",
        "total": len(workers_data),
        "completed": 0,
        "failed": 0,
        "message": "Processing...",
    }

    _, drive_service = google_auth.get_google_clients()
    db: Session = SessionLocal()

    try:
        for entry in workers_data:
            email = entry["email"]
            name = entry.get("name", "")
            location = entry.get("location", "")
            cv_url = entry.get("cv_url", "")
            source_id = entry.get("source_id")

            try:
                worker = db.query(Worker).filter(Worker.email == email).first()
                if not worker:
                    worker = Worker(email=email, name=name, status="processing")
                    db.add(worker)
                    db.flush()
                else:
                    worker.status = "processing"
                    db.flush()

                cv_paths = cv_downloader.get_cv_paths(email, name, cv_url, drive_service)
                if not cv_paths:
                    worker.status = "failed"
                    db.commit()
                    _jobs[job_id]["failed"] += 1
                    continue

                texts = [pdf_parser.extract_text(p) for p in cv_paths]
                combined = "\n\n".join(t for t in texts if t)
                if not combined.strip():
                    worker.status = "failed"
                    db.commit()
                    _jobs[job_id]["failed"] += 1
                    continue

                extraction = skill_extractor.extract_skills(combined)
                if not extraction:
                    worker.status = "failed"
                    db.commit()
                    _jobs[job_id]["failed"] += 1
                    continue

                _upsert_worker_from_extraction(
                    db, name, email, location, cv_url, extraction,
                    source_id=int(source_id) if source_id else None,
                )
                db.commit()
                _jobs[job_id]["completed"] += 1

            except Exception:
                logger.exception("Failed to process %s", email)
                db.rollback()
                _jobs[job_id]["failed"] += 1

        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["message"] = (
            f"Done: {_jobs[job_id]['completed']} succeeded, "
            f"{_jobs[job_id]['failed']} failed"
        )
    except Exception:
        logger.exception("Background job %s crashed", job_id)
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["message"] = "Job crashed unexpectedly"
    finally:
        db.close()


def create_job_id() -> str:
    return str(uuid.uuid4())[:8]
