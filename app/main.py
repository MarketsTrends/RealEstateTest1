from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Query

from app.db.comps_repo import fetch_sales_comps
from app.db.conn import get_connection
from app.engine import ENGINE_VERSION
from app.engine.irr_npv import irr, npv
from app.engine.loan import monthly_payment, remaining_balance
from app.engine.metrics import (
    break_even_occupancy,
    cap_rate,
    cash_on_cash,
    dscr,
    effective_rent_annual,
    gross_rent_annual,
    noi_annual,
)
from app.engine.proforma import build_pro_forma_yearly
from app.engine.scenarios import scenario_inputs
from app.errors import add_exception_handlers
from app.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    CompRecord,
    CompsQuery,
    CompsResponse,
    CompsStats,
    MetaResponse,
    PropertyType,
    ProFormaYear,
    ScenarioResponse,
    rounded_metrics,
)
from app.settings import get_settings

app = FastAPI(title="RealEstate MVP")
add_exception_handlers(app)


def compute_metrics(payload: AnalysisRequest) -> tuple[dict[str, Any], list[str], list[float], list[dict[str, Any]]]:
    warnings: list[str] = []
    acq = payload.acquisition
    inc = payload.income
    exp = payload.expenses
    fin = payload.financing
    exit_data = payload.exit

    total_cost = acq.purchase_price_eur + acq.fees_and_works_eur
    if abs((fin.loan_amount_eur + fin.down_payment_eur) - acq.purchase_price_eur) > 0.01:
        warnings.append("loan_amount_eur + down_payment_eur differs from purchase_price_eur")

    gross = gross_rent_annual(inc.monthly_rent_eur, inc.other_monthly_income_eur)
    effective = effective_rent_annual(gross, inc.vacancy_rate)
    noi = noi_annual(effective, exp.annual_operating_expenses_eur)

    pmt = monthly_payment(fin.loan_amount_eur, fin.interest_rate_annual, fin.term_years)
    annual_debt = pmt * 12
    cashflow = noi - annual_debt

    dscr_value = dscr(noi, annual_debt)
    if dscr_value is None:
        warnings.append("DSCR unavailable because annual debt service is zero")

    break_even = break_even_occupancy(exp.annual_operating_expenses_eur, annual_debt, gross)
    if break_even is None:
        warnings.append("Break-even occupancy unavailable because gross rent is zero")

    sale_price = acq.purchase_price_eur * ((1 + exit_data.appreciation_rate_annual) ** exit_data.hold_years)
    months_paid = min(fin.term_years * 12, exit_data.hold_years * 12)
    loan_balance = remaining_balance(
        fin.loan_amount_eur,
        fin.interest_rate_annual,
        fin.term_years,
        months_paid,
        payment=pmt,
    )
    sale_net = sale_price * (1 - exit_data.sale_cost_rate)
    sale_proceeds_net = sale_net - loan_balance

    cash_invested = fin.down_payment_eur + acq.fees_and_works_eur
    cocr = cash_on_cash(cashflow, cash_invested)

    cashflows = [-cash_invested]
    if exit_data.hold_years > 1:
        cashflows.extend([cashflow] * (exit_data.hold_years - 1))
    cashflows.append(cashflow + sale_proceeds_net)

    irr_value = irr(cashflows)
    if irr_value is None:
        warnings.append("IRR unavailable for given cashflows")

    npv_value = npv(payload.valuation.discount_rate_annual_for_npv, cashflows)

    metrics = {
        "gross_rent_annual_eur": gross,
        "effective_rent_annual_eur": effective,
        "noi_annual_eur": noi,
        "cap_rate_on_purchase_price": cap_rate(noi, acq.purchase_price_eur),
        "cap_rate_on_total_cost": cap_rate(noi, total_cost),
        "loan_payment_monthly_eur": pmt,
        "annual_debt_service_eur": annual_debt,
        "cashflow_annual_eur": cashflow,
        "cashflow_monthly_eur": cashflow / 12,
        "cash_on_cash_return": cocr,
        "dscr": dscr_value,
        "break_even_occupancy": break_even,
        "sale_price_year_n_eur": sale_price,
        "loan_balance_end_of_hold_eur": loan_balance,
        "sale_proceeds_net_eur": sale_proceeds_net,
        "npv_eur": npv_value,
        "irr_annual": irr_value,
    }

    pro_forma = build_pro_forma_yearly(
        purchase_price=acq.purchase_price_eur,
        appreciation_rate_annual=exit_data.appreciation_rate_annual,
        monthly_rent=inc.monthly_rent_eur,
        other_monthly_income=inc.other_monthly_income_eur,
        vacancy_rate=inc.vacancy_rate,
        annual_operating_expenses=exp.annual_operating_expenses_eur,
        loan_amount=fin.loan_amount_eur,
        interest_rate_annual=fin.interest_rate_annual,
        term_years=fin.term_years,
        hold_years=exit_data.hold_years,
    )
    return metrics, warnings, cashflows, pro_forma


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {"app_version": settings.app_version, "engine_version": ENGINE_VERSION}


@app.post("/analysis", response_model=AnalysisResponse)
def analysis(payload: AnalysisRequest) -> AnalysisResponse:
    metrics_base, warnings, _cashflows, pro_forma = compute_metrics(payload)

    scenarios: dict[str, ScenarioResponse] = {}
    for name, (deltas, scenario_payload) in scenario_inputs(payload).items():
        scen_metrics, _, _, _ = compute_metrics(scenario_payload)
        scenarios[name] = ScenarioResponse(deltas=deltas, metrics=rounded_metrics(scen_metrics))

    return AnalysisResponse(
        meta=MetaResponse(
            engine_version=ENGINE_VERSION,
            created_at=datetime.now(timezone.utc),
            warnings=warnings,
        ),
        metrics=rounded_metrics(metrics_base),
        pro_forma_yearly=[
            ProFormaYear(**{k: round(v, 2) if isinstance(v, float) else v for k, v in row.items()})
            for row in pro_forma
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
