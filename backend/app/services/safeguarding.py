import base64
import hmac
import io
import json
import time
from binascii import Error as BinasciiError
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from re import search, sub
from secrets import token_urlsafe
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.config import Settings, get_settings
from app.models.enums import (
    AttendanceStatus,
    BackgroundCheckStatus,
    CommunicationChannel,
    CommunicationMessageType,
    CommunicationScopeType,
    ComplianceCredentialStatus,
    ConsentCaptureChannel,
    ConsentRequestStatus,
    ConsentScopeType,
    ConsentStatus,
    IncidentReportPackageStatus,
    InsuranceClaimStatus,
    MedicalClearanceStatus,
    ParticipationClearanceStatus,
    SafeguardingIncidentSeverity,
    SafeguardingIncidentType,
    SafeguardingIncidentStatus,
    MessageDeliveryStatus,
)
from app.models.event import (
    ActivityConsent,
    AttendanceRecord,
    BackgroundCheck,
    BackgroundCheckEvidenceDocument,
    ComplianceCredential,
    ConsentRequest,
    Event,
    IncidentInsuranceClaim,
    IncidentMedicalClearance,
    IncidentReportPackage,
    InsurancePolicy,
    SafeguardingEvidencePolicyRule,
    SafeguardingIncident,
    SafeguardingIncidentAccessGrant,
)
from app.models.agent import AgentDecisionAppeal
from app.models.communication import CommunicationMessage, MessageRecipient
from app.models.identity import AppUser, Person
from app.models.organization import Organization
from app.models.performance import (
    OppositionScoutingVideoAsset,
    PerformanceAchievementAward,
    PerformanceGoal,
    PerformanceMatchPlayerGuidanceFeedback,
    PerformanceMatchPlayerGuidancePublishAudit,
    PerformanceMatchTrackingRun,
    PerformanceMatchTrackingSample,
)
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry
from app.schemas.safeguarding import (
    ActivityConsentCreate,
    BackgroundCheckCreate,
    BackgroundCheckEvidenceDocumentLinkCreate,
    BackgroundCheckEvidenceDocumentLinkRead,
    BackgroundCheckEvidenceDocumentRead,
    BackgroundCheckEvidenceDocumentReviewCreate,
    BackgroundCheckEvidenceDocumentUploadCreate,
    BackgroundCheckProviderSubmissionRead,
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
    FamilyCoordinationDigestCreate,
    FamilyCoordinationDigestRead,
    FamilyCoordinationDigestWorkerRunRead,
    FamilyCoordinationRowRead,
    FamilyDashboardActionRead,
    FamilyDashboardRead,
    FamilyScheduleConflictRead,
    FamilyConsentRequestRead,
    FamilyConsentResponseCreate,
    FamilyMatchGuidanceFeedbackCreate,
    FamilyEventSummaryRead,
    FamilyEventRsvpCreate,
    FamilyMatchGuidanceRead,
    GuardianAccountReadinessRead,
    GuardianPortalInviteBatchCreate,
    GuardianPortalInviteBatchRead,
    GuardianPortalInviteCreate,
    GuardianPortalInviteRead,
    GuardianPortalInviteReminderWorkerRunRead,
    FamilyPerformanceAwardRead,
    FamilyPerformanceGoalRead,
    FamilyPerformanceSummaryRead,
    GuardianRelationshipCreate,
    SafeguardingEvidencePolicyRuleCreate,
    SafeguardingEvidencePolicyRuleRead,
    SafeguardingEvidencePolicyRuleUpdate,
    SafeguardingIncidentAccessGrantCreate,
    SafeguardingIncidentAccessGrantRead,
    SafeguardingIncidentAccessGrantRevoke,
    SafeguardingIncidentAccessControlRead,
    SafeguardingIncidentEvidenceApprovalPolicyRead,
    SafeguardingIncidentEvidenceReviewActionCreate,
    SafeguardingIncidentEvidenceReviewActionRead,
    SafeguardingIncidentEvidenceReviewItemRead,
    SafeguardingIncidentEvidenceLinkCreate,
    SafeguardingIncidentEvidenceLinkRead,
    SafeguardingIncidentEvidenceUploadCreate,
    SafeguardingIncidentEvidenceUploadRead,
    SafeguardingIncidentInvestigationActionCreate,
    SafeguardingIncidentInvestigationActionRead,
    IncidentReportPackageArtifactLinkRead,
    IncidentReportPackageProviderSubmissionRead,
    IncidentInsuranceClaimCreate,
    IncidentInsuranceClaimProviderSyncRead,
    IncidentInsuranceClaimUpdate,
    InsuranceCoverageVerificationCreate,
    InsuranceCoverageVerificationRead,
    InsurancePolicyCreate,
    InsurancePolicyRead,
    InsurancePolicyUpdate,
    InsurancePortfolioSummaryRead,
    IncidentMedicalClearanceCreate,
    IncidentMedicalClearanceProviderSyncRead,
    IncidentMedicalClearanceUpdate,
    IncidentReportPackageCreate,
    IncidentReportPackageUpdate,
    KnownChannelConsentCapture,
    SafeguardingIncidentCreate,
    SafeguardingIncidentRead,
    SafeguardingIncidentUpdate,
    TokenConsentCapture,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship
from app.services.communications import create_message_for_recipients, destination_for_channel, dispatch_message
from app.services.secrets import resolve_secret, resolve_secret_sync
from app.services.storage.objects import get_object, put_object


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def datetime_is_before(value: datetime | None, boundary: datetime) -> bool:
    if value is None:
        return False
    comparable = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    boundary_utc = boundary.replace(tzinfo=UTC) if boundary.tzinfo is None else boundary.astimezone(UTC)
    return comparable < boundary_utc


def today_utc() -> date:
    return utc_now().date()


MEDICAL_INCIDENT_TYPES = {
    SafeguardingIncidentType.INJURY,
    SafeguardingIncidentType.MEDICAL,
}
BLOCKING_MEDICAL_FOLLOW_UP_VALUES = {"yes", "urgent", "required", "true"}

CLAIM_TYPE_POLICY_TYPES = {
    "injury_medical": {"accident_medical", "medical", "participant_accident", "travel_accident"},
    "liability": {"general_liability", "directors_officers", "event_liability"},
    "equipment_damage": {"equipment", "equipment_property", "property"},
    "property_damage": {"property", "equipment_property", "facility_property"},
    "travel": {"travel", "travel_accident", "event_cancellation"},
    "other": {"general_liability", "other"},
}
OPEN_INSURANCE_CLAIM_STATUSES = {
    InsuranceClaimStatus.DRAFT,
    InsuranceClaimStatus.READY,
    InsuranceClaimStatus.SUBMITTED,
    InsuranceClaimStatus.ACKNOWLEDGED,
    InsuranceClaimStatus.IN_REVIEW,
    InsuranceClaimStatus.APPROVED,
    InsuranceClaimStatus.PARTIALLY_PAID,
}


def normalize_provider_profile(value: str | None, default: str) -> str:
    normalized = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return normalized or default


def selected_provider_profile(configured: str | None, inferred: str) -> str:
    normalized = normalize_provider_profile(configured, "auto")
    return inferred if normalized in {"auto", "infer", "default"} else normalized


def provider_schema_id(scope: str, profile: str) -> str:
    return f"safeguarding.{scope}.{profile}.v1"


def provider_schema_id_from_payload(payload: dict[str, object]) -> str:
    schema = payload.get("provider_schema")
    if isinstance(schema, dict):
        schema_id = schema.get("schema_id")
        if schema_id:
            return str(schema_id)
    return "safeguarding.provider.unknown.v1"


def infer_regulatory_provider_profile(
    package: IncidentReportPackage,
    incident: SafeguardingIncident,
) -> str:
    text = " ".join(
        [
            package.agency_name,
            package.jurisdiction,
            incident.title,
            incident.description or "",
            incident.incident_type.value,
        ]
    ).lower()
    if "safe" in text and "sport" in text or incident.incident_type in {
        SafeguardingIncidentType.SAFEGUARDING,
        SafeguardingIncidentType.MISCONDUCT,
    }:
        return "safe_sport"
    if any(marker in text for marker in ["school", "education", "ministry"]):
        return "school_sport_authority"
    if any(marker in text for marker in ["federation", "association", "league"]):
        return "federation_discipline"
    if any(marker in text for marker in ["county", "local", "municipal"]):
        return "local_safeguarding_office"
    return "standard_regulatory"


def infer_insurance_provider_profile(claim: IncidentInsuranceClaim) -> str:
    claim_type = claim.claim_type.value
    if claim_type == "injury_medical":
        return "medical_claim"
    if claim_type in {"equipment_damage", "property_damage"}:
        return "property_equipment_claim"
    if claim_type == "liability":
        return "liability_claim"
    if claim_type == "travel":
        return "travel_claim"
    return "standard_claim"


def infer_medical_provider_profile(
    clearance: IncidentMedicalClearance,
    incident: SafeguardingIncident,
) -> str:
    text = " ".join(
        [
            clearance.clearance_type,
            clearance.return_to_play_stage or "",
            clearance.provider_name or "",
            incident.title,
            incident.description or "",
            incident.immediate_action or "",
        ]
    ).lower()
    if any(marker in text for marker in ["concussion", "head impact", "head injury"]):
        return "concussion_return_to_play"
    if "physio" in text or "rehab" in text:
        return "physiotherapy_clearance"
    if "school" in text:
        return "school_medical_clearance"
    if "return" in text and "play" in text:
        return "return_to_play_clearance"
    return "standard_medical_clearance"


def infer_screening_provider_profile(check: BackgroundCheck) -> str:
    text = " ".join([check.provider, check.check_type]).lower()
    if "safe" in text and "sport" in text or "safeguard" in text:
        return "safe_sport_screening"
    if "checkr" in text:
        return "checkr_screening"
    if "first" in text and "advantage" in text:
        return "first_advantage_screening"
    if any(marker in text for marker in ["police", "criminal", "government", "dbs"]):
        return "government_clearance"
    if any(marker in text for marker in ["coach", "staff", "volunteer"]):
        return "youth_sport_staff_screening"
    return "standard_screening"


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


async def get_insurance_policy(db: AsyncSession, policy_id: UUID) -> InsurancePolicy:
    policy = await db.get(InsurancePolicy, policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance policy not found")
    return policy


async def get_insurance_policy_for_organization(
    db: AsyncSession,
    policy_id: UUID,
    organization_id: UUID,
) -> InsurancePolicy:
    policy = await get_insurance_policy(db, policy_id)
    if policy.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance policy not found")
    return policy


def insurance_policy_covers_claim_type(policy: InsurancePolicy, claim_type: object) -> bool:
    claim_type_value = getattr(claim_type, "value", str(claim_type))
    policy_type = policy.policy_type.strip().lower()
    return policy_type in CLAIM_TYPE_POLICY_TYPES.get(claim_type_value, {policy_type})


def insurance_policy_active_on(policy: InsurancePolicy, activity_date: date) -> bool:
    return policy.status in {"active", "expiring"} and policy.effective_on <= activity_date <= policy.expires_on


def insurance_policy_renewal_due(policy: InsurancePolicy, today: date) -> bool:
    if policy.status not in {"active", "expiring"}:
        return False
    return (policy.expires_on - today).days <= policy.renewal_notice_days


async def best_insurance_policy_for_claim_type(
    db: AsyncSession,
    organization_id: UUID,
    claim_type: object,
    activity_date: date,
) -> InsurancePolicy | None:
    policies = list(
        (
            await db.scalars(
                select(InsurancePolicy)
                .where(InsurancePolicy.organization_id == organization_id)
                .where(InsurancePolicy.status.in_(["active", "expiring"]))
                .order_by(InsurancePolicy.expires_on.asc(), InsurancePolicy.coverage_limit_cents.desc())
            )
        ).all()
    )
    for policy in policies:
        if insurance_policy_covers_claim_type(policy, claim_type) and insurance_policy_active_on(policy, activity_date):
            return policy
    return None


async def insurance_policy_read(db: AsyncSession, policy: InsurancePolicy) -> InsurancePolicyRead:
    claims = list(
        (
            await db.scalars(
                select(IncidentInsuranceClaim).where(
                    IncidentInsuranceClaim.organization_id == policy.organization_id,
                    IncidentInsuranceClaim.insurance_policy_id == policy.id,
                )
            )
        ).all()
    )
    today = today_utc()
    return InsurancePolicyRead(
        id=policy.id,
        organization_id=policy.organization_id,
        name=policy.name,
        policy_type=policy.policy_type,
        provider_name=policy.provider_name,
        policy_number=policy.policy_number,
        group_number=policy.group_number,
        broker_name=policy.broker_name,
        broker_email=policy.broker_email,
        broker_phone=policy.broker_phone,
        coverage_summary=policy.coverage_summary,
        covered_subjects=policy.covered_subjects,
        exclusions=policy.exclusions,
        coverage_limit_cents=policy.coverage_limit_cents,
        deductible_cents=policy.deductible_cents,
        premium_cents=policy.premium_cents,
        currency=policy.currency,
        effective_on=policy.effective_on,
        expires_on=policy.expires_on,
        renewal_notice_days=policy.renewal_notice_days,
        certificate_url=policy.certificate_url,
        document_url=policy.document_url,
        notes=policy.notes,
        status=policy.status,
        claim_count=len(claims),
        open_claim_count=sum(1 for claim in claims if claim.status in OPEN_INSURANCE_CLAIM_STATUSES),
        paid_claims_cents=sum(claim.paid_amount_cents for claim in claims),
        renewal_due=insurance_policy_renewal_due(policy, today),
        days_until_expiry=(policy.expires_on - today).days,
    )


async def ensure_manage_safeguarding_incident(
    authz: AuthorizationService,
    incident: SafeguardingIncident,
    identity: CurrentIdentity,
) -> None:
    can_manage_case = await authz.check(
        resource_type="safeguarding_incident",
        resource_id=str(incident.id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if can_manage_case:
        return
    await ensure_org_manage(authz, incident.organization_id, identity)


async def ensure_review_safeguarding_incident_evidence(
    authz: AuthorizationService,
    incident: SafeguardingIncident,
    identity: CurrentIdentity,
) -> None:
    can_review = await authz.check(
        resource_type="safeguarding_incident",
        resource_id=str(incident.id),
        permission="review_evidence",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if can_review:
        return
    await ensure_manage_safeguarding_incident(authz, incident, identity)


async def sync_safeguarding_incident_access_controls(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident: SafeguardingIncident,
    authz: AuthorizationService,
) -> SafeguardingIncidentAccessControlRead:
    touched: list[str] = []

    async def touch(relationship: Relationship) -> None:
        await authz.touch(relationship)
        touched.append(
            f"{relationship.resource_type}:{relationship.resource_id}#{relationship.relation}@"
            f"{relationship.subject_type}:{relationship.subject_id}"
        )

    async def touch_person_and_users(relation: str, person_id: UUID) -> None:
        await touch(
            Relationship(
                resource_type="safeguarding_incident",
                resource_id=str(incident.id),
                relation=relation,
                subject_type="person",
                subject_id=str(person_id),
            )
        )
        user_ids = await app_user_ids_for_person(db, person_id)
        for user_id in user_ids:
            await touch(
                Relationship(
                    resource_type="safeguarding_incident",
                    resource_id=str(incident.id),
                    relation=relation,
                    subject_type="user",
                    subject_id=str(user_id),
                )
            )

    await touch(
        Relationship(
            resource_type="safeguarding_incident",
            resource_id=str(incident.id),
            relation="parent_org",
            subject_type="organization",
            subject_id=str(incident.organization_id),
        )
    )
    await touch_person_and_users("case_manager", identity.person_id)
    await touch(
        Relationship(
            resource_type="safeguarding_incident",
            resource_id=str(incident.id),
            relation="case_manager",
            subject_type="user",
            subject_id=str(identity.user_id),
        )
    )
    await touch(
        Relationship(
            resource_type="safeguarding_incident",
            resource_id=str(incident.id),
            relation="evidence_reviewer",
            subject_type="user",
            subject_id=str(identity.user_id),
        )
    )
    if incident.event_id is not None:
        await touch(
            Relationship(
                resource_type="safeguarding_incident",
                resource_id=str(incident.id),
                relation="event",
                subject_type="event",
                subject_id=str(incident.event_id),
            )
        )
    if incident.team_id is not None:
        await touch(
            Relationship(
                resource_type="safeguarding_incident",
                resource_id=str(incident.id),
                relation="team",
                subject_type="team",
                subject_id=str(incident.team_id),
            )
        )
    if incident.reported_by_person_id is not None:
        await touch_person_and_users("reporter", incident.reported_by_person_id)
    if incident.assigned_to_person_id is not None:
        await touch_person_and_users("assigned_to", incident.assigned_to_person_id)
    if incident.athlete_person_id is not None:
        await touch_person_and_users("athlete", incident.athlete_person_id)
        guardians = (
            await db.scalars(
                select(GuardianRelationship).where(
                    GuardianRelationship.athlete_person_id == incident.athlete_person_id
                )
            )
        ).all()
        for guardian in guardians:
            await touch_person_and_users("guardian", guardian.guardian_person_id)
            if guardian.can_view_medical:
                await touch_person_and_users("medical_viewer", guardian.guardian_person_id)
    if incident.regulatory_report_required:
        await touch_person_and_users("regulator", identity.person_id)
    access_grants = (
        await db.scalars(
            select(SafeguardingIncidentAccessGrant).where(
                SafeguardingIncidentAccessGrant.incident_id == incident.id,
                SafeguardingIncidentAccessGrant.active.is_(True),
            )
        )
    ).all()
    for grant in access_grants:
        await touch_person_and_users(grant.relation, grant.person_id)

    can_manage_case = await authz.check(
        resource_type="safeguarding_incident",
        resource_id=str(incident.id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    can_review_evidence = await authz.check(
        resource_type="safeguarding_incident",
        resource_id=str(incident.id),
        permission="review_evidence",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    return SafeguardingIncidentAccessControlRead(
        incident_id=incident.id,
        organization_id=incident.organization_id,
        relationship_count=len(touched),
        touched_relationships=touched,
        can_manage_case=can_manage_case,
        can_review_evidence=can_review_evidence,
        synced_at=utc_now(),
    )


async def sync_safeguarding_incident_access_controls_by_id(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident_id: UUID,
    authz: AuthorizationService,
) -> SafeguardingIncidentAccessControlRead:
    incident = await db.get(SafeguardingIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await ensure_manage_safeguarding_incident(authz, incident, identity)
    return await sync_safeguarding_incident_access_controls(db, identity, incident, authz)


async def create_safeguarding_incident_access_grant(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident_id: UUID,
    payload: SafeguardingIncidentAccessGrantCreate,
    authz: AuthorizationService,
) -> SafeguardingIncidentAccessGrantRead:
    incident = await db.get(SafeguardingIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await ensure_manage_safeguarding_incident(authz, incident, identity)
    await validate_person_in_organization(db, incident.organization_id, payload.person_id)
    grant = SafeguardingIncidentAccessGrant(
        organization_id=incident.organization_id,
        incident_id=incident.id,
        person_id=payload.person_id,
        relation=payload.relation,
        active=True,
        granted_by_person_id=identity.person_id,
        granted_reason=payload.reason,
    )
    db.add(grant)
    await db.commit()
    await db.refresh(grant)
    await apply_safeguarding_incident_access_grant(db, authz, grant)
    return safeguarding_incident_access_grant_read(grant)


async def list_safeguarding_incident_access_grants(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident_id: UUID,
    authz: AuthorizationService,
    active: bool | None = None,
) -> list[SafeguardingIncidentAccessGrantRead]:
    incident = await db.get(SafeguardingIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await ensure_manage_safeguarding_incident(authz, incident, identity)
    statement = select(SafeguardingIncidentAccessGrant).where(
        SafeguardingIncidentAccessGrant.incident_id == incident.id
    )
    if active is not None:
        statement = statement.where(SafeguardingIncidentAccessGrant.active.is_(active))
    grants = (
        await db.scalars(
            statement.order_by(
                SafeguardingIncidentAccessGrant.active.desc(),
                SafeguardingIncidentAccessGrant.created_at.desc(),
            )
        )
    ).all()
    return [safeguarding_incident_access_grant_read(grant) for grant in grants]


async def revoke_safeguarding_incident_access_grant(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident_id: UUID,
    grant_id: UUID,
    payload: SafeguardingIncidentAccessGrantRevoke,
    authz: AuthorizationService,
) -> SafeguardingIncidentAccessGrantRead:
    incident = await db.get(SafeguardingIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    grant = await db.get(SafeguardingIncidentAccessGrant, grant_id)
    if grant is None or grant.incident_id != incident.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access grant not found")
    await ensure_manage_safeguarding_incident(authz, incident, identity)
    if grant.active:
        grant.active = False
        grant.revoked_by_person_id = identity.person_id
        grant.revoked_reason = payload.reason
        grant.revoked_at = utc_now()
        await db.commit()
        await db.refresh(grant)
        await delete_safeguarding_incident_access_grant(db, authz, grant)
    return safeguarding_incident_access_grant_read(grant)


async def apply_safeguarding_incident_access_grant(
    db: AsyncSession,
    authz: AuthorizationService,
    grant: SafeguardingIncidentAccessGrant,
) -> None:
    for relationship in await safeguarding_incident_person_relationships(
        db,
        grant.incident_id,
        grant.relation,
        grant.person_id,
    ):
        await authz.touch(relationship)


async def delete_safeguarding_incident_access_grant(
    db: AsyncSession,
    authz: AuthorizationService,
    grant: SafeguardingIncidentAccessGrant,
) -> None:
    for relationship in await safeguarding_incident_person_relationships(
        db,
        grant.incident_id,
        grant.relation,
        grant.person_id,
    ):
        await authz.delete(relationship)


async def safeguarding_incident_person_relationships(
    db: AsyncSession,
    incident_id: UUID,
    relation: str,
    person_id: UUID,
) -> list[Relationship]:
    relationships = [
        Relationship(
            resource_type="safeguarding_incident",
            resource_id=str(incident_id),
            relation=relation,
            subject_type="person",
            subject_id=str(person_id),
        )
    ]
    for user_id in await app_user_ids_for_person(db, person_id):
        relationships.append(
            Relationship(
                resource_type="safeguarding_incident",
                resource_id=str(incident_id),
                relation=relation,
                subject_type="user",
                subject_id=str(user_id),
            )
        )
    return relationships


async def app_user_ids_for_person(db: AsyncSession, person_id: UUID) -> list[UUID]:
    return list((await db.scalars(select(AppUser.id).where(AppUser.person_id == person_id))).all())


async def create_safeguarding_evidence_policy_rule(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: SafeguardingEvidencePolicyRuleCreate,
    authz: AuthorizationService,
) -> SafeguardingEvidencePolicyRuleRead:
    await ensure_org_manage(authz, payload.organization_id, identity)
    existing = await db.scalar(
        select(SafeguardingEvidencePolicyRule).where(
            SafeguardingEvidencePolicyRule.organization_id == payload.organization_id,
            SafeguardingEvidencePolicyRule.rule_code == payload.rule_code,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Evidence policy rule already exists")
    rule = SafeguardingEvidencePolicyRule(
        organization_id=payload.organization_id,
        rule_code=payload.rule_code,
        title=payload.title,
        active=payload.active,
        incident_type=payload.incident_type.value if payload.incident_type else None,
        minimum_severity=payload.minimum_severity.value if payload.minimum_severity else None,
        evidence_type_contains=payload.evidence_type_contains,
        medical_follow_up_values=payload.medical_follow_up_values,
        regulatory_required=payload.regulatory_required,
        athlete_linked_required=payload.athlete_linked_required,
        required_approval_level=normalize_provider_profile(payload.required_approval_level, "safeguarding_lead"),
        risk_level=payload.risk_level,
        recommended_review_status=payload.recommended_review_status,
        block_acceptance=payload.block_acceptance,
        rationale=payload.rationale,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return safeguarding_evidence_policy_rule_read(rule)


async def list_safeguarding_evidence_policy_rules(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    active: bool | None = None,
) -> list[SafeguardingEvidencePolicyRuleRead]:
    await ensure_org_manage(authz, organization_id, identity)
    return [
        safeguarding_evidence_policy_rule_read(rule)
        for rule in await active_safeguarding_evidence_policy_rules(db, organization_id, active=active)
    ]


async def update_safeguarding_evidence_policy_rule(
    db: AsyncSession,
    identity: CurrentIdentity,
    rule_id: UUID,
    payload: SafeguardingEvidencePolicyRuleUpdate,
    authz: AuthorizationService,
) -> SafeguardingEvidencePolicyRuleRead:
    rule = await db.get(SafeguardingEvidencePolicyRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence policy rule not found")
    await ensure_org_manage(authz, rule.organization_id, identity)
    if payload.title is not None:
        rule.title = payload.title
    if payload.active is not None:
        rule.active = payload.active
    if payload.incident_type is not None:
        rule.incident_type = payload.incident_type.value
    if payload.minimum_severity is not None:
        rule.minimum_severity = payload.minimum_severity.value
    if payload.evidence_type_contains is not None:
        rule.evidence_type_contains = payload.evidence_type_contains
    if payload.medical_follow_up_values is not None:
        rule.medical_follow_up_values = payload.medical_follow_up_values
    if payload.regulatory_required is not None:
        rule.regulatory_required = payload.regulatory_required
    if payload.athlete_linked_required is not None:
        rule.athlete_linked_required = payload.athlete_linked_required
    if payload.required_approval_level is not None:
        rule.required_approval_level = normalize_provider_profile(payload.required_approval_level, "safeguarding_lead")
    if payload.risk_level is not None:
        rule.risk_level = payload.risk_level
    if payload.recommended_review_status is not None:
        rule.recommended_review_status = payload.recommended_review_status
    if payload.block_acceptance is not None:
        rule.block_acceptance = payload.block_acceptance
    if payload.rationale is not None:
        rule.rationale = payload.rationale
    await db.commit()
    await db.refresh(rule)
    return safeguarding_evidence_policy_rule_read(rule)


async def active_safeguarding_evidence_policy_rules(
    db: AsyncSession,
    organization_id: UUID,
    *,
    active: bool | None = True,
) -> list[SafeguardingEvidencePolicyRule]:
    statement = select(SafeguardingEvidencePolicyRule).where(
        SafeguardingEvidencePolicyRule.organization_id == organization_id
    )
    if active is not None:
        statement = statement.where(SafeguardingEvidencePolicyRule.active.is_(active))
    return list(
        (
            await db.scalars(
                statement.order_by(
                    SafeguardingEvidencePolicyRule.active.desc(),
                    SafeguardingEvidencePolicyRule.risk_level.desc(),
                    SafeguardingEvidencePolicyRule.rule_code,
                )
            )
        ).all()
    )


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
    await db.flush()
    await sync_safeguarding_incident_access_controls(db, identity, incident, authz)
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
    await ensure_manage_safeguarding_incident(authz, incident, identity)

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

    await sync_safeguarding_incident_access_controls(db, identity, incident, authz)
    await db.commit()
    await db.refresh(incident)
    return incident


async def apply_safeguarding_incident_investigation_action(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident_id: UUID,
    payload: SafeguardingIncidentInvestigationActionCreate,
    authz: AuthorizationService,
) -> SafeguardingIncidentInvestigationActionRead:
    incident = await db.get(SafeguardingIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await ensure_manage_safeguarding_incident(authz, incident, identity)

    actioned_at = utc_now()
    normalized_action = normalize_provider_profile(payload.action_type, "investigation")
    assigned_to_person_id = payload.assigned_to_person_id
    if payload.assign_to_self:
        assigned_to_person_id = identity.person_id
    if assigned_to_person_id is not None:
        await validate_person_in_organization(db, incident.organization_id, assigned_to_person_id)
        incident.assigned_to_person_id = assigned_to_person_id

    if payload.status is not None:
        incident.status = payload.status
    elif normalized_action in {"triage", "assign", "assign_self"}:
        incident.status = SafeguardingIncidentStatus.TRIAGED
    elif normalized_action in {"investigate", "finding", "follow_up", "escalate"}:
        incident.status = SafeguardingIncidentStatus.INVESTIGATING
    if payload.close_incident or normalized_action in {"resolve", "resolved", "close", "closed"}:
        incident.status = SafeguardingIncidentStatus.CLOSED if normalized_action in {"close", "closed"} else SafeguardingIncidentStatus.RESOLVED
        incident.resolved_at = incident.resolved_at or actioned_at

    if payload.severity is not None:
        incident.severity = payload.severity
    elif normalized_action == "escalate" and incident.severity in {
        SafeguardingIncidentSeverity.LOW,
        SafeguardingIncidentSeverity.MEDIUM,
    }:
        incident.severity = SafeguardingIncidentSeverity.HIGH

    if payload.parent_notified:
        incident.parent_notified_at = incident.parent_notified_at or actioned_at
    if payload.medical_follow_up_required is not None:
        incident.medical_follow_up_required = payload.medical_follow_up_required
    if payload.regulatory_report_required is not None:
        incident.regulatory_report_required = payload.regulatory_report_required
    elif normalized_action == "escalate" and incident.severity in {
        SafeguardingIncidentSeverity.HIGH,
        SafeguardingIncidentSeverity.CRITICAL,
    }:
        incident.regulatory_report_required = True

    action_summary = safeguarding_investigation_action_summary(
        normalized_action,
        payload,
        incident,
        actioned_at,
    )
    append_safeguarding_incident_resolution_note(incident, actioned_at, action_summary)
    await sync_safeguarding_incident_access_controls(db, identity, incident, authz)

    await db.commit()
    await db.refresh(incident)
    return SafeguardingIncidentInvestigationActionRead(
        incident_id=incident.id,
        organization_id=incident.organization_id,
        action_type=normalized_action,
        status=incident.status,
        severity=incident.severity,
        assigned_to_person_id=incident.assigned_to_person_id,
        regulatory_report_required=incident.regulatory_report_required,
        medical_follow_up_required=incident.medical_follow_up_required,
        action_summary=action_summary,
        resolution_notes=incident.resolution_notes,
        actioned_at=actioned_at,
    )


async def upload_safeguarding_incident_evidence(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident_id: UUID,
    payload: SafeguardingIncidentEvidenceUploadCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> SafeguardingIncidentEvidenceUploadRead:
    incident = await db.get(SafeguardingIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await ensure_manage_safeguarding_incident(authz, incident, identity)
    content = decode_safeguarding_upload_content(payload.content_base64)
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Evidence file is empty")
    selected_settings = settings or get_settings()
    uploaded_at = utc_now()
    checksum = sha256(content).hexdigest()
    safe_name = safe_safeguarding_upload_filename(payload.filename, fallback="incident-evidence")
    storage_name = f"{checksum[:16]}-{safe_name}"
    relative_path = (
        Path(str(incident.organization_id))
        / str(incident.id)
        / storage_name
    ).as_posix()
    stored = put_object(
        selected_settings,
        local_root=selected_settings.safeguarding_incident_evidence_dir,
        local_url_prefix=selected_settings.safeguarding_incident_evidence_url_prefix,
        key=relative_path,
        content=content,
        content_type=payload.content_type or "application/octet-stream",
    )
    evidence_note = (
        f"Evidence uploaded: {safe_name} ({payload.evidence_type}, {payload.review_status}, "
        f"{len(content)} bytes, checksum {checksum}, {stored.url})."
    )
    if payload.notes:
        evidence_note = f"{evidence_note} Notes: {payload.notes}"
    append_safeguarding_incident_resolution_note(incident, uploaded_at, evidence_note)
    if payload.review_status == "accepted" and incident.status == SafeguardingIncidentStatus.OPEN:
        incident.status = SafeguardingIncidentStatus.INVESTIGATING

    await sync_safeguarding_incident_access_controls(db, identity, incident, authz)
    await db.commit()
    await db.refresh(incident)
    return SafeguardingIncidentEvidenceUploadRead(
        incident_id=incident.id,
        organization_id=incident.organization_id,
        filename=safe_name,
        content_type=payload.content_type or "application/octet-stream",
        evidence_type=payload.evidence_type,
        review_status=payload.review_status,
        size_bytes=len(content),
        checksum=checksum,
        evidence_url=stored.url,
        storage_key=relative_path,
        uploaded_at=uploaded_at,
        incident=safeguarding_incident_read(incident),
    )


async def create_signed_safeguarding_incident_evidence_link(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident_id: UUID,
    payload: SafeguardingIncidentEvidenceLinkCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> SafeguardingIncidentEvidenceLinkRead:
    incident = await db.get(SafeguardingIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await ensure_review_safeguarding_incident_evidence(authz, incident, identity)
    selected_settings = settings or get_settings()
    storage_name = validate_safeguarding_incident_evidence_storage_key(
        payload.storage_key,
        incident.organization_id,
        incident.id,
    )
    content = get_object(
        selected_settings,
        local_root=selected_settings.safeguarding_incident_evidence_dir,
        key=payload.storage_key,
    )
    checksum = sha256(content).hexdigest()
    if payload.checksum and payload.checksum != checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Evidence checksum does not match stored object")
    now = utc_now()
    expires_at = now + timedelta(
        seconds=payload.ttl_seconds or selected_settings.safeguarding_incident_evidence_url_ttl_seconds
    )
    signed_url = signed_safeguarding_incident_evidence_url(
        selected_settings,
        incident.organization_id,
        incident.id,
        storage_name,
        checksum,
        expires_at,
    )
    evidence_url = f"{selected_settings.safeguarding_incident_evidence_url_prefix.rstrip('/')}/{payload.storage_key}"
    return SafeguardingIncidentEvidenceLinkRead(
        incident_id=incident.id,
        organization_id=incident.organization_id,
        signed_url=signed_url,
        expires_at=expires_at,
        filename=payload.filename,
        content_type=payload.content_type,
        checksum=checksum,
        size_bytes=len(content),
        evidence_url=evidence_url,
        storage_key=payload.storage_key,
    )


async def list_safeguarding_incident_evidence_review_queue(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    review_status: str | None = None,
    settings: Settings | None = None,
) -> list[SafeguardingIncidentEvidenceReviewItemRead]:
    await ensure_org_manage(authz, organization_id, identity)
    selected_settings = settings or get_settings()
    rule_rows = await active_safeguarding_evidence_policy_rules(db, organization_id)
    incidents = await list_safeguarding_incidents(db, organization_id)
    items: list[SafeguardingIncidentEvidenceReviewItemRead] = []
    for incident in incidents:
        incident_items = safeguarding_incident_evidence_review_items(
            incident,
            selected_settings,
            rule_rows,
        )
        items.extend(incident_items)
    if review_status:
        normalized_status = review_status.strip().lower()
        items = [item for item in items if item.review_status == normalized_status]
    return sorted(
        items,
        key=lambda item: (item.review_status == "needs_review", item.uploaded_at),
        reverse=True,
    )


async def get_safeguarding_incident_evidence_approval_policy(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident_id: UUID,
    storage_key: str,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> SafeguardingIncidentEvidenceApprovalPolicyRead:
    incident = await db.get(SafeguardingIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await ensure_review_safeguarding_incident_evidence(authz, incident, identity)
    selected_settings = settings or get_settings()
    validate_safeguarding_incident_evidence_storage_key(
        storage_key,
        incident.organization_id,
        incident.id,
    )
    rule_rows = await active_safeguarding_evidence_policy_rules(db, incident.organization_id)
    items = safeguarding_incident_evidence_review_items(incident, selected_settings, rule_rows)
    item = next((candidate for candidate in items if candidate.storage_key == storage_key), None)
    if item is None or item.approval_policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence upload not found in case notes")
    return item.approval_policy


async def review_safeguarding_incident_evidence(
    db: AsyncSession,
    identity: CurrentIdentity,
    incident_id: UUID,
    payload: SafeguardingIncidentEvidenceReviewActionCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> SafeguardingIncidentEvidenceReviewActionRead:
    incident = await db.get(SafeguardingIncident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await ensure_org_manage(authz, incident.organization_id, identity)
    selected_settings = settings or get_settings()
    storage_name = validate_safeguarding_incident_evidence_storage_key(
        payload.storage_key,
        incident.organization_id,
        incident.id,
    )
    rule_rows = await active_safeguarding_evidence_policy_rules(db, incident.organization_id)
    existing_items = safeguarding_incident_evidence_review_items(incident, selected_settings, rule_rows)
    current_item = next((item for item in existing_items if item.storage_key == payload.storage_key), None)
    if current_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence upload not found in case notes")
    content = get_object(
        selected_settings,
        local_root=selected_settings.safeguarding_incident_evidence_dir,
        key=payload.storage_key,
    )
    checksum = sha256(content).hexdigest()
    if payload.checksum and payload.checksum != checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Evidence checksum does not match stored object")

    reviewed_at = utc_now()
    normalized_status = payload.review_status.strip().lower()
    if (
        normalized_status == "accepted"
        and current_item.approval_policy is not None
        and current_item.approval_policy.acceptance_blocked_by_policy
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence approval policy requires escalation before acceptance",
        )
    if normalized_status in {"accepted", "needs_review"} and incident.status == SafeguardingIncidentStatus.OPEN:
        incident.status = SafeguardingIncidentStatus.INVESTIGATING
    if normalized_status == "escalated" or payload.escalate_incident:
        incident.status = SafeguardingIncidentStatus.INVESTIGATING
        if incident.severity in {
            SafeguardingIncidentSeverity.LOW,
            SafeguardingIncidentSeverity.MEDIUM,
        }:
            incident.severity = SafeguardingIncidentSeverity.HIGH
        if payload.regulatory_report_required is None:
            incident.regulatory_report_required = True
    if payload.regulatory_report_required is not None:
        incident.regulatory_report_required = payload.regulatory_report_required

    action_summary = safeguarding_evidence_review_summary(
        filename=payload.filename,
        storage_key=payload.storage_key,
        storage_name=storage_name,
        review_status=normalized_status,
        reviewer_person_id=identity.person_id,
        checksum=checksum,
        size_bytes=len(content),
        review_notes=payload.review_notes,
    )
    append_safeguarding_incident_resolution_note(incident, reviewed_at, action_summary)
    await sync_safeguarding_incident_access_controls(db, identity, incident, authz)

    await db.commit()
    await db.refresh(incident)
    updated_rule_rows = await active_safeguarding_evidence_policy_rules(db, incident.organization_id)
    updated_items = safeguarding_incident_evidence_review_items(incident, selected_settings, updated_rule_rows)
    updated_item = next((item for item in updated_items if item.storage_key == payload.storage_key), None)
    return SafeguardingIncidentEvidenceReviewActionRead(
        incident_id=incident.id,
        organization_id=incident.organization_id,
        filename=payload.filename,
        review_status=normalized_status,
        reviewer_person_id=identity.person_id,
        reviewed_at=reviewed_at,
        checksum=checksum,
        size_bytes=len(content),
        storage_key=payload.storage_key,
        incident_status=incident.status,
        incident_severity=incident.severity,
        regulatory_report_required=incident.regulatory_report_required,
        action_summary=action_summary,
        resolution_notes=incident.resolution_notes,
        approval_policy=updated_item.approval_policy if updated_item is not None else None,
    )


async def read_signed_safeguarding_incident_evidence(
    organization_id: UUID,
    incident_id: UUID,
    filename: str,
    checksum: str,
    expires: int,
    signature: str,
    settings: Settings | None = None,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    if "/" in filename or "\\" in filename or filename in {"", ".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid evidence name")
    if expires < int(time.time()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Evidence link expired")
    expected = safeguarding_incident_evidence_signature(
        selected_settings,
        organization_id,
        incident_id,
        filename,
        checksum,
        expires,
    )
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid evidence signature")
    storage_key = (Path(str(organization_id)) / str(incident_id) / filename).as_posix()
    content = get_object(
        selected_settings,
        local_root=selected_settings.safeguarding_incident_evidence_dir,
        key=storage_key,
    )
    actual_checksum = sha256(content).hexdigest()
    if actual_checksum != checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Evidence checksum mismatch")
    return {
        "content": content,
        "content_type": safeguarding_evidence_content_type_for_filename(filename),
        "filename": public_safeguarding_evidence_filename(filename),
        "checksum": actual_checksum,
    }


def validate_safeguarding_incident_evidence_storage_key(
    storage_key: str,
    organization_id: UUID,
    incident_id: UUID,
) -> str:
    expected_prefix = (Path(str(organization_id)) / str(incident_id)).as_posix() + "/"
    normalized = storage_key.strip()
    if (
        not normalized.startswith(expected_prefix)
        or "\\" in normalized
        or "/../" in normalized
        or normalized.endswith("/")
    ):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid evidence storage key")
    storage_name = normalized.rsplit("/", 1)[-1]
    if storage_name in {"", ".", ".."}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid evidence storage key")
    return storage_name


def signed_safeguarding_incident_evidence_url(
    settings: Settings,
    organization_id: UUID,
    incident_id: UUID,
    storage_name: str,
    checksum: str,
    expires_at: datetime,
) -> str:
    expires = int(expires_at.timestamp())
    signature = safeguarding_incident_evidence_signature(
        settings,
        organization_id,
        incident_id,
        storage_name,
        checksum,
        expires,
    )
    safe_name = quote(storage_name, safe="")
    return (
        f"{settings.api_prefix}/safeguarding/incident-evidence/{organization_id}/{incident_id}/{safe_name}"
        f"?checksum={checksum}&expires={expires}&signature={signature}"
    )


def safeguarding_incident_evidence_signature(
    settings: Settings,
    organization_id: UUID,
    incident_id: UUID,
    storage_name: str,
    checksum: str,
    expires: int,
) -> str:
    payload = f"{organization_id}/{incident_id}/{storage_name}:{checksum}:{expires}"
    digest = hmac.new(
        safeguarding_incident_evidence_signing_key(settings),
        payload.encode(),
        sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def safeguarding_incident_evidence_signing_key(settings: Settings) -> bytes:
    key = resolve_secret_sync(
        settings,
        env_value=settings.safeguarding_incident_evidence_signing_key,
        path=settings.safeguarding_incident_evidence_signing_key_secret_path,
        field_name=settings.safeguarding_incident_evidence_signing_key_secret_field,
        label="safeguarding incident evidence signing key",
    )
    return (key or "local-safeguarding-evidence-key").encode()


def public_safeguarding_evidence_filename(storage_name: str) -> str:
    parts = storage_name.split("-", 1)
    return parts[1] if len(parts) == 2 else storage_name


def safeguarding_evidence_content_type_for_filename(filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower()
    if extension in {"jpg", "jpeg"}:
        return "image/jpeg"
    if extension == "png":
        return "image/png"
    if extension == "pdf":
        return "application/pdf"
    if extension == "txt":
        return "text/plain; charset=utf-8"
    return "application/octet-stream"


def decode_safeguarding_upload_content(content_base64: str) -> bytes:
    encoded = content_base64.split(",", 1)[1] if "," in content_base64 else content_base64
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, BinasciiError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid file encoding") from exc


def safeguarding_incident_evidence_review_items(
    incident: SafeguardingIncident,
    settings: Settings,
    rule_rows: list[SafeguardingEvidencePolicyRule] | None = None,
) -> list[SafeguardingIncidentEvidenceReviewItemRead]:
    reviews = safeguarding_incident_evidence_review_updates(incident)
    items: list[SafeguardingIncidentEvidenceReviewItemRead] = []
    for line in (incident.resolution_notes or "").splitlines():
        item = parse_safeguarding_incident_evidence_upload_note(incident, settings, line)
        if item is None:
            continue
        review = reviews.get(item.storage_key)
        if review is not None:
            item.review_status = review["review_status"]
            item.latest_reviewed_at = review["reviewed_at"]
            item.latest_review_notes = review["notes"]
        item.approval_policy = safeguarding_incident_evidence_approval_policy(incident, item, rule_rows or [])
        items.append(item)
    return items


def safeguarding_incident_evidence_approval_policy(
    incident: SafeguardingIncident,
    item: SafeguardingIncidentEvidenceReviewItemRead,
    rule_rows: list[SafeguardingEvidencePolicyRule],
) -> SafeguardingIncidentEvidenceApprovalPolicyRead:
    required_levels: list[str] = []
    rationale: list[str] = []
    matched_rule_codes: list[str] = []
    rule_risk_levels: list[str] = []
    rule_recommended_statuses: list[str] = []
    block_acceptance = False

    add_approval_level(
        required_levels,
        rationale,
        "safeguarding_lead",
        "Every safeguarding evidence item requires safeguarding lead review before acceptance.",
    )
    if incident.incident_type in {SafeguardingIncidentType.SAFEGUARDING, SafeguardingIncidentType.MISCONDUCT}:
        add_approval_level(
            required_levels,
            rationale,
            "safeguarding_committee",
            "Safeguarding or misconduct evidence requires committee visibility.",
        )
    if incident.severity in {SafeguardingIncidentSeverity.HIGH, SafeguardingIncidentSeverity.CRITICAL}:
        add_approval_level(
            required_levels,
            rationale,
            "senior_operator",
            "High or critical incident severity requires senior operator escalation.",
        )
    if (
        incident.incident_type in MEDICAL_INCIDENT_TYPES
        or incident.medical_follow_up_required in BLOCKING_MEDICAL_FOLLOW_UP_VALUES
        or contains_any(item.evidence_type, {"medical", "injury", "clearance", "concussion"})
    ):
        add_approval_level(
            required_levels,
            rationale,
            "medical",
            "Medical or injury-linked evidence requires medical review before operational closure.",
        )
    if incident.regulatory_report_required or incident.severity == SafeguardingIncidentSeverity.CRITICAL:
        add_approval_level(
            required_levels,
            rationale,
            "regulatory",
            "Regulatory or critical cases require reporting-policy review.",
        )
    if incident.athlete_person_id is not None and (
        incident.severity in {SafeguardingIncidentSeverity.HIGH, SafeguardingIncidentSeverity.CRITICAL}
        or incident.incident_type in {SafeguardingIncidentType.SAFEGUARDING, SafeguardingIncidentType.MISCONDUCT}
    ):
        add_approval_level(
            required_levels,
            rationale,
            "guardian_communications",
            "Athlete-linked high-risk evidence requires guardian communication review.",
        )
    for rule in rule_rows:
        if not safeguarding_evidence_policy_rule_matches(rule, incident, item):
            continue
        matched_rule_codes.append(rule.rule_code)
        add_approval_level(required_levels, rationale, rule.required_approval_level, rule.rationale)
        rule_risk_levels.append(rule.risk_level)
        rule_recommended_statuses.append(rule.recommended_review_status)
        block_acceptance = block_acceptance or rule.block_acceptance

    policy_risk_level = safeguarding_evidence_policy_risk_level(incident, required_levels)
    policy_risk_level = highest_safeguarding_policy_risk([policy_risk_level, *rule_risk_levels])
    approval_required = policy_risk_level in {"high", "critical"}
    if item.review_status == "accepted":
        approval_status = "approved"
        missing_levels: list[str] = []
    elif item.review_status == "rejected":
        approval_status = "rejected"
        missing_levels = []
    elif item.review_status == "escalated":
        approval_status = "escalated"
        missing_levels = []
    elif approval_required:
        approval_status = "escalation_required"
        missing_levels = required_levels
    else:
        approval_status = "lead_review_pending"
        missing_levels = required_levels[:1]
    recommended_status = item.review_status
    if item.review_status == "needs_review":
        recommended_status = highest_recommended_review_status(
            [
                "escalated" if approval_required else item.review_status,
                *rule_recommended_statuses,
            ]
        )
    acceptance_blocked = (approval_required or block_acceptance) and item.review_status == "needs_review"
    policy_summary = safeguarding_evidence_policy_summary(
        policy_risk_level,
        approval_status,
        required_levels,
        missing_levels,
    )
    return SafeguardingIncidentEvidenceApprovalPolicyRead(
        incident_id=item.incident_id,
        organization_id=item.organization_id,
        incident_title=item.incident_title,
        incident_status=item.incident_status,
        incident_severity=item.incident_severity,
        filename=item.filename,
        content_type=item.content_type,
        evidence_type=item.evidence_type,
        review_status=item.review_status,
        policy_risk_level=policy_risk_level,
        approval_required=approval_required,
        approval_status=approval_status,
        required_approval_levels=required_levels,
        missing_approval_levels=missing_levels,
        recommended_review_status=recommended_status,
        acceptance_blocked_by_policy=acceptance_blocked,
        policy_summary=policy_summary,
        rationale=rationale,
        matched_rule_codes=matched_rule_codes,
    )


def add_approval_level(
    levels: list[str],
    rationale: list[str],
    level: str,
    reason: str,
) -> None:
    if level not in levels:
        levels.append(level)
        rationale.append(reason)


def safeguarding_evidence_policy_risk_level(
    incident: SafeguardingIncident,
    required_levels: list[str],
) -> str:
    if incident.severity == SafeguardingIncidentSeverity.CRITICAL:
        return "critical"
    if (
        incident.severity == SafeguardingIncidentSeverity.HIGH
        or len(required_levels) >= 3
        or incident.incident_type in {SafeguardingIncidentType.SAFEGUARDING, SafeguardingIncidentType.MISCONDUCT}
    ):
        return "high"
    if incident.severity == SafeguardingIncidentSeverity.MEDIUM or len(required_levels) == 2:
        return "medium"
    return "low"


def safeguarding_evidence_policy_rule_matches(
    rule: SafeguardingEvidencePolicyRule,
    incident: SafeguardingIncident,
    item: SafeguardingIncidentEvidenceReviewItemRead,
) -> bool:
    if not rule.active:
        return False
    if rule.incident_type and rule.incident_type != incident.incident_type.value:
        return False
    if rule.minimum_severity and severity_rank(incident.severity.value) < severity_rank(rule.minimum_severity):
        return False
    if rule.evidence_type_contains and rule.evidence_type_contains.lower() not in item.evidence_type.lower():
        return False
    if rule.medical_follow_up_values:
        values = {value.strip().lower() for value in rule.medical_follow_up_values.split(",") if value.strip()}
        if incident.medical_follow_up_required.lower() not in values:
            return False
    if rule.regulatory_required is not None and incident.regulatory_report_required is not rule.regulatory_required:
        return False
    if rule.athlete_linked_required is not None and (incident.athlete_person_id is not None) is not rule.athlete_linked_required:
        return False
    return True


def severity_rank(value: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(value, 0)


def highest_safeguarding_policy_risk(values: list[str]) -> str:
    return max((value for value in values if value), key=severity_rank, default="low")


def highest_recommended_review_status(statuses: list[str]) -> str:
    status_rank = {"accepted": 1, "needs_review": 2, "rejected": 3, "escalated": 4}
    return max(
        (status_value for status_value in statuses if status_value),
        key=lambda value: status_rank.get(value, 0),
        default="needs_review",
    )


def contains_any(value: str, needles: set[str]) -> bool:
    lowered = value.lower()
    return any(needle in lowered for needle in needles)


def safeguarding_evidence_policy_summary(
    risk_level: str,
    approval_status: str,
    required_levels: list[str],
    missing_levels: list[str],
) -> str:
    if approval_status == "approved":
        return f"{risk_level.title()}-risk evidence is approved under {', '.join(required_levels)} policy."
    if approval_status == "escalated":
        return f"{risk_level.title()}-risk evidence has been escalated for required policy review."
    if approval_status == "rejected":
        return f"{risk_level.title()}-risk evidence was rejected; policy review is closed."
    if missing_levels:
        return f"{risk_level.title()}-risk evidence still needs {', '.join(missing_levels)} approval."
    return f"{risk_level.title()}-risk evidence is waiting for safeguarding lead review."


def safeguarding_evidence_policy_rule_read(
    rule: SafeguardingEvidencePolicyRule,
) -> SafeguardingEvidencePolicyRuleRead:
    return SafeguardingEvidencePolicyRuleRead(
        id=rule.id,
        organization_id=rule.organization_id,
        rule_code=rule.rule_code,
        title=rule.title,
        active=rule.active,
        incident_type=SafeguardingIncidentType(rule.incident_type) if rule.incident_type else None,
        minimum_severity=SafeguardingIncidentSeverity(rule.minimum_severity) if rule.minimum_severity else None,
        evidence_type_contains=rule.evidence_type_contains,
        medical_follow_up_values=rule.medical_follow_up_values,
        regulatory_required=rule.regulatory_required,
        athlete_linked_required=rule.athlete_linked_required,
        required_approval_level=rule.required_approval_level,
        risk_level=rule.risk_level,
        recommended_review_status=rule.recommended_review_status,
        block_acceptance=rule.block_acceptance,
        rationale=rule.rationale,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def safeguarding_incident_access_grant_read(
    grant: SafeguardingIncidentAccessGrant,
) -> SafeguardingIncidentAccessGrantRead:
    return SafeguardingIncidentAccessGrantRead(
        id=grant.id,
        organization_id=grant.organization_id,
        incident_id=grant.incident_id,
        person_id=grant.person_id,
        relation=grant.relation,
        active=grant.active,
        granted_by_person_id=grant.granted_by_person_id,
        revoked_by_person_id=grant.revoked_by_person_id,
        granted_reason=grant.granted_reason,
        revoked_reason=grant.revoked_reason,
        revoked_at=grant.revoked_at,
        created_at=grant.created_at,
        updated_at=grant.updated_at,
    )


def parse_safeguarding_incident_evidence_upload_note(
    incident: SafeguardingIncident,
    settings: Settings,
    line: str,
) -> SafeguardingIncidentEvidenceReviewItemRead | None:
    match = search(
        r"^(?P<uploaded_at>\S+) Evidence uploaded: (?P<filename>.+?) "
        r"\((?P<evidence_type>[^,]+), (?P<review_status>[^,]+), "
        r"(?P<size_bytes>\d+) bytes, checksum (?P<checksum>[a-fA-F0-9]{64}), "
        r"(?P<evidence_url>[^)]+)\)\.(?: Notes: (?P<notes>.*))?$",
        line,
    )
    if match is None:
        return None
    evidence_url = match.group("evidence_url")
    storage_key = storage_key_from_safeguarding_incident_evidence_url(settings, evidence_url)
    if storage_key is None:
        return None
    try:
        validate_safeguarding_incident_evidence_storage_key(
            storage_key,
            incident.organization_id,
            incident.id,
        )
        uploaded_at = datetime.fromisoformat(match.group("uploaded_at"))
    except (HTTPException, ValueError):
        return None
    filename = match.group("filename")
    return SafeguardingIncidentEvidenceReviewItemRead(
        incident_id=incident.id,
        organization_id=incident.organization_id,
        incident_title=incident.title,
        incident_status=incident.status,
        incident_severity=incident.severity,
        filename=filename,
        content_type=safeguarding_evidence_content_type_for_filename(filename),
        evidence_type=match.group("evidence_type").strip(),
        review_status=match.group("review_status").strip().lower(),
        size_bytes=int(match.group("size_bytes")),
        checksum=match.group("checksum").lower(),
        evidence_url=evidence_url,
        storage_key=storage_key,
        uploaded_at=uploaded_at,
        latest_review_notes=match.group("notes"),
    )


def storage_key_from_safeguarding_incident_evidence_url(
    settings: Settings,
    evidence_url: str,
) -> str | None:
    prefix = settings.safeguarding_incident_evidence_url_prefix.rstrip("/") + "/"
    if not evidence_url.startswith(prefix):
        return None
    storage_key = evidence_url.removeprefix(prefix).strip()
    return storage_key or None


def safeguarding_incident_evidence_review_updates(
    incident: SafeguardingIncident,
) -> dict[str, dict[str, object]]:
    reviews: dict[str, dict[str, object]] = {}
    for line in (incident.resolution_notes or "").splitlines():
        match = search(
            r"^(?P<reviewed_at>\S+) Evidence review: (?P<storage_key>\S+) "
            r"\((?P<filename>.*?)\) marked "
            r"(?P<review_status>needs_review|accepted|rejected|escalated) by "
            r"(?P<reviewer>[^.]+)\. Checksum (?P<checksum>[a-fA-F0-9]{64}), "
            r"(?P<size_bytes>\d+) bytes\.(?: Notes: (?P<notes>.*))?$",
            line,
        )
        if match is None:
            continue
        try:
            reviewed_at = datetime.fromisoformat(match.group("reviewed_at"))
        except ValueError:
            continue
        storage_key = match.group("storage_key")
        prior = reviews.get(storage_key)
        if prior is not None and prior["reviewed_at"] >= reviewed_at:
            continue
        reviews[storage_key] = {
            "review_status": match.group("review_status"),
            "reviewed_at": reviewed_at,
            "notes": match.group("notes"),
        }
    return reviews


def safeguarding_evidence_review_summary(
    *,
    filename: str,
    storage_key: str,
    storage_name: str,
    review_status: str,
    reviewer_person_id: UUID | None,
    checksum: str,
    size_bytes: int,
    review_notes: str | None,
) -> str:
    safe_filename = safe_safeguarding_upload_filename(filename, fallback=public_safeguarding_evidence_filename(storage_name))
    summary = (
        f"Evidence review: {storage_key} ({safe_filename}) marked {review_status} "
        f"by {reviewer_person_id or 'unknown'}. Checksum {checksum}, {size_bytes} bytes."
    )
    if review_notes:
        summary = f"{summary} Notes: {review_notes}"
    return summary


def safe_safeguarding_upload_filename(filename: str, *, fallback: str) -> str:
    cleaned = sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip(".-")
    return cleaned[:180] or fallback


def safeguarding_incident_read(incident: SafeguardingIncident) -> SafeguardingIncidentRead:
    return SafeguardingIncidentRead(
        id=incident.id,
        organization_id=incident.organization_id,
        event_id=incident.event_id,
        team_id=incident.team_id,
        athlete_person_id=incident.athlete_person_id,
        reported_by_person_id=incident.reported_by_person_id,
        assigned_to_person_id=incident.assigned_to_person_id,
        incident_type=incident.incident_type,
        severity=incident.severity,
        status=incident.status,
        occurred_at=incident.occurred_at,
        location=incident.location,
        title=incident.title,
        description=incident.description,
        immediate_action=incident.immediate_action,
        parent_notified_at=incident.parent_notified_at,
        medical_follow_up_required=incident.medical_follow_up_required,
        regulatory_report_required=incident.regulatory_report_required,
        resolution_notes=incident.resolution_notes,
        resolved_at=incident.resolved_at,
        created_at=incident.created_at,
    )


def safeguarding_investigation_action_summary(
    action_type: str,
    payload: SafeguardingIncidentInvestigationActionCreate,
    incident: SafeguardingIncident,
    actioned_at: datetime,
) -> str:
    parts = [
        f"Investigation action '{action_type}' recorded.",
        f"Status: {incident.status.value}.",
        f"Severity: {incident.severity.value}.",
    ]
    if incident.assigned_to_person_id is not None:
        parts.append(f"Assigned to {incident.assigned_to_person_id}.")
    if payload.finding_summary:
        parts.append(f"Finding: {payload.finding_summary}")
    if payload.next_step:
        parts.append(f"Next step: {payload.next_step}")
    if payload.parent_notified:
        parts.append("Parent/guardian notification confirmed.")
    if incident.medical_follow_up_required in BLOCKING_MEDICAL_FOLLOW_UP_VALUES:
        parts.append(f"Medical follow-up: {incident.medical_follow_up_required}.")
    if incident.regulatory_report_required:
        parts.append("Regulatory reporting required.")
    if incident.resolved_at is not None and incident.status in {
        SafeguardingIncidentStatus.RESOLVED,
        SafeguardingIncidentStatus.CLOSED,
    }:
        parts.append(f"Resolved at {incident.resolved_at.isoformat()}.")
    parts.append(f"Actioned at {actioned_at.isoformat()}.")
    return " ".join(parts)


def append_safeguarding_incident_resolution_note(
    incident: SafeguardingIncident,
    at: datetime,
    message: str,
) -> None:
    entry = f"{at.isoformat()} {message}"
    incident.resolution_notes = "\n".join(part for part in [incident.resolution_notes, entry] if part)


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


async def submit_incident_report_package_to_regulator(
    db: AsyncSession,
    identity: CurrentIdentity,
    package_id: UUID,
    artifact_format: str,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> IncidentReportPackageProviderSubmissionRead:
    package = await db.get(IncidentReportPackage, package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report package not found")
    await ensure_org_manage(authz, package.organization_id, identity)
    incident = await db.get(SafeguardingIncident, package.incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    selected_settings = settings or get_settings()
    submitted_at = utc_now()
    generated_at = datetime.fromtimestamp(int(submitted_at.timestamp()), tz=UTC)
    artifact = build_incident_report_package_artifact(package, incident, artifact_format, generated_at)
    stored = persist_incident_report_package_artifact(package, artifact, selected_settings)
    package.status = IncidentReportPackageStatus.SUBMITTED
    package.submitted_by_person_id = identity.person_id
    package.submitted_at = package.submitted_at or submitted_at
    payload = incident_report_package_regulator_payload(
        package,
        incident,
        artifact,
        stored,
        selected_settings.safeguarding_regulatory_report_provider_profile,
    )
    package.submission_payload = json.dumps(payload, sort_keys=True, default=str)
    append_incident_report_package_note(
        package,
        submitted_at,
        f"Prepared regulatory portal submission in {selected_settings.safeguarding_regulatory_report_delivery_mode} mode.",
    )
    result = await deliver_incident_report_package_regulator_payload(
        selected_settings,
        package,
        payload,
        submitted_at,
        artifact_url=stored["artifact_url"],
        storage_key=stored["storage_key"],
        checksum=str(artifact["checksum"]),
    )
    await db.commit()
    await db.refresh(package)
    return result.model_copy(
        update={
            "provider_reference": package.external_reference,
            "package_status": package.status,
        }
    )


async def deliver_incident_report_package_regulator_payload(
    settings: Settings,
    package: IncidentReportPackage,
    payload: dict[str, object],
    submitted_at: datetime,
    *,
    artifact_url: str,
    storage_key: str,
    checksum: str,
) -> IncidentReportPackageProviderSubmissionRead:
    result = IncidentReportPackageProviderSubmissionRead(
        package_id=package.id,
        organization_id=package.organization_id,
        incident_id=package.incident_id,
        agency_name=package.agency_name,
        jurisdiction=package.jurisdiction,
        provider_profile=str(payload.get("provider_profile") or "standard_regulatory"),
        provider_schema_id=provider_schema_id_from_payload(payload),
        delivery_mode=settings.safeguarding_regulatory_report_delivery_mode,
        delivery_attempted=False,
        delivered=False,
        provider_status_code=None,
        provider_reference=package.external_reference,
        package_status=package.status,
        artifact_url=artifact_url,
        storage_key=storage_key,
        checksum=checksum,
        failure_reason=None,
        submitted_at=submitted_at,
    )
    if settings.safeguarding_regulatory_report_delivery_mode == "record_only":
        append_incident_report_package_note(
            package,
            submitted_at,
            "Record-only regulatory submission; package is ready for manual portal filing.",
        )
        return result.model_copy(
            update={
                "failure_reason": "Record-only regulatory mode; package prepared for manual portal submission.",
            }
        )
    if not settings.safeguarding_regulatory_report_webhook_url:
        failure = "Regulatory webhook mode is enabled but no webhook URL is configured."
        append_incident_report_package_note(package, submitted_at, failure)
        return result.model_copy(update={"failure_reason": failure})

    raw_body = json.dumps(payload, sort_keys=True, default=str).encode()
    timestamp = str(int(submitted_at.timestamp()))
    headers = incident_report_package_regulator_headers(settings, raw_body, timestamp)
    try:
        async with httpx.AsyncClient(timeout=settings.safeguarding_regulatory_report_timeout_seconds) as client:
            response = await client.post(
                settings.safeguarding_regulatory_report_webhook_url,
                json=payload,
                headers=headers,
            )
        delivered = 200 <= response.status_code < 300
        response_payload = parse_insurer_response_json(response.text) if response.text else {}
        if delivered:
            apply_incident_report_package_regulator_response(package, response_payload, submitted_at)
            append_incident_report_package_note(
                package,
                submitted_at,
                f"Regulatory portal accepted submission with HTTP {response.status_code}.",
            )
        else:
            append_incident_report_package_note(
                package,
                submitted_at,
                f"Regulatory portal returned HTTP {response.status_code}.",
            )
        return result.model_copy(
            update={
                "delivery_attempted": True,
                "delivered": delivered,
                "provider_status_code": response.status_code,
                "provider_reference": package.external_reference,
                "package_status": package.status,
                "failure_reason": None if delivered else f"Regulatory webhook returned {response.status_code}: {response.text[:500]}",
            }
        )
    except httpx.HTTPError as error:
        append_incident_report_package_note(
            package,
            submitted_at,
            f"Regulatory portal delivery failed: {error}",
        )
        return result.model_copy(
            update={
                "delivery_attempted": True,
                "failure_reason": f"Regulatory webhook delivery failed: {error}",
            }
        )


def incident_report_package_regulator_payload(
    package: IncidentReportPackage,
    incident: SafeguardingIncident,
    artifact: dict[str, object],
    stored: dict[str, str],
    configured_profile: str | None = None,
) -> dict[str, object]:
    profile = selected_provider_profile(
        configured_profile,
        infer_regulatory_provider_profile(package, incident),
    )
    return {
        "event_type": "incident_report_package.submit",
        "provider_profile": profile,
        "provider_schema": incident_report_package_regulator_provider_schema(
            profile,
            package,
            incident,
            artifact,
            stored,
        ),
        "package_id": str(package.id),
        "organization_id": str(package.organization_id),
        "incident_id": str(package.incident_id),
        "agency_name": package.agency_name,
        "jurisdiction": package.jurisdiction,
        "status": package.status.value,
        "due_at": package.due_at,
        "external_reference": package.external_reference,
        "narrative": package.narrative,
        "checklist_json": package.checklist_json,
        "artifact": {
            "artifact_format": artifact["artifact_format"],
            "filename": artifact["download_filename"],
            "content_type": artifact["content_type"],
            "checksum": artifact["checksum"],
            "size_bytes": artifact["size_bytes"],
            "artifact_url": stored["artifact_url"],
            "storage_key": stored["storage_key"],
        },
        "incident": {
            "title": incident.title,
            "incident_type": incident.incident_type.value,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "occurred_at": incident.occurred_at,
            "location": incident.location,
            "description": incident.description,
            "immediate_action": incident.immediate_action,
            "parent_notified_at": incident.parent_notified_at,
            "medical_follow_up_required": incident.medical_follow_up_required,
            "regulatory_report_required": incident.regulatory_report_required,
        },
    }


def incident_report_package_regulator_provider_schema(
    profile: str,
    package: IncidentReportPackage,
    incident: SafeguardingIncident,
    artifact: dict[str, object],
    stored: dict[str, str],
) -> dict[str, object]:
    field_map = {
        "case_reference": "external_reference",
        "agency": "agency_name",
        "jurisdiction": "jurisdiction",
        "incident_category": "incident.incident_type",
        "severity": "incident.severity",
        "occurred_at": "incident.occurred_at",
        "narrative": "narrative",
        "evidence_uri": "artifact.artifact_url",
    }
    provider_payload: dict[str, object]
    if profile == "school_sport_authority":
        provider_payload = {
            "learner_safety_case": {
                "school_sport_reference": package.external_reference,
                "education_jurisdiction": package.jurisdiction,
                "reporting_body": package.agency_name,
                "learner_activity_context": incident.location,
                "guardian_notification_recorded": incident.parent_notified_at is not None,
                "medical_follow_up": incident.medical_follow_up_required,
                "document_uri": stored["artifact_url"],
            }
        }
    elif profile == "safe_sport":
        provider_payload = {
            "safesport_case": {
                "case_reference": package.external_reference,
                "reporting_organization_id": str(package.organization_id),
                "allegation_type": incident.incident_type.value,
                "risk_level": incident.severity.value,
                "immediate_protective_action": incident.immediate_action,
                "evidence_checksum": artifact["checksum"],
            }
        }
    elif profile == "federation_discipline":
        provider_payload = {
            "disciplinary_notice": {
                "federation_reference": package.external_reference,
                "competition_or_event_location": incident.location,
                "incident_status": incident.status.value,
                "rules_checklist": package.checklist_json,
                "artifact_storage_key": stored["storage_key"],
            }
        }
    else:
        provider_payload = {
            "statutory_incident_report": {
                "portal_reference": package.external_reference,
                "agency": package.agency_name,
                "jurisdiction": package.jurisdiction,
                "incident_title": incident.title,
                "incident_summary": incident.description,
                "artifact_url": stored["artifact_url"],
            }
        }
    return {
        "schema_id": provider_schema_id("regulatory", profile),
        "version": "1.0",
        "profile": profile,
        "required_fields": [
            "agency_name",
            "jurisdiction",
            "incident.title",
            "incident.occurred_at",
            "artifact.artifact_url",
            "artifact.checksum",
        ],
        "field_map": field_map,
        "status_mapping": {
            "submitted": "submitted",
            "accepted": "accepted",
            "rejected": "rejected",
            "withdrawn": "withdrawn",
        },
        "provider_payload": provider_payload,
    }


def incident_report_package_regulator_headers(
    settings: Settings,
    raw_body: bytes,
    timestamp: str,
) -> dict[str, str]:
    signing_key = resolve_secret_sync(
        settings,
        env_value=settings.safeguarding_regulatory_report_webhook_key,
        path=settings.safeguarding_regulatory_report_webhook_key_secret_path,
        field_name=settings.safeguarding_regulatory_report_webhook_key_secret_field,
        label="regulatory report webhook key",
    )
    key = (signing_key or settings.agent_webhook_key or "local-regulatory-report-key").encode()
    signature = hmac.new(key, timestamp.encode() + b"." + raw_body, sha256).hexdigest()
    return {
        "content-type": "application/json",
        "x-afrolete-regulatory-timestamp": timestamp,
        "x-afrolete-regulatory-signature": signature,
    }


def apply_incident_report_package_regulator_response(
    package: IncidentReportPackage,
    response_payload: dict[str, object],
    submitted_at: datetime,
) -> None:
    provider_reference = response_payload.get("external_reference") or response_payload.get("provider_reference")
    if provider_reference:
        package.external_reference = str(provider_reference)[:240]
    status_value = response_payload.get("status") or response_payload.get("package_status")
    if status_value:
        try:
            package.status = IncidentReportPackageStatus(str(status_value).lower())
        except ValueError:
            pass
    if package.status == IncidentReportPackageStatus.ACCEPTED:
        package.accepted_at = package.accepted_at or submitted_at
    notes = response_payload.get("notes")
    if notes:
        append_incident_report_package_note(package, submitted_at, str(notes))


def append_incident_report_package_note(
    package: IncidentReportPackage,
    at: datetime,
    message: str,
) -> None:
    entry = f"{at.isoformat()} {message}"
    package.notes = f"{package.notes}\n{entry}" if package.notes else entry


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


async def create_insurance_policy(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: InsurancePolicyCreate,
    authz: AuthorizationService,
) -> InsurancePolicy:
    await ensure_org_manage(authz, payload.organization_id, identity)
    existing = await db.scalar(
        select(InsurancePolicy).where(
            InsurancePolicy.organization_id == payload.organization_id,
            InsurancePolicy.policy_number == payload.policy_number,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insurance policy number already exists")
    policy = InsurancePolicy(**payload.model_dump())
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


async def list_insurance_policies(
    db: AsyncSession,
    organization_id: UUID,
    status_filter: str | None = None,
) -> list[InsurancePolicyRead]:
    statement = select(InsurancePolicy).where(InsurancePolicy.organization_id == organization_id)
    if status_filter is not None:
        statement = statement.where(InsurancePolicy.status == status_filter)
    policies = list(
        (
            await db.scalars(
                statement.order_by(
                    InsurancePolicy.expires_on.asc(),
                    InsurancePolicy.name.asc(),
                    InsurancePolicy.created_at.desc(),
                )
            )
        ).all()
    )
    return [
        await insurance_policy_read(db, policy)
        for policy in policies
    ]


async def update_insurance_policy(
    db: AsyncSession,
    identity: CurrentIdentity,
    policy_id: UUID,
    payload: InsurancePolicyUpdate,
    authz: AuthorizationService,
) -> InsurancePolicy:
    policy = await get_insurance_policy(db, policy_id)
    await ensure_org_manage(authz, policy.organization_id, identity)
    update_data = payload.model_dump(exclude_unset=True)
    effective_on = update_data.get("effective_on", policy.effective_on)
    expires_on = update_data.get("expires_on", policy.expires_on)
    if expires_on < effective_on:
        raise HTTPException(status_code=422, detail="expires_on must be on or after effective_on")
    if "policy_number" in update_data and update_data["policy_number"] != policy.policy_number:
        existing = await db.scalar(
            select(InsurancePolicy).where(
                InsurancePolicy.organization_id == policy.organization_id,
                InsurancePolicy.policy_number == update_data["policy_number"],
                InsurancePolicy.id != policy.id,
            )
        )
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insurance policy number already exists")
    for field, value in update_data.items():
        setattr(policy, field, value)
    await db.commit()
    await db.refresh(policy)
    return policy


async def insurance_portfolio_summary(
    db: AsyncSession,
    organization_id: UUID,
) -> InsurancePortfolioSummaryRead:
    policies = list(
        (
            await db.scalars(
                select(InsurancePolicy).where(InsurancePolicy.organization_id == organization_id)
            )
        ).all()
    )
    claims = list(
        (
            await db.scalars(
                select(IncidentInsuranceClaim).where(IncidentInsuranceClaim.organization_id == organization_id)
            )
        ).all()
    )
    today = today_utc()
    active_policies = [policy for policy in policies if insurance_policy_active_on(policy, today)]
    expiring_policies = [policy for policy in policies if insurance_policy_renewal_due(policy, today)]
    return InsurancePortfolioSummaryRead(
        organization_id=organization_id,
        policy_count=len(policies),
        active_policy_count=len(active_policies),
        expiring_policy_count=len(expiring_policies),
        annual_premium_cents=sum(policy.premium_cents for policy in active_policies),
        coverage_limit_cents=sum(policy.coverage_limit_cents for policy in active_policies),
        claim_count=len(claims),
        open_claim_count=sum(1 for claim in claims if claim.status in OPEN_INSURANCE_CLAIM_STATUSES),
        paid_claims_cents=sum(claim.paid_amount_cents for claim in claims),
        currencies=sorted({policy.currency for policy in policies} | {claim.currency for claim in claims}),
        renewal_alerts=[
            f"{policy.name} ({policy.policy_number}) expires on {policy.expires_on.isoformat()}."
            for policy in expiring_policies[:10]
        ],
    )


async def verify_insurance_coverage(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: InsuranceCoverageVerificationCreate,
    authz: AuthorizationService,
) -> InsuranceCoverageVerificationRead:
    await ensure_org_manage(authz, payload.organization_id, identity)
    activity_date = payload.activity_date or today_utc()
    if payload.incident_id is not None:
        incident = await db.get(SafeguardingIncident, payload.incident_id)
        if incident is None or incident.organization_id != payload.organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
        activity_date = incident.occurred_at.date()
    policy = None
    if payload.policy_id is not None:
        policy = await get_insurance_policy_for_organization(db, payload.policy_id, payload.organization_id)
    else:
        policy = await best_insurance_policy_for_claim_type(
            db,
            payload.organization_id,
            payload.claim_type,
            activity_date,
        )
    if policy is None:
        return InsuranceCoverageVerificationRead(
            organization_id=payload.organization_id,
            claim_type=payload.claim_type,
            policy_id=None,
            policy_number=None,
            provider_name=None,
            covered=False,
            coverage_limit_cents=0,
            deductible_cents=0,
            estimated_payable_cents=0,
            currency="USD",
            reason="No active matching policy covers this claim type and date.",
            renewal_due=False,
            certificate_url=None,
        )
    covers_type = insurance_policy_covers_claim_type(policy, payload.claim_type)
    active = insurance_policy_active_on(policy, activity_date)
    within_limit = payload.amount_cents <= 0 or policy.coverage_limit_cents <= 0 or payload.amount_cents <= policy.coverage_limit_cents
    covered = covers_type and active and within_limit
    if not covers_type:
        reason = f"{policy.policy_type} does not normally cover {payload.claim_type.value} claims."
    elif not active:
        reason = f"Policy is not active on {activity_date.isoformat()}."
    elif not within_limit:
        reason = "Requested amount exceeds the recorded coverage limit."
    else:
        reason = "Coverage appears valid for this claim type and incident date."
    payable_base = min(payload.amount_cents, policy.coverage_limit_cents) if policy.coverage_limit_cents else payload.amount_cents
    estimated_payable = max(payable_base - policy.deductible_cents, 0) if covered else 0
    return InsuranceCoverageVerificationRead(
        organization_id=payload.organization_id,
        claim_type=payload.claim_type,
        policy_id=policy.id,
        policy_number=policy.policy_number,
        provider_name=policy.provider_name,
        covered=covered,
        coverage_limit_cents=policy.coverage_limit_cents,
        deductible_cents=policy.deductible_cents,
        estimated_payable_cents=estimated_payable,
        currency=policy.currency,
        reason=reason,
        renewal_due=insurance_policy_renewal_due(policy, today_utc()),
        certificate_url=policy.certificate_url,
    )


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
    selected_policy: InsurancePolicy | None = None
    if payload.insurance_policy_id is not None:
        selected_policy = await get_insurance_policy_for_organization(
            db,
            payload.insurance_policy_id,
            payload.organization_id,
        )
    if payload.claimant_person_id is not None:
        await validate_person_in_organization(db, payload.organization_id, payload.claimant_person_id)
    create_data = payload.model_dump()
    if selected_policy is not None:
        create_data["provider_name"] = selected_policy.provider_name
        create_data["policy_number"] = create_data.get("policy_number") or selected_policy.policy_number
        create_data["currency"] = selected_policy.currency
    claim = IncidentInsuranceClaim(
        prepared_by_person_id=identity.person_id,
        **create_data,
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
    if payload.insurance_policy_id is not None:
        selected_policy = await get_insurance_policy_for_organization(db, payload.insurance_policy_id, claim.organization_id)
        claim.insurance_policy_id = selected_policy.id
        claim.provider_name = selected_policy.provider_name
        claim.policy_number = selected_policy.policy_number
        claim.currency = selected_policy.currency
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


async def submit_incident_insurance_claim_to_provider(
    db: AsyncSession,
    identity: CurrentIdentity,
    claim_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> IncidentInsuranceClaimProviderSyncRead:
    claim = await db.get(IncidentInsuranceClaim, claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")
    await ensure_org_manage(authz, claim.organization_id, identity)
    incident = await db.get(SafeguardingIncident, claim.incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    selected_settings = settings or get_settings()
    now = utc_now()
    payload = incident_insurance_claim_provider_payload(
        claim,
        incident,
        "submit",
        selected_settings.safeguarding_insurance_claim_provider_profile,
    )
    claim.submitted_by_person_id = identity.person_id
    claim.submitted_at = claim.submitted_at or now
    claim.status = InsuranceClaimStatus.SUBMITTED
    claim.submission_payload = json.dumps(payload, sort_keys=True, default=str)
    append_incident_insurance_claim_log(
        claim,
        now,
        "Prepared insurer claim submission",
        selected_settings.safeguarding_insurance_claim_delivery_mode,
    )
    result = await deliver_incident_insurance_claim_provider_payload(
        selected_settings,
        claim,
        payload,
        now,
        action="submit",
    )
    await db.commit()
    await db.refresh(claim)
    return result.model_copy(update={"claim_status": claim.status})


async def poll_incident_insurance_claim_provider_status(
    db: AsyncSession,
    identity: CurrentIdentity,
    claim_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> IncidentInsuranceClaimProviderSyncRead:
    claim = await db.get(IncidentInsuranceClaim, claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")
    await ensure_org_manage(authz, claim.organization_id, identity)
    incident = await db.get(SafeguardingIncident, claim.incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    selected_settings = settings or get_settings()
    now = utc_now()
    payload = incident_insurance_claim_provider_payload(
        claim,
        incident,
        "status_poll",
        selected_settings.safeguarding_insurance_claim_provider_profile,
    )
    result = await deliver_incident_insurance_claim_provider_payload(
        selected_settings,
        claim,
        payload,
        now,
        action="status_poll",
    )
    await db.commit()
    await db.refresh(claim)
    return result.model_copy(update={"claim_status": claim.status})


async def deliver_incident_insurance_claim_provider_payload(
    settings: Settings,
    claim: IncidentInsuranceClaim,
    payload: dict[str, object],
    now: datetime,
    *,
    action: str,
) -> IncidentInsuranceClaimProviderSyncRead:
    result = IncidentInsuranceClaimProviderSyncRead(
        claim_id=claim.id,
        organization_id=claim.organization_id,
        action=action,
        provider_profile=str(payload.get("provider_profile") or "standard_claim"),
        provider_schema_id=provider_schema_id_from_payload(payload),
        delivery_mode=settings.safeguarding_insurance_claim_delivery_mode,
        delivery_attempted=False,
        delivered=False,
        provider_status_code=None,
        provider_reference=claim.claim_number,
        tracking_url=claim.tracking_url,
        claim_status=claim.status,
        failure_reason=None,
        synced_at=now,
    )
    if settings.safeguarding_insurance_claim_delivery_mode == "record_only":
        append_incident_insurance_claim_log(
            claim,
            now,
            f"Record-only insurer {action}; provider payload stored for manual handling",
            settings.safeguarding_insurance_claim_delivery_mode,
        )
        return result.model_copy(update={"failure_reason": "Record-only insurer mode; payload prepared for manual provider handling."})
    if not settings.safeguarding_insurance_claim_webhook_url:
        failure = "Insurer webhook mode is enabled but no webhook URL is configured."
        append_incident_insurance_claim_log(claim, now, failure, settings.safeguarding_insurance_claim_delivery_mode)
        return result.model_copy(update={"failure_reason": failure})

    raw_body = json.dumps(payload, sort_keys=True, default=str).encode()
    timestamp = str(int(now.timestamp()))
    headers = incident_insurance_claim_provider_headers(settings, raw_body, timestamp)
    try:
        async with httpx.AsyncClient(timeout=settings.safeguarding_insurance_claim_timeout_seconds) as client:
            response = await client.post(
                settings.safeguarding_insurance_claim_webhook_url,
                json=payload,
                headers=headers,
            )
        delivered = 200 <= response.status_code < 300
        response_payload = parse_insurer_response_json(response.text) if response.text else {}
        if delivered:
            apply_incident_insurance_claim_provider_response(claim, response_payload, now)
            append_incident_insurance_claim_log(
                claim,
                now,
                f"Insurer {action} accepted with HTTP {response.status_code}",
                settings.safeguarding_insurance_claim_delivery_mode,
            )
        else:
            append_incident_insurance_claim_log(
                claim,
                now,
                f"Insurer {action} returned HTTP {response.status_code}",
                settings.safeguarding_insurance_claim_delivery_mode,
            )
        return result.model_copy(
            update={
                "delivery_attempted": True,
                "delivered": delivered,
                "provider_status_code": response.status_code,
                "provider_reference": claim.claim_number,
                "tracking_url": claim.tracking_url,
                "claim_status": claim.status,
                "failure_reason": None if delivered else f"Insurer webhook returned {response.status_code}: {response.text[:500]}",
            }
        )
    except httpx.HTTPError as error:
        append_incident_insurance_claim_log(
            claim,
            now,
            f"Insurer {action} delivery failed: {error}",
            settings.safeguarding_insurance_claim_delivery_mode,
        )
        return result.model_copy(
            update={
                "delivery_attempted": True,
                "failure_reason": f"Insurer webhook delivery failed: {error}",
            }
        )


def incident_insurance_claim_provider_payload(
    claim: IncidentInsuranceClaim,
    incident: SafeguardingIncident,
    action: str,
    configured_profile: str | None = None,
) -> dict[str, object]:
    profile = selected_provider_profile(
        configured_profile,
        infer_insurance_provider_profile(claim),
    )
    return {
        "event_type": f"incident_insurance_claim.{action}",
        "provider_profile": profile,
        "provider_schema": incident_insurance_claim_provider_schema(profile, claim, incident, action),
        "claim_id": str(claim.id),
        "organization_id": str(claim.organization_id),
        "incident_id": str(claim.incident_id),
        "insurance_policy_id": str(claim.insurance_policy_id) if claim.insurance_policy_id else None,
        "claim_type": claim.claim_type.value,
        "status": claim.status.value,
        "provider_name": claim.provider_name,
        "policy_number": claim.policy_number,
        "claim_number": claim.claim_number,
        "claimed_amount_cents": claim.claimed_amount_cents,
        "approved_amount_cents": claim.approved_amount_cents,
        "paid_amount_cents": claim.paid_amount_cents,
        "reserve_amount_cents": claim.reserve_amount_cents,
        "currency": claim.currency,
        "tracking_url": claim.tracking_url,
        "documentation_checklist_json": claim.documentation_checklist_json,
        "submission_payload": claim.submission_payload,
        "incident": {
            "title": incident.title,
            "incident_type": incident.incident_type.value,
            "severity": incident.severity.value,
            "occurred_at": incident.occurred_at,
            "location": incident.location,
            "description": incident.description,
            "immediate_action": incident.immediate_action,
            "medical_follow_up_required": incident.medical_follow_up_required,
        },
    }


def incident_insurance_claim_provider_schema(
    profile: str,
    claim: IncidentInsuranceClaim,
    incident: SafeguardingIncident,
    action: str,
) -> dict[str, object]:
    field_map = {
        "afrolete_policy_id": "insurance_policy_id",
        "policy_id": "policy_number",
        "claim_reference": "claim_number",
        "loss_type": "claim_type",
        "loss_date": "incident.occurred_at",
        "loss_location": "incident.location",
        "claimed_amount_minor": "claimed_amount_cents",
        "reserve_amount_minor": "reserve_amount_cents",
        "currency": "currency",
        "supporting_documents": "documentation_checklist_json",
    }
    if profile == "medical_claim":
        provider_payload = {
            "medical_expense_claim": {
                "operation": action,
                "policy_number": claim.policy_number,
                "claimant_person_id": str(claim.claimant_person_id) if claim.claimant_person_id else None,
                "injury_description": incident.description,
                "first_aid_or_referral": incident.immediate_action,
                "follow_up_required": incident.medical_follow_up_required,
                "amount_requested_cents": claim.claimed_amount_cents,
                "reserve_cents": claim.reserve_amount_cents,
            }
        }
    elif profile == "property_equipment_claim":
        provider_payload = {
            "property_loss_notice": {
                "operation": action,
                "policy_number": claim.policy_number,
                "damage_context": incident.description,
                "location": incident.location,
                "estimated_loss_cents": claim.claimed_amount_cents,
                "evidence_checklist": claim.documentation_checklist_json,
            }
        }
    elif profile == "liability_claim":
        provider_payload = {
            "liability_notice": {
                "operation": action,
                "policy_number": claim.policy_number,
                "incident_summary": incident.description,
                "immediate_mitigation": incident.immediate_action,
                "severity": incident.severity.value,
                "reserve_cents": claim.reserve_amount_cents,
            }
        }
    elif profile == "travel_claim":
        provider_payload = {
            "travel_incident_claim": {
                "operation": action,
                "policy_number": claim.policy_number,
                "travel_incident_reference": str(incident.id),
                "location": incident.location,
                "amount_requested_cents": claim.claimed_amount_cents,
                "status": claim.status.value,
            }
        }
    else:
        provider_payload = {
            "standard_claim_notice": {
                "operation": action,
                "policy_number": claim.policy_number,
                "claim_type": claim.claim_type.value,
                "claim_number": claim.claim_number,
                "amount_requested_cents": claim.claimed_amount_cents,
                "currency": claim.currency,
            }
        }
    return {
        "schema_id": provider_schema_id("insurance", profile),
        "version": "1.0",
        "profile": profile,
        "required_fields": [
            "provider_name",
            "claim_type",
            "policy_number",
            "incident.occurred_at",
            "incident.description",
            "claimed_amount_cents",
            "currency",
        ],
        "field_map": field_map,
        "status_mapping": {
            "submitted": "submitted",
            "acknowledged": "acknowledged",
            "in_review": "in_review",
            "approved": "approved",
            "partially_paid": "partially_paid",
            "paid": "paid",
            "denied": "denied",
            "closed": "closed",
        },
        "provider_payload": provider_payload,
    }


def incident_insurance_claim_provider_headers(
    settings: Settings,
    raw_body: bytes,
    timestamp: str,
) -> dict[str, str]:
    signing_key = resolve_secret_sync(
        settings,
        env_value=settings.safeguarding_insurance_claim_webhook_key,
        path=settings.safeguarding_insurance_claim_webhook_key_secret_path,
        field_name=settings.safeguarding_insurance_claim_webhook_key_secret_field,
        label="insurer claim webhook key",
    )
    signature = hmac.new((signing_key or settings.agent_webhook_key or "local-insurer-claim-key").encode(), timestamp.encode() + b"." + raw_body, sha256).hexdigest()
    return {
        "content-type": "application/json",
        "x-afrolete-insurer-timestamp": timestamp,
        "x-afrolete-insurer-signature": signature,
    }


def parse_insurer_response_json(response_text: str) -> dict[str, object]:
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def apply_incident_insurance_claim_provider_response(
    claim: IncidentInsuranceClaim,
    response_payload: dict[str, object],
    now: datetime,
) -> None:
    claim_number = response_payload.get("claim_number") or response_payload.get("provider_reference")
    if claim_number:
        claim.claim_number = str(claim_number)[:160]
    tracking_url = response_payload.get("tracking_url")
    if tracking_url:
        claim.tracking_url = str(tracking_url)[:500]
    for field in ["approved_amount_cents", "paid_amount_cents", "reserve_amount_cents"]:
        value = response_payload.get(field)
        if isinstance(value, int) and value >= 0:
            setattr(claim, field, value)
    status_value = response_payload.get("status") or response_payload.get("claim_status")
    if status_value:
        try:
            claim.status = InsuranceClaimStatus(str(status_value).lower())
        except ValueError:
            pass
    if claim.status in {InsuranceClaimStatus.SUBMITTED, InsuranceClaimStatus.ACKNOWLEDGED, InsuranceClaimStatus.IN_REVIEW}:
        claim.submitted_at = claim.submitted_at or now
    if claim.status in {InsuranceClaimStatus.PAID, InsuranceClaimStatus.DENIED, InsuranceClaimStatus.CLOSED}:
        claim.closed_at = claim.closed_at or now
    notes = response_payload.get("notes")
    if notes:
        claim.notes = str(notes)[:4000]


def append_incident_insurance_claim_log(
    claim: IncidentInsuranceClaim,
    at: datetime,
    message: str,
    mode: str,
) -> None:
    entry = f"{at.isoformat()} [{mode}] {message}"
    claim.communication_log = f"{claim.communication_log}\n{entry}" if claim.communication_log else entry


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


async def submit_incident_medical_clearance_to_provider(
    db: AsyncSession,
    identity: CurrentIdentity,
    clearance_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> IncidentMedicalClearanceProviderSyncRead:
    clearance = await db.get(IncidentMedicalClearance, clearance_id)
    if clearance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical clearance not found")
    await ensure_org_manage(authz, clearance.organization_id, identity)
    incident = await db.get(SafeguardingIncident, clearance.incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    selected_settings = settings or get_settings()
    now = utc_now()
    clearance.reviewed_by_person_id = identity.person_id
    clearance.assessed_at = clearance.assessed_at or now
    payload = incident_medical_clearance_provider_payload(
        clearance,
        incident,
        "submit",
        selected_settings.safeguarding_medical_clearance_provider_profile,
    )
    append_incident_medical_clearance_note(
        clearance,
        now,
        f"Prepared medical portal submission in {selected_settings.safeguarding_medical_clearance_delivery_mode} mode.",
    )
    result = await deliver_incident_medical_clearance_provider_payload(
        selected_settings,
        clearance,
        payload,
        now,
        action="submit",
    )
    await db.commit()
    await db.refresh(clearance)
    return result.model_copy(update={"clearance_status": clearance.status})


async def poll_incident_medical_clearance_provider_status(
    db: AsyncSession,
    identity: CurrentIdentity,
    clearance_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> IncidentMedicalClearanceProviderSyncRead:
    clearance = await db.get(IncidentMedicalClearance, clearance_id)
    if clearance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical clearance not found")
    await ensure_org_manage(authz, clearance.organization_id, identity)
    incident = await db.get(SafeguardingIncident, clearance.incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    selected_settings = settings or get_settings()
    now = utc_now()
    payload = incident_medical_clearance_provider_payload(
        clearance,
        incident,
        "status_poll",
        selected_settings.safeguarding_medical_clearance_provider_profile,
    )
    result = await deliver_incident_medical_clearance_provider_payload(
        selected_settings,
        clearance,
        payload,
        now,
        action="status_poll",
    )
    await db.commit()
    await db.refresh(clearance)
    return result.model_copy(update={"clearance_status": clearance.status})


async def deliver_incident_medical_clearance_provider_payload(
    settings: Settings,
    clearance: IncidentMedicalClearance,
    payload: dict[str, object],
    now: datetime,
    *,
    action: str,
) -> IncidentMedicalClearanceProviderSyncRead:
    result = IncidentMedicalClearanceProviderSyncRead(
        clearance_id=clearance.id,
        organization_id=clearance.organization_id,
        incident_id=clearance.incident_id,
        athlete_person_id=clearance.athlete_person_id,
        action=action,
        provider_profile=str(payload.get("provider_profile") or "standard_medical_clearance"),
        provider_schema_id=provider_schema_id_from_payload(payload),
        delivery_mode=settings.safeguarding_medical_clearance_delivery_mode,
        delivery_attempted=False,
        delivered=False,
        provider_status_code=None,
        provider_reference=clearance.documentation_object_key,
        clearance_status=clearance.status,
        documentation_object_key=clearance.documentation_object_key,
        failure_reason=None,
        synced_at=now,
    )
    if settings.safeguarding_medical_clearance_delivery_mode == "record_only":
        append_incident_medical_clearance_note(
            clearance,
            now,
            f"Record-only medical portal {action}; payload prepared for manual provider handling.",
        )
        return result.model_copy(
            update={"failure_reason": "Record-only medical portal mode; payload prepared for manual provider handling."}
        )
    if not settings.safeguarding_medical_clearance_webhook_url:
        failure = "Medical portal webhook mode is enabled but no webhook URL is configured."
        append_incident_medical_clearance_note(clearance, now, failure)
        return result.model_copy(update={"failure_reason": failure})

    raw_body = json.dumps(payload, sort_keys=True, default=str).encode()
    timestamp = str(int(now.timestamp()))
    headers = incident_medical_clearance_provider_headers(settings, raw_body, timestamp)
    try:
        async with httpx.AsyncClient(timeout=settings.safeguarding_medical_clearance_timeout_seconds) as client:
            response = await client.post(
                settings.safeguarding_medical_clearance_webhook_url,
                json=payload,
                headers=headers,
            )
        delivered = 200 <= response.status_code < 300
        response_payload = parse_insurer_response_json(response.text) if response.text else {}
        if delivered:
            apply_incident_medical_clearance_provider_response(clearance, response_payload, now)
            append_incident_medical_clearance_note(
                clearance,
                now,
                f"Medical portal {action} accepted with HTTP {response.status_code}.",
            )
        else:
            append_incident_medical_clearance_note(
                clearance,
                now,
                f"Medical portal {action} returned HTTP {response.status_code}.",
            )
        return result.model_copy(
            update={
                "delivery_attempted": True,
                "delivered": delivered,
                "provider_status_code": response.status_code,
                "provider_reference": clearance.documentation_object_key,
                "clearance_status": clearance.status,
                "documentation_object_key": clearance.documentation_object_key,
                "failure_reason": None if delivered else f"Medical portal webhook returned {response.status_code}: {response.text[:500]}",
            }
        )
    except httpx.HTTPError as error:
        append_incident_medical_clearance_note(
            clearance,
            now,
            f"Medical portal {action} delivery failed: {error}",
        )
        return result.model_copy(
            update={
                "delivery_attempted": True,
                "failure_reason": f"Medical portal webhook delivery failed: {error}",
            }
        )


def incident_medical_clearance_provider_payload(
    clearance: IncidentMedicalClearance,
    incident: SafeguardingIncident,
    action: str,
    configured_profile: str | None = None,
) -> dict[str, object]:
    profile = selected_provider_profile(
        configured_profile,
        infer_medical_provider_profile(clearance, incident),
    )
    return {
        "event_type": f"incident_medical_clearance.{action}",
        "provider_profile": profile,
        "provider_schema": incident_medical_clearance_provider_schema(profile, clearance, incident, action),
        "clearance_id": str(clearance.id),
        "organization_id": str(clearance.organization_id),
        "incident_id": str(clearance.incident_id),
        "athlete_person_id": str(clearance.athlete_person_id),
        "clearance_type": clearance.clearance_type,
        "status": clearance.status.value,
        "assessed_at": clearance.assessed_at,
        "valid_from": clearance.valid_from,
        "valid_until": clearance.valid_until,
        "restrictions": clearance.restrictions,
        "return_to_play_stage": clearance.return_to_play_stage,
        "provider_name": clearance.provider_name,
        "documentation_object_key": clearance.documentation_object_key,
        "incident": {
            "title": incident.title,
            "incident_type": incident.incident_type.value,
            "severity": incident.severity.value,
            "occurred_at": incident.occurred_at,
            "location": incident.location,
            "description": incident.description,
            "immediate_action": incident.immediate_action,
            "medical_follow_up_required": incident.medical_follow_up_required,
        },
    }


def incident_medical_clearance_provider_schema(
    profile: str,
    clearance: IncidentMedicalClearance,
    incident: SafeguardingIncident,
    action: str,
) -> dict[str, object]:
    field_map = {
        "patient_reference": "athlete_person_id",
        "case_reference": "incident_id",
        "review_type": "clearance_type",
        "clinical_status": "status",
        "assessment_time": "assessed_at",
        "valid_from": "valid_from",
        "valid_until": "valid_until",
        "restrictions": "restrictions",
        "return_to_play_stage": "return_to_play_stage",
        "document_reference": "documentation_object_key",
    }
    if profile == "concussion_return_to_play":
        provider_payload = {
            "concussion_rtp_clearance": {
                "operation": action,
                "athlete_person_id": str(clearance.athlete_person_id),
                "incident_summary": incident.description,
                "removal_from_play_action": incident.immediate_action,
                "current_stage": clearance.return_to_play_stage,
                "restrictions": clearance.restrictions,
                "clearance_status": clearance.status.value,
                "minimum_required_documentation": [
                    "initial_head_injury_assessment",
                    "symptom_free_confirmation",
                    "graduated_return_to_play_steps",
                    "licensed_clinician_signoff",
                ],
            }
        }
    elif profile == "physiotherapy_clearance":
        provider_payload = {
            "rehabilitation_clearance": {
                "operation": action,
                "athlete_person_id": str(clearance.athlete_person_id),
                "injury_context": incident.description,
                "functional_restrictions": clearance.restrictions,
                "return_stage": clearance.return_to_play_stage,
                "validity_window": {
                    "from": clearance.valid_from,
                    "until": clearance.valid_until,
                },
            }
        }
    elif profile == "school_medical_clearance":
        provider_payload = {
            "school_activity_medical_clearance": {
                "operation": action,
                "learner_person_id": str(clearance.athlete_person_id),
                "activity_incident_id": str(incident.id),
                "school_activity_location": incident.location,
                "participation_decision": clearance.status.value,
                "guardian_notification_recorded": incident.parent_notified_at is not None,
                "school_restrictions": clearance.restrictions,
            }
        }
    else:
        provider_payload = {
            "return_to_play_clearance": {
                "operation": action,
                "athlete_person_id": str(clearance.athlete_person_id),
                "clearance_type": clearance.clearance_type,
                "status": clearance.status.value,
                "return_to_play_stage": clearance.return_to_play_stage,
                "restrictions": clearance.restrictions,
                "documentation_object_key": clearance.documentation_object_key,
            }
        }
    return {
        "schema_id": provider_schema_id("medical", profile),
        "version": "1.0",
        "profile": profile,
        "required_fields": [
            "athlete_person_id",
            "incident_id",
            "clearance_type",
            "status",
            "assessed_at",
            "return_to_play_stage",
        ],
        "field_map": field_map,
        "status_mapping": {
            "pending_review": "pending_review",
            "restricted": "restricted",
            "cleared": "cleared",
            "not_cleared": "not_cleared",
            "expired": "expired",
        },
        "provider_payload": provider_payload,
    }


def incident_medical_clearance_provider_headers(
    settings: Settings,
    raw_body: bytes,
    timestamp: str,
) -> dict[str, str]:
    signing_key = resolve_secret_sync(
        settings,
        env_value=settings.safeguarding_medical_clearance_webhook_key,
        path=settings.safeguarding_medical_clearance_webhook_key_secret_path,
        field_name=settings.safeguarding_medical_clearance_webhook_key_secret_field,
        label="medical clearance webhook key",
    )
    key = (signing_key or settings.agent_webhook_key or "local-medical-clearance-key").encode()
    signature = hmac.new(key, timestamp.encode() + b"." + raw_body, sha256).hexdigest()
    return {
        "content-type": "application/json",
        "x-afrolete-medical-timestamp": timestamp,
        "x-afrolete-medical-signature": signature,
    }


def apply_incident_medical_clearance_provider_response(
    clearance: IncidentMedicalClearance,
    response_payload: dict[str, object],
    now: datetime,
) -> None:
    status_value = response_payload.get("status") or response_payload.get("clearance_status")
    if status_value:
        try:
            clearance.status = MedicalClearanceStatus(str(status_value).lower())
        except ValueError:
            pass
    provider_reference = response_payload.get("documentation_object_key") or response_payload.get("provider_reference")
    if provider_reference:
        clearance.documentation_object_key = str(provider_reference)[:500]
    for field in ["restrictions", "return_to_play_stage", "provider_name"]:
        value = response_payload.get(field)
        if value:
            setattr(clearance, field, str(value)[:4000] if field == "restrictions" else str(value)[:240])
    assessed_at = response_payload.get("assessed_at")
    if isinstance(assessed_at, str):
        try:
            clearance.assessed_at = datetime.fromisoformat(assessed_at.replace("Z", "+00:00"))
        except ValueError:
            clearance.assessed_at = clearance.assessed_at or now
    elif clearance.status in {MedicalClearanceStatus.CLEARED, MedicalClearanceStatus.RESTRICTED}:
        clearance.assessed_at = clearance.assessed_at or now
    for field in ["valid_from", "valid_until"]:
        value = response_payload.get(field)
        if isinstance(value, str):
            try:
                setattr(clearance, field, date.fromisoformat(value[:10]))
            except ValueError:
                pass
    notes = response_payload.get("notes")
    if notes:
        append_incident_medical_clearance_note(clearance, now, str(notes))


def append_incident_medical_clearance_note(
    clearance: IncidentMedicalClearance,
    at: datetime,
    message: str,
) -> None:
    entry = f"{at.isoformat()} {message}"
    clearance.notes = f"{clearance.notes}\n{entry}" if clearance.notes else entry


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


async def upload_background_check_evidence_document(
    db: AsyncSession,
    identity: CurrentIdentity,
    check_id: UUID,
    payload: BackgroundCheckEvidenceDocumentUploadCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> BackgroundCheckEvidenceDocumentRead:
    check = await db.get(BackgroundCheck, check_id)
    if check is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check not found")
    await ensure_org_manage(authz, check.organization_id, identity)
    content = decode_safeguarding_upload_content(payload.content_base64)
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Evidence document is empty")

    selected_settings = settings or get_settings()
    uploaded_at = utc_now()
    checksum = sha256(content).hexdigest()
    safe_name = safe_safeguarding_upload_filename(payload.filename, fallback="background-check-evidence")
    storage_name = f"{checksum[:16]}-{safe_name}"
    relative_path = (
        Path("background-checks")
        / str(check.organization_id)
        / str(check.id)
        / storage_name
    ).as_posix()
    stored = put_object(
        selected_settings,
        local_root=selected_settings.safeguarding_incident_evidence_dir,
        local_url_prefix=selected_settings.safeguarding_incident_evidence_url_prefix,
        key=relative_path,
        content=content,
        content_type=payload.content_type or "application/octet-stream",
    )
    document = BackgroundCheckEvidenceDocument(
        organization_id=check.organization_id,
        background_check_id=check.id,
        person_id=check.person_id,
        uploaded_by_person_id=identity.person_id,
        reviewed_by_person_id=identity.person_id if payload.review_status != "needs_review" else None,
        filename=safe_name,
        content_type=payload.content_type or "application/octet-stream",
        document_type=payload.document_type,
        review_status=payload.review_status,
        size_bytes=len(content),
        checksum=checksum,
        storage_key=relative_path,
        evidence_url=stored.url,
        provider_reference=payload.provider_reference,
        reviewed_at=uploaded_at if payload.review_status != "needs_review" else None,
        review_notes=payload.notes if payload.review_status != "needs_review" else None,
        notes=payload.notes,
    )
    db.add(document)
    apply_background_check_evidence_review_to_check(
        check,
        review_status=payload.review_status,
        reviewed_at=uploaded_at,
        reviewer_person_id=identity.person_id,
        risk_level=None,
        check_status=None,
        result_summary=None,
        review_notes=payload.notes,
        document=document,
    )

    await db.commit()
    await db.refresh(document)
    await db.refresh(check)
    return background_check_evidence_document_read(document, check)


async def list_background_check_evidence_documents(
    db: AsyncSession,
    identity: CurrentIdentity,
    check_id: UUID,
    authz: AuthorizationService,
) -> list[BackgroundCheckEvidenceDocumentRead]:
    check = await db.get(BackgroundCheck, check_id)
    if check is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check not found")
    await ensure_org_manage(authz, check.organization_id, identity)
    statement = (
        select(BackgroundCheckEvidenceDocument)
        .where(BackgroundCheckEvidenceDocument.background_check_id == check.id)
        .order_by(BackgroundCheckEvidenceDocument.created_at.desc())
    )
    documents = list((await db.scalars(statement)).all())
    return [background_check_evidence_document_read(document, check) for document in documents]


async def review_background_check_evidence_document(
    db: AsyncSession,
    identity: CurrentIdentity,
    document_id: UUID,
    payload: BackgroundCheckEvidenceDocumentReviewCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> BackgroundCheckEvidenceDocumentRead:
    document = await db.get(BackgroundCheckEvidenceDocument, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence document not found")
    check = await db.get(BackgroundCheck, document.background_check_id)
    if check is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check not found")
    await ensure_org_manage(authz, check.organization_id, identity)
    selected_settings = settings or get_settings()
    content = get_object(
        selected_settings,
        local_root=selected_settings.safeguarding_incident_evidence_dir,
        key=document.storage_key,
    )
    checksum = sha256(content).hexdigest()
    if checksum != document.checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Evidence checksum mismatch")

    reviewed_at = utc_now()
    document.review_status = payload.review_status
    document.reviewed_by_person_id = identity.person_id
    document.reviewed_at = reviewed_at
    document.review_notes = payload.review_notes
    apply_background_check_evidence_review_to_check(
        check,
        review_status=payload.review_status,
        reviewed_at=reviewed_at,
        reviewer_person_id=identity.person_id,
        risk_level=payload.risk_level,
        check_status=payload.check_status,
        result_summary=payload.result_summary,
        review_notes=payload.review_notes,
        document=document,
    )

    await db.commit()
    await db.refresh(document)
    await db.refresh(check)
    return background_check_evidence_document_read(document, check)


async def create_signed_background_check_evidence_document_link(
    db: AsyncSession,
    identity: CurrentIdentity,
    document_id: UUID,
    payload: BackgroundCheckEvidenceDocumentLinkCreate,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> BackgroundCheckEvidenceDocumentLinkRead:
    document = await db.get(BackgroundCheckEvidenceDocument, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence document not found")
    check = await db.get(BackgroundCheck, document.background_check_id)
    if check is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check not found")
    await ensure_org_manage(authz, check.organization_id, identity)
    selected_settings = settings or get_settings()
    storage_name = validate_background_check_evidence_storage_key(
        document.storage_key,
        check.organization_id,
        check.id,
    )
    content = get_object(
        selected_settings,
        local_root=selected_settings.safeguarding_incident_evidence_dir,
        key=document.storage_key,
    )
    checksum = sha256(content).hexdigest()
    if checksum != document.checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Evidence checksum mismatch")
    now = utc_now()
    expires_at = now + timedelta(
        seconds=payload.ttl_seconds or selected_settings.safeguarding_incident_evidence_url_ttl_seconds
    )
    signed_url = signed_background_check_evidence_url(
        selected_settings,
        check.organization_id,
        check.id,
        storage_name,
        checksum,
        expires_at,
    )
    return BackgroundCheckEvidenceDocumentLinkRead(
        document_id=document.id,
        background_check_id=check.id,
        organization_id=check.organization_id,
        signed_url=signed_url,
        expires_at=expires_at,
        filename=document.filename,
        content_type=document.content_type,
        checksum=checksum,
        size_bytes=len(content),
        evidence_url=document.evidence_url,
        storage_key=document.storage_key,
    )


async def read_signed_background_check_evidence_document(
    organization_id: UUID,
    check_id: UUID,
    filename: str,
    checksum: str,
    expires: int,
    signature: str,
    settings: Settings | None = None,
) -> dict[str, object]:
    selected_settings = settings or get_settings()
    if "/" in filename or "\\" in filename or filename in {"", ".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid evidence name")
    if expires < int(time.time()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Evidence link expired")
    expected = background_check_evidence_signature(
        selected_settings,
        organization_id,
        check_id,
        filename,
        checksum,
        expires,
    )
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid evidence signature")
    storage_key = (Path("background-checks") / str(organization_id) / str(check_id) / filename).as_posix()
    content = get_object(
        selected_settings,
        local_root=selected_settings.safeguarding_incident_evidence_dir,
        key=storage_key,
    )
    actual_checksum = sha256(content).hexdigest()
    if actual_checksum != checksum:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Evidence checksum mismatch")
    return {
        "content": content,
        "content_type": safeguarding_evidence_content_type_for_filename(filename),
        "filename": public_safeguarding_evidence_filename(filename),
        "checksum": actual_checksum,
    }


async def submit_background_check_to_screening_provider(
    db: AsyncSession,
    identity: CurrentIdentity,
    check_id: UUID,
    authz: AuthorizationService,
    settings: Settings | None = None,
) -> BackgroundCheckProviderSubmissionRead:
    check = await db.get(BackgroundCheck, check_id)
    if check is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check not found")
    await ensure_org_manage(authz, check.organization_id, identity)
    person = await db.get(Person, check.person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

    selected_settings = settings or get_settings()
    now = utc_now()
    check.status = BackgroundCheckStatus.IN_PROGRESS
    check.requested_at = check.requested_at or now
    check.requested_by_person_id = check.requested_by_person_id or identity.person_id
    check.external_reference = check.external_reference or background_check_external_reference(check)
    payload = background_check_screening_provider_payload(
        check,
        person,
        selected_settings.safeguarding_screening_submission_provider_profile,
    )
    append_background_check_note(
        check,
        now,
        (
            "Prepared screening provider submission "
            f"{payload['provider_schema']['schema_id']} in "
            f"{selected_settings.safeguarding_screening_submission_delivery_mode} mode."
        ),
    )
    result = await deliver_background_check_screening_provider_payload(
        selected_settings,
        check,
        payload,
        now,
    )
    await db.commit()
    await db.refresh(check)
    return result.model_copy(
        update={
            "external_reference": check.external_reference,
            "check_status": check.status,
        }
    )


def background_check_external_reference(check: BackgroundCheck) -> str:
    provider_slug = normalize_provider_profile(check.provider, "screening")
    return f"{provider_slug}-{str(check.id)[:8]}"


async def deliver_background_check_screening_provider_payload(
    settings: Settings,
    check: BackgroundCheck,
    payload: dict[str, object],
    submitted_at: datetime,
) -> BackgroundCheckProviderSubmissionRead:
    provider_schema = payload.get("provider_schema")
    provider_payload: dict[str, object] = {}
    if isinstance(provider_schema, dict) and isinstance(provider_schema.get("provider_payload"), dict):
        provider_payload = provider_schema["provider_payload"]
    result = BackgroundCheckProviderSubmissionRead(
        background_check_id=check.id,
        organization_id=check.organization_id,
        person_id=check.person_id,
        provider=check.provider,
        check_type=check.check_type,
        provider_profile=str(payload.get("provider_profile") or "standard_screening"),
        provider_schema_id=provider_schema_id_from_payload(payload),
        delivery_mode=settings.safeguarding_screening_submission_delivery_mode,
        delivery_attempted=False,
        delivered=False,
        provider_status_code=None,
        external_reference=check.external_reference,
        check_status=check.status,
        provider_payload=provider_payload,
        failure_reason=None,
        submitted_at=submitted_at,
    )
    if settings.safeguarding_screening_submission_delivery_mode == "record_only":
        append_background_check_note(
            check,
            submitted_at,
            "Record-only screening submission; provider packet is ready for manual handling.",
        )
        return result.model_copy(
            update={
                "failure_reason": "Record-only screening mode; payload prepared for manual provider handling.",
            }
        )
    if not settings.safeguarding_screening_submission_webhook_url:
        failure = "Screening submission webhook mode is enabled but no webhook URL is configured."
        append_background_check_note(check, submitted_at, failure)
        return result.model_copy(update={"failure_reason": failure})

    raw_body = json.dumps(payload, sort_keys=True, default=str).encode()
    timestamp = str(int(submitted_at.timestamp()))
    headers = background_check_screening_provider_headers(settings, raw_body, timestamp)
    try:
        async with httpx.AsyncClient(timeout=settings.safeguarding_screening_submission_timeout_seconds) as client:
            response = await client.post(
                settings.safeguarding_screening_submission_webhook_url,
                json=payload,
                headers=headers,
            )
        delivered = 200 <= response.status_code < 300
        response_payload = parse_insurer_response_json(response.text) if response.text else {}
        if delivered:
            apply_background_check_screening_submission_response(check, response_payload, submitted_at)
            append_background_check_note(
                check,
                submitted_at,
                f"Screening provider accepted submission with HTTP {response.status_code}.",
            )
        else:
            append_background_check_note(
                check,
                submitted_at,
                f"Screening provider returned HTTP {response.status_code}.",
            )
        return result.model_copy(
            update={
                "delivery_attempted": True,
                "delivered": delivered,
                "provider_status_code": response.status_code,
                "external_reference": check.external_reference,
                "check_status": check.status,
                "failure_reason": None if delivered else f"Screening webhook returned {response.status_code}: {response.text[:500]}",
            }
        )
    except httpx.HTTPError as error:
        append_background_check_note(
            check,
            submitted_at,
            f"Screening provider delivery failed: {error}",
        )
        return result.model_copy(
            update={
                "delivery_attempted": True,
                "failure_reason": f"Screening webhook delivery failed: {error}",
            }
        )


def background_check_screening_provider_payload(
    check: BackgroundCheck,
    person: Person,
    configured_profile: str | None = None,
) -> dict[str, object]:
    profile = selected_provider_profile(
        configured_profile,
        infer_screening_provider_profile(check),
    )
    return {
        "event_type": "background_check.submit",
        "provider_profile": profile,
        "provider_schema": background_check_screening_provider_schema(profile, check, person),
        "background_check_id": str(check.id),
        "organization_id": str(check.organization_id),
        "person_id": str(check.person_id),
        "provider": check.provider,
        "check_type": check.check_type,
        "status": check.status.value,
        "requested_at": check.requested_at,
        "expires_at": check.expires_at,
        "external_reference": check.external_reference,
        "person": {
            "display_name": person.display_name,
            "date_of_birth": person.date_of_birth,
            "primary_email": person.primary_email,
            "primary_phone": person.primary_phone,
            "country_code": person.country_code,
        },
    }


def background_check_screening_provider_schema(
    profile: str,
    check: BackgroundCheck,
    person: Person,
) -> dict[str, object]:
    field_map = {
        "candidate_reference": "person_id",
        "candidate_name": "person.display_name",
        "candidate_email": "person.primary_email",
        "candidate_phone": "person.primary_phone",
        "candidate_country": "person.country_code",
        "screening_package": "check_type",
        "customer_reference": "external_reference",
        "requested_at": "requested_at",
    }
    if profile == "safe_sport_screening":
        provider_payload = {
            "safesport_screening_request": {
                "member_reference": str(check.person_id),
                "organization_reference": str(check.organization_id),
                "screening_level": check.check_type,
                "candidate_name": person.display_name,
                "candidate_email": person.primary_email,
                "country_code": person.country_code,
                "case_reference": check.external_reference,
            }
        }
    elif profile == "government_clearance":
        provider_payload = {
            "government_clearance_application": {
                "applicant_reference": str(check.person_id),
                "legal_name": person.display_name,
                "date_of_birth": person.date_of_birth,
                "country_code": person.country_code,
                "clearance_type": check.check_type,
                "submission_reference": check.external_reference,
            }
        }
    elif profile == "checkr_screening":
        provider_payload = {
            "checkr_candidate_package": {
                "candidate_id": str(check.person_id),
                "email": person.primary_email,
                "phone": person.primary_phone,
                "package": check.check_type,
                "work_location_country": person.country_code,
                "external_id": check.external_reference,
            }
        }
    elif profile == "first_advantage_screening":
        provider_payload = {
            "first_advantage_order": {
                "order_reference": check.external_reference,
                "applicant": {
                    "id": str(check.person_id),
                    "name": person.display_name,
                    "email": person.primary_email,
                    "phone": person.primary_phone,
                },
                "screening_package": check.check_type,
            }
        }
    elif profile == "youth_sport_staff_screening":
        provider_payload = {
            "youth_sport_staff_screen": {
                "staff_person_id": str(check.person_id),
                "role_screening_type": check.check_type,
                "candidate_name": person.display_name,
                "contact_email": person.primary_email,
                "external_reference": check.external_reference,
                "safeguarding_context": "minor-facing sports role",
            }
        }
    else:
        provider_payload = {
            "standard_screening_request": {
                "candidate_reference": str(check.person_id),
                "candidate_name": person.display_name,
                "candidate_email": person.primary_email,
                "screening_type": check.check_type,
                "external_reference": check.external_reference,
            }
        }
    return {
        "schema_id": provider_schema_id("screening", profile),
        "version": "1.0",
        "profile": profile,
        "required_fields": [
            "person_id",
            "person.display_name",
            "provider",
            "check_type",
            "requested_at",
            "external_reference",
        ],
        "field_map": field_map,
        "status_mapping": {
            "requested": "requested",
            "processing": "in_progress",
            "clear": "clear",
            "consider": "review_required",
            "adverse": "failed",
            "expired": "expired",
        },
        "provider_payload": provider_payload,
    }


def background_check_screening_provider_headers(
    settings: Settings,
    raw_body: bytes,
    timestamp: str,
) -> dict[str, str]:
    signing_key = resolve_secret_sync(
        settings,
        env_value=settings.safeguarding_screening_submission_webhook_key,
        path=settings.safeguarding_screening_submission_webhook_key_secret_path,
        field_name=settings.safeguarding_screening_submission_webhook_key_secret_field,
        label="screening submission webhook key",
    )
    key = (signing_key or settings.agent_webhook_key or "local-screening-submission-key").encode()
    signature = hmac.new(key, timestamp.encode() + b"." + raw_body, sha256).hexdigest()
    return {
        "content-type": "application/json",
        "x-afrolete-screening-timestamp": timestamp,
        "x-afrolete-screening-signature": signature,
    }


def apply_background_check_screening_submission_response(
    check: BackgroundCheck,
    response_payload: dict[str, object],
    now: datetime,
) -> None:
    external_reference = response_payload.get("external_reference") or response_payload.get("provider_reference")
    if external_reference:
        check.external_reference = str(external_reference)[:240]
    status_value = response_payload.get("status") or response_payload.get("provider_status")
    if status_value:
        provider_result = BackgroundCheckProviderResultCreate(
            provider=check.provider,
            external_reference=check.external_reference,
            provider_status=str(status_value),
        )
        check.status = background_check_status_from_provider(provider_result)
    if response_payload.get("risk_level"):
        check.risk_level = str(response_payload["risk_level"])[:40].lower()
    if response_payload.get("result_summary"):
        check.result_summary = str(response_payload["result_summary"])[:4000]
    if check.status in {
        BackgroundCheckStatus.CLEAR,
        BackgroundCheckStatus.REVIEW_REQUIRED,
        BackgroundCheckStatus.FAILED,
    }:
        check.completed_at = check.completed_at or now
    notes = response_payload.get("notes")
    if notes:
        append_background_check_note(check, now, str(notes))


def append_background_check_note(
    check: BackgroundCheck,
    at: datetime,
    message: str,
) -> None:
    entry = f"{at.isoformat()} {message}"
    check.notes = "\n".join(part for part in [check.notes, entry] if part)


def apply_background_check_evidence_review_to_check(
    check: BackgroundCheck,
    *,
    review_status: str,
    reviewed_at: datetime,
    reviewer_person_id: UUID | None,
    risk_level: str | None,
    check_status: BackgroundCheckStatus | None,
    result_summary: str | None,
    review_notes: str | None,
    document: BackgroundCheckEvidenceDocument,
) -> None:
    normalized_status = review_status.strip().lower()
    if normalized_status != "needs_review":
        check.reviewed_by_person_id = reviewer_person_id
    if check_status is not None:
        check.status = check_status
    elif normalized_status == "accepted":
        check.status = BackgroundCheckStatus.CLEAR
    elif normalized_status in {"rejected", "escalated", "needs_review"}:
        check.status = BackgroundCheckStatus.REVIEW_REQUIRED
    if check.status in {BackgroundCheckStatus.CLEAR, BackgroundCheckStatus.FAILED} or (
        check_status is not None and check.status == BackgroundCheckStatus.REVIEW_REQUIRED
    ):
        check.completed_at = check.completed_at or reviewed_at
    if risk_level is not None:
        check.risk_level = risk_level.lower()
    elif normalized_status == "accepted" and check.risk_level in {"unknown", "medium", "high", "critical"}:
        check.risk_level = "low"
    elif normalized_status == "escalated" and check.risk_level in {"unknown", "low"}:
        check.risk_level = "high"
    if result_summary is not None:
        check.result_summary = result_summary
    elif normalized_status == "accepted" and not check.result_summary:
        check.result_summary = f"Screening evidence {document.filename} accepted for {check.check_type}."
    append_background_check_note(
        check,
        reviewed_at,
        (
            f"Evidence document {document.filename} ({document.document_type}) marked {normalized_status}; "
            f"checksum {document.checksum}; storage {document.storage_key}."
            + (f" Notes: {review_notes}" if review_notes else "")
        ),
    )


def background_check_evidence_document_read(
    document: BackgroundCheckEvidenceDocument,
    check: BackgroundCheck,
) -> BackgroundCheckEvidenceDocumentRead:
    return BackgroundCheckEvidenceDocumentRead(
        id=document.id,
        organization_id=document.organization_id,
        background_check_id=document.background_check_id,
        person_id=document.person_id,
        uploaded_by_person_id=document.uploaded_by_person_id,
        reviewed_by_person_id=document.reviewed_by_person_id,
        filename=document.filename,
        content_type=document.content_type,
        document_type=document.document_type,
        review_status=document.review_status,
        size_bytes=document.size_bytes,
        checksum=document.checksum,
        storage_key=document.storage_key,
        evidence_url=document.evidence_url,
        provider_reference=document.provider_reference,
        reviewed_at=document.reviewed_at,
        review_notes=document.review_notes,
        notes=document.notes,
        background_check_status=check.status,
        background_check_risk_level=check.risk_level,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def validate_background_check_evidence_storage_key(
    storage_key: str,
    organization_id: UUID,
    check_id: UUID,
) -> str:
    expected_prefix = (Path("background-checks") / str(organization_id) / str(check_id)).as_posix() + "/"
    normalized = storage_key.strip()
    if (
        not normalized.startswith(expected_prefix)
        or "\\" in normalized
        or "/../" in normalized
        or normalized.endswith("/")
    ):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid evidence storage key")
    storage_name = normalized.rsplit("/", 1)[-1]
    if storage_name in {"", ".", ".."}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid evidence storage key")
    return storage_name


def signed_background_check_evidence_url(
    settings: Settings,
    organization_id: UUID,
    check_id: UUID,
    storage_name: str,
    checksum: str,
    expires_at: datetime,
) -> str:
    expires = int(expires_at.timestamp())
    signature = background_check_evidence_signature(
        settings,
        organization_id,
        check_id,
        storage_name,
        checksum,
        expires,
    )
    safe_name = quote(storage_name, safe="")
    return (
        f"{settings.api_prefix}/safeguarding/background-check-evidence/{organization_id}/{check_id}/{safe_name}"
        f"?checksum={checksum}&expires={expires}&signature={signature}"
    )


def background_check_evidence_signature(
    settings: Settings,
    organization_id: UUID,
    check_id: UUID,
    storage_name: str,
    checksum: str,
    expires: int,
) -> str:
    payload = f"background-checks/{organization_id}/{check_id}/{storage_name}:{checksum}:{expires}"
    digest = hmac.new(
        safeguarding_incident_evidence_signing_key(settings),
        payload.encode(),
        sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


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


async def list_guardian_account_readiness(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[GuardianAccountReadinessRead]:
    await ensure_org_manage(authz, organization_id, identity)
    athlete_person = aliased(Person)
    guardian_person = aliased(Person)
    rows = (
        await db.execute(
            select(GuardianRelationship, athlete_person, AthleteProfile, guardian_person)
            .join(athlete_person, athlete_person.id == GuardianRelationship.athlete_person_id)
            .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
            .join(
                guardian_person,
                guardian_person.id == GuardianRelationship.guardian_person_id,
                isouter=False,
            )
            .where(AthleteProfile.organization_id == organization_id)
            .order_by(athlete_person.display_name, GuardianRelationship.is_primary.desc())
        )
    ).all()

    readiness: list[GuardianAccountReadinessRead] = []
    for relationship, athlete, _, guardian in rows:
        linked_user = await db.scalar(
            select(AppUser)
            .where(AppUser.person_id == guardian.id)
            .order_by(AppUser.created_at.desc())
            .limit(1)
        )
        email_user = None
        if guardian.primary_email:
            email_user = await db.scalar(
                select(AppUser)
                .where(func.lower(AppUser.email) == guardian.primary_email.lower())
                .order_by(AppUser.created_at.desc())
                .limit(1)
            )
        status_value, action = guardian_account_status(guardian, linked_user, email_user)
        latest_invite = await latest_guardian_portal_invite(db, organization_id, guardian.id)
        latest_message, latest_recipient = latest_invite if latest_invite else (None, None)
        readiness.append(
            GuardianAccountReadinessRead(
                relationship_id=relationship.id,
                athlete_person_id=relationship.athlete_person_id,
                athlete_name=athlete.display_name,
                guardian_person_id=guardian.id,
                guardian_name=guardian.display_name,
                guardian_email=guardian.primary_email,
                guardian_phone=guardian.primary_phone,
                account_status=status_value,
                linked_app_user_id=linked_user.id if linked_user else None,
                keycloak_sub=linked_user.keycloak_sub if linked_user else None,
                email_matches_app_user=email_user is not None,
                can_receive_invite=bool(guardian.primary_email),
                last_invite_message_id=latest_message.id if latest_message else None,
                last_invite_channel=latest_message.channel if latest_message else None,
                last_invite_destination=latest_recipient.destination if latest_recipient else None,
                last_invite_delivery_status=latest_recipient.delivery_status.value if latest_recipient else None,
                last_invite_created_at=latest_message.created_at if latest_message else None,
                last_invite_sent_at=latest_message.sent_at if latest_message else None,
                recommended_action=action,
            )
        )
    return readiness


async def create_guardian_portal_invite_batch(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: GuardianPortalInviteBatchCreate,
    authz: AuthorizationService,
) -> GuardianPortalInviteBatchRead:
    readiness = await list_guardian_account_readiness(db, identity, payload.organization_id, authz)
    invited: list[GuardianPortalInviteRead] = []
    skipped: list[str] = []
    skipped_recent = 0
    skipped_no_destination = 0
    skipped_not_ready = 0
    skipped_linked = 0
    cutoff = utc_now() - timedelta(hours=payload.skip_recent_hours)
    invite_statuses = {"invite_ready", "pending_link"}

    for item in readiness[: payload.limit]:
        if item.account_status == "linked" and not payload.include_linked_accounts:
            skipped_linked += 1
            skipped.append(f"{item.guardian_name}: already linked")
            continue
        if item.account_status not in invite_statuses and item.account_status != "linked":
            skipped_not_ready += 1
            skipped.append(f"{item.guardian_name}: {item.account_status}")
            continue
        if (
            payload.skip_recent_hours > 0
            and item.last_invite_created_at is not None
            and not datetime_is_before(item.last_invite_created_at, cutoff)
        ):
            skipped_recent += 1
            skipped.append(f"{item.guardian_name}: invited recently")
            continue
        if payload.channel != CommunicationChannel.IN_APP:
            has_destination = item.guardian_email if payload.channel == CommunicationChannel.EMAIL else item.guardian_phone
            if not has_destination:
                skipped_no_destination += 1
                skipped.append(f"{item.guardian_name}: no {payload.channel.value} destination")
                continue
        try:
            invite = await create_guardian_portal_invite(
                db,
                identity,
                item.relationship_id,
                GuardianPortalInviteCreate(
                    organization_id=payload.organization_id,
                    channel=payload.channel,
                    portal_url=payload.portal_url,
                    dispatch_now=payload.dispatch_now,
                ),
                authz,
            )
        except HTTPException as error:
            skipped_no_destination += 1
            skipped.append(f"{item.guardian_name}: {error.detail}")
            continue
        invited.append(invite)

    return GuardianPortalInviteBatchRead(
        organization_id=payload.organization_id,
        channel=payload.channel,
        considered=len(readiness[: payload.limit]),
        invited=len(invited),
        skipped_recent=skipped_recent,
        skipped_no_destination=skipped_no_destination,
        skipped_not_ready=skipped_not_ready,
        skipped_linked=skipped_linked,
        dispatch_attempted=sum(item.dispatch_attempted for item in invited),
        dispatch_delivered=sum(item.dispatch_delivered for item in invited),
        dispatch_queued=sum(item.dispatch_queued for item in invited),
        dispatch_failed=sum(item.dispatch_failed for item in invited),
        invites=invited,
        skipped=skipped[:25],
    )


async def latest_guardian_portal_invite(
    db: AsyncSession,
    organization_id: UUID,
    guardian_person_id: UUID,
) -> tuple[CommunicationMessage, MessageRecipient] | None:
    row = (
        await db.execute(
            select(CommunicationMessage, MessageRecipient)
            .join(MessageRecipient, MessageRecipient.message_id == CommunicationMessage.id)
            .where(CommunicationMessage.organization_id == organization_id)
            .where(CommunicationMessage.message_type == CommunicationMessageType.REQUEST)
            .where(CommunicationMessage.scope_type == CommunicationScopeType.PERSON)
            .where(CommunicationMessage.scope_id == guardian_person_id)
            .where(MessageRecipient.person_id == guardian_person_id)
            .where(
                or_(
                    CommunicationMessage.subject.ilike("%family portal%"),
                    CommunicationMessage.body.ilike("%family portal%"),
                )
            )
            .order_by(CommunicationMessage.created_at.desc())
            .limit(1)
        )
    ).first()
    return (row[0], row[1]) if row is not None else None


async def run_guardian_portal_invite_reminder_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    channel: CommunicationChannel = CommunicationChannel.EMAIL,
    invited_before_hours: int = 24,
    repeat_after_hours: int = 24,
    limit: int = 100,
    dry_run: bool = False,
) -> GuardianPortalInviteReminderWorkerRunRead:
    cutoff = utc_now() - timedelta(hours=invited_before_hours)
    statement = (
        select(CommunicationMessage, MessageRecipient, Person)
        .join(MessageRecipient, MessageRecipient.message_id == CommunicationMessage.id)
        .join(Person, Person.id == MessageRecipient.person_id)
        .join(GuardianRelationship, GuardianRelationship.guardian_person_id == Person.id)
        .join(
            AthleteProfile,
            and_(
                AthleteProfile.person_id == GuardianRelationship.athlete_person_id,
                AthleteProfile.organization_id == CommunicationMessage.organization_id,
            ),
        )
        .where(CommunicationMessage.message_type == CommunicationMessageType.REQUEST)
        .where(CommunicationMessage.scope_type == CommunicationScopeType.PERSON)
        .where(CommunicationMessage.scope_id == Person.id)
        .where(func.coalesce(CommunicationMessage.sent_at, CommunicationMessage.created_at) <= cutoff)
        .where(
            or_(
                CommunicationMessage.subject.ilike("%family portal%"),
                CommunicationMessage.body.ilike("%family portal%"),
            )
        )
        .order_by(CommunicationMessage.created_at.asc())
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(CommunicationMessage.organization_id == organization_id)
    rows = (await db.execute(statement)).all()
    seen_guardians: set[UUID] = set()
    reminded_guardian_ids: list[UUID] = []
    message_ids: list[UUID] = []
    skipped_count = 0
    failed_count = 0

    for invite, _recipient, guardian in rows:
        if guardian.id in seen_guardians:
            skipped_count += 1
            continue
        seen_guardians.add(guardian.id)
        linked_user = await db.scalar(select(AppUser.id).where(AppUser.person_id == guardian.id).limit(1))
        if linked_user is not None:
            skipped_count += 1
            continue
        if await has_recent_guardian_portal_reminder(db, invite.organization_id, guardian.id, repeat_after_hours):
            skipped_count += 1
            continue
        destination = destination_for_channel(guardian, channel)
        if destination is None and channel != CommunicationChannel.IN_APP:
            skipped_count += 1
            continue
        if dry_run:
            skipped_count += 1
            continue
        try:
            reminder = await create_message_for_recipients(
                db,
                organization_id=invite.organization_id,
                message_type=CommunicationMessageType.REMINDER,
                channel=channel,
                scope_type=CommunicationScopeType.PERSON,
                scope_id=guardian.id,
                recipient_person_ids=[guardian.id],
                subject="Family portal sign-in reminder",
                body=guardian_portal_reminder_body(guardian, invite),
                urgent=False,
                created_by_person_id=None,
            )
            reminded_guardian_ids.append(guardian.id)
            message_ids.append(reminder.id)
        except Exception:
            failed_count += 1
            await db.rollback()
    return GuardianPortalInviteReminderWorkerRunRead(
        organization_id=organization_id,
        eligible_count=len(seen_guardians),
        executed_count=len(seen_guardians),
        reminded_count=len(message_ids),
        skipped_count=skipped_count,
        failed_count=failed_count,
        dry_run=dry_run,
        guardian_person_ids=reminded_guardian_ids,
        message_ids=message_ids,
    )


async def has_recent_guardian_portal_reminder(
    db: AsyncSession,
    organization_id: UUID,
    guardian_person_id: UUID,
    repeat_after_hours: int,
) -> bool:
    cutoff = utc_now() - timedelta(hours=repeat_after_hours)
    existing = await db.scalar(
        select(CommunicationMessage.id)
        .where(CommunicationMessage.organization_id == organization_id)
        .where(CommunicationMessage.message_type == CommunicationMessageType.REMINDER)
        .where(CommunicationMessage.scope_type == CommunicationScopeType.PERSON)
        .where(CommunicationMessage.scope_id == guardian_person_id)
        .where(CommunicationMessage.created_at >= cutoff)
        .where(
            or_(
                CommunicationMessage.subject.ilike("%family portal%"),
                CommunicationMessage.body.ilike("%family portal%"),
            )
        )
        .limit(1)
    )
    return existing is not None


def guardian_portal_reminder_body(guardian: Person, invite: CommunicationMessage) -> str:
    return "\n\n".join(
        [
            f"Hello {guardian.display_name},",
            "This is a reminder to complete your AfroLete family portal sign-in.",
            "Your club uses the family portal for consent requests, event RSVPs, schedule updates, and athlete development visibility.",
            f"Original invite: {invite.subject}",
            "Open the family portal from the invitation link and sign in with the email address where you received it.",
        ]
    )


async def create_guardian_portal_invite(
    db: AsyncSession,
    identity: CurrentIdentity,
    relationship_id: UUID,
    payload: GuardianPortalInviteCreate,
    authz: AuthorizationService,
) -> GuardianPortalInviteRead:
    await ensure_org_manage(authz, payload.organization_id, identity)
    relationship = await db.get(GuardianRelationship, relationship_id)
    if relationship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guardian relationship not found")
    athlete_profile = await db.scalar(
        select(AthleteProfile).where(
            AthleteProfile.organization_id == payload.organization_id,
            AthleteProfile.person_id == relationship.athlete_person_id,
        )
    )
    if athlete_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guardian relationship not found")
    organization = await db.get(Organization, payload.organization_id)
    athlete = await db.get(Person, relationship.athlete_person_id)
    guardian = await db.get(Person, relationship.guardian_person_id)
    if organization is None or athlete is None or guardian is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guardian relationship not found")
    destination = destination_for_channel(guardian, payload.channel)
    if destination is None and payload.channel != CommunicationChannel.IN_APP:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Guardian has no destination for {payload.channel.value}",
        )

    linked_user = await db.scalar(
        select(AppUser)
        .where(AppUser.person_id == guardian.id)
        .order_by(AppUser.created_at.desc())
        .limit(1)
    )
    email_user = None
    if guardian.primary_email:
        email_user = await db.scalar(
            select(AppUser)
            .where(func.lower(AppUser.email) == guardian.primary_email.lower())
            .order_by(AppUser.created_at.desc())
            .limit(1)
        )
    status_value, action = guardian_account_status(guardian, linked_user, email_user)
    portal_url = guardian_portal_invite_url(payload.portal_url, payload.organization_id, relationship.id, guardian)
    subject = payload.subject or f"{organization.public_name or organization.name} family portal invitation"
    body = payload.body or guardian_portal_invite_body(
        organization=organization,
        athlete=athlete,
        guardian=guardian,
        portal_url=portal_url,
        account_status=status_value,
    )
    if "family portal" not in body.lower():
        body = f"{body}\n\nFamily portal: {portal_url}"
    message = await create_message_for_recipients(
        db,
        organization_id=payload.organization_id,
        message_type=CommunicationMessageType.REQUEST,
        channel=payload.channel,
        scope_type=CommunicationScopeType.PERSON,
        scope_id=guardian.id,
        recipient_person_ids=[guardian.id],
        subject=subject,
        body=body,
        urgent=False,
        created_by_person_id=identity.person_id,
    )
    dispatch_summary = None
    if payload.dispatch_now:
        dispatch_summary = await dispatch_message(db, identity, message.id, authz)
    recipient = await db.scalar(
        select(MessageRecipient).where(
            MessageRecipient.message_id == message.id,
            MessageRecipient.person_id == guardian.id,
        )
    )
    return GuardianPortalInviteRead(
        relationship_id=relationship.id,
        organization_id=payload.organization_id,
        guardian_person_id=guardian.id,
        guardian_name=guardian.display_name,
        athlete_person_id=athlete.id,
        athlete_name=athlete.display_name,
        account_status=status_value,
        channel=payload.channel,
        destination=recipient.destination if recipient else destination,
        portal_url=portal_url,
        message_id=message.id,
        recipient_id=recipient.id if recipient else None,
        delivery_status=recipient.delivery_status.value if recipient else None,
        dispatch_attempted=dispatch_summary.attempted if dispatch_summary else 0,
        dispatch_sent=dispatch_summary.sent if dispatch_summary else 0,
        dispatch_delivered=dispatch_summary.delivered if dispatch_summary else 0,
        dispatch_failed=dispatch_summary.failed if dispatch_summary else 0,
        dispatch_suppressed=dispatch_summary.suppressed if dispatch_summary else 0,
        dispatch_queued=dispatch_summary.queued if dispatch_summary else 0,
        recommended_action=action,
    )


def guardian_portal_invite_url(
    base_url: str,
    organization_id: UUID,
    relationship_id: UUID,
    guardian: Person,
) -> str:
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault("organization_id", str(organization_id))
    query.setdefault("relationship_id", str(relationship_id))
    query.setdefault("guardian_sub", f"guardian-{relationship_id}")
    query.setdefault("guardian_name", guardian.display_name)
    if guardian.primary_email:
        query.setdefault("guardian_email", guardian.primary_email)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def guardian_portal_invite_body(
    *,
    organization: Organization,
    athlete: Person,
    guardian: Person,
    portal_url: str,
    account_status: str,
) -> str:
    organization_name = organization.public_name or organization.name
    account_instruction = (
        "Your portal account is already linked; sign in to review your family dashboard."
        if account_status == "linked"
        else "Sign in using this email address so AfroLete can link your guardian record automatically."
    )
    if account_status == "pending_link":
        account_instruction = "Your sign-in email is recognized; sign in once to complete the account link."
    return "\n\n".join(
        [
            f"Hello {guardian.display_name},",
            f"{organization_name} has invited you to the AfroLete family portal for {athlete.display_name}.",
            account_instruction,
            f"Open the family portal: {portal_url}",
            "From the portal you can review consent requests, RSVP for events, monitor schedule conflicts, and see family-visible athlete development updates.",
        ]
    )


def guardian_account_status(
    guardian: Person,
    linked_user: AppUser | None,
    email_user: AppUser | None,
) -> tuple[str, str]:
    if linked_user is not None:
        return (
            "linked",
            "Guardian has a linked AfroLete account and can use authenticated family workflows.",
        )
    if email_user is not None and email_user.person_id is None:
        return (
            "pending_link",
            "Ask the guardian to sign in once; the identity bridge will attach this email-matched account.",
        )
    if email_user is not None and email_user.person_id != guardian.id:
        return (
            "email_conflict",
            "Resolve the existing app user using this email before inviting the guardian.",
        )
    if guardian.primary_email:
        return (
            "invite_ready",
            "Invite this guardian to sign in with the recorded email; the identity bridge will attach the account.",
        )
    if guardian.primary_phone:
        return (
            "phone_only",
            "Collect an email address before Keycloak self-service onboarding.",
        )
    return (
        "missing_contact",
        "Add guardian email or phone contact details before issuing portal access.",
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


async def list_my_family_match_guidance(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    limit: int = 20,
) -> list[FamilyMatchGuidanceRead]:
    from app.services.performance import (
        build_player_match_guidance,
        decode_match_tracking_summary,
        player_match_guidance_feedback_for_recipient,
    )

    relationship_rows = (
        await db.execute(
            select(GuardianRelationship, Person, AthleteProfile)
            .join(Person, Person.id == GuardianRelationship.athlete_person_id)
            .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
            .where(AthleteProfile.organization_id == organization_id)
            .where(GuardianRelationship.guardian_person_id == identity.person_id)
            .order_by(GuardianRelationship.is_primary.desc(), Person.display_name)
        )
    ).all()
    child_context = {
        relationship.athlete_person_id: (athlete.display_name, relationship.relationship)
        for relationship, athlete, _profile in relationship_rows
    }
    if not child_context:
        return []

    audit_rows = (
        await db.execute(
            select(PerformanceMatchPlayerGuidancePublishAudit, MessageRecipient)
            .join(
                MessageRecipient,
                MessageRecipient.message_id == PerformanceMatchPlayerGuidancePublishAudit.message_id,
            )
            .where(PerformanceMatchPlayerGuidancePublishAudit.organization_id == organization_id)
            .where(PerformanceMatchPlayerGuidancePublishAudit.player_person_id.in_(list(child_context)))
            .where(PerformanceMatchPlayerGuidancePublishAudit.status == "published")
            .where(MessageRecipient.person_id == identity.person_id)
            .order_by(
                PerformanceMatchPlayerGuidancePublishAudit.published_at.desc(),
                PerformanceMatchPlayerGuidancePublishAudit.created_at.desc(),
            )
            .limit(limit * 4)
        )
    ).all()

    guidance: list[FamilyMatchGuidanceRead] = []
    seen: set[tuple[UUID, UUID, str]] = set()
    for audit, recipient in audit_rows:
        key = (audit.player_person_id, audit.tracking_run_id, audit.track_id)
        if key in seen:
            continue
        seen.add(key)
        run = await db.get(PerformanceMatchTrackingRun, audit.tracking_run_id)
        if run is None or run.organization_id != organization_id:
            continue
        sample = await db.scalar(
            select(PerformanceMatchTrackingSample)
            .where(PerformanceMatchTrackingSample.tracking_run_id == run.id)
            .where(PerformanceMatchTrackingSample.track_id == audit.track_id)
            .where(PerformanceMatchTrackingSample.person_id == audit.player_person_id)
            .order_by(PerformanceMatchTrackingSample.timestamp_seconds.desc())
            .limit(1)
        )
        if sample is None:
            continue
        video_asset = await db.get(OppositionScoutingVideoAsset, run.video_asset_id)
        if video_asset is None:
            continue
        summary = decode_match_tracking_summary(run.summary_json)
        metric = next(
            (
                item
                for item in summary.get("player_metrics", [])
                if isinstance(item, dict) and str(item.get("track_id")) == audit.track_id
            ),
            None,
        )
        if metric is None:
            continue
        athlete_name, relationship = child_context[audit.player_person_id]
        card = build_player_match_guidance(
            run=run,
            video_asset=video_asset,
            sample=sample,
            metric=metric,
            summary=summary,
            publish_audit=audit,
            player_recipient=recipient,
            feedback=await player_match_guidance_feedback_for_recipient(db, recipient.id),
        )
        guidance.append(
            FamilyMatchGuidanceRead(
                athlete_person_id=audit.player_person_id,
                athlete_name=athlete_name,
                relationship=relationship,
                **card,
            )
        )
        if len(guidance) >= limit:
            break
    return guidance


async def submit_my_family_match_guidance_feedback(
    db: AsyncSession,
    identity: CurrentIdentity,
    recipient_id: UUID,
    payload: FamilyMatchGuidanceFeedbackCreate,
) -> PerformanceMatchPlayerGuidanceFeedback:
    from app.services.performance import (
        player_match_guidance_feedback_for_recipient,
        queue_player_match_guidance_feedback_agent_review,
    )

    recipient = await db.get(MessageRecipient, recipient_id)
    if recipient is None or recipient.person_id != identity.person_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family match guidance recipient not found")
    audit = await db.scalar(
        select(PerformanceMatchPlayerGuidancePublishAudit)
        .where(PerformanceMatchPlayerGuidancePublishAudit.message_id == recipient.message_id)
        .where(PerformanceMatchPlayerGuidancePublishAudit.status == "published")
        .limit(1)
    )
    if audit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published match guidance not found")
    if audit.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization mismatch")
    guardian_relationship = await db.scalar(
        select(GuardianRelationship)
        .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
        .where(AthleteProfile.organization_id == audit.organization_id)
        .where(GuardianRelationship.athlete_person_id == audit.player_person_id)
        .where(GuardianRelationship.guardian_person_id == identity.person_id)
        .limit(1)
    )
    if guardian_relationship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family match guidance not found")

    existing = await player_match_guidance_feedback_for_recipient(db, recipient.id)
    now = datetime.now(UTC)
    response_text = (payload.response_text or "").strip() or None
    priority_focus = (payload.priority_focus or "").strip() or None
    if existing is None:
        feedback = PerformanceMatchPlayerGuidanceFeedback(
            organization_id=audit.organization_id,
            tracking_run_id=audit.tracking_run_id,
            video_asset_id=audit.video_asset_id,
            publish_audit_id=audit.id,
            message_id=audit.message_id,
            message_recipient_id=recipient.id,
            person_id=identity.person_id,
            status=payload.status.strip().lower(),
            rating=payload.rating,
            response_text=response_text,
            priority_focus=priority_focus,
            requested_follow_up=payload.requested_follow_up,
            completed_action_count=payload.completed_action_count,
            submitted_at=now,
        )
        db.add(feedback)
    else:
        feedback = existing
        feedback.status = payload.status.strip().lower()
        feedback.rating = payload.rating
        feedback.response_text = response_text
        feedback.priority_focus = priority_focus
        feedback.requested_follow_up = payload.requested_follow_up
        feedback.completed_action_count = payload.completed_action_count
        feedback.submitted_at = now
    if recipient.delivery_status != MessageDeliveryStatus.READ:
        recipient.delivery_status = MessageDeliveryStatus.READ
        recipient.read_at = now
    if payload.requested_follow_up and feedback.agent_task_id is None:
        await db.flush()
        agent_task = await queue_player_match_guidance_feedback_agent_review(
            db,
            identity,
            organization_id=audit.organization_id,
            tracking_run_id=audit.tracking_run_id,
            video_asset_id=audit.video_asset_id,
            publish_audit_id=audit.id,
            message_recipient_id=recipient.id,
            person_id=identity.person_id,
            track_id=audit.track_id,
            player_label=f"{audit.player_label} family",
            status_value=feedback.status,
            priority_focus=priority_focus or feedback.status,
        )
        feedback.agent_task_id = agent_task.id
    await db.commit()
    await db.refresh(feedback)
    return feedback


async def get_my_family_dashboard(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> FamilyDashboardRead:
    family = await list_my_family(db, identity, organization_id)
    performance = await list_my_family_performance(db, identity, organization_id)
    events = await list_my_family_events(db, identity, organization_id, limit=100)
    consent_requests = await list_my_family_consent_requests(db, identity, organization_id)
    inbox_rows = (
        await db.execute(
            select(MessageRecipient, CommunicationMessage)
            .join(CommunicationMessage, CommunicationMessage.id == MessageRecipient.message_id)
            .where(CommunicationMessage.organization_id == organization_id)
            .where(MessageRecipient.person_id == identity.person_id)
        )
    ).all()
    unread_rows = [
        (recipient, message)
        for recipient, message in inbox_rows
        if recipient.delivery_status != MessageDeliveryStatus.READ
    ]
    urgent_unread_count = sum(1 for _, message in unread_rows if message.urgent)
    ai_tasks = await family_ai_task_rows(db, identity, organization_id)
    open_ai_appeal_count = int(
        await db.scalar(
            select(func.count(AgentDecisionAppeal.id))
            .where(AgentDecisionAppeal.organization_id == organization_id)
            .where(AgentDecisionAppeal.submitted_by_person_id == identity.person_id)
            .where(AgentDecisionAppeal.resolved_at.is_(None))
        )
        or 0
    )
    rsvp_needed_events = [event for event in events if event.attendance_status is None]
    clearance_blocked_events = [
        event
        for event in events
        if event.clearance_status != ParticipationClearanceStatus.CLEARED
    ]
    schedule_conflicts = family_schedule_conflicts(events)
    active_goal_count = sum(item.active_goal_count for item in performance)
    award_count = sum(item.award_count for item in performance)
    action_items = family_dashboard_actions(
        consent_requests,
        rsvp_needed_events,
        clearance_blocked_events,
        schedule_conflicts,
        unread_rows,
        open_ai_appeal_count,
    )
    next_action_label = action_items[0].title if action_items else "Family workspace is current"
    return FamilyDashboardRead(
        organization_id=organization_id,
        guardian_person_id=identity.person_id,
        generated_at=utc_now(),
        child_count=len(family),
        pending_consent_count=len(consent_requests),
        unread_message_count=len(unread_rows),
        urgent_unread_count=urgent_unread_count,
        upcoming_event_count=len(events),
        rsvp_needed_count=len(rsvp_needed_events),
        clearance_blocked_count=len(clearance_blocked_events),
        schedule_conflict_count=len(schedule_conflicts),
        active_goal_count=active_goal_count,
        award_count=award_count,
        ai_recommendation_count=len(ai_tasks),
        open_ai_appeal_count=open_ai_appeal_count,
        next_event_at=events[0].starts_at if events else None,
        next_action_label=next_action_label,
        action_items=action_items,
        schedule_conflicts=schedule_conflicts,
    )


async def get_my_family_coordination(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> list[FamilyCoordinationRowRead]:
    from app.services.organizations import list_family_registration_inquiries

    family = await list_my_family(db, identity, organization_id)
    registrations = await list_family_registration_inquiries(db, identity, organization_id)
    consent_requests = await list_my_family_consent_requests(db, identity, organization_id)
    events = await list_my_family_events(db, identity, organization_id, limit=100)
    performance = await list_my_family_performance(db, identity, organization_id)
    ai_tasks = await family_ai_task_rows(db, identity, organization_id)

    rows: dict[str, FamilyCoordinationRowRead] = {}
    name_to_key: dict[str, str] = {}
    for athlete in family:
        key = str(athlete.athlete_person_id)
        rows[key] = FamilyCoordinationRowRead(
            key=key,
            athlete_person_id=athlete.athlete_person_id,
            athlete_name=athlete.athlete_name,
            relationship=athlete.relationship,
            registration_count=0,
            missing_document_count=0,
            pending_consent_count=0,
            rsvp_needed_count=0,
            clearance_blocked_count=0,
            active_goal_count=0,
            ai_recommendation_count=0,
            next_action_label="Current",
            next_action_detail="No urgent family action is pending for this child.",
            action_href=None,
            urgency_score=0,
        )
        name_to_key[normalize_family_name(athlete.athlete_name)] = key

    for registration in registrations:
        if registration.status == "converted":
            continue
        key = name_to_key.get(normalize_family_name(registration.athlete_name), f"registration-{registration.id}")
        row = ensure_family_coordination_row(rows, key, registration.athlete_name, "registration")
        row.registration_count += 1
        row.missing_document_count += len(registration.missing_documents)
        resume_href = (
            f"{registration.public_site_path}?"
            f"{urlencode({'inquiry_id': str(registration.id), 'email': registration.email})}"
        )
        if not registration.packet_complete:
            row.next_action_label = "Continue packet"
            row.next_action_detail = (
                f"Missing {', '.join(registration.missing_documents)} before staff can verify this registration."
                if registration.missing_documents
                else registration.next_steps[0]
                if registration.next_steps
                else "Finish the registration packet before staff conversion."
            )
            row.action_href = resume_href
        elif row.next_action_label == "Current":
            row.next_action_label = "Review admissions"
            row.next_action_detail = "Packet is complete and waiting for admissions review."
            row.action_href = resume_href

    for request in consent_requests:
        row = ensure_family_coordination_row(
            rows,
            str(request.athlete_person_id),
            request.athlete_name,
            "guardian",
            athlete_person_id=request.athlete_person_id,
        )
        row.pending_consent_count += 1
        if row.next_action_label in {"Current", "Review admissions"}:
            row.next_action_label = "Respond to consent"
            row.next_action_detail = f"{request.scope_type.value} consent is pending through {request.channel.value}."
            row.action_href = None

    for event in events:
        row = ensure_family_coordination_row(
            rows,
            str(event.athlete_person_id),
            event.athlete_name,
            "guardian",
            athlete_person_id=event.athlete_person_id,
        )
        if event.attendance_status is None:
            row.rsvp_needed_count += 1
            if row.next_action_label in {"Current", "Review admissions"}:
                row.next_action_label = "RSVP"
                row.next_action_detail = f"{event.title} needs a family RSVP."
                row.action_href = None
        if event.clearance_status != ParticipationClearanceStatus.CLEARED:
            row.clearance_blocked_count += 1
            if row.next_action_label in {"Current", "Review admissions", "RSVP"}:
                row.next_action_label = "Resolve clearance"
                row.next_action_detail = f"{event.title} is blocked: {event.reason}"
                row.action_href = None

    for item in performance:
        row = ensure_family_coordination_row(
            rows,
            str(item.athlete_person_id),
            item.athlete_name,
            "guardian",
            athlete_person_id=item.athlete_person_id,
        )
        row.active_goal_count = item.active_goal_count

    for task in ai_tasks:
        athlete_name = task.get("athlete_name")
        status_value = str(task.get("status") or "")
        if not athlete_name or status_value in {"completed", "cancelled"}:
            continue
        athlete_name_text = str(athlete_name)
        key = name_to_key.get(normalize_family_name(athlete_name_text), f"ai-{normalize_family_name(athlete_name_text)}")
        row = ensure_family_coordination_row(rows, key, athlete_name_text, "AI recommendation")
        row.ai_recommendation_count += 1
        if row.next_action_label in {"Current", "Review admissions"}:
            row.next_action_label = "Review AI"
            row.next_action_detail = str(task.get("simple_explanation") or task.get("title") or "Review the AI recommendation.")
            row.action_href = None

    for row in rows.values():
        row.urgency_score = family_coordination_urgency(row)

    return sorted(rows.values(), key=lambda item: (-item.urgency_score, item.athlete_name))


async def create_family_coordination_digest(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: FamilyCoordinationDigestCreate,
    authz: AuthorizationService | None = None,
) -> FamilyCoordinationDigestRead:
    rows = await get_my_family_coordination(db, identity, payload.organization_id)
    organization = await db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    action_rows = [row for row in rows if row.urgency_score > 0]
    selected_rows = (action_rows or rows)[: payload.max_rows]
    subject = f"{organization.public_name or organization.name} family action digest"
    body = family_coordination_digest_body(
        organization_name=organization.public_name or organization.name,
        guardian_name=identity.display_name,
        rows=selected_rows,
        portal_url=family_coordination_digest_portal_url(payload.portal_url, payload.organization_id),
    )
    message = await create_message_for_recipients(
        db,
        organization_id=payload.organization_id,
        message_type=CommunicationMessageType.REMINDER,
        channel=payload.channel,
        scope_type=CommunicationScopeType.PERSON,
        scope_id=identity.person_id,
        recipient_person_ids=[identity.person_id],
        subject=subject,
        body=body,
        urgent=any(row.urgency_score >= 10 for row in selected_rows),
        created_by_person_id=identity.person_id,
    )
    dispatch_summary = None
    if payload.dispatch_now:
        dispatch_summary = await dispatch_message(
            db,
            identity,
            message.id,
            authz,
            enforce_manage_communications_scope=False,
        )
    recipient = await db.scalar(
        select(MessageRecipient).where(
            MessageRecipient.message_id == message.id,
            MessageRecipient.person_id == identity.person_id,
        )
    )
    return FamilyCoordinationDigestRead(
        organization_id=payload.organization_id,
        guardian_person_id=identity.person_id,
        channel=payload.channel,
        message_id=message.id,
        recipient_id=recipient.id if recipient else None,
        delivery_status=recipient.delivery_status.value if recipient else None,
        action_count=len(action_rows),
        top_urgency_score=selected_rows[0].urgency_score if selected_rows else 0,
        subject=subject,
        body=body,
        dispatch_attempted=dispatch_summary.attempted if dispatch_summary else 0,
        dispatch_sent=dispatch_summary.sent if dispatch_summary else 0,
        dispatch_delivered=dispatch_summary.delivered if dispatch_summary else 0,
        dispatch_failed=dispatch_summary.failed if dispatch_summary else 0,
        dispatch_suppressed=dispatch_summary.suppressed if dispatch_summary else 0,
        dispatch_queued=dispatch_summary.queued if dispatch_summary else 0,
    )


async def run_family_coordination_digest_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    channel: CommunicationChannel = CommunicationChannel.IN_APP,
    portal_url: str = "https://afrolete.lindela.io/family",
    repeat_after_hours: int = 24,
    limit: int = 100,
    dry_run: bool = False,
) -> FamilyCoordinationDigestWorkerRunRead:
    statement = (
        select(AppUser, Person, Organization)
        .join(Person, Person.id == AppUser.person_id)
        .join(GuardianRelationship, GuardianRelationship.guardian_person_id == Person.id)
        .join(AthleteProfile, AthleteProfile.person_id == GuardianRelationship.athlete_person_id)
        .join(Organization, Organization.id == AthleteProfile.organization_id)
        .order_by(Organization.name, Person.display_name)
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(Organization.id == organization_id)
    rows = (await db.execute(statement)).all()
    seen_guardians: set[tuple[UUID, UUID]] = set()
    eligible_count = 0
    executed_count = 0
    created_count = 0
    skipped_count = 0
    failed_count = 0
    guardian_person_ids: list[UUID] = []
    message_ids: list[UUID] = []

    for app_user, guardian, organization in rows:
        key = (guardian.id, organization.id)
        if key in seen_guardians:
            skipped_count += 1
            continue
        seen_guardians.add(key)
        identity = CurrentIdentity(
            user_id=app_user.id,
            person_id=guardian.id,
            keycloak_sub=app_user.keycloak_sub,
            email=app_user.email,
            display_name=app_user.display_name or guardian.display_name,
        )
        try:
            coordination = await get_my_family_coordination(db, identity, organization.id)
            if not any(row.urgency_score > 0 for row in coordination):
                skipped_count += 1
                continue
            eligible_count += 1
            if await has_recent_family_coordination_digest(db, organization.id, guardian.id, repeat_after_hours):
                skipped_count += 1
                continue
            if dry_run:
                skipped_count += 1
                continue
            digest = await create_family_coordination_digest(
                db,
                identity,
                FamilyCoordinationDigestCreate(
                    organization_id=organization.id,
                    channel=channel,
                    portal_url=portal_url,
                    dispatch_now=True,
                ),
                None,
            )
            executed_count += 1
            created_count += 1
            guardian_person_ids.append(guardian.id)
            message_ids.append(digest.message_id)
        except Exception:
            failed_count += 1
            await db.rollback()

    return FamilyCoordinationDigestWorkerRunRead(
        organization_id=organization_id,
        eligible_count=eligible_count,
        executed_count=executed_count,
        created_count=created_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        dry_run=dry_run,
        guardian_person_ids=guardian_person_ids,
        message_ids=message_ids,
    )


async def has_recent_family_coordination_digest(
    db: AsyncSession,
    organization_id: UUID,
    guardian_person_id: UUID,
    repeat_after_hours: int,
) -> bool:
    cutoff = utc_now() - timedelta(hours=repeat_after_hours)
    existing = await db.scalar(
        select(CommunicationMessage.id)
        .where(CommunicationMessage.organization_id == organization_id)
        .where(CommunicationMessage.message_type == CommunicationMessageType.REMINDER)
        .where(CommunicationMessage.scope_type == CommunicationScopeType.PERSON)
        .where(CommunicationMessage.scope_id == guardian_person_id)
        .where(CommunicationMessage.created_at >= cutoff)
        .where(
            or_(
                CommunicationMessage.subject.ilike("%family action digest%"),
                CommunicationMessage.body.ilike("%family coordination digest%"),
            )
        )
        .limit(1)
    )
    return existing is not None


def family_coordination_digest_body(
    *,
    organization_name: str,
    guardian_name: str,
    rows: list[FamilyCoordinationRowRead],
    portal_url: str,
) -> str:
    if not rows:
        summary = "Your family workspace is current. No urgent coordination actions are pending."
    else:
        summary = "\n".join(
            (
                f"- {row.athlete_name}: {row.next_action_label} "
                f"({row.next_action_detail})"
            )
            for row in rows
        )
    return "\n\n".join(
        [
            f"Hello {guardian_name},",
            f"Here is your {organization_name} family coordination digest.",
            summary,
            f"Open the family portal: {portal_url}",
            "AfroLete ranks these items from registration packets, consent requests, RSVP needs, clearance blockers, goals, and AI recommendations.",
        ]
    )


def family_coordination_digest_portal_url(base_url: str, organization_id: UUID) -> str:
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault("organization_id", str(organization_id))
    query.setdefault("autoload", "1")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def ensure_family_coordination_row(
    rows: dict[str, FamilyCoordinationRowRead],
    key: str,
    athlete_name: str,
    relationship: str,
    athlete_person_id: UUID | None = None,
) -> FamilyCoordinationRowRead:
    if key in rows:
        return rows[key]
    rows[key] = FamilyCoordinationRowRead(
        key=key,
        athlete_person_id=athlete_person_id,
        athlete_name=athlete_name,
        relationship=relationship,
        registration_count=0,
        missing_document_count=0,
        pending_consent_count=0,
        rsvp_needed_count=0,
        clearance_blocked_count=0,
        active_goal_count=0,
        ai_recommendation_count=0,
        next_action_label="Current",
        next_action_detail="No urgent family action is pending for this child.",
        action_href=None,
        urgency_score=0,
    )
    return rows[key]


def family_coordination_urgency(row: FamilyCoordinationRowRead) -> int:
    return (
        row.missing_document_count * 8
        + row.pending_consent_count * 7
        + row.clearance_blocked_count * 6
        + row.rsvp_needed_count * 4
        + row.registration_count * 3
        + row.ai_recommendation_count * 2
    )


def normalize_family_name(value: str) -> str:
    return sub(r"\s+", " ", value.strip().lower())


async def family_ai_task_rows(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> list[dict[str, object]]:
    from app.services.agents import list_my_agent_family_tasks

    return await list_my_agent_family_tasks(db, identity, organization_id)


def family_dashboard_actions(
    consent_requests: list[FamilyConsentRequestRead],
    rsvp_needed_events: list[FamilyEventSummaryRead],
    clearance_blocked_events: list[FamilyEventSummaryRead],
    schedule_conflicts: list[FamilyScheduleConflictRead],
    unread_rows: list[tuple[MessageRecipient, CommunicationMessage]],
    open_ai_appeal_count: int,
) -> list[FamilyDashboardActionRead]:
    actions: list[FamilyDashboardActionRead] = []
    for request in consent_requests[:3]:
        actions.append(
            FamilyDashboardActionRead(
                priority="high",
                action_type="consent",
                title=f"Consent needed for {request.athlete_name}",
                detail=f"{request.scope_type.value} consent via {request.channel.value}.",
                athlete_person_id=request.athlete_person_id,
                consent_request_id=request.id,
                due_at=request.expires_at,
            )
        )
    for event in clearance_blocked_events[:3]:
        actions.append(
            FamilyDashboardActionRead(
                priority="high",
                action_type="clearance",
                title=f"Clearance blocked for {event.athlete_name}",
                detail=f"{event.title}: {event.reason}",
                athlete_person_id=event.athlete_person_id,
                event_id=event.event_id,
                due_at=event.starts_at,
            )
        )
    for conflict in schedule_conflicts[:3]:
        actions.append(
            FamilyDashboardActionRead(
                priority="high",
                action_type="schedule_conflict",
                title="Family schedule conflict",
                detail=conflict.recommendation,
                event_id=conflict.event_ids[0] if conflict.event_ids else None,
                due_at=conflict.starts_at,
            )
        )
    for event in rsvp_needed_events[:3]:
        actions.append(
            FamilyDashboardActionRead(
                priority="medium",
                action_type="rsvp",
                title=f"RSVP for {event.title}",
                detail=f"{event.athlete_name} is not confirmed yet.",
                athlete_person_id=event.athlete_person_id,
                event_id=event.event_id,
                due_at=event.starts_at,
            )
        )
    for recipient, message in unread_rows[:3]:
        actions.append(
            FamilyDashboardActionRead(
                priority="high" if message.urgent else "medium",
                action_type="message",
                title=message.subject,
                detail=f"{message.message_type.value} message on {message.channel.value}.",
                due_at=message.sent_at or recipient.created_at,
            )
        )
    if open_ai_appeal_count:
        actions.append(
            FamilyDashboardActionRead(
                priority="medium",
                action_type="ai_appeal",
                title="AI appeal awaiting review",
                detail=f"{open_ai_appeal_count} family AI appeal(s) are still open.",
            )
        )
    priority_order = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda item: (priority_order.get(item.priority, 9), family_action_sort_datetime(item.due_at)))
    return actions[:8]


def family_action_sort_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.max.replace(tzinfo=UTC)
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def family_schedule_conflicts(events: list[FamilyEventSummaryRead]) -> list[FamilyScheduleConflictRead]:
    conflicts: list[FamilyScheduleConflictRead] = []
    seen_pairs: set[tuple[UUID, UUID, UUID, UUID]] = set()
    sorted_events = sorted(events, key=lambda item: family_event_start(item))
    for index, first in enumerate(sorted_events):
        first_start = family_event_start(first)
        first_end = family_event_end(first)
        for second in sorted_events[index + 1 :]:
            if first.event_id == second.event_id and first.athlete_person_id == second.athlete_person_id:
                continue
            second_start = family_event_start(second)
            second_end = family_event_end(second)
            if first_start >= second_end or second_start >= first_end:
                continue
            ordered_pair = sorted(
                [
                    (first.athlete_person_id, first.event_id),
                    (second.athlete_person_id, second.event_id),
                ],
                key=lambda pair: (str(pair[0]), str(pair[1])),
            )
            pair_key = ordered_pair[0] + ordered_pair[1]
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            athlete_names = sorted({first.athlete_name, second.athlete_name})
            event_titles = [first.title, second.title]
            starts_at = max(first_start, second_start)
            ends_at = min(first_end, second_end)
            conflicts.append(
                FamilyScheduleConflictRead(
                    starts_at=starts_at,
                    ends_at=ends_at,
                    athlete_names=athlete_names,
                    event_titles=event_titles,
                    event_ids=[first.event_id, second.event_id],
                    recommendation=(
                        f"{' and '.join(athlete_names)} have overlapping commitments: "
                        f"{first.title} and {second.title}. Check carpool, pickup, or reschedule options."
                    ),
                )
            )
    return sorted(conflicts, key=lambda item: item.starts_at)[:10]


def family_event_start(event: FamilyEventSummaryRead) -> datetime:
    return event.starts_at.replace(tzinfo=UTC) if event.starts_at.tzinfo is None else event.starts_at.astimezone(UTC)


def family_event_end(event: FamilyEventSummaryRead) -> datetime:
    value = event.ends_at or event.starts_at + timedelta(hours=2)
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


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
        if datetime_is_before(request.expires_at, now):
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
    if datetime_is_before(request.expires_at, now):
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
    if datetime_is_before(request.expires_at, now):
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
