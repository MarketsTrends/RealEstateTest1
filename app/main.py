from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, Query

from app.db.comps_repo import fetch_sales_comps
from app.db.conn import get_connection
from app.engine import ENGINE_VERSION
from app.engine.analysis import analyze_financials
from app.engine.risk_flags import build_risk_flags
from app.engine.scenarios import scenario_inputs
from app.errors import add_exception_handlers
from app.schemas import (
    AnalysisMeta,
    AnalysisRequest,
    AnalysisResponse,
    CompRecord,
    CompsQuery,
    CompsResponse,
    CompsStats,
    PropertyType,
    ScenarioOutput,
    YearlyProjection,
    rounded_metrics,
)
from app.settings import get_settings

app = FastAPI(title="RealEstate MVP")
add_exception_handlers(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {"app_version": settings.app_version, "engine_version": ENGINE_VERSION}


@app.post("/analysis", response_model=AnalysisResponse)
def analysis(payload: AnalysisRequest) -> AnalysisResponse:
    base_metrics, warnings, _cashflows, yearly = analyze_financials(payload)

    risk_flags = build_risk_flags(
        payload,
        dscr_value=base_metrics["dscr"],
        break_even_occupancy_value=base_metrics["break_even_occupancy"],
    )

    scenarios: dict[str, ScenarioOutput] = {}
    for name, (deltas, scenario_payload) in scenario_inputs(payload).items():
        scenario_metrics, _, _, _ = analyze_financials(scenario_payload)
        scenarios[name] = ScenarioOutput(deltas=deltas, metrics=rounded_metrics(scenario_metrics))

    return AnalysisResponse(
        meta=AnalysisMeta(
            engine_version=ENGINE_VERSION,
            created_at=datetime.now(timezone.utc),
            warnings=warnings,
        ),
        metrics=rounded_metrics(base_metrics),
        risk_flags=risk_flags,
        pro_forma_yearly=[
            YearlyProjection(**{k: round(v, 2) if isinstance(v, float) else v for k, v in row.items()})
            for row in yearly
        ],
        scenarios=scenarios,
    )


@app.get("/comps/sales", response_model=CompsResponse)
def comps_sales(
    lat: float,
    lon: float,
    radius_m: int = Query(default=1000, ge=1),
    months_back: int = Query(default=24, ge=1),
    property_type: PropertyType = PropertyType.unknown,
    surface_m2: float | None = Query(default=None, ge=0),
    surface_tolerance_pct: float = Query(default=0.2, ge=0, le=1),
) -> CompsResponse:
    settings = get_settings()
    query = CompsQuery(lat=lat, lon=lon, radius_m=radius_m, months_back=months_back)

    if not settings.database_url:
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
        with get_connection(settings.database_url) as conn:
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
