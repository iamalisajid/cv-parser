"""Pydantic request/response models for the API layer."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Skills ───────────────────────────────────────────────────────────────────

class SkillOut(BaseModel):
    id: int
    category: str
    skill_name: str
    proficiency: str
    context: str = "professional"

    model_config = {"from_attributes": True}


class SkillCategoryOut(BaseModel):
    category: str
    skills: list[str]


# ── Workers ──────────────────────────────────────────────────────────────────

class WorkerSummary(BaseModel):
    id: int
    name: str
    email: str
    location: str
    education_level: str
    education_field: str
    years_of_experience: Optional[int]
    domain_expertise_rating: Optional[int]
    overall_score: Optional[int]
    status: str
    skill_count: int = 0
    domain_score: Optional[int] = None
    subdomain_score: Optional[int] = None
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WorkerDetail(BaseModel):
    id: int
    name: str
    email: str
    location: str
    education_level: str
    education_field: str
    years_of_experience: Optional[int]
    domain_expertise_rating: Optional[int]
    overall_score: Optional[int]
    summary: str
    reasoning: str
    cv_url: str
    status: str
    skills: list[SkillOut]
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WorkerListResponse(BaseModel):
    items: list[WorkerSummary]
    total: int
    page: int
    page_size: int


# ── Query ────────────────────────────────────────────────────────────────────

PROFICIENCY_ORDER = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Expert": 4}


class SkillCondition(BaseModel):
    skill_name: str
    min_proficiency: str = Field(
        default="Beginner",
        description="Minimum proficiency: Beginner, Intermediate, Advanced, Expert",
    )
    category: Optional[str] = None


class SkillQuery(BaseModel):
    conditions: list[SkillCondition]
    match_all: bool = Field(
        default=True,
        description="True for AND logic, False for OR logic",
    )
    page: int = 1
    page_size: int = 50


# ── Stats ────────────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_workers: int
    completed_workers: int
    pending_workers: int
    avg_overall_score: Optional[float]
    avg_domain_expertise: Optional[float]
    score_distribution: list[dict]
    experience_brackets: list[dict]
    education_breakdown: list[dict]
    top_skills: list[dict]
    category_coverage: list[dict]


# ── Export ───────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    format: str = Field(default="csv", description="csv, json, or sheets")
    worker_ids: Optional[list[int]] = None
    skill_filters: Optional[list[SkillCondition]] = None


# ── Jobs ─────────────────────────────────────────────────────────────────────

class JobStatus(BaseModel):
    job_id: str
    status: str
    total: int = 0
    completed: int = 0
    failed: int = 0
    message: str = ""


# ── Ingest ───────────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    job_id: str
    message: str
    workers_queued: int = 0


# ── Data Sources ─────────────────────────────────────────────────────────────

class DataSourceCreate(BaseModel):
    name: str
    sheet_url: str
    gid: str = "0"
    tab_name: str = ""


class DataSourceOut(BaseModel):
    id: int
    name: str
    sheet_url: str
    sheet_id: str
    gid: str
    tab_name: str
    created_by: str
    last_synced_at: Optional[datetime] = None
    worker_count: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SheetTabOut(BaseModel):
    gid: str
    title: str
    row_count: int = 0


# ── Saved Views ──────────────────────────────────────────────────────────────

class SavedViewCreate(BaseModel):
    name: str
    description: str = ""
    view_type: str = Field(description="'workers' or 'query'")
    filters: str = Field(description="JSON string of filter state")


class SavedViewUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    filters: Optional[str] = None


class SavedViewOut(BaseModel):
    id: int
    name: str
    description: str
    view_type: str
    filters: str
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Domain Scoring ───────────────────────────────────────────────────────────

class DomainScoreOut(BaseModel):
    domain: str
    score: int


class SubdomainScoreOut(BaseModel):
    subdomain: str
    tier: str
    score: int
