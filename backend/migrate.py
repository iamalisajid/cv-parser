"""Lightweight schema migrations for the CV Parser database.

Runs idempotent ALTER TABLE statements that SQLAlchemy's create_all() cannot
handle (adding columns to existing tables).  Safe to run repeatedly.
"""

from __future__ import annotations

from sqlalchemy import text

from backend.database import engine, create_tables


MIGRATIONS: list[str] = [
    "ALTER TABLE workers ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES data_sources(id) ON DELETE SET NULL",
]


def run_migrations() -> None:
    create_tables()

    with engine.begin() as conn:
        for ddl in MIGRATIONS:
            conn.execute(text(ddl))

    print("  migrate: done")


if __name__ == "__main__":
    run_migrations()
