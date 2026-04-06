from fastapi import HTTPException

from app.schemas import AnalysisRequest
from app.services import memo_service
from app.settings import Settings


def sample_payload() -> AnalysisRequest:
    return AnalysisRequest(
        property={"property_type": "apartment", "country_code": "FR", "lat": 48.86, "lon": 2.35},
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


def test_generate_memo_raises_503_without_api_key() -> None:
    settings = Settings(
        app_name="x",
        app_version="x",
        database_url=None,
        openai_api_key=None,
        openai_model="gpt-4.1-mini",
    )
    try:
        memo_service.generate_memo(sample_payload(), settings)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 503


def test_memo_context_assembly_with_comps_none() -> None:
    payload = sample_payload()
    analysis = memo_service.run_analysis(payload)
    context = memo_service.build_memo_context(payload, analysis=analysis, comps=None)
    assert context["analysis"]["metrics"]["noi_annual_eur"] is not None
    assert context["comps"] is None


def test_generate_memo_handles_llm_failure(monkeypatch) -> None:
    def fake_call_openai_json(**_: object):
        raise HTTPException(status_code=502, detail="Memo generation failed")

    monkeypatch.setattr(memo_service, "_call_openai_json", fake_call_openai_json)

    settings = Settings(
        app_name="x",
        app_version="x",
        database_url=None,
        openai_api_key="test",
        openai_model="gpt-4.1-mini",
    )
    try:
        memo_service.generate_memo(sample_payload(), settings)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 502


def test_generate_memo_success_with_mocked_llm(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_call_openai_json(*, api_key: str, model: str, context: dict[str, object]) -> dict[str, object]:
        captured["api_key"] = api_key
        captured["model"] = model
        captured["context"] = context
        return {
            "summary": "The deal looks investable but remains sensitive to debt cushion and exit assumptions.",
            "investment_view": "cautious",
            "key_strengths": [
                "Positive annual cash flow on the base case",
                "Clear deterministic underwriting",
                "Relevant Paris comps input is available or checked",
            ],
            "key_risks": [
                "Debt cushion is limited",
                "Exit assumptions matter materially",
                "Operating downside could pressure returns",
            ],
            "sensitivity_points": [
                "Vacancy changes",
                "Interest rate level",
                "Resale pricing",
            ],
            "next_checks": [
                "Verify rent level against market reality",
                "Review building condition and upcoming works",
                "Confirm financing terms with lender",
            ],
            "disclaimer": "This memo is explanatory only and does not recalculate financial outputs.",
        }

    monkeypatch.setattr(memo_service, "_call_openai_json", fake_call_openai_json)

    settings = Settings(
        app_name="x",
        app_version="x",
        database_url=None,
        openai_api_key="test-key",
        openai_model="gpt-4.1-mini",
    )

    result = memo_service.generate_memo(sample_payload(), settings)

    assert result.investment_view == "cautious"
    assert result.summary.startswith("The deal looks investable")
    assert len(result.key_strengths) == 3
    assert len(result.key_risks) == 3
    assert len(result.sensitivity_points) == 3
    assert len(result.next_checks) == 3
    assert "does not recalculate" in result.disclaimer

    context = captured["context"]
    assert isinstance(context, dict)
    assert "analysis" in context
    assert "request" in context
    assert "notes" in context
    assert context["notes"]["pre_tax_only"] is True


def test_memo_endpoint_returns_structured_json_on_success(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    def fake_generate_memo(payload, settings):
        return {
            "summary": "Test summary",
            "investment_view": "balanced",
            "key_strengths": ["A"],
            "key_risks": ["B"],
            "sensitivity_points": ["C"],
            "next_checks": ["D"],
            "disclaimer": "Test disclaimer",
        }

    monkeypatch.setattr("app.api.memo.generate_memo", fake_generate_memo)

    client = TestClient(app)
    response = client.post(
        "/memo",
        json={
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
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["investment_view"] == "balanced"
    assert "summary" in body
    assert "key_strengths" in body
