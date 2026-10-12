"""Seed the database from an existing output/results.csv file."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from backend.database import SessionLocal, Worker, Skill, create_tables

logger = logging.getLogger(__name__)

NA_VALUES = {"N/A", "", "nan", "False", "false"}

FIXED_COLUMNS = {
    "Name",
    "Email",
    "Location",
    "Education Level",
    "Education Field",
    "Years of Experience",
    "Domain Expertise Rating",
    "Overall Score",
    "Summary",
    "Reasoning",
}


def _safe_int(val) -> int | None:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def seed_from_csv(csv_path: str | Path = "output/results.csv") -> int:
    """Import workers and skills from the wide-format results CSV.

    Returns the number of workers imported.
    """
    csv_path = Path(csv_path)
    if not csv_path.is_file():
        logger.warning("No CSV found at %s -- skipping seed.", csv_path)
        return 0

    df = pd.read_csv(csv_path, keep_default_na=False, na_values=[""])
    if df.empty:
        return 0

    skill_columns = [c for c in df.columns if c not in FIXED_COLUMNS]

    create_tables()
    db: Session = SessionLocal()
    imported = 0

    try:
        for _, row in df.iterrows():
            email = str(row.get("Email", "")).strip()
            if not email:
                continue

            existing = db.query(Worker).filter(Worker.email == email).first()
            if existing:
                continue

            worker = Worker(
                name=str(row.get("Name", "")),
                email=email,
                location=str(row.get("Location", "")),
                education_level=str(row.get("Education Level", "")),
                education_field=str(row.get("Education Field", "")),
                years_of_experience=_safe_int(row.get("Years of Experience")),
                domain_expertise_rating=_safe_int(row.get("Domain Expertise Rating")),
                overall_score=_safe_int(row.get("Overall Score")),
                summary=str(row.get("Summary", "")),
                reasoning=str(row.get("Reasoning", "")),
                status="completed",
            )
            db.add(worker)
            db.flush()

            for col in skill_columns:
                val = str(row.get(col, "")).strip()
                if val in NA_VALUES:
                    continue
                parts = col.split(" | ", maxsplit=1)
                category = parts[0] if len(parts) == 2 else "Other"
                skill_name = parts[1] if len(parts) == 2 else col
                db.add(Skill(
                    worker_id=worker.id,
                    category=category,
                    skill_name=skill_name,
                    proficiency=val,
                    context="professional",
                ))

            imported += 1

        db.commit()
        logger.info("Seeded %d workers from %s", imported, csv_path)
    except Exception:
        db.rollback()
        logger.exception("Seed failed")
        raise
    finally:
        db.close()

    return imported


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = seed_from_csv()
    print(f"Imported {count} workers.")
