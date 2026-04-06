from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analysis_endpoint_success() -> None:
    payload = {
        "property": {"property_type": "apartment", "country_code": "FR"},
        "acquisition": {"purchase_price_eur": 200000, "fees_and_works_eur": 15000},
        "income": {"monthly_rent_eur": 1350, "other_monthly_income_eur": 0, "vacancy_rate": 0.05},
        "expenses": {"annual_operating_expenses_eur": 4000},
        "financing": {
            "down_payment_eur": 40000,
            "loan_amount_eur": 160000,
            "interest_rate_annual": 0.032,
            "term_years": 20,
        },
        "exit": {"hold_years": 10, "appreciation_rate_annual": 0.02, "sale_cost_rate": 0.06},
        "valuation": {"discount_rate_annual_for_npv": 0.10},
        "model": {"cashflow_frequency": "annual", "debt_compounding": "monthly", "rounding": "cent"},
    }
    response = client.post("/analysis", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["gross_rent_annual_eur"] == 16200.0
    assert "created_at" in data["meta"]
    assert set(data["scenarios"].keys()) == {"base", "optimistic", "prudent"}


def test_health_and_version() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    version_resp = client.get("/version")
    assert version_resp.status_code == 200
    assert "app_version" in version_resp.json()
