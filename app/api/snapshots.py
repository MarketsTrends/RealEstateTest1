from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas import SnapshotResponse, SnapshotSaveRequest, SnapshotSummary
from app.services.snapshot_service import get_snapshot, list_snapshots, save_snapshot
from app.settings import get_settings

router = APIRouter(prefix="", tags=["snapshots"])


@router.post("/analysis/save", response_model=SnapshotSummary)
def post_analysis_save(payload: SnapshotSaveRequest) -> SnapshotSummary:
    return save_snapshot(payload, get_settings())


@router.get("/analysis/{snapshot_id}", response_model=SnapshotResponse)
def get_analysis_snapshot(snapshot_id: str) -> SnapshotResponse:
    return get_snapshot(snapshot_id, get_settings())


@router.get("/analyses", response_model=list[SnapshotSummary])
def get_recent_analyses(limit: int = Query(default=20, ge=1, le=100)) -> list[SnapshotSummary]:
    return list_snapshots(get_settings(), limit=limit)
