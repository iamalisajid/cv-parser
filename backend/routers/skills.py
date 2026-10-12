"""Skill listing, querying, and taxonomy endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from backend.api_schemas import (
    PROFICIENCY_ORDER,
    SkillCategoryOut,
    SkillQuery,
    WorkerListResponse,
    WorkerSummary,
)
from backend.database import Skill, Worker, get_db

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=list[SkillCategoryOut])
def list_skills(db: Session = Depends(get_db)) -> list[SkillCategoryOut]:
    """Return all unique skills grouped by category for filter dropdowns."""
    rows = (
        db.query(Skill.category, Skill.skill_name)
        .distinct()
        .order_by(Skill.category, Skill.skill_name)
        .all()
    )
    grouped: dict[str, list[str]] = {}
    for cat, name in rows:
        grouped.setdefault(cat, []).append(name)
    return [SkillCategoryOut(category=c, skills=s) for c, s in sorted(grouped.items())]


@router.get("/names")
def list_skill_names(db: Session = Depends(get_db)):
    """Flat list of unique skill names for autocomplete."""
    rows = db.query(distinct(Skill.skill_name)).order_by(Skill.skill_name).all()
    return [r[0] for r in rows]


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """Flat list of unique categories."""
    rows = db.query(distinct(Skill.category)).order_by(Skill.category).all()
    return [r[0] for r in rows]


@router.post("/query", response_model=WorkerListResponse)
def query_by_skills(
    body: SkillQuery,
    db: Session = Depends(get_db),
) -> WorkerListResponse:
    """Advanced skill-based query with AND/OR logic."""
    if not body.conditions:
        workers = db.query(Worker).filter(Worker.status == "completed").all()
        total = len(workers)
        items = _workers_to_summaries(db, workers)
        return WorkerListResponse(
            items=items, total=total, page=body.page, page_size=body.page_size
        )

    candidate_sets: list[set[int]] = []

    for cond in body.conditions:
        min_ord = PROFICIENCY_ORDER.get(cond.min_proficiency, 1)
        valid_levels = [k for k, v in PROFICIENCY_ORDER.items() if v >= min_ord]

        sq = db.query(Skill.worker_id).filter(
            Skill.skill_name.ilike(f"%{cond.skill_name}%"),
            Skill.proficiency.in_(valid_levels),
        )
        if cond.category:
            sq = sq.filter(Skill.category.ilike(f"%{cond.category}%"))

        ids = {r[0] for r in sq.distinct().all()}
        candidate_sets.append(ids)

    if body.match_all:
        final_ids = candidate_sets[0]
        for s in candidate_sets[1:]:
            final_ids &= s
    else:
        final_ids: set[int] = set()
        for s in candidate_sets:
            final_ids |= s

    if not final_ids:
        return WorkerListResponse(
            items=[], total=0, page=body.page, page_size=body.page_size
        )

    total = len(final_ids)
    offset = (body.page - 1) * body.page_size
    workers = (
        db.query(Worker)
        .filter(Worker.id.in_(final_ids))
        .order_by(Worker.overall_score.desc().nullslast())
        .offset(offset)
        .limit(body.page_size)
        .all()
    )

    items = _workers_to_summaries(db, workers)
    return WorkerListResponse(
        items=items, total=total, page=body.page, page_size=body.page_size
    )


def _workers_to_summaries(db: Session, workers: list[Worker]) -> list[WorkerSummary]:
    summaries = []
    for w in workers:
        skill_count = db.query(func.count(Skill.id)).filter(Skill.worker_id == w.id).scalar() or 0
        summaries.append(WorkerSummary(
            id=w.id,
            name=w.name,
            email=w.email,
            location=w.location,
            education_level=w.education_level or "",
            education_field=w.education_field or "",
            years_of_experience=w.years_of_experience,
            domain_expertise_rating=w.domain_expertise_rating,
            overall_score=w.overall_score,
            status=w.status,
            skill_count=skill_count,
            processed_at=w.processed_at,
            created_at=w.created_at,
        ))
    return summaries
