from __future__ import annotations

import hmac
import json
import time
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from . import types as t

JsonObject = t.JsonObject
QueryParams = t.QueryParams


class AfroLeteRequestError(RuntimeError):
    def __init__(self, *, status: int, reason: str, body: Any) -> None:
        super().__init__(f"AfroLete request failed with {status} {reason}")
        self.status = status
        self.reason = reason
        self.body = body


def expected_webhook_signature(
    *,
    payload: str | bytes,
    timestamp: str,
    signing_secret: str,
) -> str:
    raw_payload = payload.encode("utf-8") if isinstance(payload, str) else payload
    signing_secret_hash = sha256(signing_secret.encode("utf-8")).hexdigest()
    signed = f"{timestamp}.".encode("utf-8") + raw_payload
    digest = hmac.new(signing_secret_hash.encode("utf-8"), signed, sha256).hexdigest()
    return f"sha256={digest}"


def verify_webhook_signature(
    *,
    payload: str | bytes,
    timestamp: str,
    signature: str,
    signing_secret: str,
    tolerance_seconds: int | None = 300,
    now: float | None = None,
) -> bool:
    if tolerance_seconds is not None:
        try:
            timestamp_seconds = int(timestamp)
        except ValueError:
            return False
        current_seconds = time.time() if now is None else now
        if abs(current_seconds - timestamp_seconds) > tolerance_seconds:
            return False
    expected = expected_webhook_signature(
        payload=payload,
        timestamp=timestamp,
        signing_secret=signing_secret,
    )
    return hmac.compare_digest(signature.strip(), expected)


@dataclass(frozen=True)
class _OrganizationResource:
    client: AfroLeteClient

    def get(self, *, organization_id: str) -> t.Organization:
        return self.client.request("GET", "/organization", query={"organization_id": organization_id})


@dataclass(frozen=True)
class _PeopleResource:
    client: AfroLeteClient

    def create(self, payload: t.PersonCreate) -> t.Person:
        return self.client.request("POST", "/people", body=payload)

    def link_guardian(
        self,
        athlete_person_id: str,
        payload: t.GuardianLinkCreate,
    ) -> t.GuardianRelationship:
        return self.client.request(
            "POST",
            f"/people/{athlete_person_id}/guardians",
            body=payload,
        )

    def create_consent_request(
        self,
        athlete_person_id: str,
        payload: t.ConsentRequestCreate,
    ) -> t.ConsentRequest:
        return self.client.request(
            "POST",
            f"/people/{athlete_person_id}/consent-requests",
            body=payload,
        )


@dataclass(frozen=True)
class _TeamsResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str) -> list[t.Team]:
        return self.client.request("GET", "/teams", query={"organization_id": organization_id})

    def create(self, payload: t.TeamCreate) -> t.Team:
        return self.client.request("POST", "/teams", body=payload)

    def add_member(self, team_id: str, payload: t.TeamMemberAdd) -> t.TeamRosterEntry:
        return self.client.request("POST", f"/teams/{team_id}/members", body=payload)


@dataclass(frozen=True)
class _EventsResource:
    client: AfroLeteClient
    attendance: _EventAttendanceResource

    def list(self, *, organization_id: str, team_id: str | None = None) -> list[t.Event]:
        return self.client.request(
            "GET",
            "/events",
            query={"organization_id": organization_id, "team_id": team_id},
        )

    def create(self, payload: t.EventCreate) -> t.Event:
        return self.client.request("POST", "/events", body=payload)


@dataclass(frozen=True)
class _EventAttendanceResource:
    client: AfroLeteClient

    def list(self, event_id: str, *, organization_id: str) -> list[t.AttendanceRecord]:
        return self.client.request(
            "GET",
            f"/events/{event_id}/attendance",
            query={"organization_id": organization_id},
        )

    def record(
        self,
        event_id: str,
        *,
        organization_id: str,
        payload: t.AttendanceRecordUpsert,
    ) -> t.AttendanceRecord:
        return self.client.request(
            "POST",
            f"/events/{event_id}/attendance",
            query={"organization_id": organization_id},
            body=payload,
        )


@dataclass(frozen=True)
class _AgentTasksResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str, agent_id: str | None = None) -> list[t.AgentTask]:
        return self.client.request(
            "GET",
            "/agents/tasks",
            query={"organization_id": organization_id, "agent_id": agent_id},
        )

    def queue(self, agent_id: str, payload: t.AgentTaskCreate) -> t.AgentTask:
        return self.client.request("POST", f"/agents/{agent_id}/tasks", body=payload)


@dataclass(frozen=True)
class _AgentsResource:
    client: AfroLeteClient
    tasks: _AgentTasksResource

    def list(self, *, organization_id: str) -> list[t.Agent]:
        return self.client.request("GET", "/agents", query={"organization_id": organization_id})


@dataclass(frozen=True)
class _CommunicationTemplatesResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str) -> list[t.CommunicationTemplate]:
        return self.client.request(
            "GET",
            "/communications/templates",
            query={"organization_id": organization_id},
        )

    def create(self, payload: t.CommunicationTemplateCreate) -> t.CommunicationTemplate:
        return self.client.request("POST", "/communications/templates", body=payload)


@dataclass(frozen=True)
class _CommunicationMessagesResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str) -> list[t.CommunicationMessage]:
        return self.client.request(
            "GET",
            "/communications/messages",
            query={"organization_id": organization_id},
        )

    def create(self, payload: t.CommunicationMessageCreate) -> t.CommunicationMessage:
        return self.client.request("POST", "/communications/messages", body=payload)

    def recipients(self, message_id: str, *, organization_id: str) -> list[t.MessageRecipient]:
        return self.client.request(
            "GET",
            f"/communications/messages/{message_id}/recipients",
            query={"organization_id": organization_id},
        )

    def dispatch(self, message_id: str, *, organization_id: str) -> t.CommunicationDispatchSummary:
        return self.client.request(
            "POST",
            f"/communications/messages/{message_id}/dispatch",
            query={"organization_id": organization_id},
        )


@dataclass(frozen=True)
class _CommunicationsResource:
    templates: _CommunicationTemplatesResource
    messages: _CommunicationMessagesResource


@dataclass(frozen=True)
class _BillingPlansResource:
    client: AfroLeteClient

    def list(self) -> list[t.BillingPlan]:
        return self.client.request("GET", "/billing/plans")


@dataclass(frozen=True)
class _BillingSubscriptionsResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str) -> list[t.BillingSubscription]:
        return self.client.request(
            "GET",
            "/billing/subscriptions",
            query={"organization_id": organization_id},
        )


@dataclass(frozen=True)
class _BillingMetersResource:
    client: AfroLeteClient

    def list(self) -> list[t.BillingUsageMeter]:
        return self.client.request("GET", "/billing/meters")


@dataclass(frozen=True)
class _BillingUsageResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str) -> list[t.BillingUsageRecord]:
        return self.client.request(
            "GET",
            "/billing/usage",
            query={"organization_id": organization_id},
        )

    def record(self, payload: t.BillingUsageRecordCreate) -> t.BillingUsageRecord:
        return self.client.request("POST", "/billing/usage", body=payload)


@dataclass(frozen=True)
class _BillingInvoicesResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str) -> list[t.BillingInvoice]:
        return self.client.request(
            "GET",
            "/billing/invoices",
            query={"organization_id": organization_id},
        )


@dataclass(frozen=True)
class _BillingEntitlementsResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str) -> list[t.BillingEntitlement]:
        return self.client.request(
            "GET",
            "/billing/entitlements",
            query={"organization_id": organization_id},
        )


@dataclass(frozen=True)
class _BillingSummaryResource:
    client: AfroLeteClient

    def get(self, *, organization_id: str) -> t.BillingSummary:
        return self.client.request(
            "GET",
            "/billing/summary",
            query={"organization_id": organization_id},
        )


@dataclass(frozen=True)
class _BillingResource:
    plans: _BillingPlansResource
    subscriptions: _BillingSubscriptionsResource
    meters: _BillingMetersResource
    usage: _BillingUsageResource
    invoices: _BillingInvoicesResource
    entitlements: _BillingEntitlementsResource
    summary: _BillingSummaryResource


@dataclass(frozen=True)
class _TrainingDrillsResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str, sport: str | None = None) -> list[t.TrainingDrill]:
        return self.client.request(
            "GET",
            "/training/drills",
            query={"organization_id": organization_id, "sport": sport},
        )

    def create(self, payload: t.TrainingDrillCreate) -> t.TrainingDrill:
        return self.client.request("POST", "/training/drills", body=payload)


@dataclass(frozen=True)
class _TrainingPlanItemsResource:
    client: AfroLeteClient

    def list(self, plan_id: str, *, organization_id: str) -> list[t.TrainingPlanItem]:
        return self.client.request(
            "GET",
            f"/training/plans/{plan_id}/items",
            query={"organization_id": organization_id},
        )

    def add(
        self,
        plan_id: str,
        *,
        organization_id: str,
        payload: t.TrainingPlanItemCreate,
    ) -> t.TrainingPlanItem:
        return self.client.request(
            "POST",
            f"/training/plans/{plan_id}/items",
            query={"organization_id": organization_id},
            body=payload,
        )


@dataclass(frozen=True)
class _TrainingPlansResource:
    client: AfroLeteClient
    items: _TrainingPlanItemsResource

    def list(
        self,
        *,
        organization_id: str,
        team_id: str | None = None,
        athlete_profile_id: str | None = None,
    ) -> list[t.TrainingPlan]:
        return self.client.request(
            "GET",
            "/training/plans",
            query={
                "organization_id": organization_id,
                "team_id": team_id,
                "athlete_profile_id": athlete_profile_id,
            },
        )

    def create(self, payload: t.TrainingPlanCreate) -> t.TrainingPlan:
        return self.client.request("POST", "/training/plans", body=payload)


@dataclass(frozen=True)
class _TrainingSessionFeedbackResource:
    client: AfroLeteClient

    def list(self, session_plan_id: str, *, organization_id: str) -> list[t.TrainingSessionFeedback]:
        return self.client.request(
            "GET",
            f"/training/sessions/{session_plan_id}/feedback",
            query={"organization_id": organization_id},
        )

    def record(
        self,
        session_plan_id: str,
        *,
        organization_id: str,
        payload: t.TrainingSessionFeedbackCreate,
    ) -> t.TrainingSessionFeedback:
        return self.client.request(
            "POST",
            f"/training/sessions/{session_plan_id}/feedback",
            query={"organization_id": organization_id},
            body=payload,
        )


@dataclass(frozen=True)
class _TrainingSessionsResource:
    client: AfroLeteClient
    feedback: _TrainingSessionFeedbackResource

    def list(self, *, organization_id: str, team_id: str | None = None) -> list[t.TrainingSession]:
        return self.client.request(
            "GET",
            "/training/sessions",
            query={"organization_id": organization_id, "team_id": team_id},
        )

    def create(self, payload: t.TrainingSessionCreate) -> t.TrainingSession:
        return self.client.request("POST", "/training/sessions", body=payload)


@dataclass(frozen=True)
class _TrainingAvailabilityResource:
    client: AfroLeteClient

    def suggest(self, payload: t.TrainingAvailabilityCreate) -> t.TrainingAvailability:
        return self.client.request("POST", "/training/availability", body=payload)


@dataclass(frozen=True)
class _TrainingCalendarResource:
    client: AfroLeteClient

    def export(
        self,
        *,
        organization_id: str,
        team_id: str | None = None,
        starts_at: str | None = None,
        ends_at: str | None = None,
    ) -> t.TrainingCalendarArtifact:
        return self.client.request(
            "GET",
            "/training/calendar-artifact",
            query={
                "organization_id": organization_id,
                "team_id": team_id,
                "starts_at": starts_at,
                "ends_at": ends_at,
            },
        )


@dataclass(frozen=True)
class _TrainingResource:
    drills: _TrainingDrillsResource
    plans: _TrainingPlansResource
    sessions: _TrainingSessionsResource
    availability: _TrainingAvailabilityResource
    calendar: _TrainingCalendarResource


@dataclass(frozen=True)
class _PerformanceMetricsResource:
    client: AfroLeteClient

    def list(
        self,
        *,
        organization_id: str,
        sport: str | None = None,
    ) -> list[t.PerformanceMetricDefinition]:
        return self.client.request(
            "GET",
            "/performance/metrics",
            query={"organization_id": organization_id, "sport": sport},
        )


@dataclass(frozen=True)
class _PerformanceObservationsResource:
    client: AfroLeteClient

    def list(self, athlete_profile_id: str, *, organization_id: str) -> list[t.PerformanceObservation]:
        return self.client.request(
            "GET",
            f"/performance/athletes/{athlete_profile_id}/observations",
            query={"organization_id": organization_id},
        )

    def create(
        self,
        athlete_profile_id: str,
        payload: t.PerformanceObservationCreate,
    ) -> t.PerformanceObservation:
        return self.client.request(
            "POST",
            f"/performance/athletes/{athlete_profile_id}/observations",
            body=payload,
        )


@dataclass(frozen=True)
class _PerformanceResource:
    metrics: _PerformanceMetricsResource
    observations: _PerformanceObservationsResource


class AfroLeteClient:
    def __init__(self, *, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.organization = _OrganizationResource(self)
        self.people = _PeopleResource(self)
        self.teams = _TeamsResource(self)
        self.events = _EventsResource(self, attendance=_EventAttendanceResource(self))
        self.agents = _AgentsResource(self, tasks=_AgentTasksResource(self))
        self.communications = _CommunicationsResource(
            templates=_CommunicationTemplatesResource(self),
            messages=_CommunicationMessagesResource(self),
        )
        self.billing = _BillingResource(
            plans=_BillingPlansResource(self),
            subscriptions=_BillingSubscriptionsResource(self),
            meters=_BillingMetersResource(self),
            usage=_BillingUsageResource(self),
            invoices=_BillingInvoicesResource(self),
            entitlements=_BillingEntitlementsResource(self),
            summary=_BillingSummaryResource(self),
        )
        self.training = _TrainingResource(
            drills=_TrainingDrillsResource(self),
            plans=_TrainingPlansResource(self, items=_TrainingPlanItemsResource(self)),
            sessions=_TrainingSessionsResource(
                self,
                feedback=_TrainingSessionFeedbackResource(self),
            ),
            availability=_TrainingAvailabilityResource(self),
            calendar=_TrainingCalendarResource(self),
        )
        self.performance = _PerformanceResource(
            metrics=_PerformanceMetricsResource(self),
            observations=_PerformanceObservationsResource(self),
        )

    def me(self) -> t.DeveloperApiKeyInspection:
        return self.request("GET", "/me")

    def request(
        self,
        method: str,
        path: str,
        *,
        query: QueryParams | None = None,
        body: JsonObject | None = None,
    ) -> Any:
        url = f"{self.base_url}/api/v1/sdk{path}"
        if query:
            encoded_query = urlencode(
                {
                    key: str(value)
                    for key, value in query.items()
                    if value is not None
                }
            )
            if encoded_query:
                url = f"{url}?{encoded_query}"

        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "X-Afrolete-API-Key": self.api_key,
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"

        request = Request(url, data=payload, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return _decode_response(response.read())
        except HTTPError as error:
            raise AfroLeteRequestError(
                status=error.code,
                reason=error.reason,
                body=_decode_response(error.read()),
            ) from error


def _decode_response(raw_body: bytes) -> Any:
    if not raw_body:
        return None
    text = raw_body.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text
