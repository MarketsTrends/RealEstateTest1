import pytest

from app.engine.loan import monthly_payment
from app.main import compute_metrics
from app.schemas import AnalysisRequest


def base_payload() -> AnalysisRequest:
    return AnalysisRequest(
        property={"property_type": "unknown"},
        acquisition={"purchase_price_eur": 100000, "fees_and_works_eur": 10000},
        income={"monthly_rent_eur": 1000, "vacancy_rate": 0.05},
        expenses={"annual_operating_expenses_eur": 2000},
        financing={
            "down_payment_eur": 20000,
            "loan_amount_eur": 80000,
            "interest_rate_annual": 0.03,
            "term_years": 20,
        },
        exit={"hold_years": 5, "appreciation_rate_annual": 0.01, "sale_cost_rate": 0.06},
        valuation={"discount_rate_annual_for_npv": 0.10},
        model={"cashflow_frequency": "annual", "debt_compounding": "monthly", "rounding": "cent"},
    )


def test_zero_rate_payment() -> None:
    assert monthly_payment(120000, 0.0, 20) == pytest.approx(500.0, abs=1e-9)


def test_zero_rent_break_even_warning() -> None:
    payload = base_payload()
    payload.income.monthly_rent_eur = 0
    metrics, warnings, _, _ = compute_metrics(payload)
    assert metrics["break_even_occupancy"] is None
    assert any("Break-even occupancy unavailable" in w for w in warnings)


def test_zero_debt_dscr_warning_and_cashflow_equals_noi() -> None:
    payload = base_payload()
    payload.financing.loan_amount_eur = 0
    payload.financing.down_payment_eur = payload.acquisition.purchase_price_eur
    metrics, warnings, _, _ = compute_metrics(payload)
    assert metrics["dscr"] is None
    assert metrics["cashflow_annual_eur"] == pytest.approx(metrics["noi_annual_eur"], abs=1e-9)
    assert any("DSCR unavailable" in w for w in warnings)


def test_one_year_negative_appreciation() -> None:
    payload = base_payload()
    payload.exit.hold_years = 1
    payload.exit.appreciation_rate_annual = -0.10
    payload.exit.sale_cost_rate = 0.0
    metrics, _, _, _ = compute_metrics(payload)
    assert metrics["sale_price_year_n_eur"] == pytest.approx(90000.0, abs=0.01)


def test_negative_inputs_validation_http_422() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    resp = client.post(
        "/analysis",
        json={
            "property": {"property_type": "unknown"},
            "acquisition": {"purchase_price_eur": -1, "fees_and_works_eur": 0},
            "income": {"monthly_rent_eur": 1000},
            "expenses": {"annual_operating_expenses_eur": 1000},
            "financing": {
                "down_payment_eur": 0,
                "loan_amount_eur": 1000,
                "interest_rate_annual": 0.03,
                "term_years": 20,
            },
            "exit": {"hold_years": 10, "appreciation_rate_annual": 0.02},
            "valuation": {"discount_rate_annual_for_npv": 0.1},
            "model": {"cashflow_frequency": "annual", "debt_compounding": "monthly", "rounding": "cent"},
        },
    )
    assert resp.status_code == 422
