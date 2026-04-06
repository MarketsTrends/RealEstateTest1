from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.db.conn import get_connection
from app.db.snapshots_repo import fetch_recent_snapshots, fetch_snapshot_by_id, insert_snapshot
from app.schemas import (
    AnalysisResponse,
    SnapshotResponse,
    SnapshotSaveRequest,
    SnapshotSummary,
)
from app.services.analysis_service import run_analysis
from app.settings import Settings


def _default_title(payload: SnapshotSaveRequest) -> str:
    address = payload.request.property.address
    base = address if address else payload.request.property.property_type.value
    date_part = datetime.now(timezone.utc).date().isoformat()
    return f"{base} · {date_part}"


def save_snapshot(payload: SnapshotSaveRequest, settings: Settings) -> SnapshotSummary:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="Snapshot storage unavailable: DATABASE_URL not configured")

    # Product-integrity rule: snapshot analysis is always recomputed from request at save time.
    # This avoids storing mismatched request/output pairs if client-side derived state is stale.
    analysis: AnalysisResponse = run_analysis(payload.request)
    snapshot_id = str(uuid4())
    title = payload.title.strip() if payload.title and payload.title.strip() else _default_title(payload)

    try:
        with get_connection(settings.database_url) as conn:
            inserted = insert_snapshot(
                conn,
                snapshot_id=snapshot_id,
                title=title,
                address_label=payload.request.property.address,
                app_version=settings.app_version,
                engine_version=analysis.meta.engine_version,
                request_payload=payload.request.model_dump(mode="json"),
                analysis_payload=analysis.model_dump(mode="json"),
                comps_payload=payload.comps.model_dump(mode="json") if payload.comps is not None else None,
                memo_payload=payload.memo.model_dump(mode="json") if payload.memo is not None else None,
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Snapshot save failed: {exc}") from exc

    investment_view = payload.memo.investment_view if payload.memo is not None else None
    return SnapshotSummary(
        id=inserted["id"],
        created_at=inserted["created_at"],
        updated_at=inserted["updated_at"],
        title=title,
        address_label=payload.request.property.address,
        app_version=settings.app_version,
        engine_version=analysis.meta.engine_version,
        has_comps=payload.comps is not None,
        has_memo=payload.memo is not None,
        investment_view=investment_view,
    )


def get_snapshot(snapshot_id: str, settings: Settings) -> SnapshotResponse:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="Snapshot storage unavailable: DATABASE_URL not configured")

    try:
        with get_connection(settings.database_url) as conn:
            row = fetch_snapshot_by_id(conn, snapshot_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Snapshot load failed: {exc}") from exc

    if row is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return SnapshotResponse(
        id=row["id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        title=row["title"],
        address_label=row["address_label"],
        app_version=row["app_version"],
        engine_version=row["engine_version"],
        has_comps=row["comps"] is not None,
        has_memo=row["memo"] is not None,
        investment_view=row["memo"]["investment_view"] if row["memo"] is not None else None,
        request=row["request"],
        analysis=row["analysis"],
        comps=row["comps"],
        memo=row["memo"],
    )


def list_snapshots(settings: Settings, limit: int = 20) -> list[SnapshotSummary]:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="Snapshot storage unavailable: DATABASE_URL not configured")

    capped_limit = max(1, min(limit, 100))
    try:
        with get_connection(settings.database_url) as conn:
            rows = fetch_recent_snapshots(conn, capped_limit)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Snapshot list failed: {exc}") from exc

    return [SnapshotSummary(**row) for row in rows]
