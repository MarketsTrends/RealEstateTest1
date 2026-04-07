from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_comps_fallback_when_no_db(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # clear cached settings
    from app.settings import get_settings

    get_settings.cache_clear()

    response = client.get("/comps/sales", params={"lat": 48.8566, "lon": 2.3522})
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False
    assert data["stats"]["n"] == 0
    assert any("DATABASE_URL" in w for w in data["warnings"])
