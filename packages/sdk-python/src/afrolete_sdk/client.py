from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

JsonObject = dict[str, Any]
QueryParams = dict[str, str | int | float | bool | None]


class AfroLeteRequestError(RuntimeError):
    def __init__(self, *, status: int, reason: str, body: Any) -> None:
        super().__init__(f"AfroLete request failed with {status} {reason}")
        self.status = status
        self.reason = reason
        self.body = body


@dataclass(frozen=True)
class _OrganizationResource:
    client: AfroLeteClient

    def get(self, *, organization_id: str) -> JsonObject:
        return self.client.request("GET", "/organization", query={"organization_id": organization_id})


@dataclass(frozen=True)
class _PeopleResource:
    client: AfroLeteClient

    def create(self, payload: JsonObject) -> JsonObject:
        return self.client.request("POST", "/people", body=payload)

    def link_guardian(self, athlete_person_id: str, payload: JsonObject) -> JsonObject:
        return self.client.request(
            "POST",
            f"/people/{athlete_person_id}/guardians",
            body=payload,
        )

    def create_consent_request(self, athlete_person_id: str, payload: JsonObject) -> JsonObject:
        return self.client.request(
            "POST",
            f"/people/{athlete_person_id}/consent-requests",
            body=payload,
        )


@dataclass(frozen=True)
class _TeamsResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str) -> list[JsonObject]:
        return self.client.request("GET", "/teams", query={"organization_id": organization_id})

    def create(self, payload: JsonObject) -> JsonObject:
        return self.client.request("POST", "/teams", body=payload)

    def add_member(self, team_id: str, payload: JsonObject) -> JsonObject:
        return self.client.request("POST", f"/teams/{team_id}/members", body=payload)


@dataclass(frozen=True)
class _EventsResource:
    client: AfroLeteClient
    attendance: _EventAttendanceResource

    def list(self, *, organization_id: str, team_id: str | None = None) -> list[JsonObject]:
        return self.client.request(
            "GET",
            "/events",
            query={"organization_id": organization_id, "team_id": team_id},
        )

    def create(self, payload: JsonObject) -> JsonObject:
        return self.client.request("POST", "/events", body=payload)


@dataclass(frozen=True)
class _EventAttendanceResource:
    client: AfroLeteClient

    def list(self, event_id: str, *, organization_id: str) -> list[JsonObject]:
        return self.client.request(
            "GET",
            f"/events/{event_id}/attendance",
            query={"organization_id": organization_id},
        )

    def record(self, event_id: str, *, organization_id: str, payload: JsonObject) -> JsonObject:
        return self.client.request(
            "POST",
            f"/events/{event_id}/attendance",
            query={"organization_id": organization_id},
            body=payload,
        )


@dataclass(frozen=True)
class _TrainingDrillsResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str, sport: str | None = None) -> list[JsonObject]:
        return self.client.request(
            "GET",
            "/training/drills",
            query={"organization_id": organization_id, "sport": sport},
        )

    def create(self, payload: JsonObject) -> JsonObject:
        return self.client.request("POST", "/training/drills", body=payload)


@dataclass(frozen=True)
class _TrainingResource:
    drills: _TrainingDrillsResource


@dataclass(frozen=True)
class _PerformanceMetricsResource:
    client: AfroLeteClient

    def list(self, *, organization_id: str, sport: str | None = None) -> list[JsonObject]:
        return self.client.request(
            "GET",
            "/performance/metrics",
            query={"organization_id": organization_id, "sport": sport},
        )


@dataclass(frozen=True)
class _PerformanceObservationsResource:
    client: AfroLeteClient

    def list(self, athlete_profile_id: str, *, organization_id: str) -> list[JsonObject]:
        return self.client.request(
            "GET",
            f"/performance/athletes/{athlete_profile_id}/observations",
            query={"organization_id": organization_id},
        )

    def create(self, athlete_profile_id: str, payload: JsonObject) -> JsonObject:
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
        self.training = _TrainingResource(drills=_TrainingDrillsResource(self))
        self.performance = _PerformanceResource(
            metrics=_PerformanceMetricsResource(self),
            observations=_PerformanceObservationsResource(self),
        )

    def me(self) -> JsonObject:
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
