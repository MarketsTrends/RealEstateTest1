from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas import CompsResponse, PropertyType
from app.services.comps_service import get_sales_comps
from app.settings import get_settings

router = APIRouter(prefix="", tags=["comps"])


@router.get("/comps/sales", response_model=CompsResponse)
def get_comps_sales(
    lat: float,
    lon: float,
    radius_m: int = Query(default=1000, ge=1),
    months_back: int = Query(default=24, ge=1),
    property_type: PropertyType = PropertyType.unknown,
    surface_m2: float | None = Query(default=None, ge=0),
    surface_tolerance_pct: float = Query(default=0.2, ge=0, le=1),
) -> CompsResponse:
    settings = get_settings()
    return get_sales_comps(
        database_url=settings.database_url,
        lat=lat,
        lon=lon,
        radius_m=radius_m,
        months_back=months_back,
        property_type=property_type,
        surface_m2=surface_m2,
        surface_tolerance_pct=surface_tolerance_pct,
    )
