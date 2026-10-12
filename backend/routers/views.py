"""Saved views CRUD endpoints."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api_schemas import SavedViewCreate, SavedViewOut, SavedViewUpdate
from backend.database import SavedView, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/views", tags=["views"])


@router.get("", response_model=list[SavedViewOut])
def list_views(
    view_type: str = Query("", description="Filter by type: workers, query"),
    db: Session = Depends(get_db),
) -> list[SavedViewOut]:
    q = db.query(SavedView)
    if view_type:
        q = q.filter(SavedView.view_type == view_type)
    views = q.order_by(SavedView.updated_at.desc()).all()
    return [SavedViewOut.model_validate(v) for v in views]


@router.post("", response_model=SavedViewOut, status_code=201)
def create_view(
    body: SavedViewCreate,
    db: Session = Depends(get_db),
) -> SavedViewOut:
    try:
        json.loads(body.filters)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="filters must be valid JSON")

    if body.view_type not in ("workers", "query"):
        raise HTTPException(status_code=400, detail="view_type must be 'workers' or 'query'")

    view = SavedView(
        name=body.name,
        description=body.description,
        view_type=body.view_type,
        filters=body.filters,
    )
    db.add(view)
    db.commit()
    db.refresh(view)
    return SavedViewOut.model_validate(view)


@router.get("/{view_id}", response_model=SavedViewOut)
def get_view(view_id: int, db: Session = Depends(get_db)) -> SavedViewOut:
    view = db.query(SavedView).filter(SavedView.id == view_id).first()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")
    return SavedViewOut.model_validate(view)


@router.put("/{view_id}", response_model=SavedViewOut)
def update_view(
    view_id: int,
    body: SavedViewUpdate,
    db: Session = Depends(get_db),
) -> SavedViewOut:
    view = db.query(SavedView).filter(SavedView.id == view_id).first()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")

    if body.name is not None:
        view.name = body.name
    if body.description is not None:
        view.description = body.description
    if body.filters is not None:
        try:
            json.loads(body.filters)
        except (json.JSONDecodeError, TypeError):
            raise HTTPException(status_code=400, detail="filters must be valid JSON")
        view.filters = body.filters

    view.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(view)
    return SavedViewOut.model_validate(view)


@router.delete("/{view_id}", status_code=204)
def delete_view(view_id: int, db: Session = Depends(get_db)):
    view = db.query(SavedView).filter(SavedView.id == view_id).first()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")
    db.delete(view)
    db.commit()
