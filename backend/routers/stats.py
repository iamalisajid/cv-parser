"""Dashboard statistics endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api_schemas import StatsResponse
from backend.database import Skill, Worker, get_db

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    total = db.query(func.count(Worker.id)).scalar() or 0
    completed = db.query(func.count(Worker.id)).filter(Worker.status == "completed").scalar() or 0
    pending = db.query(func.count(Worker.id)).filter(Worker.status.in_(["pending", "processing"])).scalar() or 0

    avg_score = db.query(func.avg(Worker.overall_score)).filter(
        Worker.overall_score.isnot(None)
    ).scalar()
    avg_domain = db.query(func.avg(Worker.domain_expertise_rating)).filter(
        Worker.domain_expertise_rating.isnot(None)
    ).scalar()

    score_dist = _score_distribution(db)
    exp_brackets = _experience_brackets(db)
    edu_breakdown = _education_breakdown(db)
    top_skills = _top_skills(db, limit=20)
    cat_coverage = _category_coverage(db)

    return StatsResponse(
        total_workers=total,
        completed_workers=completed,
        pending_workers=pending,
        avg_overall_score=round(avg_score, 1) if avg_score else None,
        avg_domain_expertise=round(avg_domain, 1) if avg_domain else None,
        score_distribution=score_dist,
        experience_brackets=exp_brackets,
        education_breakdown=edu_breakdown,
        top_skills=top_skills,
        category_coverage=cat_coverage,
    )


def _score_distribution(db: Session) -> list[dict]:
    buckets = [(0, 20), (21, 40), (41, 60), (61, 80), (81, 100)]
    result = []
    for lo, hi in buckets:
        count = (
            db.query(func.count(Worker.id))
            .filter(Worker.overall_score >= lo, Worker.overall_score <= hi)
            .scalar() or 0
        )
        result.append({"range": f"{lo}-{hi}", "count": count})
    return result


def _experience_brackets(db: Session) -> list[dict]:
    brackets = [
        ("0-2 years", 0, 2),
        ("3-5 years", 3, 5),
        ("6-10 years", 6, 10),
        ("10+ years", 11, 100),
    ]
    result = []
    for label, lo, hi in brackets:
        count = (
            db.query(func.count(Worker.id))
            .filter(
                Worker.years_of_experience >= lo,
                Worker.years_of_experience <= hi,
            )
            .scalar() or 0
        )
        result.append({"bracket": label, "count": count})
    return result


def _education_breakdown(db: Session) -> list[dict]:
    rows = (
        db.query(Worker.education_level, func.count(Worker.id))
        .filter(Worker.education_level.isnot(None), Worker.education_level != "")
        .group_by(Worker.education_level)
        .order_by(func.count(Worker.id).desc())
        .all()
    )
    return [{"level": level, "count": count} for level, count in rows]


def _top_skills(db: Session, limit: int = 20) -> list[dict]:
    rows = (
        db.query(Skill.skill_name, func.count(Skill.id).label("cnt"))
        .group_by(Skill.skill_name)
        .order_by(func.count(Skill.id).desc())
        .limit(limit)
        .all()
    )
    return [{"skill": name, "count": count} for name, count in rows]


def _category_coverage(db: Session) -> list[dict]:
    rows = (
        db.query(
            Skill.category,
            func.count(func.distinct(Skill.worker_id)).label("workers"),
        )
        .group_by(Skill.category)
        .order_by(func.count(func.distinct(Skill.worker_id)).desc())
        .all()
    )
    return [{"category": cat, "workers": count} for cat, count in rows]
