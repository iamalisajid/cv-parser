"""FastAPI application for the CV Parser API."""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure the project root is importable for existing modules
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from backend.migrate import run_migrations
from backend.routers import auth, export, ingest, skills, sources, stats, views, workers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    run_migrations()
    logger.info("Database tables & migrations ensured.")

    csv_path = Path("output/results.csv")
    if csv_path.is_file():
        from backend.database import SessionLocal, Worker
        db = SessionLocal()
        count = db.query(Worker).count()
        db.close()
        if count == 0:
            logger.info("Database empty -- seeding from %s", csv_path)
            from backend.seed import seed_from_csv
            seed_from_csv(csv_path)

    yield


app = FastAPI(
    title="CV Parser API",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workers.router)
app.include_router(skills.router)
app.include_router(stats.router)
app.include_router(export.router)
app.include_router(ingest.router)
app.include_router(sources.router)
app.include_router(views.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


dist_path = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if dist_path.is_dir():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="frontend")
