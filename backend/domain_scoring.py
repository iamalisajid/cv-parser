"""Domain-specific scoring computed from existing skill data."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.database import Skill

PROFICIENCY_WEIGHT = {"Expert": 4, "Advanced": 3, "Intermediate": 2, "Beginner": 1}
CONTEXT_WEIGHT = {"professional": 1.0, "academic": 0.8, "hobby": 0.5}
MAX_PROFICIENCY = PROFICIENCY_WEIGHT["Expert"]

DOMAINS: dict[str, list[str]] = {
    "Data Science": [
        "Data Science - Machine Learning",
        "Data Science - Deep Learning",
        "Data Science - NLP",
        "Data Science - Computer Vision",
        "Data Science - Statistics",
        "Data Science - Data Engineering",
        "Data Science - Generative AI",
    ],
    "Machine Learning": [
        "Data Science - Machine Learning",
        "Data Science - Deep Learning",
    ],
    "NLP": ["Data Science - NLP"],
    "Computer Vision": ["Data Science - Computer Vision"],
    "Generative AI": ["Data Science - Generative AI"],
    "Software Engineering": ["Software Engineering"],
    "Cloud & Infrastructure": ["Cloud & Infrastructure"],
    "Data Engineering": ["Data Science - Data Engineering"],
    "Full Stack": ["Software Engineering", "Programming Languages", "Tools & Frameworks"],
}


def list_domains() -> list[str]:
    return sorted(DOMAINS.keys())


def compute_domain_score(skills: list[Skill], domain: str) -> int:
    """Return a 0-100 score for how well a set of skills matches a domain.

    The score reflects both the breadth (number of relevant skills) and depth
    (proficiency level weighted by context) of the worker's skills in the
    target domain's categories.
    """
    categories = DOMAINS.get(domain)
    if not categories:
        return 0

    relevant = [s for s in skills if s.category in categories]
    if not relevant:
        return 0

    total_weighted = 0.0
    for s in relevant:
        prof = PROFICIENCY_WEIGHT.get(s.proficiency, 1)
        ctx = CONTEXT_WEIGHT.get(s.context, 0.5)
        total_weighted += prof * ctx

    max_possible = len(relevant) * MAX_PROFICIENCY * 1.0
    raw = (total_weighted / max_possible) * 100 if max_possible else 0

    breadth_bonus = min(len(relevant) / 5.0, 1.0) * 15
    score = raw * 0.85 + breadth_bonus

    return min(int(round(score)), 100)


def compute_all_domain_scores(skills: list[Skill]) -> dict[str, int]:
    """Compute scores for every defined domain."""
    return {domain: compute_domain_score(skills, domain) for domain in DOMAINS}


def compute_domain_score_for_worker(
    db: Session, worker_id: int, domain: str
) -> int:
    skills = db.query(Skill).filter(Skill.worker_id == worker_id).all()
    return compute_domain_score(skills, domain)


def compute_all_domain_scores_for_worker(
    db: Session, worker_id: int
) -> dict[str, int]:
    skills = db.query(Skill).filter(Skill.worker_id == worker_id).all()
    return compute_all_domain_scores(skills)
