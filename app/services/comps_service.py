from __future__ import annotations

from app.db.comps_repo import fetch_sales_comps
from app.db.conn import get_connection
from app.schemas import CompRecord, CompsQuery, CompsResponse, CompsStats, PropertyType


def get_sales_comps(
    *,
    database_url: str | None,
    lat: float,
    lon: float,
    radius_m: int,
    months_back: int,
    property_type: PropertyType,
    surface_m2: float | None,
    surface_tolerance_pct: float,
) -> CompsResponse:
    query = CompsQuery(lat=lat, lon=lon, radius_m=radius_m, months_back=months_back)

    if not database_url:
        return CompsResponse(
            available=False,
            warnings=["DATABASE_URL not configured; comps unavailable"],
            query=query,
            stats=CompsStats(
                n=0,
                median_price_per_sqm_eur=None,
                p25_price_per_sqm_eur=None,
                p75_price_per_sqm_eur=None,
                median_price_eur=None,
                median_surface_m2=None,
            ),
            comps=[],
        )

    warnings: list[str] = []
    try:
        with get_connection(database_url) as conn:
            stats_raw, comps_raw = fetch_sales_comps(
                conn,
                lat=lat,
                lon=lon,
                radius_m=radius_m,
                months_back=months_back,
                property_type=property_type,
                surface_m2=surface_m2,
                surface_tolerance_pct=surface_tolerance_pct,
            )
    except Exception as exc:
        warnings.append(f"Database unavailable: {exc}")
        return CompsResponse(
            available=False,
            warnings=warnings,
            query=query,
            stats=CompsStats(
                n=0,
                median_price_per_sqm_eur=None,
                p25_price_per_sqm_eur=None,
                p75_price_per_sqm_eur=None,
                median_price_eur=None,
                median_surface_m2=None,
            ),
            comps=[],
        )

    return CompsResponse(
        available=True,
        warnings=warnings,
        query=query,
        stats=CompsStats(
            n=stats_raw["n"],
            median_price_per_sqm_eur=round(stats_raw["median_price_per_sqm_eur"], 2)
            if stats_raw["median_price_per_sqm_eur"] is not None
            else None,
            p25_price_per_sqm_eur=round(stats_raw["p25_price_per_sqm_eur"], 2)
            if stats_raw["p25_price_per_sqm_eur"] is not None
            else None,
            p75_price_per_sqm_eur=round(stats_raw["p75_price_per_sqm_eur"], 2)
            if stats_raw["p75_price_per_sqm_eur"] is not None
            else None,
            median_price_eur=round(stats_raw["median_price_eur"], 2)
            if stats_raw["median_price_eur"] is not None
            else None,
            median_surface_m2=round(stats_raw["median_surface_m2"], 2)
            if stats_raw["median_surface_m2"] is not None
            else None,
        ),
        comps=[
            CompRecord(
                transaction_id=c["transaction_id"],
                sold_at=c["sold_at"],
                price_eur=round(c["price_eur"], 2),
                surface_m2=round(c["surface_m2"], 2) if c["surface_m2"] is not None else None,
                rooms=c["rooms"],
                property_type=c["property_type"],
                distance_m=round(c["distance_m"], 2),
            )
            for c in comps_raw
        ],
    )
