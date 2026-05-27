from fastapi.testclient import TestClient

from app.main import create_app


def test_healthz() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_platform_summary_mentions_ai_agents() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/platform")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product"] == "AfroLete"
    assert any(item["key"] == "ai-agents" for item in payload["capabilities"])

