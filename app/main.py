from __future__ import annotations

from fastapi import FastAPI

from app.api.analysis import router as analysis_router
from app.api.comps import router as comps_router
from app.api.memo import router as memo_router
from app.api.snapshots import router as snapshots_router
from app.api.reports import router as reports_router
from app.engine import ENGINE_VERSION
from app.errors import add_exception_handlers
from app.settings import get_settings

app = FastAPI(title="RealEstate MVP")
add_exception_handlers(app)
app.include_router(analysis_router)
app.include_router(comps_router)
app.include_router(reports_router)
app.include_router(memo_router)
app.include_router(snapshots_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {"app_version": settings.app_version, "engine_version": ENGINE_VERSION}
