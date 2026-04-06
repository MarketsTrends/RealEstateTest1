from app.main import compute_metrics
from app.schemas import AnalysisRequest


def _payload() -> AnalysisRequest:
    return AnalysisRequest(
        property={"property_type": "apartment"},
        acquisition={"purchase_price_eur": 200000, "fees_and_works_eur": 15000},
        income={"monthly_rent_eur": 1350, "vacancy_rate": 0.05},
        expenses={"annual_operating_expenses_eur": 4000},
        financing={
            "down_payment_eur": 40000,
            "loan_amount_eur": 160000,
            "interest_rate_annual": 0.032,
            "term_years": 20,
        },
        exit={"hold_years": 10, "appreciation_rate_annual": 0.02, "sale_cost_rate": 0.06},
        valuation={"discount_rate_annual_for_npv": 0.10},
        model={"cashflow_frequency": "annual", "debt_compounding": "monthly", "rounding": "cent"},
    )


def test_example_case_values() -> None:
    payload = _payload()
    metrics, warnings, _cashflows, _pro_forma = compute_metrics(payload)

    assert warnings == []
    assert metrics["loan_payment_monthly_eur"] == pytest_approx(903.4605276, 1e-7)
    assert metrics["annual_debt_service_eur"] == pytest_approx(10841.5263308, 1e-6)
    assert metrics["gross_rent_annual_eur"] == pytest_approx(16200, 0.01)
    assert metrics["effective_rent_annual_eur"] == pytest_approx(15390, 0.01)
    assert metrics["noi_annual_eur"] == pytest_approx(11390, 0.01)
    assert metrics["cap_rate_on_purchase_price"] == pytest_approx(0.05695, 1e-6)
    assert metrics["cap_rate_on_total_cost"] == pytest_approx(11390 / 215000, 1e-6)
    assert metrics["cashflow_annual_eur"] == pytest_approx(548.4736692, 1e-6)
    assert metrics["cash_on_cash_return"] == pytest_approx(metrics["cashflow_annual_eur"] / 55000, 1e-6)
    assert metrics["dscr"] == pytest_approx(11390 / 10841.5263308, 1e-6)
    assert metrics["break_even_occupancy"] == pytest_approx((4000 + 10841.5263308) / 16200, 1e-6)
    assert metrics["sale_price_year_n_eur"] == pytest_approx(200000 * (1.02**10), 0.01)
    assert metrics["loan_balance_end_of_hold_eur"] == pytest_approx(92675.2721912, 1e-6)
    assert metrics["sale_proceeds_net_eur"] == pytest_approx(
        metrics["sale_price_year_n_eur"] * (1 - 0.06) - metrics["loan_balance_end_of_hold_eur"], 0.01
    )
    assert metrics["irr_annual"] == pytest_approx(0.10203942048, 1e-6)
    assert metrics["npv_eur"] == pytest_approx(995.12625097, 1e-2)


def pytest_approx(value: float, tol: float):
    import pytest

    return pytest.approx(value, abs=tol)
