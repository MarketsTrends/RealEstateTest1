from __future__ import annotations

from app.schemas import AnalysisRequest


def scenario_inputs(base: AnalysisRequest) -> dict[str, tuple[dict[str, float], AnalysisRequest]]:
    optimistic_deltas = {
        "monthly_rent_pct": 0.05,
        "vacancy_pts": -0.01,
        "interest_rate_pts": -0.005,
        "appreciation_pts": 0.01,
        "operating_expenses_pct": -0.05,
        "sale_cost_pts": -0.01,
    }
    prudent_deltas = {
        "monthly_rent_pct": -0.05,
        "vacancy_pts": 0.02,
        "interest_rate_pts": 0.01,
        "appreciation_pts": -0.01,
        "operating_expenses_pct": 0.08,
        "sale_cost_pts": 0.01,
    }

    opt = base.model_copy(deep=True)
    opt.income.monthly_rent_eur *= 1 + optimistic_deltas["monthly_rent_pct"]
    opt.income.vacancy_rate = max(0.0, min(1.0, opt.income.vacancy_rate + optimistic_deltas["vacancy_pts"]))
    opt.financing.interest_rate_annual = max(
        0.0, opt.financing.interest_rate_annual + optimistic_deltas["interest_rate_pts"]
    )
    opt.exit.appreciation_rate_annual = max(
        -0.5,
        min(0.5, opt.exit.appreciation_rate_annual + optimistic_deltas["appreciation_pts"]),
    )
    opt.expenses.annual_operating_expenses_eur *= 1 + optimistic_deltas["operating_expenses_pct"]
    opt.exit.sale_cost_rate = max(0.0, min(1.0, opt.exit.sale_cost_rate + optimistic_deltas["sale_cost_pts"]))

    pru = base.model_copy(deep=True)
    pru.income.monthly_rent_eur *= 1 + prudent_deltas["monthly_rent_pct"]
    pru.income.vacancy_rate = max(0.0, min(1.0, pru.income.vacancy_rate + prudent_deltas["vacancy_pts"]))
    pru.financing.interest_rate_annual = max(
        0.0, pru.financing.interest_rate_annual + prudent_deltas["interest_rate_pts"]
    )
    pru.exit.appreciation_rate_annual = max(
        -0.5,
        min(0.5, pru.exit.appreciation_rate_annual + prudent_deltas["appreciation_pts"]),
    )
    pru.expenses.annual_operating_expenses_eur *= 1 + prudent_deltas["operating_expenses_pct"]
    pru.exit.sale_cost_rate = max(0.0, min(1.0, pru.exit.sale_cost_rate + prudent_deltas["sale_cost_pts"]))

    return {
        "base": ({}, base),
        "optimistic": (optimistic_deltas, opt),
        "prudent": (prudent_deltas, pru),
    }
