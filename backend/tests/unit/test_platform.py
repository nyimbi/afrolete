from app.api.v1.routes.platform import _parse_host_port, _safe_url_without_credentials


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


def test_infrastructure_status_is_secret_safe(client) -> None:
    response = client.get("/api/v1/infrastructure")

    assert response.status_code == 200
    payload = response.json()
    component_keys = {item["key"] for item in payload["components"]}
    assert {"postgres", "keycloak", "spicedb", "openbao", "object-storage", "redis", "temporal"} <= component_keys
    serialized = response.text.lower()
    assert "spicedb_key" not in serialized
    assert "openbao_token" not in serialized
    assert "secret_key" not in serialized


def test_infrastructure_helpers_redact_credentials() -> None:
    assert _safe_url_without_credentials("redis://:secret@localhost:6379/0") == "redis://localhost:6379/0"
    assert _parse_host_port("temporal.lindela.io:7233", 7233) == ("temporal.lindela.io", 7233)
