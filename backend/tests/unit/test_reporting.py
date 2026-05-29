from app.core.config import Settings
from app.services import reporting as reporting_service


def create_reporting_context(client, identity_headers):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Reporting Intelligence Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Reporting U17",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    member = client.post(
        f"/api/v1/organizations/{organization['id']}/members",
        headers=identity_headers,
        json={
            "email": "reporting-athlete@example.com",
            "display_name": "Reporting Athlete",
            "role": "athlete",
        },
    ).json()
    roster = client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=identity_headers,
        json={
            "person_id": member["subject_id"],
            "role": "player",
            "status": "active",
        },
    ).json()
    return organization, team, roster


def test_reporting_insight_generation_can_use_live_model_provider(
    client,
    identity_headers,
    monkeypatch,
) -> None:
    organization, team, roster = create_reporting_context(client, identity_headers)
    definition = client.post(
        "/api/v1/reporting/definitions",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Performance risk packet",
            "category": "performance",
            "default_format": "online",
            "ai_assisted": True,
        },
    ).json()
    client.post(
        "/api/v1/reporting/reports",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "report_definition_id": definition["id"],
            "team_id": team["id"],
            "title": "Weekly risk review",
            "output_format": "online",
        },
    )
    client.post(
        "/api/v1/reporting/risk-scores",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "athlete_profile_id": roster["athlete_profile_id"],
            "model_name": "local-risk-v1",
            "score": 88,
            "drivers": "Workload spike and low recovery.",
            "recommendation": "Reduce load and notify coach.",
            "valid_for_date": "2026-06-04",
        },
    )
    captured = {}

    async def fake_provider(settings, organization_id, summary, reports, risks, highest_risk, severity, evidence, recommendation):
        captured["mode"] = settings.reporting_insight_generation_mode
        captured["model"] = settings.reporting_insight_generation_model
        captured["organization_id"] = str(organization_id)
        captured["report_count"] = len(reports)
        captured["risk_count"] = len(risks)
        captured["highest_risk"] = highest_risk
        captured["severity"] = severity.value
        captured["evidence"] = evidence
        captured["recommendation"] = recommendation
        captured["summary_reports"] = summary["generated_reports"]
        return {
            "provider": "webhook",
            "model_policy": "report-model-v4",
            "status_code": 200,
            "provider_reference": "insight-provider-456",
            "notes": "Provider generated stakeholder risk insight.",
            "payload": {
                "title": "Provider risk packet review",
                "insight_type": "provider_reporting_review",
                "severity": "critical",
                "confidence": 0.93,
                "evidence": "Provider found report delivery lag and high athlete risk.",
                "recommendation": "Escalate the high-risk athlete and publish the packet.",
                "model_name": "report-model-v4",
                "provider_reference": "insight-provider-456",
            },
        }

    monkeypatch.setattr(
        reporting_service,
        "get_settings",
        lambda: Settings(
            reporting_insight_generation_mode="webhook",
            reporting_insight_generation_model="report-model-v4",
            reporting_insight_generation_webhook_url="https://model.example/reporting",
            reporting_insight_generation_webhook_key="secret",
        ),
    )
    monkeypatch.setattr(reporting_service, "request_reporting_insight_provider", fake_provider)

    response = client.post(
        f"/api/v1/reporting/insights/generate?organization_id={organization['id']}",
        headers=identity_headers,
    )

    assert response.status_code == 201
    insight = response.json()
    assert captured["mode"] == "webhook"
    assert captured["report_count"] == 1
    assert captured["risk_count"] == 1
    assert captured["highest_risk"] == 88
    assert captured["severity"] == "critical"
    assert captured["summary_reports"] == 1
    assert insight["title"] == "Provider risk packet review"
    assert insight["insight_type"] == "provider_reporting_review"
    assert insight["severity"] == "critical"
    assert insight["confidence"] == 0.93
    assert insight["model_name"] == "report-model-v4"
    assert "Provider reference: insight-provider-456" in insight["evidence"]
    assert insight["recommendation"] == "Escalate the high-risk athlete and publish the packet."


def test_reporting_insight_generation_webhook_signature_headers() -> None:
    body = reporting_service.reporting_insight_generation_body(
        {"event": "afrolete.reporting.insight.generate"}
    )
    headers = reporting_service.reporting_insight_generation_headers(
        Settings(reporting_insight_generation_webhook_key="secret"),
        body,
        "secret",
    )

    assert headers["User-Agent"] == "AfroLete-Reporting-Insight/1.0"
    assert headers["X-Afrolete-Reporting-Key-Source"] == "env"
    timestamp = headers["X-Afrolete-Reporting-Timestamp"]
    expected = reporting_service.reporting_insight_generation_signature("secret", timestamp, body)
    assert headers["X-Afrolete-Reporting-Signature"] == expected
