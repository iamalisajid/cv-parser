"""SQLAlchemy models and engine configuration for the CV Parser API."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cvparser:cvparser@localhost:5433/cvparser",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    sheet_url = Column(Text, nullable=False)
    sheet_id = Column(String(255), nullable=False)
    gid = Column(String(100), default="0")
    tab_name = Column(String(255), default="")
    created_by = Column(String(255), default="")
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    worker_count = Column(Integer, default=0)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, default="")
    email = Column(String(255), unique=True, nullable=False, index=True)
    location = Column(String(255), default="")
    education_level = Column(String(100), default="")
    education_field = Column(String(255), default="")
    years_of_experience = Column(Integer, nullable=True)
    domain_expertise_rating = Column(Integer, nullable=True)
    overall_score = Column(Integer, nullable=True)
    summary = Column(Text, default="")
    reasoning = Column(Text, default="")
    cv_url = Column(Text, default="")
    status = Column(String(50), default="pending", index=True)
    source_id = Column(
        Integer, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    skills = relationship(
        "Skill", back_populates="worker", cascade="all, delete-orphan"
    )
    source = relationship("DataSource")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(
        Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False
    )
    category = Column(String(255), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    proficiency = Column(String(50), nullable=False, index=True)
    context = Column(String(50), default="professional")

    worker = relationship("Worker", back_populates="skills")


class SavedView(Base):
    __tablename__ = "saved_views"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    view_type = Column(String(50), nullable=False)
    filters = Column(Text, nullable=False)
    created_by = Column(String(255), default="")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


Index("ix_skills_category_skill", Skill.category, Skill.skill_name)
Index("ix_skills_worker_category", Skill.worker_id, Skill.category)


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:  # type: ignore[misc]
    db = SessionLocal()
    try:
        yield db  # type: ignore[misc]
    finally:
        db.close()
