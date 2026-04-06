from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import HTTPException

from app.schemas import AnalysisRequest, SnapshotSaveRequest
from app.services import snapshot_service
from app.services.analysis_service import run_analysis
from app.settings import Settings


def sample_request() -> AnalysisRequest:
    return AnalysisRequest(
        property={"property_type": "apartment", "country_code": "FR", "address": "Paris 11e"},
        acquisition={"purchase_price_eur": 200000, "fees_and_works_eur": 15000},
        income={"monthly_rent_eur": 1350, "other_monthly_income_eur": 0, "vacancy_rate": 0.05},
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


@contextmanager
def fake_conn_ctx(_db_url: str):
    yield object()


def test_save_snapshot_success_when_analysis_omitted(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_insert_snapshot(conn, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {
            "id": kwargs["snapshot_id"],
            "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }

    monkeypatch.setattr(snapshot_service, "get_connection", fake_conn_ctx)
    monkeypatch.setattr(snapshot_service, "insert_snapshot", fake_insert_snapshot)

    settings = Settings("x", "0.1.0", "postgresql://test", None, "gpt-4.1-mini")
    payload = SnapshotSaveRequest(request=sample_request(), analysis=None, comps=None, memo=None, title=None)

    result = snapshot_service.save_snapshot(payload, settings)

    assert result.id
    assert result.has_comps is False
    assert result.has_memo is False
    assert captured["analysis_payload"] is not None
    assert captured["title"].startswith("Paris 11e")


def test_save_snapshot_stores_null_optional_payloads(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_insert_snapshot(conn, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {
            "id": kwargs["snapshot_id"],
            "created_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
        }

    monkeypatch.setattr(snapshot_service, "get_connection", fake_conn_ctx)
    monkeypatch.setattr(snapshot_service, "insert_snapshot", fake_insert_snapshot)

    settings = Settings("x", "0.1.0", "postgresql://test", None, "gpt-4.1-mini")
    req = sample_request()
    payload = SnapshotSaveRequest(request=req, analysis=run_analysis(req), comps=None, memo=None, title="Deal A")

    result = snapshot_service.save_snapshot(payload, settings)

    assert result.title == "Deal A"
    assert captured["comps_payload"] is None
    assert captured["memo_payload"] is None


def test_save_snapshot_recomputes_analysis_even_if_provided(monkeypatch) -> None:
    captured: dict[str, object] = {}
    req = sample_request()
    computed = run_analysis(req)

    def fake_insert_snapshot(conn, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {
            "id": kwargs["snapshot_id"],
            "created_at": datetime(2026, 1, 6, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 1, 6, tzinfo=timezone.utc),
        }

    def fake_run_analysis(payload):  # type: ignore[no-untyped-def]
        return computed

    monkeypatch.setattr(snapshot_service, "get_connection", fake_conn_ctx)
    monkeypatch.setattr(snapshot_service, "insert_snapshot", fake_insert_snapshot)
    monkeypatch.setattr(snapshot_service, "run_analysis", fake_run_analysis)

    settings = Settings("x", "0.1.0", "postgresql://test", None, "gpt-4.1-mini")
    payload = SnapshotSaveRequest(request=req, analysis=run_analysis(req), comps=None, memo=None, title="Deal B")

    snapshot_service.save_snapshot(payload, settings)

    assert captured["analysis_payload"]["meta"]["engine_version"] == computed.meta.engine_version


def test_get_snapshot_success(monkeypatch) -> None:
    req = sample_request()
    analysis = run_analysis(req)

    def fake_fetch_snapshot_by_id(conn, snapshot_id: str):  # type: ignore[no-untyped-def]
        assert snapshot_id == "abc"
        return {
            "id": "abc",
            "created_at": datetime(2026, 1, 3, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 1, 3, tzinfo=timezone.utc),
            "title": "Saved deal",
            "address_label": "Paris 11e",
            "app_version": "0.1.0",
            "engine_version": analysis.meta.engine_version,
            "request": req.model_dump(mode="json"),
            "analysis": analysis.model_dump(mode="json"),
            "comps": None,
            "memo": None,
        }

    monkeypatch.setattr(snapshot_service, "get_connection", fake_conn_ctx)
    monkeypatch.setattr(snapshot_service, "fetch_snapshot_by_id", fake_fetch_snapshot_by_id)

    settings = Settings("x", "0.1.0", "postgresql://test", None, "gpt-4.1-mini")
    result = snapshot_service.get_snapshot("abc", settings)

    assert result.id == "abc"
    assert result.analysis.metrics.noi_annual_eur is not None


def test_get_snapshot_not_found(monkeypatch) -> None:
    def fake_fetch_snapshot_by_id(conn, snapshot_id: str):  # type: ignore[no-untyped-def]
        return None

    monkeypatch.setattr(snapshot_service, "get_connection", fake_conn_ctx)
    monkeypatch.setattr(snapshot_service, "fetch_snapshot_by_id", fake_fetch_snapshot_by_id)

    settings = Settings("x", "0.1.0", "postgresql://test", None, "gpt-4.1-mini")
    try:
        snapshot_service.get_snapshot("missing", settings)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404


def test_list_snapshots_recent(monkeypatch) -> None:
    def fake_fetch_recent_snapshots(conn, limit: int):  # type: ignore[no-untyped-def]
        assert limit == 2
        return [
            {
                "id": "a",
                "created_at": datetime(2026, 1, 5, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 1, 5, tzinfo=timezone.utc),
                "title": "A",
                "address_label": None,
                "app_version": "0.1.0",
                "engine_version": "0.1.0",
                "has_comps": False,
                "has_memo": True,
                "investment_view": "balanced",
            }
        ]

    monkeypatch.setattr(snapshot_service, "get_connection", fake_conn_ctx)
    monkeypatch.setattr(snapshot_service, "fetch_recent_snapshots", fake_fetch_recent_snapshots)

    settings = Settings("x", "0.1.0", "postgresql://test", None, "gpt-4.1-mini")
    rows = snapshot_service.list_snapshots(settings, limit=2)

    assert len(rows) == 1
    assert rows[0].id == "a"
