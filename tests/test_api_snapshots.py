from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import SnapshotResponse, SnapshotSummary

client = TestClient(app)


def base_request_json() -> dict:
    return {
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


def test_analysis_save_endpoint_success(monkeypatch) -> None:
    def fake_save_snapshot(payload, settings):
        return SnapshotSummary(
            id="snap-1",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            title="Saved",
            address_label=None,
            app_version="0.1.0",
            engine_version="0.1.0",
            has_comps=False,
            has_memo=False,
            investment_view=None,
        )

    monkeypatch.setattr("app.api.snapshots.save_snapshot", fake_save_snapshot)

    response = client.post("/analysis/save", json={"request": base_request_json()})
    assert response.status_code == 200
    assert response.json()["id"] == "snap-1"


def test_analysis_get_endpoint_not_found(monkeypatch) -> None:
    from fastapi import HTTPException

    def fake_get_snapshot(snapshot_id, settings):
        raise HTTPException(status_code=404, detail="Snapshot not found")

    monkeypatch.setattr("app.api.snapshots.get_snapshot", fake_get_snapshot)

    response = client.get("/analysis/missing")
    assert response.status_code == 404


def test_analysis_get_endpoint_success(monkeypatch) -> None:
    analysis_body = client.post("/analysis", json=base_request_json()).json()

    def fake_get_snapshot(snapshot_id, settings):
        return SnapshotResponse(
            id="snap-2",
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            title="Saved",
            address_label=None,
            app_version="0.1.0",
            engine_version=analysis_body["meta"]["engine_version"],
            has_comps=False,
            has_memo=False,
            investment_view=None,
            request=base_request_json(),
            analysis=analysis_body,
            comps=None,
            memo=None,
        )

    monkeypatch.setattr("app.api.snapshots.get_snapshot", fake_get_snapshot)

    response = client.get("/analysis/snap-2")
    assert response.status_code == 200
    assert response.json()["analysis"]["metrics"]["noi_annual_eur"] is not None


def test_analyses_list_endpoint_success(monkeypatch) -> None:
    def fake_list_snapshots(settings, limit=20):
        return [
            SnapshotSummary(
                id="snap-3",
                created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
                updated_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
                title="Recent",
                address_label="Paris",
                app_version="0.1.0",
                engine_version="0.1.0",
                has_comps=True,
                has_memo=True,
                investment_view="cautious",
            )
        ]

    monkeypatch.setattr("app.api.snapshots.list_snapshots", fake_list_snapshots)

    response = client.get("/analyses", params={"limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "snap-3"
