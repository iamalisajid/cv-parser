"""Worker CRUD and filtered listing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api_schemas import (
    DomainScoreOut,
    SubdomainScoreOut,
    WorkerDetail,
    WorkerListResponse,
    WorkerSummary,
)
from backend.database import Skill, Worker, get_db
from backend.domain_scoring import (
    compute_all_domain_scores_for_worker,
    compute_domain_score,
    list_domains,
)
from backend.subdomain_scoring import (
    compute_all_subdomain_scores_for_worker,
    compute_subdomain_score,
    list_subdomains,
)

router = APIRouter(prefix="/api", tags=["workers"])


@router.get("/domains")
def get_domains() -> list[str]:
    return list_domains()


@router.get("/workers", response_model=WorkerListResponse)
def list_workers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str = Query("", description="Search name or email"),
    status: str = Query("", description="Filter by status"),
    min_score: int | None = Query(None, ge=0, le=100),
    max_score: int | None = Query(None, ge=0, le=100),
    min_yoe: int | None = Query(None, ge=0),
    max_yoe: int | None = Query(None),
    education_level: str = Query(""),
    skill_name: str = Query("", description="Filter workers who have this skill"),
    skill_category: str = Query("", description="Filter by skill category"),
    min_proficiency: str = Query("", description="Minimum proficiency level"),
    domain: str = Query("", description="Domain to compute score for"),
    min_domain_score: int | None = Query(None, ge=0, le=100),
    subdomain: str = Query("", description="Subdomain to compute score for"),
    min_subdomain_score: int | None = Query(None, ge=0, le=100),
    sort_by: str = Query("overall_score", description="Sort column"),
    sort_dir: str = Query("desc", description="asc or desc"),
    db: Session = Depends(get_db),
) -> WorkerListResponse:
    q = db.query(Worker)

    if search:
        pattern = f"%{search}%"
        q = q.filter(
            (Worker.name.ilike(pattern)) | (Worker.email.ilike(pattern))
        )

    if status:
        q = q.filter(Worker.status == status)

    if min_score is not None:
        q = q.filter(Worker.overall_score >= min_score)
    if max_score is not None:
        q = q.filter(Worker.overall_score <= max_score)

    if min_yoe is not None:
        q = q.filter(Worker.years_of_experience >= min_yoe)
    if max_yoe is not None:
        q = q.filter(Worker.years_of_experience <= max_yoe)

    if education_level:
        q = q.filter(Worker.education_level.ilike(f"%{education_level}%"))

    if skill_name or skill_category:
        skill_q = db.query(Skill.worker_id)
        if skill_name:
            skill_q = skill_q.filter(Skill.skill_name.ilike(f"%{skill_name}%"))
        if skill_category:
            skill_q = skill_q.filter(Skill.category.ilike(f"%{skill_category}%"))
        if min_proficiency:
            from backend.api_schemas import PROFICIENCY_ORDER
            min_ord = PROFICIENCY_ORDER.get(min_proficiency, 0)
            levels = [k for k, v in PROFICIENCY_ORDER.items() if v >= min_ord]
            skill_q = skill_q.filter(Skill.proficiency.in_(levels))
        worker_ids = [r[0] for r in skill_q.distinct().all()]
        q = q.filter(Worker.id.in_(worker_ids)) if worker_ids else q.filter(False)

    is_dynamic_sort = (sort_by == "domain_score" and domain) or (
        sort_by == "subdomain_score" and subdomain
    )

    if not is_dynamic_sort:
        total = q.count()
        sort_col = getattr(Worker, sort_by, Worker.overall_score)
        if sort_dir == "asc":
            q = q.order_by(sort_col.asc().nullslast())
        else:
            q = q.order_by(sort_col.desc().nullslast())
        workers = q.offset((page - 1) * page_size).limit(page_size).all()
    else:
        workers = q.all()

    items = []
    for w in workers:
        skill_count = db.query(func.count(Skill.id)).filter(Skill.worker_id == w.id).scalar() or 0
        w_skills = None
        d_score = None
        sd_score = None
        if domain or subdomain:
            w_skills = db.query(Skill).filter(Skill.worker_id == w.id).all()
        if domain and w_skills is not None:
            d_score = compute_domain_score(w_skills, domain)
        if subdomain and w_skills is not None:
            sd_score = compute_subdomain_score(w_skills, subdomain)
        items.append(WorkerSummary(
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
            domain_score=d_score,
            subdomain_score=sd_score,
            processed_at=w.processed_at,
            created_at=w.created_at,
        ))

    if min_domain_score is not None and domain:
        items = [i for i in items if (i.domain_score or 0) >= min_domain_score]
    if min_subdomain_score is not None and subdomain:
        items = [i for i in items if (i.subdomain_score or 0) >= min_subdomain_score]

    if is_dynamic_sort:
        if sort_by == "subdomain_score":
            items.sort(
                key=lambda i: i.subdomain_score or 0,
                reverse=(sort_dir == "desc"),
            )
        else:
            items.sort(
                key=lambda i: i.domain_score or 0,
                reverse=(sort_dir == "desc"),
            )
        total = len(items)
        start = (page - 1) * page_size
        items = items[start : start + page_size]
    elif (min_domain_score is not None and domain) or (
        min_subdomain_score is not None and subdomain
    ):
        total = len(items)
        start = (page - 1) * page_size
        items = items[start : start + page_size]

    return WorkerListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/workers/{worker_id}", response_model=WorkerDetail)
def get_worker(worker_id: int, db: Session = Depends(get_db)) -> WorkerDetail:
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    return WorkerDetail(
        id=worker.id,
        name=worker.name,
        email=worker.email,
        location=worker.location,
        education_level=worker.education_level or "",
        education_field=worker.education_field or "",
        years_of_experience=worker.years_of_experience,
        domain_expertise_rating=worker.domain_expertise_rating,
        overall_score=worker.overall_score,
        summary=worker.summary or "",
        reasoning=worker.reasoning or "",
        cv_url=worker.cv_url or "",
        status=worker.status,
        skills=[],
        processed_at=worker.processed_at,
        created_at=worker.created_at,
    )


@router.get("/workers/{worker_id}/skills")
def get_worker_skills(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    skills = db.query(Skill).filter(Skill.worker_id == worker_id).order_by(
        Skill.category, Skill.skill_name
    ).all()

    grouped: dict[str, list[dict]] = {}
    for s in skills:
        grouped.setdefault(s.category, []).append({
            "skill_name": s.skill_name,
            "proficiency": s.proficiency,
            "context": s.context,
        })

    return {"worker_id": worker_id, "skills_by_category": grouped}


@router.get("/workers/{worker_id}/domain-scores", response_model=list[DomainScoreOut])
def get_worker_domain_scores(
    worker_id: int, db: Session = Depends(get_db)
) -> list[DomainScoreOut]:
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    scores = compute_all_domain_scores_for_worker(db, worker_id)
    return [
        DomainScoreOut(domain=d, score=s)
        for d, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)
    ]


@router.get("/subdomains")
def get_subdomains() -> list[dict]:
    return list_subdomains()


@router.get(
    "/workers/{worker_id}/subdomain-scores",
    response_model=list[SubdomainScoreOut],
)
def get_worker_subdomain_scores(
    worker_id: int, db: Session = Depends(get_db)
) -> list[SubdomainScoreOut]:
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    raw = compute_all_subdomain_scores_for_worker(db, worker_id)
    return [
        SubdomainScoreOut(
            subdomain=r["subdomain"],
            tier=r["tier"],
            score=r["score"],
        )
        for r in sorted(raw, key=lambda x: x["score"], reverse=True)
    ]
