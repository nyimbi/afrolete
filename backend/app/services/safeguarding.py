import base64
import hmac
import io
import time
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from secrets import token_urlsafe
from urllib.parse import quote
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.enums import (
    AttendanceStatus,
    BackgroundCheckStatus,
    ComplianceCredentialStatus,
    ConsentCaptureChannel,
    ConsentRequestStatus,
    ConsentScopeType,
    ConsentStatus,
    IncidentReportPackageStatus,
    InsuranceClaimStatus,
    MedicalClearanceStatus,
    ParticipationClearanceStatus,
    SafeguardingIncidentType,
    SafeguardingIncidentStatus,
)
from app.models.event import (
    ActivityConsent,
    AttendanceRecord,
    BackgroundCheck,
    ComplianceCredential,
    ConsentRequest,
    Event,
    IncidentInsuranceClaim,
    IncidentMedicalClearance,
    IncidentReportPackage,
    SafeguardingIncident,
)
from app.models.identity import Person
from app.models.organization import Organization
from app.models.performance import PerformanceAchievementAward, PerformanceGoal
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry
from app.schemas.safeguarding import (
    ActivityConsentCreate,
    BackgroundCheckCreate,
    BackgroundCheckProviderResultCreate,
    BackgroundCheckProviderResultRead,
    BackgroundCheckUpdate,
    ComplianceQueueItemRead,
    ComplianceReconciliationRead,
    ComplianceReconciliationWorkerRunRead,
    ComplianceCredentialCreate,
    ComplianceSummaryRead,
    ComplianceCredentialUpdate,
    ConsentRequestCreate,
    FamilyAthleteSummaryRead,
    FamilyConsentRequestRead,
    FamilyConsentResponseCreate,
    FamilyEventSummaryRead,
    FamilyEventRsvpCreate,
    FamilyPerformanceAwardRead,
    FamilyPerformanceGoalRead,
    FamilyPerformanceSummaryRead,
    GuardianRelationshipCreate,
    IncidentReportPackageArtifactLinkRead,
    IncidentInsuranceClaimCreate,
    IncidentInsuranceClaimUpdate,
    IncidentMedicalClearanceCreate,
    IncidentMedicalClearanceUpdate,
    IncidentReportPackageCreate,
    IncidentReportPackageUpdate,
    KnownChannelConsentCapture,
    SafeguardingIncidentCreate,
    SafeguardingIncidentUpdate,
    TokenConsentCapture,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship
from app.services.secrets import resolve_secret, resolve_secret_sync
from app.services.storage.objects import get_object, put_object


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def today_utc() -> date:
    return utc_now().date()


MEDICAL_INCIDENT_TYPES = {
    SafeguardingIncidentType.INJURY,
    SafeguardingIncidentType.MEDICAL,
}
BLOCKING_MEDICAL_FOLLOW_UP_VALUES = {"yes", "urgent", "required", "true"}


def is_minor_on(person: Person, on_date: date) -> bool | None:
    if person.date_of_birth is None:
        return None
    birthday_passed = (on_date.month, on_date.day) >= (
        person.date_of_birth.month,
        person.date_of_birth.day,
    )
    age = on_date.year - person.date_of_birth.year - (0 if birthday_passed else 1)
    return age < 18


def normalized_scope_id(
    organization_id: UUID,
    scope_type: ConsentScopeType,
    scope_id: UUID | None,
) -> UUID:
    if scope_type == ConsentScopeType.ORGANIZATION:
        return organization_id
    if scope_id is None:
        raise HTTPException(status_code=422, detail="Team and event consents require scope_id")
    return scope_id


async def validate_incident_refs(
    db: AsyncSession,
    organization_id: UUID,
    event_id: UUID | None,
    team_id: UUID | None,
    athlete_person_id: UUID | None,
    assigned_to_person_id: UUID | None,
) -> None:
    if event_id is not None:
        event = await db.get(Event, event_id)
        if event is None or event.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if team_id is not None:
        team = await db.get(Team, team_id)
        if team is None or team.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if athlete_person_id is not None:
        athlete_profile = await db.scalar(
            select(AthleteProfile).where(
                AthleteProfile.organization_id == organization_id,
                AthleteProfile.person_id == athlete_person_id,
            )
        )
        if athlete_profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    if assigned_to_person_id is not None:
        await validate_person_in_organization(db, organization_id, assigned_to_person_id)


async def validate_person_in_organization(
    db: AsyncSession,
    organization_id: UUID,
    person_id: UUID,
) -> None:
    person = await db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")


async def ensure_org_manage(
    authz: AuthorizationService,
    organization_id: UUID,
    identity: CurrentIdentity,
) -> None:
    can_manage = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_guardian_relationship(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: GuardianRelationshipCreate,
    authz: AuthorizationService,
) -> GuardianRelationship:
    await ensure_org_manage(authz, payload.organization_id, identity)

    athlete = await db.get(Person, payload.athlete_person_id)
    if athlete is None:
        raise HTTPException(status_code=404, detail="Athlete not found")

    guardian = None
    if payload.guardian_person_id is not None:
        guardian = await db.get(Person, payload.guardian_person_id)
        if guardian is None:
            raise HTTPException(status_code=404, detail="Guardian not found")
    elif payload.guardian_email is not None or payload.guardian_phone is not None:
        if payload.guardian_email is not None:
            guardian = await db.scalar(
                select(Person).where(Person.primary_email == payload.guardian_email)
            )
        if guardian is None and payload.guardian_phone is not None:
            guardian = await db.scalar(
                select(Person).where(Person.primary_phone == payload.guardian_phone)
            )
        if guardian is None:
            guardian = Person(
                display_name=payload.guardian_display_name
                or payload.guardian_email
                or payload.guardian_phone
                or "Guardian",
                primary_email=payload.guardian_email,
                primary_phone=payload.guardian_phone,
            )
            db.add(guardian)
            await db.flush()
        elif payload.guardian_phone and not guardian.primary_phone:
            guardian.primary_phone = payload.guardian_phone

    if guardian is None:
        raise HTTPException(status_code=422, detail="Missing guardian")

    existing = await db.scalar(
        select(GuardianRelationship).where(
            GuardianRelationship.athlete_person_id == payload.athlete_person_id,
            GuardianRelationship.guardian_person_id == guardian.id,
        )
    )
    if existing is not None:
        return existing

    relationship = GuardianRelationship(
        athlete_person_id=payload.athlete_person_id,
        guardian_person_id=guardian.id,
        relationship_kind=payload.relationship_kind,
        relationship=payload.relationship or payload.relationship_kind.value.replace("_", " "),
        can_sign_consent=payload.can_sign_consent,
        can_view_medical=payload.can_view_medical,
        emergency_contact=payload.emergency_contact,
        can_pick_up=payload.can_pick_up,
        is_primary=payload.is_primary,
        notes=payload.notes,
    )
    db.add(relationship)
    await authz.touch(
        Relationship(
            resource_type="athlete_profile",
            resource_id=str(payload.athlete_person_id),
            relation="guardian",
            subject_type="person",
            subject_id=str(guardian.id),
        )
    )
    await db.commit()
    await db.refresh(relationship)
    return relationship


async def create_safeguarding_incident(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SafeguardingIncidentCreate,
    authz: AuthorizationService,
) -> SafeguardingIncident:
    await ensure_org_manage(authz, payload.organization_id, identity)
    await validate_incident_refs(
        db,
        payload.organization_id,
        payload.event_id,
        payload.team_id,
        payload.athlete_person_id,
        payload.assigned_to_person_id,
    )
    incident = SafeguardingIncident(
        reported_by_person_id=identity.person_id,
        **payload.model_dump(),
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return incident


async def list_safeguarding_incidents(
    db: AsyncSession,
    organization_id: UUID,
    status_filter: SafeguardingIncidentStatus | None = None,
) -> list[SafeguardingIncident]:
    statement = select(SafeguardingIncident).where(
        SafeguardingIncident.organization_id == organization_id
    )
    if status_filter is not None:
        statement = statement.where(SafeguardingIncident.status == status_filter)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    SafeguardingIncident.status,
                    SafeguardingIncident.occurred_at.desc(),
                )
            )
        ).all()
    )


async def update_safeguarding_incident(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident_id: UUID,
    payload: SafeguardingIncidentUpdate,
    authz: AuthorizationService,
) -> SafeguardingIncident:
    incident = await db.get(SafeguardingIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await ensure_org_manage(authz, incident.organization_id, identity)

    if payload.assigned_to_person_id is not None:
        await validate_person_in_organization(db, incident.organization_id, payload.assigned_to_person_id)
        incident.assigned_to_person_id = payload.assigned_to_person_id
    if payload.status is not None:
        incident.status = payload.status
        if payload.status in {SafeguardingIncidentStatus.RESOLVED, SafeguardingIncidentStatus.CLOSED}:
            incident.resolved_at = incident.resolved_at or utc_now()
    if payload.severity is not None:
        incident.severity = payload.severity
    if payload.parent_notified_at is not None:
        incident.parent_notified_at = payload.parent_notified_at
    if payload.medical_follow_up_required is not None:
        incident.medical_follow_up_required = payload.medical_follow_up_required
    if payload.regulatory_report_required is not None:
        incident.regulatory_report_required = payload.regulatory_report_required
    if payload.resolution_notes is not None:
        incident.resolution_notes = payload.resolution_notes

    await db.commit()
    await db.refresh(incident)
    return incident


def default_incident_report_narrative(incident: SafeguardingIncident) -> str:
    parts = [
        f"Incident: {incident.title}",
        f"Type: {incident.incident_type.value}",
        f"Severity: {incident.severity.value}",
        f"Occurred: {incident.occurred_at.isoformat()}",
        f"Location: {incident.location or 'not recorded'}",
        "",
        incident.description,
    ]
    if incident.immediate_action:
        parts.extend(["", f"Immediate action: {incident.immediate_action}"])
    if incident.parent_notified_at:
        parts.append(f"Parent/guardian notified: {incident.parent_notified_at.isoformat()}")
    if incident.medical_follow_up_required != "unknown":
        parts.append(f"Medical follow-up: {incident.medical_follow_up_required}")
    return "\n".join(parts)


def slug_for_filename(value: str) -> str:
    normalized = "".join(character.lower() if character.isalnum() else "-" for character in value)
    parts = [part for part in normalized.split("-") if part]
    return "-".join(parts[:6]) or "incident-report"


def artifact_field(label: str, value: object | None) -> str:
    if value is None or value == "":
        return f"- {label}: not recorded"
    if isinstance(value, datetime | date):
        return f"- {label}: {value.isoformat()}"
    return f"- {label}: {value}"


def render_incident_report_package_markdown(
    package: IncidentReportPackage,
    incident: SafeguardingIncident,
    generated_at: datetime,
) -> str:
    lines = [
        "# AfroLete Incident Regulatory Report Package",
        "",
        "## Package",
        artifact_field("Package ID", package.id),
        artifact_field("Generated", generated_at),
        artifact_field("Agency", package.agency_name),
        artifact_field("Jurisdiction", package.jurisdiction),
        artifact_field("Status", package.status.value),
        artifact_field("Due", package.due_at),
        artifact_field("External reference", package.external_reference),
        artifact_field("Submitted", package.submitted_at),
        artifact_field("Accepted", package.accepted_at),
        "",
        "## Incident",
        artifact_field("Incident ID", incident.id),
        artifact_field("Title", incident.title),
        artifact_field("Type", incident.incident_type.value),
        artifact_field("Severity", incident.severity.value),
        artifact_field("Status", incident.status.value),
        artifact_field("Occurred", incident.occurred_at),
        artifact_field("Location", incident.location),
        artifact_field("Event ID", incident.event_id),
        artifact_field("Team ID", incident.team_id),
        artifact_field("Athlete person ID", incident.athlete_person_id),
        "",
        "## Narrative",
        package.narrative,
        "",
        "## Incident Description",
        incident.description,
        "",
        "## Immediate Action",
        incident.immediate_action or "Not recorded.",
        "",
        "## Guardian and Medical Follow-up",
        artifact_field("Parent/guardian notified", incident.parent_notified_at),
        artifact_field("Medical follow-up required", incident.medical_follow_up_required),
        artifact_field("Regulatory report required", incident.regulatory_report_required),
        "",
        "## Checklist",
        package.checklist_json or "No checklist has been attached.",
        "",
        "## Submission Payload",
        package.submission_payload or "No electronic submission payload has been attached.",
        "",
        "## Notes",
        package.notes or "No operator notes recorded.",
        "",
        "## Artifact Integrity",
        "Generated from current AfroLete incident and regulatory package records.",
    ]
    return "\n".join(str(line) for line in lines)


def wrapped_pdf_lines(value: str, width: int) -> list[str]:
    words = value.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}"
    lines.append(current)
    return lines


def pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def simple_pdf_from_lines(lines: list[str], title: str) -> bytes:
    chunks = [lines[index : index + 46] for index in range(0, len(lines), 46)] or [[]]
    page_objects: list[bytes] = []
    page_ids: list[int] = []
    for page_index, chunk in enumerate(chunks):
        page_id = 4 + page_index * 2
        stream_id = page_id + 1
        page_ids.append(page_id)
        page_lines = [title, f"Page {page_index + 1} of {len(chunks)}", "", *chunk]
        text_commands = ["BT", "/F1 9 Tf", "54 748 Td"]
        for line_index, line in enumerate(page_lines):
            if line_index:
                text_commands.append("0 -13 Td")
            text_commands.append(f"({pdf_escape(line[:112])}) Tj")
        text_commands.append("ET")
        stream = "\n".join(text_commands).encode()
        page_objects.extend(
            [
                (
                    f"{page_id} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    f"/Resources << /Font << /F1 3 0 R >> >> /Contents {stream_id} 0 R >> endobj\n"
                ).encode(),
                (
                    f"{stream_id} 0 obj << /Length {len(stream)} >> stream\n".encode()
                    + stream
                    + b"\nendstream endobj\n"
                ),
            ]
        )
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        f"2 0 obj << /Type /Pages /Kids [{kids}] /Count {len(chunks)} >> endobj\n".encode(),
        b"3 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        *page_objects,
    ]
    output = io.BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]
    for item in objects:
        offsets.append(output.tell())
        output.write(item)
    xref_at = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode())
    output.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode())
    output.write(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    )
    return output.getvalue()


def render_incident_report_package_pdf(markdown_content: str, package: IncidentReportPackage) -> bytes:
    lines: list[str] = []
    for raw_line in markdown_content.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            lines.extend(["AfroLete Incident Regulatory Report Package", ""])
            continue
        if line.startswith("## "):
            lines.extend(["", line[3:], ""])
            continue
        if not line:
            lines.append("")
            continue
        lines.extend(wrapped_pdf_lines(line, 92))
    return simple_pdf_from_lines(lines, title=f"Incident report {str(package.id)[:8]}")


def build_incident_report_package_artifact(
    package: IncidentReportPackage,
    incident: SafeguardingIncident,
    artifact_format: str,
    generated_at: datetime,
) -> dict[str, object]:
    normalized_format = artifact_format.lower().strip()
    if normalized_format not in {"markdown", "pdf"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported report package format")

    content = render_incident_report_package_markdown(package, incident, generated_at)
    filename_slug = slug_for_filename(package.agency_name)
    if normalized_format == "pdf":
        content_bytes = render_incident_report_package_pdf(content, package)
        return {
            "id": package.id,
            "organization_id": package.organization_id,
            "incident_id": package.incident_id,
            "generated_at": generated_at,
            "download_filename": f"afrolete-incident-report-{filename_slug}-{str(package.id)[:8]}.pdf",
            "content_type": "application/pdf",
            "artifact_format": "pdf",
            "content": "",
            "content_base64": base64.b64encode(content_bytes).decode(),
            "checksum": sha256(content_bytes).hexdigest(),
            "size_bytes": len(content_bytes),
        }
    content_bytes = content.encode("utf-8")
    return {
        "id": package.id,
        "organization_id": package.organization_id,
        "incident_id": package.incident_id,
        "generated_at": generated_at,
        "download_filename": f"afrolete-incident-report-{filename_slug}-{str(package.id)[:8]}.md",
        "content_type": "text/markdown; charset=utf-8",
        "artifact_format": "markdown",
        "content": content,
        "content_base64": None,
        "checksum": sha256(content_bytes).hexdigest(),
        "size_bytes": len(content_bytes),
    }


def incident_report_package_artifact_bytes(artifact: dict[str, object]) -> bytes:
    if artifact["content_base64"]:
        return base64.b64decode(str(artifact["content_base64"]))
    return str(artifact["content"]).encode("utf-8")


def persist_incident_report_package_artifact(
    package: IncidentReportPackage,
    artifact: dict[str, object],
    settings: Settings,
) -> dict[str, str]:
    checksum = str(artifact["checksum"])
    filename = str(artifact["download_filename"])
    storage_name = f"{checksum[:16]}-{filename}"
    storage_key = (Path(str(package.organization_id)) / str(package.id) / storage_name).as_posix()
    stored = put_object(
        settings,
        local_root=settings.safeguarding_incident_artifact_dir,
        local_url_prefix=settings.safeguarding_incident_artifact_url_prefix,
        key=storage_key,
        content=incident_report_package_artifact_bytes(artifact),
        content_type=str(artifact["content_type"]),
    )
    return {
        "artifact_url": stored.url,
        "storage_path": stored.path,
        "storage_key": stored.key,
        "storage_name": storage_name,
    }


async def get_incident_report_package_artifact(
    db: AsyncSession,
    identity: CurrentIdentity,
    package_id: UUID,
    artifact_format: str,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> dict[str, object]:
    package = await db.get(IncidentReportPackage, package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report package not found")
    await ensure_org_manage(authz, package.organization_id, identity)
    incident = await db.get(SafeguardingIncident, package.incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    artifact = build_incident_report_package_artifact(package, incident, artifact_format, utc_now())
    stored = persist_incident_report_package_artifact(package, artifact, settings or get_settings())
    artifact.update({"artifact_url": stored["artifact_url"], "storage_key": stored["storage_key"]})
    return artifact


def incident_report_artifact_signing_key(settings: Settings) -> bytes:
    key = resolve_secret_sync(
        settings,
        env_value=settings.safeguarding_incident_artifact_signing_key,
        path=settings.safeguarding_incident_artifact_signing_key_secret_path,
        field_name=settings.safeguarding_incident_artifact_signing_key_secret_field,
        label="safeguarding incident artifact signing key",
    )
    return (key or "local-safeguarding-artifact-key").encode()


def incident_report_artifact_signature(
    settings: Settings,
    organization_id: UUID,
    package_id: UUID,
    storage_name: str,
    artifact_format: str,
    generated: int,
    expires: int,
) -> str:
    payload = f"{organization_id}/{package_id}/{storage_name}:{artifact_format}:{generated}:{expires}"
    digest = hmac.new(
        incident_report_artifact_signing_key(settings),
        payload.encode(),
        sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def signed_incident_report_artifact_url(
    settings: Settings,
    organization_id: UUID,
    package_id: UUID,
    storage_name: str,
    artifact_format: str,
    generated_at: datetime,
    expires_at: datetime,
) -> str:
    generated = int(generated_at.timestamp())
    expires = int(expires_at.timestamp())
    signature = incident_report_artifact_signature(
        settings,
        organization_id,
        package_id,
        storage_name,
        artifact_format,
        generated,
        expires,
    )
    safe_name = quote(storage_name, safe="")
    return (
        f"{settings.api_prefix}/safeguarding/incident-report-artifacts/{organization_id}/{package_id}/{safe_name}"
        f"?artifact_format={artifact_format}&generated={generated}&expires={expires}&signature={signature}"
    )


async def create_signed_incident_report_package_artifact_link(
    db: AsyncSession,
    identity: CurrentIdentity,
    package_id: UUID,
    artifact_format: str,
    ttl_seconds: int | None,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> IncidentReportPackageArtifactLinkRead:
    package = await db.get(IncidentReportPackage, package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report package not found")
    await ensure_org_manage(authz, package.organization_id, identity)
    incident = await db.get(SafeguardingIncident, package.incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    selected_settings = settings or get_settings()
    generated_at = datetime.fromtimestamp(int(utc_now().timestamp()), tz=UTC)
    artifact = build_incident_report_package_artifact(package, incident, artifact_format, generated_at)
    stored = persist_incident_report_package_artifact(package, artifact, selected_settings)
    expires_at = generated_at + timedelta(
        seconds=ttl_seconds or selected_settings.safeguarding_incident_artifact_url_ttl_seconds
    )
    signed_url = signed_incident_report_artifact_url(
        selected_settings,
        package.organization_id,
        package.id,
        stored["storage_name"],
        str(artifact["artifact_format"]),
        generated_at,
        expires_at,
    )
    return IncidentReportPackageArtifactLinkRead(
        id=package.id,
        organization_id=package.organization_id,
        incident_id=package.incident_id,
        generated_at=generated_at,
        artifact_format=str(artifact["artifact_format"]),
        signed_url=signed_url,
        expires_at=expires_at,
        content_type=str(artifact["content_type"]),
        filename=str(artifact["download_filename"]),
        checksum=str(artifact["checksum"]),
        size_bytes=int(artifact["size_bytes"]),
        artifact_url=stored["artifact_url"],
        storage_key=stored["storage_key"],
    )


async def read_signed_incident_report_package_artifact(
    db: AsyncSession,
    organization_id: UUID,
    package_id: UUID,
    filename: str,
    artifact_format: str,
    generated: int,
    expires: int,
    signature: str,
    settings: Settings | None = None,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    if "/" in filename or "\\" in filename or filename in {"", ".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid artifact name")
    if expires < int(time.time()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Artifact link expired")
    normalized_format = artifact_format.lower().strip()
    expected = incident_report_artifact_signature(
        selected_settings,
        organization_id,
        package_id,
        filename,
        normalized_format,
        generated,
        expires,
    )
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid artifact signature")
    package = await db.get(IncidentReportPackage, package_id)
    if package is None or package.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report package not found")

    storage_key = (Path(str(organization_id)) / str(package_id) / filename).as_posix()
    content_bytes = get_object(
        selected_settings,
        local_root=selected_settings.safeguarding_incident_artifact_dir,
        key=storage_key,
    )
    return {
        "content": content_bytes,
        "content_type": incident_report_artifact_content_type_for_filename(filename),
        "filename": public_incident_report_artifact_filename(filename),
        "checksum": sha256(content_bytes).hexdigest(),
    }


def public_incident_report_artifact_filename(storage_name: str) -> str:
    parts = storage_name.split("-", 1)
    return parts[1] if len(parts) == 2 else storage_name


def incident_report_artifact_content_type_for_filename(filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower()
    if extension == "pdf":
        return "application/pdf"
    if extension == "md":
        return "text/markdown; charset=utf-8"
    return "application/octet-stream"


async def create_incident_report_package(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: IncidentReportPackageCreate,
    authz: AuthorizationService,
) -> IncidentReportPackage:
    await ensure_org_manage(authz, payload.organization_id, identity)
    incident = await db.get(SafeguardingIncident, payload.incident_id)
    if incident is None or incident.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    incident.regulatory_report_required = True
    package = IncidentReportPackage(
        prepared_by_person_id=identity.person_id,
        narrative=payload.narrative or default_incident_report_narrative(incident),
        **payload.model_dump(exclude={"narrative"}),
    )
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


async def list_incident_report_packages(
    db: AsyncSession,
    organization_id: UUID,
    status_filter: IncidentReportPackageStatus | None = None,
) -> list[IncidentReportPackage]:
    statement = select(IncidentReportPackage).where(
        IncidentReportPackage.organization_id == organization_id
    )
    if status_filter is not None:
        statement = statement.where(IncidentReportPackage.status == status_filter)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    IncidentReportPackage.status,
                    IncidentReportPackage.due_at.nulls_last(),
                    IncidentReportPackage.created_at.desc(),
                )
            )
        ).all()
    )


async def update_incident_report_package(
    db: AsyncSession,
    identity: CurrentIdentity,
    package_id: UUID,
    payload: IncidentReportPackageUpdate,
    authz: AuthorizationService,
) -> IncidentReportPackage:
    package = await db.get(IncidentReportPackage, package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report package not found")
    await ensure_org_manage(authz, package.organization_id, identity)

    if payload.status is not None:
        package.status = payload.status
        if payload.status == IncidentReportPackageStatus.SUBMITTED:
            package.submitted_by_person_id = identity.person_id
            package.submitted_at = payload.submitted_at or package.submitted_at or utc_now()
        if payload.status == IncidentReportPackageStatus.ACCEPTED:
            package.accepted_at = payload.accepted_at or package.accepted_at or utc_now()
    for field in [
        "due_at",
        "submitted_at",
        "accepted_at",
        "external_reference",
        "narrative",
        "checklist_json",
        "submission_payload",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(package, field, value)

    await db.commit()
    await db.refresh(package)
    return package


async def create_incident_insurance_claim(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: IncidentInsuranceClaimCreate,
    authz: AuthorizationService,
) -> IncidentInsuranceClaim:
    await ensure_org_manage(authz, payload.organization_id, identity)
    incident = await db.get(SafeguardingIncident, payload.incident_id)
    if incident is None or incident.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    if payload.claimant_person_id is not None:
        await validate_person_in_organization(db, payload.organization_id, payload.claimant_person_id)
    claim = IncidentInsuranceClaim(
        prepared_by_person_id=identity.person_id,
        **payload.model_dump(),
    )
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    return claim


async def list_incident_insurance_claims(
    db: AsyncSession,
    organization_id: UUID,
    status_filter: InsuranceClaimStatus | None = None,
) -> list[IncidentInsuranceClaim]:
    statement = select(IncidentInsuranceClaim).where(
        IncidentInsuranceClaim.organization_id == organization_id
    )
    if status_filter is not None:
        statement = statement.where(IncidentInsuranceClaim.status == status_filter)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    IncidentInsuranceClaim.status,
                    IncidentInsuranceClaim.submitted_at.desc().nulls_last(),
                    IncidentInsuranceClaim.created_at.desc(),
                )
            )
        ).all()
    )


async def update_incident_insurance_claim(
    db: AsyncSession,
    identity: CurrentIdentity,
    claim_id: UUID,
    payload: IncidentInsuranceClaimUpdate,
    authz: AuthorizationService,
) -> IncidentInsuranceClaim:
    claim = await db.get(IncidentInsuranceClaim, claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")
    await ensure_org_manage(authz, claim.organization_id, identity)

    if payload.claimant_person_id is not None:
        await validate_person_in_organization(db, claim.organization_id, payload.claimant_person_id)
        claim.claimant_person_id = payload.claimant_person_id
    if payload.status is not None:
        claim.status = payload.status
        if payload.status == InsuranceClaimStatus.SUBMITTED:
            claim.submitted_by_person_id = identity.person_id
            claim.submitted_at = payload.submitted_at or claim.submitted_at or utc_now()
        if payload.status in {
            InsuranceClaimStatus.PAID,
            InsuranceClaimStatus.DENIED,
            InsuranceClaimStatus.CLOSED,
        }:
            claim.closed_at = payload.closed_at or claim.closed_at or utc_now()
    for field in [
        "policy_number",
        "claim_number",
        "coverage_verified_at",
        "submitted_at",
        "closed_at",
        "claimed_amount_cents",
        "approved_amount_cents",
        "paid_amount_cents",
        "reserve_amount_cents",
        "tracking_url",
        "documentation_checklist_json",
        "submission_payload",
        "communication_log",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(claim, field, value)

    await db.commit()
    await db.refresh(claim)
    return claim


async def create_incident_medical_clearance(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: IncidentMedicalClearanceCreate,
    authz: AuthorizationService,
) -> IncidentMedicalClearance:
    await ensure_org_manage(authz, payload.organization_id, identity)
    incident = await db.get(SafeguardingIncident, payload.incident_id)
    if incident is None or incident.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    athlete_person_id = payload.athlete_person_id or incident.athlete_person_id
    if athlete_person_id is None:
        raise HTTPException(status_code=422, detail="Medical clearance requires an athlete")
    await validate_incident_refs(db, payload.organization_id, None, None, athlete_person_id, None)
    clearance = IncidentMedicalClearance(
        athlete_person_id=athlete_person_id,
        **payload.model_dump(exclude={"athlete_person_id"}),
    )
    db.add(clearance)
    await db.commit()
    await db.refresh(clearance)
    return clearance


async def list_incident_medical_clearances(
    db: AsyncSession,
    organization_id: UUID,
    status_filter: MedicalClearanceStatus | None = None,
) -> list[IncidentMedicalClearance]:
    statement = select(IncidentMedicalClearance).where(
        IncidentMedicalClearance.organization_id == organization_id
    )
    if status_filter is not None:
        statement = statement.where(IncidentMedicalClearance.status == status_filter)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    IncidentMedicalClearance.status,
                    IncidentMedicalClearance.valid_until.nulls_last(),
                    IncidentMedicalClearance.created_at.desc(),
                )
            )
        ).all()
    )


async def update_incident_medical_clearance(
    db: AsyncSession,
    identity: CurrentIdentity,
    clearance_id: UUID,
    payload: IncidentMedicalClearanceUpdate,
    authz: AuthorizationService,
) -> IncidentMedicalClearance:
    clearance = await db.get(IncidentMedicalClearance, clearance_id)
    if clearance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical clearance not found")
    await ensure_org_manage(authz, clearance.organization_id, identity)

    if payload.reviewed_by_person_id is not None:
        await validate_person_in_organization(db, clearance.organization_id, payload.reviewed_by_person_id)
        clearance.reviewed_by_person_id = payload.reviewed_by_person_id
    if payload.status is not None:
        clearance.status = payload.status
        if payload.status in {MedicalClearanceStatus.CLEARED, MedicalClearanceStatus.RESTRICTED}:
            clearance.assessed_at = payload.assessed_at or clearance.assessed_at or utc_now()
    for field in [
        "assessed_at",
        "valid_from",
        "valid_until",
        "restrictions",
        "return_to_play_stage",
        "provider_name",
        "documentation_object_key",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(clearance, field, value)

    await db.commit()
    await db.refresh(clearance)
    return clearance


async def create_background_check(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: BackgroundCheckCreate,
    authz: AuthorizationService,
) -> BackgroundCheck:
    await ensure_org_manage(authz, payload.organization_id, identity)
    await validate_person_in_organization(db, payload.organization_id, payload.person_id)
    check = BackgroundCheck(
        requested_by_person_id=identity.person_id,
        **payload.model_dump(),
    )
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return check


async def list_background_checks(
    db: AsyncSession,
    organization_id: UUID,
    status_filter: BackgroundCheckStatus | None = None,
) -> list[BackgroundCheck]:
    statement = select(BackgroundCheck).where(BackgroundCheck.organization_id == organization_id)
    if status_filter is not None:
        statement = statement.where(BackgroundCheck.status == status_filter)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    BackgroundCheck.status,
                    BackgroundCheck.expires_at.nulls_last(),
                    BackgroundCheck.requested_at.desc(),
                )
            )
        ).all()
    )


async def update_background_check(
    db: AsyncSession,
    identity: CurrentIdentity,
    check_id: UUID,
    payload: BackgroundCheckUpdate,
    authz: AuthorizationService,
) -> BackgroundCheck:
    check = await db.get(BackgroundCheck, check_id)
    if check is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check not found")
    await ensure_org_manage(authz, check.organization_id, identity)

    if payload.reviewed_by_person_id is not None:
        await validate_person_in_organization(db, check.organization_id, payload.reviewed_by_person_id)
        check.reviewed_by_person_id = payload.reviewed_by_person_id
    for field in [
        "status",
        "risk_level",
        "completed_at",
        "expires_at",
        "external_reference",
        "result_summary",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(check, field, value)

    await db.commit()
    await db.refresh(check)
    return check


async def resolve_safeguarding_screening_webhook_key(settings: Settings) -> str:
    return await resolve_secret(
        settings,
        env_value=settings.safeguarding_screening_webhook_signing_key,
        path=settings.safeguarding_screening_webhook_signing_key_secret_path,
        field_name=settings.safeguarding_screening_webhook_signing_key_secret_field,
        label="safeguarding screening webhook signing key",
    )


async def validate_safeguarding_screening_signature(
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    settings: Settings | None = None,
) -> dict[str, bool]:
    settings = settings or get_settings()
    signing_key = await resolve_safeguarding_screening_webhook_key(settings)
    if not signing_key:
        return {"signature_required": False, "signature_validated": False}
    if not timestamp_header or not signature_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing screening provider signature")
    try:
        timestamp_value = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid screening provider timestamp") from exc
    if abs(int(time.time()) - timestamp_value) > settings.safeguarding_screening_webhook_tolerance_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale screening provider signature")
    expected = hmac.new(
        signing_key.encode("utf-8"),
        timestamp_header.encode("utf-8") + b"." + raw_body,
        sha256,
    ).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid screening provider signature")
    return {"signature_required": True, "signature_validated": True}


def background_check_status_from_provider(
    payload: BackgroundCheckProviderResultCreate,
) -> BackgroundCheckStatus:
    if payload.status is not None:
        return payload.status
    normalized_status = (payload.provider_status or "").strip().lower().replace("-", "_").replace(" ", "_")
    status_map = {
        "clear": BackgroundCheckStatus.CLEAR,
        "cleared": BackgroundCheckStatus.CLEAR,
        "passed": BackgroundCheckStatus.CLEAR,
        "complete": BackgroundCheckStatus.CLEAR,
        "completed": BackgroundCheckStatus.CLEAR,
        "review": BackgroundCheckStatus.REVIEW_REQUIRED,
        "review_required": BackgroundCheckStatus.REVIEW_REQUIRED,
        "needs_review": BackgroundCheckStatus.REVIEW_REQUIRED,
        "consider": BackgroundCheckStatus.REVIEW_REQUIRED,
        "adverse": BackgroundCheckStatus.FAILED,
        "failed": BackgroundCheckStatus.FAILED,
        "blocked": BackgroundCheckStatus.FAILED,
        "denied": BackgroundCheckStatus.FAILED,
        "processing": BackgroundCheckStatus.IN_PROGRESS,
        "in_progress": BackgroundCheckStatus.IN_PROGRESS,
        "pending": BackgroundCheckStatus.REQUESTED,
        "requested": BackgroundCheckStatus.REQUESTED,
        "expired": BackgroundCheckStatus.EXPIRED,
    }
    if normalized_status in status_map:
        return status_map[normalized_status]
    normalized_risk = (payload.risk_level or "").strip().lower()
    if normalized_risk in {"critical", "high", "elevated", "medium"}:
        return BackgroundCheckStatus.REVIEW_REQUIRED
    if normalized_risk in {"low", "clear", "none"}:
        return BackgroundCheckStatus.CLEAR
    return BackgroundCheckStatus.IN_PROGRESS


async def ingest_background_check_provider_result(
    db: AsyncSession,
    payload: BackgroundCheckProviderResultCreate,
    raw_body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    settings: Settings | None = None,
) -> BackgroundCheckProviderResultRead:
    signature_result = await validate_safeguarding_screening_signature(
        raw_body,
        timestamp_header,
        signature_header,
        settings,
    )
    check: BackgroundCheck | None = None
    if payload.background_check_id is not None:
        check = await db.get(BackgroundCheck, payload.background_check_id)
        if check is not None and payload.organization_id is not None and check.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check not found")
    else:
        statement = select(BackgroundCheck).where(
            BackgroundCheck.provider == payload.provider,
            BackgroundCheck.external_reference == payload.external_reference,
        )
        if payload.organization_id is not None:
            statement = statement.where(BackgroundCheck.organization_id == payload.organization_id)
        check = await db.scalar(statement.order_by(BackgroundCheck.requested_at.desc()))
    if check is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check not found")

    provider_status = background_check_status_from_provider(payload)
    check.status = provider_status
    check.provider = payload.provider
    if payload.external_reference is not None:
        check.external_reference = payload.external_reference
    check.risk_level = (payload.risk_level or check.risk_level or "unknown").lower()
    if payload.completed_at is not None:
        check.completed_at = payload.completed_at
    elif provider_status in {
        BackgroundCheckStatus.CLEAR,
        BackgroundCheckStatus.REVIEW_REQUIRED,
        BackgroundCheckStatus.FAILED,
    }:
        check.completed_at = check.completed_at or utc_now()
    if payload.expires_at is not None:
        check.expires_at = payload.expires_at
    if payload.result_summary is not None:
        check.result_summary = payload.result_summary
    provider_note_parts = [
        f"Provider result accepted from {payload.provider}.",
        f"Provider status: {payload.provider_status or provider_status.value}.",
    ]
    if payload.provider_result_id:
        provider_note_parts.append(f"Provider result ID: {payload.provider_result_id}.")
    if payload.notes:
        provider_note_parts.append(payload.notes)
    check.notes = "\n".join(part for part in [check.notes, " ".join(provider_note_parts)] if part)

    await db.commit()
    await db.refresh(check)
    return BackgroundCheckProviderResultRead(
        accepted=True,
        signature_required=signature_result["signature_required"],
        signature_validated=signature_result["signature_validated"],
        organization_id=check.organization_id,
        background_check_id=check.id,
        provider=check.provider,
        external_reference=check.external_reference,
        status=check.status,
        risk_level=check.risk_level,
        message=f"Background check updated from {payload.provider} provider result.",
    )


async def create_compliance_credential(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ComplianceCredentialCreate,
    authz: AuthorizationService,
) -> ComplianceCredential:
    await ensure_org_manage(authz, payload.organization_id, identity)
    await validate_person_in_organization(db, payload.organization_id, payload.person_id)
    credential = ComplianceCredential(**payload.model_dump())
    db.add(credential)
    await db.commit()
    await db.refresh(credential)
    return credential


async def list_compliance_credentials(
    db: AsyncSession,
    organization_id: UUID,
    status_filter: ComplianceCredentialStatus | None = None,
) -> list[ComplianceCredential]:
    statement = select(ComplianceCredential).where(
        ComplianceCredential.organization_id == organization_id
    )
    if status_filter is not None:
        statement = statement.where(ComplianceCredential.status == status_filter)
    return list(
        (
            await db.scalars(
                statement.order_by(
                    ComplianceCredential.status,
                    ComplianceCredential.renewal_due_at.nulls_last(),
                    ComplianceCredential.expires_at.nulls_last(),
                    ComplianceCredential.title,
                )
            )
        ).all()
    )


async def update_compliance_credential(
    db: AsyncSession,
    identity: CurrentIdentity,
    credential_id: UUID,
    payload: ComplianceCredentialUpdate,
    authz: AuthorizationService,
) -> ComplianceCredential:
    credential = await db.get(ComplianceCredential, credential_id)
    if credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    await ensure_org_manage(authz, credential.organization_id, identity)

    if payload.verified_by_person_id is not None:
        await validate_person_in_organization(db, credential.organization_id, payload.verified_by_person_id)
        credential.verified_by_person_id = payload.verified_by_person_id
    for field in [
        "status",
        "issuing_body",
        "credential_number",
        "issued_at",
        "expires_at",
        "renewal_due_at",
        "verification_url",
        "evidence_object_key",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(credential, field, value)

    await db.commit()
    await db.refresh(credential)
    return credential


async def reconcile_compliance_statuses(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> ComplianceReconciliationRead:
    await ensure_org_manage(authz, organization_id, identity)
    return await reconcile_compliance_for_organization(db, organization_id)


async def reconcile_compliance_for_organization(
    db: AsyncSession,
    organization_id: UUID,
) -> ComplianceReconciliationRead:
    now = utc_now()
    today = now.date()
    expiring_cutoff = today + timedelta(days=30)

    background_checks_expired = 0
    credentials_expired = 0
    credentials_expiring_soon = 0

    checks = list(
        (
            await db.scalars(
                select(BackgroundCheck).where(BackgroundCheck.organization_id == organization_id)
            )
        ).all()
    )
    for check in checks:
        if (
            check.expires_at is not None
            and check.expires_at < today
            and check.status != BackgroundCheckStatus.EXPIRED
        ):
            check.status = BackgroundCheckStatus.EXPIRED
            background_checks_expired += 1

    credentials = list(
        (
            await db.scalars(
                select(ComplianceCredential).where(
                    ComplianceCredential.organization_id == organization_id
                )
            )
        ).all()
    )
    for credential in credentials:
        if credential.status == ComplianceCredentialStatus.REVOKED:
            continue
        if (
            credential.expires_at is not None
            and credential.expires_at < today
            and credential.status != ComplianceCredentialStatus.EXPIRED
        ):
            credential.status = ComplianceCredentialStatus.EXPIRED
            credentials_expired += 1
            continue
        renewal_due = credential.renewal_due_at is not None and credential.renewal_due_at <= today
        expiry_near = credential.expires_at is not None and credential.expires_at <= expiring_cutoff
        if (
            (renewal_due or expiry_near)
            and credential.status == ComplianceCredentialStatus.VERIFIED
        ):
            credential.status = ComplianceCredentialStatus.EXPIRING_SOON
            credentials_expiring_soon += 1

    await db.commit()
    return ComplianceReconciliationRead(
        organization_id=organization_id,
        reconciled_at=now,
        background_checks_expired=background_checks_expired,
        credentials_expired=credentials_expired,
        credentials_expiring_soon=credentials_expiring_soon,
    )


async def compliance_reconciliation_organization_ids(
    db: AsyncSession,
    organization_id: UUID | None = None,
    limit: int = 25,
) -> list[UUID]:
    statement = select(Organization.id).order_by(Organization.created_at, Organization.id).limit(limit)
    if organization_id is not None:
        statement = select(Organization.id).where(Organization.id == organization_id).limit(1)
    return list((await db.scalars(statement)).all())


async def run_compliance_reconciliation_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    limit: int = 25,
) -> ComplianceReconciliationWorkerRunRead:
    organization_ids = await compliance_reconciliation_organization_ids(db, organization_id, limit)
    executed_count = 0
    failed_count = 0
    background_checks_expired = 0
    credentials_expired = 0
    credentials_expiring_soon = 0

    for org_id in organization_ids:
        try:
            result = await reconcile_compliance_for_organization(db, org_id)
            executed_count += 1
            background_checks_expired += result.background_checks_expired
            credentials_expired += result.credentials_expired
            credentials_expiring_soon += result.credentials_expiring_soon
        except Exception:
            failed_count += 1
            await db.rollback()

    return ComplianceReconciliationWorkerRunRead(
        organization_id=organization_id,
        eligible_count=len(organization_ids),
        executed_count=executed_count,
        skipped_count=max(len(organization_ids) - executed_count - failed_count, 0),
        failed_count=failed_count,
        organization_ids=organization_ids,
        background_checks_expired=background_checks_expired,
        credentials_expired=credentials_expired,
        credentials_expiring_soon=credentials_expiring_soon,
    )


async def compliance_summary(
    db: AsyncSession,
    organization_id: UUID,
) -> ComplianceSummaryRead:
    now = utc_now()
    checks = list(
        (
            await db.scalars(
                select(BackgroundCheck).where(BackgroundCheck.organization_id == organization_id)
            )
        ).all()
    )
    credentials = list(
        (
            await db.scalars(
                select(ComplianceCredential).where(
                    ComplianceCredential.organization_id == organization_id
                )
            )
        ).all()
    )
    incidents = list(
        (
            await db.scalars(
                select(SafeguardingIncident).where(
                    SafeguardingIncident.organization_id == organization_id
                )
            )
        ).all()
    )

    person_ids = {
        item.person_id
        for item in [*checks, *credentials]
        if item.person_id is not None
    } | {
        incident.athlete_person_id
        for incident in incidents
        if incident.athlete_person_id is not None
    }
    people = {}
    if person_ids:
        people = {
            person.id: person.display_name
            for person in (
                await db.scalars(select(Person).where(Person.id.in_(person_ids)))
            ).all()
        }

    clear_checks = sum(1 for check in checks if check.status == BackgroundCheckStatus.CLEAR)
    review_checks = sum(
        1
        for check in checks
        if check.status in {BackgroundCheckStatus.REVIEW_REQUIRED, BackgroundCheckStatus.FAILED}
    )
    expired_checks = sum(1 for check in checks if check.status == BackgroundCheckStatus.EXPIRED)
    verified_credentials = sum(
        1
        for credential in credentials
        if credential.status == ComplianceCredentialStatus.VERIFIED
    )
    expiring_credentials = sum(
        1
        for credential in credentials
        if credential.status == ComplianceCredentialStatus.EXPIRING_SOON
    )
    expired_credentials = sum(
        1
        for credential in credentials
        if credential.status == ComplianceCredentialStatus.EXPIRED
    )
    revoked_credentials = sum(
        1
        for credential in credentials
        if credential.status == ComplianceCredentialStatus.REVOKED
    )
    open_incidents = sum(
        1
        for incident in incidents
        if incident.status not in {SafeguardingIncidentStatus.RESOLVED, SafeguardingIncidentStatus.CLOSED}
    )
    critical_incidents = sum(
        1
        for incident in incidents
        if incident.severity.value == "critical"
        and incident.status not in {SafeguardingIncidentStatus.RESOLVED, SafeguardingIncidentStatus.CLOSED}
    )
    regulatory_incidents = sum(
        1
        for incident in incidents
        if incident.regulatory_report_required
        and incident.status not in {SafeguardingIncidentStatus.RESOLVED, SafeguardingIncidentStatus.CLOSED}
    )

    total_compliance_records = len(checks) + len(credentials)
    compliant_records = clear_checks + verified_credentials
    overall_percent = (
        round((compliant_records / total_compliance_records) * 100, 1)
        if total_compliance_records
        else 100.0
    )

    blockers: list[ComplianceQueueItemRead] = []
    renewals_due: list[ComplianceQueueItemRead] = []
    investigation_queue: list[ComplianceQueueItemRead] = []

    for check in checks:
        if check.status in {
            BackgroundCheckStatus.REVIEW_REQUIRED,
            BackgroundCheckStatus.FAILED,
            BackgroundCheckStatus.EXPIRED,
        }:
            blockers.append(
                ComplianceQueueItemRead(
                    source="background_check",
                    id=check.id,
                    person_id=check.person_id,
                    person_name=people.get(check.person_id),
                    title=check.check_type,
                    status=check.status.value,
                    due_on=check.expires_at,
                    severity="high" if check.status != BackgroundCheckStatus.EXPIRED else "critical",
                    reason=f"{check.provider} check requires compliance action",
                )
            )
    for credential in credentials:
        if credential.status in {
            ComplianceCredentialStatus.EXPIRING_SOON,
            ComplianceCredentialStatus.EXPIRED,
            ComplianceCredentialStatus.REVOKED,
        }:
            item = ComplianceQueueItemRead(
                source="credential",
                id=credential.id,
                person_id=credential.person_id,
                person_name=people.get(credential.person_id),
                title=credential.title,
                status=credential.status.value,
                due_on=credential.renewal_due_at or credential.expires_at,
                severity="critical"
                if credential.status
                in {ComplianceCredentialStatus.EXPIRED, ComplianceCredentialStatus.REVOKED}
                else "medium",
                reason=f"{credential.credential_type.value.replace('_', ' ')} needs renewal or review",
            )
            if credential.status == ComplianceCredentialStatus.EXPIRING_SOON:
                renewals_due.append(item)
            else:
                blockers.append(item)
    for incident in incidents:
        if incident.status in {
            SafeguardingIncidentStatus.OPEN,
            SafeguardingIncidentStatus.TRIAGED,
            SafeguardingIncidentStatus.INVESTIGATING,
        }:
            investigation_queue.append(
                ComplianceQueueItemRead(
                    source="incident",
                    id=incident.id,
                    person_id=incident.athlete_person_id,
                    person_name=people.get(incident.athlete_person_id),
                    title=incident.title,
                    status=incident.status.value,
                    due_on=incident.occurred_at.date(),
                    severity=incident.severity.value,
                    reason="Open safeguarding incident needs closure evidence",
                )
            )

    return ComplianceSummaryRead(
        organization_id=organization_id,
        generated_at=now,
        overall_compliance_percent=overall_percent,
        total_background_checks=len(checks),
        clear_background_checks=clear_checks,
        review_background_checks=review_checks,
        expired_background_checks=expired_checks,
        total_credentials=len(credentials),
        verified_credentials=verified_credentials,
        expiring_credentials=expiring_credentials,
        expired_credentials=expired_credentials,
        revoked_credentials=revoked_credentials,
        open_incidents=open_incidents,
        critical_incidents=critical_incidents,
        regulatory_incidents=regulatory_incidents,
        blockers=sorted(blockers, key=lambda item: (item.severity, item.due_on or date.max))[:10],
        renewals_due=sorted(renewals_due, key=lambda item: item.due_on or date.max)[:10],
        investigation_queue=sorted(
            investigation_queue,
            key=lambda item: (item.severity, item.due_on or date.max),
        )[:10],
    )


async def list_guardians_for_athlete(
    db: AsyncSession,
    athlete_person_id: UUID,
) -> list[GuardianRelationship]:
    return list(
        (
            await db.scalars(
                select(GuardianRelationship)
                .where(GuardianRelationship.athlete_person_id == athlete_person_id)
                .order_by(GuardianRelationship.is_primary.desc())
            )
        ).all()
    )


async def list_my_family(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> list[FamilyAthleteSummaryRead]:
    rows = (
        await db.execute(
            select(GuardianRelationship, Person)
            .join(Person, Person.id == GuardianRelationship.athlete_person_id)
            .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
            .where(AthleteProfile.organization_id == organization_id)
            .where(GuardianRelationship.guardian_person_id == identity.person_id)
            .order_by(GuardianRelationship.is_primary.desc(), Person.display_name)
        )
    ).all()

    summaries: list[FamilyAthleteSummaryRead] = []
    for relationship, athlete in rows:
        pending_count = await db.scalar(
            select(func.count(ConsentRequest.id))
            .where(ConsentRequest.organization_id == organization_id)
            .where(ConsentRequest.athlete_person_id == relationship.athlete_person_id)
            .where(ConsentRequest.guardian_person_id == identity.person_id)
            .where(ConsentRequest.status == ConsentRequestStatus.PENDING)
        )
        latest_consent = await db.scalar(
            select(ActivityConsent)
            .where(ActivityConsent.organization_id == organization_id)
            .where(ActivityConsent.athlete_person_id == relationship.athlete_person_id)
            .where(ActivityConsent.guardian_person_id == identity.person_id)
            .order_by(ActivityConsent.created_at.desc())
            .limit(1)
        )
        summaries.append(
            FamilyAthleteSummaryRead(
                athlete_person_id=relationship.athlete_person_id,
                athlete_name=athlete.display_name,
                relationship=relationship.relationship,
                relationship_kind=relationship.relationship_kind,
                can_sign_consent=relationship.can_sign_consent,
                can_view_medical=relationship.can_view_medical,
                emergency_contact=relationship.emergency_contact,
                pending_consent_requests=int(pending_count or 0),
                latest_consent_status=latest_consent.status if latest_consent else None,
                latest_consent_scope_type=latest_consent.scope_type if latest_consent else None,
                latest_consent_signed_at=latest_consent.signed_at if latest_consent else None,
            )
        )
    return summaries


async def list_my_family_performance(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> list[FamilyPerformanceSummaryRead]:
    rows = (
        await db.execute(
            select(GuardianRelationship, Person, AthleteProfile)
            .join(Person, Person.id == GuardianRelationship.athlete_person_id)
            .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
            .where(AthleteProfile.organization_id == organization_id)
            .where(GuardianRelationship.guardian_person_id == identity.person_id)
            .order_by(GuardianRelationship.is_primary.desc(), Person.display_name)
        )
    ).all()

    summaries: list[FamilyPerformanceSummaryRead] = []
    for _, athlete, athlete_profile in rows:
        goals = list(
            (
                await db.scalars(
                    select(PerformanceGoal)
                    .where(PerformanceGoal.organization_id == organization_id)
                    .where(PerformanceGoal.athlete_profile_id == athlete_profile.id)
                    .order_by(PerformanceGoal.status, PerformanceGoal.due_at, PerformanceGoal.created_at.desc())
                    .limit(6)
                )
            ).all()
        )
        awards = list(
            (
                await db.scalars(
                    select(PerformanceAchievementAward)
                    .where(PerformanceAchievementAward.organization_id == organization_id)
                    .where(PerformanceAchievementAward.athlete_profile_id == athlete_profile.id)
                    .order_by(PerformanceAchievementAward.awarded_at.desc())
                    .limit(6)
                )
            ).all()
        )
        summaries.append(
            FamilyPerformanceSummaryRead(
                athlete_person_id=athlete.id,
                athlete_profile_id=athlete_profile.id,
                athlete_name=athlete.display_name,
                active_goal_count=sum(1 for goal in goals if goal.status == "active"),
                achieved_goal_count=sum(1 for goal in goals if goal.status == "achieved"),
                award_count=len(awards),
                goals=[
                    FamilyPerformanceGoalRead(
                        id=goal.id,
                        title=goal.title,
                        target_value=goal.target_value,
                        current_value=goal.current_value,
                        direction=goal.direction,
                        due_at=goal.due_at,
                        status=goal.status,
                        reward_badge=goal.reward_badge,
                        notes=goal.notes,
                    )
                    for goal in goals
                ],
                awards=[
                    FamilyPerformanceAwardRead(
                        id=award.id,
                        title=award.title,
                        badge_code=award.badge_code,
                        achievement_type=award.achievement_type,
                        achieved_value=award.achieved_value,
                        threshold_value=award.threshold_value,
                        awarded_at=award.awarded_at,
                        source_summary=award.source_summary,
                    )
                    for award in awards
                ],
            )
        )
    return summaries


async def list_my_family_events(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    limit: int = 50,
) -> list[FamilyEventSummaryRead]:
    rows = (
        await db.execute(
            select(GuardianRelationship, Person)
            .join(Person, Person.id == GuardianRelationship.athlete_person_id)
            .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
            .where(AthleteProfile.organization_id == organization_id)
            .where(GuardianRelationship.guardian_person_id == identity.person_id)
            .order_by(Person.display_name)
        )
    ).all()

    summaries: list[FamilyEventSummaryRead] = []
    now = utc_now()
    for relationship, athlete in rows:
        events_by_id: dict[UUID, Event] = {}
        attendance_by_event: dict[UUID, AttendanceRecord] = {}
        attendance_rows = (
            await db.execute(
                select(AttendanceRecord, Event)
                .join(Event, Event.id == AttendanceRecord.event_id)
                .where(Event.organization_id == organization_id)
                .where(Event.starts_at >= now)
                .where(AttendanceRecord.person_id == relationship.athlete_person_id)
                .order_by(Event.starts_at)
            )
        ).all()
        for attendance, event in attendance_rows:
            events_by_id[event.id] = event
            attendance_by_event[event.id] = attendance

        team_events = (
            await db.scalars(
                select(Event)
                .join(TeamRosterEntry, TeamRosterEntry.team_id == Event.team_id)
                .join(AthleteProfile, AthleteProfile.id == TeamRosterEntry.athlete_profile_id)
                .where(Event.organization_id == organization_id)
                .where(Event.starts_at >= now)
                .where(AthleteProfile.person_id == relationship.athlete_person_id)
                .where(AthleteProfile.organization_id == organization_id)
                .order_by(Event.starts_at)
            )
        ).all()
        for event in team_events:
            events_by_id[event.id] = event

        for event in events_by_id.values():
            clearance, _, guardian_required, consent_id, reason = await clearance_for_event(
                db,
                event.id,
                relationship.athlete_person_id,
            )
            attendance = attendance_by_event.get(event.id)
            summaries.append(
                FamilyEventSummaryRead(
                    athlete_person_id=relationship.athlete_person_id,
                    athlete_name=athlete.display_name,
                    event_id=event.id,
                    team_id=event.team_id,
                    event_type=event.event_type,
                    title=event.title,
                    starts_at=event.starts_at,
                    ends_at=event.ends_at,
                    timezone=event.timezone,
                    venue_name=event.venue_name,
                    attendance_status=attendance.status if attendance else None,
                    clearance_status=clearance,
                    guardian_required=guardian_required,
                    consent_id=consent_id,
                    reason=reason,
                )
            )

    return sorted(summaries, key=lambda item: item.starts_at)[:limit]


async def respond_to_family_event(
    db: AsyncSession,
    identity: CurrentIdentity,
    event_id: UUID,
    athlete_person_id: UUID,
    payload: FamilyEventRsvpCreate,
) -> FamilyEventSummaryRead:
    relationship = await db.scalar(
        select(GuardianRelationship)
        .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
        .where(AthleteProfile.organization_id == payload.organization_id)
        .where(GuardianRelationship.guardian_person_id == identity.person_id)
        .where(GuardianRelationship.athlete_person_id == athlete_person_id)
    )
    if relationship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family relationship not found")

    event = await db.get(Event, event_id)
    if event is None or event.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not await family_event_applies_to_athlete(db, event, athlete_person_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family event not found")

    clearance, _, _, _, reason = await clearance_for_event(db, event_id, athlete_person_id)
    if payload.status == AttendanceStatus.CONFIRMED and clearance != ParticipationClearanceStatus.CLEARED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"clearance_status": clearance.value, "reason": reason},
        )

    attendance = await db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.event_id == event_id,
            AttendanceRecord.person_id == athlete_person_id,
        )
    )
    if attendance is None:
        attendance = AttendanceRecord(
            event_id=event_id,
            person_id=athlete_person_id,
            status=payload.status,
            recorded_by_person_id=identity.person_id,
            note=payload.note,
        )
        db.add(attendance)
    else:
        attendance.status = payload.status
        attendance.recorded_by_person_id = identity.person_id
        attendance.note = payload.note
    await db.commit()
    await db.refresh(attendance)
    return await family_event_summary(db, relationship, event, attendance)


async def list_my_family_consent_requests(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> list[FamilyConsentRequestRead]:
    rows = (
        await db.execute(
            select(ConsentRequest, Person)
            .join(Person, Person.id == ConsentRequest.athlete_person_id)
            .join(
                GuardianRelationship,
                and_(
                    GuardianRelationship.athlete_person_id == ConsentRequest.athlete_person_id,
                    GuardianRelationship.guardian_person_id == ConsentRequest.guardian_person_id,
                ),
            )
            .where(ConsentRequest.organization_id == organization_id)
            .where(ConsentRequest.guardian_person_id == identity.person_id)
            .where(ConsentRequest.status == ConsentRequestStatus.PENDING)
            .where(GuardianRelationship.can_sign_consent.is_(True))
            .order_by(ConsentRequest.sent_at.desc())
        )
    ).all()
    now = utc_now()
    pending: list[FamilyConsentRequestRead] = []
    expired = False
    for request, athlete in rows:
        if request.expires_at is not None and request.expires_at < now:
            request.status = ConsentRequestStatus.EXPIRED
            expired = True
            continue
        pending.append(family_consent_request_read(request, athlete.display_name))
    if expired:
        await db.commit()
    return pending


async def respond_to_family_consent_request(
    db: AsyncSession,
    identity: CurrentIdentity,
    request_id: UUID,
    payload: FamilyConsentResponseCreate,
) -> ActivityConsent:
    request = await db.get(ConsentRequest, request_id)
    if request is None or request.guardian_person_id != identity.person_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent request not found")
    if request.status != ConsentRequestStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Consent request already used")
    relationship = await db.scalar(
        select(GuardianRelationship).where(
            GuardianRelationship.athlete_person_id == request.athlete_person_id,
            GuardianRelationship.guardian_person_id == identity.person_id,
            GuardianRelationship.can_sign_consent.is_(True),
        )
    )
    if relationship is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    now = utc_now()
    if request.expires_at is not None and request.expires_at < now:
        request.status = ConsentRequestStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Consent request expired")

    consent = await upsert_activity_consent(
        db,
        organization_id=request.organization_id,
        athlete_person_id=request.athlete_person_id,
        guardian_person_id=request.guardian_person_id,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        status_value=payload.status,
        capture_channel=ConsentCaptureChannel.WEB_LINK,
        identity=identity,
        source_request_id=request.id,
        consent_text=f"Guardian responded {payload.status.value} in the family portal.",
        notes=payload.notes,
    )
    request.status = ConsentRequestStatus.FULFILLED
    request.fulfilled_at = now
    request.response_payload = payload.notes
    await db.commit()
    await db.refresh(consent)
    return consent


def family_consent_request_read(
    request: ConsentRequest,
    athlete_name: str,
) -> FamilyConsentRequestRead:
    return FamilyConsentRequestRead(
        id=request.id,
        organization_id=request.organization_id,
        athlete_person_id=request.athlete_person_id,
        athlete_name=athlete_name,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        channel=request.channel,
        destination=request.destination,
        status=request.status,
        expires_at=request.expires_at,
        sent_at=request.sent_at,
        notes=request.notes,
    )


async def family_event_applies_to_athlete(
    db: AsyncSession,
    event: Event,
    athlete_person_id: UUID,
) -> bool:
    attendance = await db.scalar(
        select(AttendanceRecord.id).where(
            AttendanceRecord.event_id == event.id,
            AttendanceRecord.person_id == athlete_person_id,
        )
    )
    if attendance is not None:
        return True
    if event.team_id is None:
        return False
    roster_entry = await db.scalar(
        select(TeamRosterEntry.id)
        .join(AthleteProfile, AthleteProfile.id == TeamRosterEntry.athlete_profile_id)
        .where(TeamRosterEntry.team_id == event.team_id)
        .where(AthleteProfile.person_id == athlete_person_id)
        .where(AthleteProfile.organization_id == event.organization_id)
    )
    return roster_entry is not None


async def family_event_summary(
    db: AsyncSession,
    relationship: GuardianRelationship,
    event: Event,
    attendance: AttendanceRecord | None = None,
) -> FamilyEventSummaryRead:
    athlete = await db.get(Person, relationship.athlete_person_id)
    if athlete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    clearance, _, guardian_required, consent_id, reason = await clearance_for_event(
        db,
        event.id,
        relationship.athlete_person_id,
    )
    return FamilyEventSummaryRead(
        athlete_person_id=relationship.athlete_person_id,
        athlete_name=athlete.display_name,
        event_id=event.id,
        team_id=event.team_id,
        event_type=event.event_type,
        title=event.title,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        timezone=event.timezone,
        venue_name=event.venue_name,
        attendance_status=attendance.status if attendance else None,
        clearance_status=clearance,
        guardian_required=guardian_required,
        consent_id=consent_id,
        reason=reason,
    )


async def consent_destination(db: AsyncSession, payload: ConsentRequestCreate) -> str:
    if payload.destination is not None:
        return payload.destination
    guardian = await db.get(Person, payload.guardian_person_id)
    if guardian is None:
        raise HTTPException(status_code=404, detail="Guardian not found")
    if payload.channel == ConsentCaptureChannel.EMAIL:
        if guardian.primary_email:
            return guardian.primary_email
    elif guardian.primary_phone:
        return guardian.primary_phone
    raise HTTPException(status_code=422, detail="No known destination for consent channel")


async def create_consent_request(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ConsentRequestCreate,
    authz: AuthorizationService,
) -> tuple[ConsentRequest, str]:
    await ensure_org_manage(authz, payload.organization_id, identity)
    relationship = await db.scalar(
        select(GuardianRelationship).where(
            GuardianRelationship.athlete_person_id == payload.athlete_person_id,
            GuardianRelationship.guardian_person_id == payload.guardian_person_id,
            GuardianRelationship.can_sign_consent.is_(True),
        )
    )
    if relationship is None:
        raise HTTPException(status_code=422, detail="Guardian cannot sign consent for athlete")

    token = token_urlsafe(32)
    request = ConsentRequest(
        organization_id=payload.organization_id,
        athlete_person_id=payload.athlete_person_id,
        guardian_person_id=payload.guardian_person_id,
        scope_type=payload.scope_type,
        scope_id=normalized_scope_id(
            payload.organization_id,
            payload.scope_type,
            payload.scope_id,
        ),
        channel=payload.channel,
        destination=await consent_destination(db, payload),
        token_hash=hash_token(token),
        status=ConsentRequestStatus.PENDING,
        expires_at=payload.expires_at,
        sent_at=utc_now(),
        external_message_id=payload.external_message_id,
        notes=payload.notes,
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request, token


async def upsert_activity_consent(
    db: AsyncSession,
    *,
    organization_id: UUID,
    athlete_person_id: UUID,
    guardian_person_id: UUID,
    scope_type: ConsentScopeType,
    scope_id: UUID | None,
    status_value: ConsentStatus,
    capture_channel: ConsentCaptureChannel,
    identity: CurrentIdentity | None = None,
    source_request_id: UUID | None = None,
    consent_text: str | None = None,
    response_payload: str | None = None,
    notes: str | None = None,
) -> ActivityConsent:
    scope_id = normalized_scope_id(organization_id, scope_type, scope_id)
    existing = await db.scalar(
        select(ActivityConsent).where(
            ActivityConsent.athlete_person_id == athlete_person_id,
            ActivityConsent.guardian_person_id == guardian_person_id,
            ActivityConsent.scope_type == scope_type,
            ActivityConsent.scope_id == scope_id,
        )
    )
    signed_at = utc_now() if status_value == ConsentStatus.GRANTED else None
    revoked_at = utc_now() if status_value == ConsentStatus.REVOKED else None
    if existing is not None:
        existing.status = status_value
        existing.capture_channel = capture_channel
        existing.source_request_id = source_request_id
        existing.signed_at = signed_at or existing.signed_at
        existing.revoked_at = revoked_at
        existing.consent_text = consent_text or existing.consent_text
        existing.notes = notes or response_payload or existing.notes
        await db.commit()
        await db.refresh(existing)
        return existing

    consent = ActivityConsent(
        organization_id=organization_id,
        athlete_person_id=athlete_person_id,
        guardian_person_id=guardian_person_id,
        scope_type=scope_type,
        scope_id=scope_id,
        status=status_value,
        source_request_id=source_request_id,
        capture_channel=capture_channel,
        signed_at=signed_at,
        revoked_at=revoked_at,
        recorded_by_person_id=identity.person_id if identity is not None else None,
        consent_text=consent_text,
        notes=notes or response_payload,
    )
    db.add(consent)
    await db.commit()
    await db.refresh(consent)
    return consent


async def create_activity_consent(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ActivityConsentCreate,
    authz: AuthorizationService,
) -> ActivityConsent:
    await ensure_org_manage(authz, payload.organization_id, identity)
    return await upsert_activity_consent(
        db,
        organization_id=payload.organization_id,
        athlete_person_id=payload.athlete_person_id,
        guardian_person_id=payload.guardian_person_id,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        status_value=payload.status,
        capture_channel=ConsentCaptureChannel.MANUAL,
        identity=identity,
        consent_text=payload.consent_text,
        notes=payload.notes,
    )


async def capture_consent_by_token(
    db: AsyncSession,
    payload: TokenConsentCapture,
) -> ActivityConsent:
    request = await db.scalar(
        select(ConsentRequest).where(ConsentRequest.token_hash == hash_token(payload.token))
    )
    if request is None:
        raise HTTPException(status_code=404, detail="Consent request not found")
    if request.status != ConsentRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="Consent request already used")
    now = utc_now()
    if request.expires_at is not None and request.expires_at < now:
        request.status = ConsentRequestStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=410, detail="Consent request expired")

    consent = await upsert_activity_consent(
        db,
        organization_id=request.organization_id,
        athlete_person_id=request.athlete_person_id,
        guardian_person_id=request.guardian_person_id,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        status_value=payload.status,
        capture_channel=request.channel,
        source_request_id=request.id,
        consent_text=payload.consent_text,
        response_payload=payload.response_payload,
        notes=payload.notes,
    )
    request.status = ConsentRequestStatus.FULFILLED
    request.fulfilled_at = now
    request.response_payload = payload.response_payload
    await db.commit()
    await db.refresh(consent)
    return consent


def channel_matches_guardian(channel: ConsentCaptureChannel, guardian: Person, source: str) -> bool:
    normalized = source.strip().lower()
    if channel == ConsentCaptureChannel.EMAIL:
        return bool(guardian.primary_email and guardian.primary_email.lower() == normalized)
    if channel in {
        ConsentCaptureChannel.SMS,
        ConsentCaptureChannel.WHATSAPP,
        ConsentCaptureChannel.TELEGRAM,
    }:
        return bool(guardian.primary_phone and guardian.primary_phone.strip() == source.strip())
    return False


async def capture_consent_by_known_channel(
    db: AsyncSession,
    payload: KnownChannelConsentCapture,
) -> ActivityConsent:
    relationships = (
        await db.execute(
            select(GuardianRelationship, Person)
            .join(Person, Person.id == GuardianRelationship.guardian_person_id)
            .where(GuardianRelationship.athlete_person_id == payload.athlete_person_id)
            .where(GuardianRelationship.can_sign_consent.is_(True))
        )
    ).all()
    for relationship, guardian in relationships:
        if channel_matches_guardian(payload.channel, guardian, payload.source_address):
            pending_request = await db.scalar(
                select(ConsentRequest)
                .where(ConsentRequest.athlete_person_id == payload.athlete_person_id)
                .where(ConsentRequest.guardian_person_id == relationship.guardian_person_id)
                .where(ConsentRequest.scope_type == payload.scope_type)
                .where(
                    ConsentRequest.scope_id
                    == normalized_scope_id(
                        payload.organization_id,
                        payload.scope_type,
                        payload.scope_id,
                    )
                )
                .where(ConsentRequest.channel == payload.channel)
                .where(ConsentRequest.status == ConsentRequestStatus.PENDING)
                .order_by(ConsentRequest.sent_at.desc())
            )
            consent = await upsert_activity_consent(
                db,
                organization_id=payload.organization_id,
                athlete_person_id=payload.athlete_person_id,
                guardian_person_id=relationship.guardian_person_id,
                scope_type=payload.scope_type,
                scope_id=normalized_scope_id(
                    payload.organization_id,
                    payload.scope_type,
                    payload.scope_id,
                ),
                status_value=payload.status,
                capture_channel=payload.channel,
                source_request_id=pending_request.id if pending_request is not None else None,
                response_payload=payload.response_payload,
                notes=payload.notes,
            )
            if pending_request is not None:
                pending_request.status = ConsentRequestStatus.FULFILLED
                pending_request.fulfilled_at = utc_now()
                pending_request.response_payload = payload.response_payload
                await db.commit()
            return consent
    raise HTTPException(status_code=404, detail="No matching guardian contact found")


async def clearance_for_event(
    db: AsyncSession,
    event_id: UUID,
    athlete_person_id: UUID,
) -> tuple[ParticipationClearanceStatus, bool, bool, UUID | None, str]:
    event = await db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    athlete = await db.get(Person, athlete_person_id)
    if athlete is None:
        raise HTTPException(status_code=404, detail="Athlete not found")

    minor = is_minor_on(athlete, event.starts_at.date())
    if minor is False:
        return (
            ParticipationClearanceStatus.CLEARED,
            False,
            False,
            None,
            "Athlete is not a minor on the event date.",
        )

    guardians = await list_guardians_for_athlete(db, athlete_person_id)
    signing_guardians = [guardian for guardian in guardians if guardian.can_sign_consent]
    if not signing_guardians:
        return (
            ParticipationClearanceStatus.NO_GUARDIAN,
            minor is True,
            True,
            None,
            "No guardian with consent authority is recorded.",
        )

    today = utc_now().date()
    applicable_scope = or_(
        and_(
            ActivityConsent.scope_type == ConsentScopeType.ORGANIZATION,
            ActivityConsent.scope_id == event.organization_id,
        ),
        and_(
            ActivityConsent.scope_type == ConsentScopeType.EVENT,
            ActivityConsent.scope_id == event_id,
        ),
        and_(
            ActivityConsent.scope_type == ConsentScopeType.TEAM,
            ActivityConsent.scope_id == event.team_id,
        ),
    )
    latest_consent = await db.scalar(
        select(ActivityConsent)
        .where(ActivityConsent.athlete_person_id == athlete_person_id)
        .where(applicable_scope)
        .order_by(ActivityConsent.updated_at.desc())
    )
    if latest_consent is None:
        return (
            ParticipationClearanceStatus.MINOR_REQUIRES_CONSENT,
            minor is True,
            True,
            None,
            "Guardian consent is required before participation.",
        )
    if latest_consent.status == ConsentStatus.DENIED:
        return (
            ParticipationClearanceStatus.CONSENT_DENIED,
            minor is True,
            True,
            latest_consent.id,
            "Guardian consent was denied.",
        )
    if latest_consent.status == ConsentStatus.EXPIRED:
        return (
            ParticipationClearanceStatus.CONSENT_EXPIRED,
            minor is True,
            True,
            latest_consent.id,
            "Guardian consent is marked expired.",
        )
    if latest_consent.status != ConsentStatus.GRANTED:
        return (
            ParticipationClearanceStatus.MINOR_REQUIRES_CONSENT,
            minor is True,
            True,
            latest_consent.id,
            "Guardian consent has not been granted.",
        )
    if latest_consent.valid_until is not None and latest_consent.valid_until < today:
        return (
            ParticipationClearanceStatus.CONSENT_EXPIRED,
            minor is True,
            True,
            latest_consent.id,
            "Guardian consent exists but has expired.",
        )
    return (
        ParticipationClearanceStatus.CLEARED,
        minor is True,
        True,
        latest_consent.id,
        "Guardian consent is recorded.",
    )


async def medical_clearance_for_event(
    db: AsyncSession,
    event_id: UUID,
    athlete_person_id: UUID,
) -> tuple[ParticipationClearanceStatus, MedicalClearanceStatus | None, UUID | None, str]:
    event = await db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    event_date = event.starts_at.date()

    blocking_incident = await db.scalar(
        select(SafeguardingIncident)
        .where(
            SafeguardingIncident.organization_id == event.organization_id,
            SafeguardingIncident.athlete_person_id == athlete_person_id,
            SafeguardingIncident.status.notin_(
                [SafeguardingIncidentStatus.RESOLVED, SafeguardingIncidentStatus.CLOSED]
            ),
        )
        .where(
            or_(
                SafeguardingIncident.incident_type.in_(tuple(MEDICAL_INCIDENT_TYPES)),
                SafeguardingIncident.medical_follow_up_required.in_(
                    tuple(BLOCKING_MEDICAL_FOLLOW_UP_VALUES)
                ),
            )
        )
        .order_by(SafeguardingIncident.occurred_at.desc())
    )
    if blocking_incident is None:
        return (
            ParticipationClearanceStatus.CLEARED,
            None,
            None,
            "No open injury or medical incident requires clearance.",
        )

    latest_clearance = await db.scalar(
        select(IncidentMedicalClearance)
        .where(
            IncidentMedicalClearance.organization_id == event.organization_id,
            IncidentMedicalClearance.incident_id == blocking_incident.id,
            IncidentMedicalClearance.athlete_person_id == athlete_person_id,
        )
        .order_by(IncidentMedicalClearance.updated_at.desc())
    )
    if latest_clearance is None:
        return (
            ParticipationClearanceStatus.MEDICAL_CLEARANCE_REQUIRED,
            None,
            None,
            f"{blocking_incident.title} requires medical clearance before participation.",
        )
    if latest_clearance.valid_from is not None and latest_clearance.valid_from > event_date:
        return (
            ParticipationClearanceStatus.MEDICAL_CLEARANCE_REQUIRED,
            latest_clearance.status,
            latest_clearance.id,
            "Medical clearance is not yet valid for this event date.",
        )
    if latest_clearance.valid_until is not None and latest_clearance.valid_until < event_date:
        return (
            ParticipationClearanceStatus.MEDICAL_CLEARANCE_EXPIRED,
            latest_clearance.status,
            latest_clearance.id,
            "Medical clearance expired before this event date.",
        )
    if latest_clearance.status == MedicalClearanceStatus.CLEARED:
        return (
            ParticipationClearanceStatus.CLEARED,
            latest_clearance.status,
            latest_clearance.id,
            "Medical clearance allows full participation.",
        )
    if latest_clearance.status == MedicalClearanceStatus.RESTRICTED:
        return (
            ParticipationClearanceStatus.CLEARED,
            latest_clearance.status,
            latest_clearance.id,
            latest_clearance.restrictions or "Medical clearance allows restricted participation.",
        )
    return (
        ParticipationClearanceStatus.MEDICAL_NOT_CLEARED,
        latest_clearance.status,
        latest_clearance.id,
        "Medical clearance does not permit participation.",
    )
