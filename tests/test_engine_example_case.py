import pytest

from app.engine.analysis import analyze_financials
from app.schemas import AnalysisRequest


def realistic_fixture() -> AnalysisRequest:
    return AnalysisRequest(
        property={"property_type": "apartment", "country_code": "FR"},
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


def test_realistic_fixture_expected_values() -> None:
    payload = realistic_fixture()
    metrics, warnings, _cashflows, yearly = analyze_financials(payload)

    assert warnings == []
    assert len(yearly) == 10
    assert metrics["loan_payment_monthly_eur"] == pytest.approx(903.4605276, abs=1e-7)
    assert metrics["annual_debt_service_eur"] == pytest.approx(10841.5263308, abs=1e-6)
    assert metrics["gross_rent_annual_eur"] == pytest.approx(16200, abs=0.01)
    assert metrics["effective_rent_annual_eur"] == pytest.approx(15390, abs=0.01)
    assert metrics["noi_annual_eur"] == pytest.approx(11390, abs=0.01)
    assert metrics["cap_rate_on_purchase_price"] == pytest.approx(0.05695, abs=1e-6)
    assert metrics["cap_rate_on_total_cost"] == pytest.approx(11390 / 215000, abs=1e-6)
    assert metrics["cashflow_annual_eur"] == pytest.approx(548.4736692, abs=1e-6)
    assert metrics["cash_on_cash_return"] == pytest.approx(metrics["cashflow_annual_eur"] / 55000, abs=1e-6)
    assert metrics["dscr"] == pytest.approx(11390 / 10841.5263308, abs=1e-6)
    assert metrics["break_even_occupancy"] == pytest.approx((4000 + 10841.5263308) / 16200, abs=1e-6)
    assert metrics["sale_price_year_n_eur"] == pytest.approx(200000 * (1.02**10), abs=0.01)
    assert metrics["loan_balance_end_of_hold_eur"] == pytest.approx(92675.2721912, abs=1e-6)
    assert metrics["sale_proceeds_net_eur"] == pytest.approx(
        metrics["sale_price_year_n_eur"] * (1 - 0.06) - metrics["loan_balance_end_of_hold_eur"],
        abs=0.01,
    )
    assert metrics["irr_annual"] == pytest.approx(0.10203942048, abs=1e-6)
    assert metrics["npv_eur"] == pytest.approx(995.12625097, abs=1e-2)
