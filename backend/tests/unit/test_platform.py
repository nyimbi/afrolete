from app.api.v1.routes.platform import (
    _auth_readiness,
    _authorization_readiness,
    _authorization_resources,
    _keycloak_discovery_details,
    _keycloak_expected_endpoints,
    _openbao_component,
    _parse_host_port,
    _redis_component,
    _safe_url_without_credentials,
    _temporal_component,
)
from app.core.config import Settings


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


def test_auth_readiness_route_is_secret_safe(client) -> None:
    response = client.get("/api/v1/infrastructure/auth-readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] in {"local", "keycloak"}
    assert "openbao_token" not in response.text.lower()
    assert "spicedb_key" not in response.text.lower()


def test_authorization_readiness_route_is_secret_safe(client) -> None:
    response = client.get("/api/v1/infrastructure/authorization-readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] in {"memory", "spicedb"}
    assert payload["relationship_count"] > 0
    assert "spicedb_key" not in response.text.lower()
    assert payload["next_actions"]


def test_authorization_readiness_reports_spicedb_blockers_without_key() -> None:
    readiness = _authorization_readiness(Settings(authz_mode="spicedb", spicedb_key=""))

    assert readiness.provider == "spicedb"
    assert readiness.status == "blocked"
    assert "API key" in readiness.blockers[0]
    assert readiness.relationship_count > readiness.permission_count


def test_authorization_readiness_reports_memory_standby() -> None:
    readiness = _authorization_readiness(Settings(authz_mode="memory"))

    assert readiness.provider == "memory"
    assert readiness.status == "standby"
    assert readiness.resources[0].resource_type == "organization"


def test_authorization_resources_cover_agent_and_incident_scopes() -> None:
    resources = {resource.resource_type: resource for resource in _authorization_resources()}

    assert "analyze" in resources["agent"].permissions
    assert "review_evidence" in resources["safeguarding_incident"].permissions
    assert "guardian" in resources["athlete_profile"].relations


def test_auth_readiness_exposes_keycloak_account_creation_endpoint() -> None:
    settings = Settings(auth_mode="keycloak", keycloak_issuer="https://auth.example.test/realms/lindela")

    readiness = _auth_readiness(settings)
    endpoints = {endpoint.key: endpoint.url for endpoint in readiness.endpoints}

    assert readiness.provider == "keycloak"
    assert readiness.status == "ready_with_warnings"
    assert endpoints["registration"] == "https://auth.example.test/realms/lindela/protocol/openid-connect/registrations"
    assert "self-registration" in readiness.warnings[0]


def test_auth_readiness_marks_local_mode_standby() -> None:
    readiness = _auth_readiness(Settings(auth_mode="local"))

    assert readiness.status == "standby"
    assert readiness.provider == "local"
    assert readiness.endpoints == []


def test_keycloak_discovery_details_are_secret_safe() -> None:
    details = _keycloak_discovery_details(
        {
            "issuer": "https://auth.example.test/realms/lindela",
            "authorization_endpoint": "https://auth.example.test/auth",
            "token_endpoint": "https://auth.example.test/token",
            "jwks_uri": "https://auth.example.test/certs",
        },
        "https://auth.example.test/realms/lindela",
    )

    assert "issuer matched" in details
    assert "token_endpoint discovered" in details
    assert "registration endpoint derived" in details


def test_keycloak_expected_endpoints_are_trimmed() -> None:
    endpoints = _keycloak_expected_endpoints("https://auth.example.test/realms/lindela/")

    assert endpoints[0].url == "https://auth.example.test/realms/lindela/.well-known/openid-configuration"
    assert endpoints[-1].key == "userinfo"


def test_infrastructure_helpers_redact_credentials() -> None:
    assert _safe_url_without_credentials("redis://:secret@localhost:6379/0") == "redis://localhost:6379/0"
    assert _parse_host_port("temporal.lindela.io:7233", 7233) == ("temporal.lindela.io", 7233)


def test_demo_infrastructure_marks_optional_services_as_standby() -> None:
    settings = Settings(env="demo", openbao_token="")

    assert _openbao_component(settings).status == "standby"
    assert _redis_component(settings).status == "standby"
    assert _temporal_component(settings).status == "standby"
