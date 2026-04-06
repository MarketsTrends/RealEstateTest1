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
