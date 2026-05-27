def test_healthz(client) -> None:
    response = client.get("/api/v1/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_platform_summary_mentions_ai_agents(client) -> None:
    response = client.get("/api/v1/platform")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product"] == "AfroLete"
    assert any(item["key"] == "ai-agents" for item in payload["capabilities"])
