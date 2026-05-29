import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import (
    BackgroundCheckStatus,
    ComplianceCredentialStatus,
    IncidentReportPackageStatus,
    InsuranceClaimStatus,
    MedicalClearanceStatus,
    SafeguardingIncidentStatus,
)
from app.schemas.safeguarding import (
    ActivityConsentCreate,
    ActivityConsentRead,
    BackgroundCheckCreate,
    BackgroundCheckEvidenceDocumentLinkCreate,
    BackgroundCheckEvidenceDocumentLinkRead,
    BackgroundCheckEvidenceDocumentRead,
    BackgroundCheckEvidenceDocumentReviewCreate,
    BackgroundCheckEvidenceDocumentUploadCreate,
    BackgroundCheckProviderResultCreate,
    BackgroundCheckProviderResultRead,
    BackgroundCheckProviderSubmissionRead,
    BackgroundCheckRead,
    BackgroundCheckUpdate,
    ComplianceCredentialCreate,
    ComplianceCredentialRead,
    ComplianceCredentialUpdate,
    ComplianceReconciliationRead,
    ComplianceSummaryRead,
    ConsentRequestCreate,
    ConsentRequestRead,
    FamilyAthleteSummaryRead,
    FamilyCoordinationDigestCreate,
    FamilyCoordinationDigestRead,
    FamilyCoordinationRowRead,
    FamilyDashboardRead,
    FamilyConsentRequestRead,
    FamilyConsentResponseCreate,
    FamilyEventSummaryRead,
    FamilyEventRsvpCreate,
    FamilyPerformanceSummaryRead,
    GuardianAccountReadinessRead,
    GuardianPortalInviteBatchCreate,
    GuardianPortalInviteBatchRead,
    GuardianPortalInviteCreate,
    GuardianPortalInviteRead,
    GuardianRelationshipCreate,
    GuardianRelationshipRead,
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
    IncidentInsuranceClaimCreate,
    IncidentInsuranceClaimProviderSyncRead,
    IncidentInsuranceClaimRead,
    IncidentInsuranceClaimUpdate,
    IncidentMedicalClearanceCreate,
    IncidentMedicalClearanceProviderSyncRead,
    IncidentMedicalClearanceRead,
    IncidentMedicalClearanceUpdate,
    IncidentReportPackageArtifactLinkRead,
    IncidentReportPackageArtifactRead,
    IncidentReportPackageCreate,
    IncidentReportPackageProviderSubmissionRead,
    IncidentReportPackageRead,
    IncidentReportPackageUpdate,
    KnownChannelConsentCapture,
    ParticipationClearanceRead,
    SafeguardingIncidentCreate,
    SafeguardingIncidentRead,
    SafeguardingIncidentUpdate,
    TokenConsentCapture,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.safeguarding import (
    apply_safeguarding_incident_investigation_action,
    capture_consent_by_known_channel,
    capture_consent_by_token,
    create_signed_safeguarding_incident_evidence_link,
    create_signed_background_check_evidence_document_link,
    clearance_for_event,
    create_activity_consent,
    create_background_check,
    create_compliance_credential,
    create_consent_request,
    create_guardian_relationship,
    create_family_coordination_digest,
    create_guardian_portal_invite,
    create_guardian_portal_invite_batch,
    create_signed_incident_report_package_artifact_link,
    create_incident_insurance_claim,
    create_incident_medical_clearance,
    create_incident_report_package,
    create_safeguarding_evidence_policy_rule,
    create_safeguarding_incident_access_grant,
    create_safeguarding_incident,
    ensure_org_manage,
    compliance_summary,
    get_incident_report_package_artifact,
    get_my_family_coordination,
    get_safeguarding_incident_evidence_approval_policy,
    ingest_background_check_provider_result,
    list_background_check_evidence_documents,
    list_background_checks,
    list_compliance_credentials,
    list_guardian_account_readiness,
    list_guardians_for_athlete,
    get_my_family_dashboard,
    list_incident_insurance_claims,
    poll_incident_insurance_claim_provider_status,
    poll_incident_medical_clearance_provider_status,
    list_incident_medical_clearances,
    list_incident_report_packages,
    list_safeguarding_evidence_policy_rules,
    list_safeguarding_incident_access_grants,
    list_safeguarding_incident_evidence_review_queue,
    list_safeguarding_incidents,
    list_my_family_consent_requests,
    list_my_family,
    list_my_family_events,
    list_my_family_performance,
    respond_to_family_consent_request,
    respond_to_family_event,
    reconcile_compliance_statuses,
    read_signed_incident_report_package_artifact,
    read_signed_background_check_evidence_document,
    read_signed_safeguarding_incident_evidence,
    review_background_check_evidence_document,
    review_safeguarding_incident_evidence,
    revoke_safeguarding_incident_access_grant,
    submit_background_check_to_screening_provider,
    submit_incident_report_package_to_regulator,
    update_background_check,
    update_compliance_credential,
    update_incident_insurance_claim,
    submit_incident_insurance_claim_to_provider,
    submit_incident_medical_clearance_to_provider,
    sync_safeguarding_incident_access_controls_by_id,
    upload_safeguarding_incident_evidence,
    upload_background_check_evidence_document,
    update_incident_medical_clearance,
    update_incident_report_package,
    update_safeguarding_evidence_policy_rule,
    update_safeguarding_incident,
)

router = APIRouter(prefix="/safeguarding", tags=["safeguarding"])


def to_guardian_read(relationship) -> GuardianRelationshipRead:
    return GuardianRelationshipRead(
        id=relationship.id,
        athlete_person_id=relationship.athlete_person_id,
        guardian_person_id=relationship.guardian_person_id,
        relationship_kind=relationship.relationship_kind,
        relationship=relationship.relationship,
        can_sign_consent=relationship.can_sign_consent,
        can_view_medical=relationship.can_view_medical,
        emergency_contact=relationship.emergency_contact,
        can_pick_up=relationship.can_pick_up,
        is_primary=relationship.is_primary,
        notes=relationship.notes,
    )


def to_consent_read(consent) -> ActivityConsentRead:
    return ActivityConsentRead(
        id=consent.id,
        organization_id=consent.organization_id,
        athlete_person_id=consent.athlete_person_id,
        guardian_person_id=consent.guardian_person_id,
        scope_type=consent.scope_type,
        scope_id=consent.scope_id,
        status=consent.status,
        source_request_id=consent.source_request_id,
        capture_channel=consent.capture_channel,
        valid_from=consent.valid_from,
        valid_until=consent.valid_until,
        signed_at=consent.signed_at,
        revoked_at=consent.revoked_at,
        recorded_by_person_id=consent.recorded_by_person_id,
        consent_text=consent.consent_text,
        notes=consent.notes,
    )


def to_request_read(request, one_time_token: str | None = None) -> ConsentRequestRead:
    return ConsentRequestRead(
        id=request.id,
        organization_id=request.organization_id,
        athlete_person_id=request.athlete_person_id,
        guardian_person_id=request.guardian_person_id,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        channel=request.channel,
        destination=request.destination,
        status=request.status,
        expires_at=request.expires_at,
        sent_at=request.sent_at,
        fulfilled_at=request.fulfilled_at,
        external_message_id=request.external_message_id,
        one_time_token=one_time_token,
    )


def to_incident_read(incident) -> SafeguardingIncidentRead:
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


def to_background_check_read(check) -> BackgroundCheckRead:
    return BackgroundCheckRead(
        id=check.id,
        organization_id=check.organization_id,
        person_id=check.person_id,
        requested_by_person_id=check.requested_by_person_id,
        reviewed_by_person_id=check.reviewed_by_person_id,
        provider=check.provider,
        check_type=check.check_type,
        status=check.status,
        risk_level=check.risk_level,
        requested_at=check.requested_at,
        completed_at=check.completed_at,
        expires_at=check.expires_at,
        external_reference=check.external_reference,
        result_summary=check.result_summary,
        notes=check.notes,
        created_at=check.created_at,
    )


def to_credential_read(credential) -> ComplianceCredentialRead:
    return ComplianceCredentialRead(
        id=credential.id,
        organization_id=credential.organization_id,
        person_id=credential.person_id,
        verified_by_person_id=credential.verified_by_person_id,
        credential_type=credential.credential_type,
        status=credential.status,
        title=credential.title,
        issuing_body=credential.issuing_body,
        credential_number=credential.credential_number,
        issued_at=credential.issued_at,
        expires_at=credential.expires_at,
        renewal_due_at=credential.renewal_due_at,
        verification_url=credential.verification_url,
        evidence_object_key=credential.evidence_object_key,
        notes=credential.notes,
        created_at=credential.created_at,
    )


def to_report_package_read(package) -> IncidentReportPackageRead:
    return IncidentReportPackageRead(
        id=package.id,
        organization_id=package.organization_id,
        incident_id=package.incident_id,
        prepared_by_person_id=package.prepared_by_person_id,
        submitted_by_person_id=package.submitted_by_person_id,
        agency_name=package.agency_name,
        jurisdiction=package.jurisdiction,
        status=package.status,
        due_at=package.due_at,
        submitted_at=package.submitted_at,
        accepted_at=package.accepted_at,
        external_reference=package.external_reference,
        narrative=package.narrative,
        checklist_json=package.checklist_json,
        submission_payload=package.submission_payload,
        notes=package.notes,
        created_at=package.created_at,
    )


def to_insurance_claim_read(claim) -> IncidentInsuranceClaimRead:
    return IncidentInsuranceClaimRead(
        id=claim.id,
        organization_id=claim.organization_id,
        incident_id=claim.incident_id,
        claimant_person_id=claim.claimant_person_id,
        prepared_by_person_id=claim.prepared_by_person_id,
        submitted_by_person_id=claim.submitted_by_person_id,
        claim_type=claim.claim_type,
        status=claim.status,
        provider_name=claim.provider_name,
        policy_number=claim.policy_number,
        claim_number=claim.claim_number,
        coverage_verified_at=claim.coverage_verified_at,
        submitted_at=claim.submitted_at,
        closed_at=claim.closed_at,
        claimed_amount_cents=claim.claimed_amount_cents,
        approved_amount_cents=claim.approved_amount_cents,
        paid_amount_cents=claim.paid_amount_cents,
        currency=claim.currency,
        reserve_amount_cents=claim.reserve_amount_cents,
        tracking_url=claim.tracking_url,
        documentation_checklist_json=claim.documentation_checklist_json,
        submission_payload=claim.submission_payload,
        communication_log=claim.communication_log,
        notes=claim.notes,
        created_at=claim.created_at,
    )


def to_medical_clearance_read(clearance) -> IncidentMedicalClearanceRead:
    return IncidentMedicalClearanceRead(
        id=clearance.id,
        organization_id=clearance.organization_id,
        incident_id=clearance.incident_id,
        athlete_person_id=clearance.athlete_person_id,
        reviewed_by_person_id=clearance.reviewed_by_person_id,
        status=clearance.status,
        clearance_type=clearance.clearance_type,
        assessed_at=clearance.assessed_at,
        valid_from=clearance.valid_from,
        valid_until=clearance.valid_until,
        restrictions=clearance.restrictions,
        return_to_play_stage=clearance.return_to_play_stage,
        provider_name=clearance.provider_name,
        documentation_object_key=clearance.documentation_object_key,
        notes=clearance.notes,
        created_at=clearance.created_at,
    )


@router.post("/guardians", response_model=GuardianRelationshipRead, status_code=201)
async def create_guardian_route(
    payload: GuardianRelationshipCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GuardianRelationshipRead:
    return to_guardian_read(await create_guardian_relationship(db, identity, payload, authz))


@router.get(
    "/athletes/{athlete_person_id}/guardians", response_model=list[GuardianRelationshipRead]
)
async def list_guardians_route(
    athlete_person_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[GuardianRelationshipRead]:
    return [
        to_guardian_read(relationship)
        for relationship in await list_guardians_for_athlete(db, athlete_person_id)
    ]


@router.get("/guardian-account-readiness", response_model=list[GuardianAccountReadinessRead])
async def list_guardian_account_readiness_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[GuardianAccountReadinessRead]:
    return await list_guardian_account_readiness(db, identity, organization_id, authz)


@router.post(
    "/guardian-account-readiness/invite-batch",
    response_model=GuardianPortalInviteBatchRead,
)
async def create_guardian_portal_invite_batch_route(
    payload: GuardianPortalInviteBatchCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GuardianPortalInviteBatchRead:
    return await create_guardian_portal_invite_batch(db, identity, payload, authz)


@router.post(
    "/guardian-account-readiness/{relationship_id}/invite",
    response_model=GuardianPortalInviteRead,
)
async def create_guardian_portal_invite_route(
    relationship_id: UUID,
    payload: GuardianPortalInviteCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> GuardianPortalInviteRead:
    return await create_guardian_portal_invite(db, identity, relationship_id, payload, authz)


@router.get("/my-family", response_model=list[FamilyAthleteSummaryRead])
async def list_my_family_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[FamilyAthleteSummaryRead]:
    return await list_my_family(db, identity, organization_id)


@router.get("/my-family/performance", response_model=list[FamilyPerformanceSummaryRead])
async def list_my_family_performance_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[FamilyPerformanceSummaryRead]:
    return await list_my_family_performance(db, identity, organization_id)


@router.get("/my-family/dashboard", response_model=FamilyDashboardRead)
async def get_my_family_dashboard_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> FamilyDashboardRead:
    return await get_my_family_dashboard(db, identity, organization_id)


@router.get("/my-family/coordination", response_model=list[FamilyCoordinationRowRead])
async def get_my_family_coordination_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[FamilyCoordinationRowRead]:
    return await get_my_family_coordination(db, identity, organization_id)


@router.post("/my-family/coordination/digest", response_model=FamilyCoordinationDigestRead)
async def create_family_coordination_digest_route(
    payload: FamilyCoordinationDigestCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FamilyCoordinationDigestRead:
    return await create_family_coordination_digest(db, identity, payload, authz)


@router.post("/incidents", response_model=SafeguardingIncidentRead, status_code=201)
async def create_safeguarding_incident_route(
    payload: SafeguardingIncidentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentRead:
    return to_incident_read(await create_safeguarding_incident(db, identity, payload, authz))


@router.get("/incidents", response_model=list[SafeguardingIncidentRead])
async def list_safeguarding_incidents_route(
    organization_id: UUID = Query(),
    status_filter: SafeguardingIncidentStatus | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[SafeguardingIncidentRead]:
    await ensure_org_manage(authz, organization_id, identity)
    return [
        to_incident_read(incident)
        for incident in await list_safeguarding_incidents(db, organization_id, status_filter)
    ]


@router.get("/incident-evidence-review-queue", response_model=list[SafeguardingIncidentEvidenceReviewItemRead])
async def list_safeguarding_incident_evidence_review_queue_route(
    organization_id: UUID = Query(),
    review_status: str | None = Query(default=None, pattern="^(needs_review|accepted|rejected|escalated)$"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[SafeguardingIncidentEvidenceReviewItemRead]:
    return await list_safeguarding_incident_evidence_review_queue(
        db,
        identity,
        organization_id,
        authz,
        review_status,
    )


@router.patch("/incidents/{incident_id}", response_model=SafeguardingIncidentRead)
async def update_safeguarding_incident_route(
    incident_id: UUID,
    payload: SafeguardingIncidentUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentRead:
    return to_incident_read(await update_safeguarding_incident(db, identity, incident_id, payload, authz))


@router.post("/incidents/{incident_id}/investigation-actions", response_model=SafeguardingIncidentInvestigationActionRead)
async def apply_safeguarding_incident_investigation_action_route(
    incident_id: UUID,
    payload: SafeguardingIncidentInvestigationActionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentInvestigationActionRead:
    return await apply_safeguarding_incident_investigation_action(
        db,
        identity,
        incident_id,
        payload,
        authz,
    )


@router.post("/incidents/{incident_id}/access-controls/sync", response_model=SafeguardingIncidentAccessControlRead)
async def sync_safeguarding_incident_access_controls_route(
    incident_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentAccessControlRead:
    return await sync_safeguarding_incident_access_controls_by_id(
        db,
        identity,
        incident_id,
        authz,
    )


@router.post("/incidents/{incident_id}/access-grants", response_model=SafeguardingIncidentAccessGrantRead, status_code=201)
async def create_safeguarding_incident_access_grant_route(
    incident_id: UUID,
    payload: SafeguardingIncidentAccessGrantCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentAccessGrantRead:
    return await create_safeguarding_incident_access_grant(db, identity, incident_id, payload, authz)


@router.get("/incidents/{incident_id}/access-grants", response_model=list[SafeguardingIncidentAccessGrantRead])
async def list_safeguarding_incident_access_grants_route(
    incident_id: UUID,
    active: bool | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[SafeguardingIncidentAccessGrantRead]:
    return await list_safeguarding_incident_access_grants(db, identity, incident_id, authz, active=active)


@router.post(
    "/incidents/{incident_id}/access-grants/{grant_id}/revoke",
    response_model=SafeguardingIncidentAccessGrantRead,
)
async def revoke_safeguarding_incident_access_grant_route(
    incident_id: UUID,
    grant_id: UUID,
    payload: SafeguardingIncidentAccessGrantRevoke,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentAccessGrantRead:
    return await revoke_safeguarding_incident_access_grant(
        db,
        identity,
        incident_id,
        grant_id,
        payload,
        authz,
    )


@router.post("/evidence-policy-rules", response_model=SafeguardingEvidencePolicyRuleRead, status_code=201)
async def create_safeguarding_evidence_policy_rule_route(
    payload: SafeguardingEvidencePolicyRuleCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingEvidencePolicyRuleRead:
    return await create_safeguarding_evidence_policy_rule(db, identity, payload, authz)


@router.get("/evidence-policy-rules", response_model=list[SafeguardingEvidencePolicyRuleRead])
async def list_safeguarding_evidence_policy_rules_route(
    organization_id: UUID = Query(),
    active: bool | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[SafeguardingEvidencePolicyRuleRead]:
    return await list_safeguarding_evidence_policy_rules(
        db,
        identity,
        organization_id,
        authz,
        active=active,
    )


@router.patch("/evidence-policy-rules/{rule_id}", response_model=SafeguardingEvidencePolicyRuleRead)
async def update_safeguarding_evidence_policy_rule_route(
    rule_id: UUID,
    payload: SafeguardingEvidencePolicyRuleUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingEvidencePolicyRuleRead:
    return await update_safeguarding_evidence_policy_rule(db, identity, rule_id, payload, authz)


@router.post("/incidents/{incident_id}/evidence", response_model=SafeguardingIncidentEvidenceUploadRead)
async def upload_safeguarding_incident_evidence_route(
    incident_id: UUID,
    payload: SafeguardingIncidentEvidenceUploadCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentEvidenceUploadRead:
    return await upload_safeguarding_incident_evidence(
        db,
        identity,
        incident_id,
        payload,
        authz,
    )


@router.post("/incidents/{incident_id}/evidence-link", response_model=SafeguardingIncidentEvidenceLinkRead)
async def create_safeguarding_incident_evidence_link_route(
    incident_id: UUID,
    payload: SafeguardingIncidentEvidenceLinkCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentEvidenceLinkRead:
    return await create_signed_safeguarding_incident_evidence_link(
        db,
        identity,
        incident_id,
        payload,
        authz,
    )


@router.get("/incidents/{incident_id}/evidence-approval-policy", response_model=SafeguardingIncidentEvidenceApprovalPolicyRead)
async def get_safeguarding_incident_evidence_approval_policy_route(
    incident_id: UUID,
    storage_key: str = Query(min_length=1, max_length=800),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentEvidenceApprovalPolicyRead:
    return await get_safeguarding_incident_evidence_approval_policy(
        db,
        identity,
        incident_id,
        storage_key,
        authz,
    )


@router.post("/incidents/{incident_id}/evidence-review", response_model=SafeguardingIncidentEvidenceReviewActionRead)
async def review_safeguarding_incident_evidence_route(
    incident_id: UUID,
    payload: SafeguardingIncidentEvidenceReviewActionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> SafeguardingIncidentEvidenceReviewActionRead:
    return await review_safeguarding_incident_evidence(
        db,
        identity,
        incident_id,
        payload,
        authz,
    )


@router.post("/incident-report-packages", response_model=IncidentReportPackageRead, status_code=201)
async def create_incident_report_package_route(
    payload: IncidentReportPackageCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentReportPackageRead:
    return to_report_package_read(await create_incident_report_package(db, identity, payload, authz))


@router.get("/incident-report-packages", response_model=list[IncidentReportPackageRead])
async def list_incident_report_packages_route(
    organization_id: UUID = Query(),
    status_filter: IncidentReportPackageStatus | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[IncidentReportPackageRead]:
    await ensure_org_manage(authz, organization_id, identity)
    return [
        to_report_package_read(package)
        for package in await list_incident_report_packages(db, organization_id, status_filter)
    ]


@router.patch("/incident-report-packages/{package_id}", response_model=IncidentReportPackageRead)
async def update_incident_report_package_route(
    package_id: UUID,
    payload: IncidentReportPackageUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentReportPackageRead:
    return to_report_package_read(
        await update_incident_report_package(db, identity, package_id, payload, authz)
    )


@router.get(
    "/incident-report-packages/{package_id}/artifact",
    response_model=IncidentReportPackageArtifactRead,
)
async def get_incident_report_package_artifact_route(
    package_id: UUID,
    artifact_format: str = Query(default="markdown", pattern="^(markdown|pdf)$"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentReportPackageArtifactRead:
    return IncidentReportPackageArtifactRead(
        **await get_incident_report_package_artifact(
            db,
            identity,
            package_id,
            artifact_format,
            authz,
        )
    )


@router.post(
    "/incident-report-packages/{package_id}/artifact-link",
    response_model=IncidentReportPackageArtifactLinkRead,
)
async def create_incident_report_package_artifact_link_route(
    package_id: UUID,
    artifact_format: str = Query(default="pdf", pattern="^(markdown|pdf)$"),
    ttl_seconds: int | None = Query(default=None, ge=60, le=86400),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentReportPackageArtifactLinkRead:
    return await create_signed_incident_report_package_artifact_link(
        db,
        identity,
        package_id,
        artifact_format,
        ttl_seconds,
        authz,
    )


@router.post(
    "/incident-report-packages/{package_id}/submit-regulator",
    response_model=IncidentReportPackageProviderSubmissionRead,
)
async def submit_incident_report_package_to_regulator_route(
    package_id: UUID,
    artifact_format: str = Query(default="pdf", pattern="^(markdown|pdf)$"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentReportPackageProviderSubmissionRead:
    return await submit_incident_report_package_to_regulator(
        db,
        identity,
        package_id,
        artifact_format,
        authz,
    )


@router.get("/incident-report-artifacts/{organization_id}/{package_id}/{filename}")
async def read_incident_report_package_artifact_route(
    organization_id: UUID,
    package_id: UUID,
    filename: str,
    artifact_format: str = Query(pattern="^(markdown|pdf)$"),
    generated: int = Query(),
    expires: int = Query(),
    signature: str = Query(),
    db: AsyncSession = Depends(get_db),
) -> Response:
    artifact = await read_signed_incident_report_package_artifact(
        db,
        organization_id,
        package_id,
        filename,
        artifact_format,
        generated,
        expires,
        signature,
    )
    return Response(
        content=artifact["content"],
        media_type=str(artifact["content_type"]),
        headers={
            "Content-Disposition": f"inline; filename={artifact['filename']}",
            "X-Afrolete-Safeguarding-Artifact-Checksum": str(artifact["checksum"]),
        },
    )


@router.get("/incident-evidence/{organization_id}/{incident_id}/{filename}")
async def read_safeguarding_incident_evidence_route(
    organization_id: UUID,
    incident_id: UUID,
    filename: str,
    checksum: str = Query(),
    expires: int = Query(),
    signature: str = Query(),
) -> Response:
    evidence = await read_signed_safeguarding_incident_evidence(
        organization_id,
        incident_id,
        filename,
        checksum,
        expires,
        signature,
    )
    return Response(
        content=evidence["content"],
        media_type=str(evidence["content_type"]),
        headers={
            "Content-Disposition": f"inline; filename={evidence['filename']}",
            "X-Afrolete-Safeguarding-Evidence-Checksum": str(evidence["checksum"]),
        },
    )


@router.get("/background-check-evidence/{organization_id}/{check_id}/{filename}")
async def read_background_check_evidence_document_route(
    organization_id: UUID,
    check_id: UUID,
    filename: str,
    checksum: str = Query(),
    expires: int = Query(),
    signature: str = Query(),
) -> Response:
    evidence = await read_signed_background_check_evidence_document(
        organization_id,
        check_id,
        filename,
        checksum,
        expires,
        signature,
    )
    return Response(
        content=evidence["content"],
        media_type=str(evidence["content_type"]),
        headers={
            "Content-Disposition": f"inline; filename={evidence['filename']}",
            "X-Afrolete-Background-Check-Evidence-Checksum": str(evidence["checksum"]),
        },
    )


@router.post("/insurance-claims", response_model=IncidentInsuranceClaimRead, status_code=201)
async def create_incident_insurance_claim_route(
    payload: IncidentInsuranceClaimCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentInsuranceClaimRead:
    return to_insurance_claim_read(await create_incident_insurance_claim(db, identity, payload, authz))


@router.get("/insurance-claims", response_model=list[IncidentInsuranceClaimRead])
async def list_incident_insurance_claims_route(
    organization_id: UUID = Query(),
    status_filter: InsuranceClaimStatus | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[IncidentInsuranceClaimRead]:
    await ensure_org_manage(authz, organization_id, identity)
    return [
        to_insurance_claim_read(claim)
        for claim in await list_incident_insurance_claims(db, organization_id, status_filter)
    ]


@router.patch("/insurance-claims/{claim_id}", response_model=IncidentInsuranceClaimRead)
async def update_incident_insurance_claim_route(
    claim_id: UUID,
    payload: IncidentInsuranceClaimUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentInsuranceClaimRead:
    return to_insurance_claim_read(
        await update_incident_insurance_claim(db, identity, claim_id, payload, authz)
    )


@router.post("/insurance-claims/{claim_id}/submit-provider", response_model=IncidentInsuranceClaimProviderSyncRead)
async def submit_incident_insurance_claim_to_provider_route(
    claim_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentInsuranceClaimProviderSyncRead:
    return await submit_incident_insurance_claim_to_provider(db, identity, claim_id, authz)


@router.post("/insurance-claims/{claim_id}/poll-provider-status", response_model=IncidentInsuranceClaimProviderSyncRead)
async def poll_incident_insurance_claim_provider_status_route(
    claim_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentInsuranceClaimProviderSyncRead:
    return await poll_incident_insurance_claim_provider_status(db, identity, claim_id, authz)


@router.post("/medical-clearances", response_model=IncidentMedicalClearanceRead, status_code=201)
async def create_incident_medical_clearance_route(
    payload: IncidentMedicalClearanceCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentMedicalClearanceRead:
    return to_medical_clearance_read(await create_incident_medical_clearance(db, identity, payload, authz))


@router.get("/medical-clearances", response_model=list[IncidentMedicalClearanceRead])
async def list_incident_medical_clearances_route(
    organization_id: UUID = Query(),
    status_filter: MedicalClearanceStatus | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[IncidentMedicalClearanceRead]:
    await ensure_org_manage(authz, organization_id, identity)
    return [
        to_medical_clearance_read(clearance)
        for clearance in await list_incident_medical_clearances(db, organization_id, status_filter)
    ]


@router.patch("/medical-clearances/{clearance_id}", response_model=IncidentMedicalClearanceRead)
async def update_incident_medical_clearance_route(
    clearance_id: UUID,
    payload: IncidentMedicalClearanceUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentMedicalClearanceRead:
    return to_medical_clearance_read(
        await update_incident_medical_clearance(db, identity, clearance_id, payload, authz)
    )


@router.post("/medical-clearances/{clearance_id}/submit-provider", response_model=IncidentMedicalClearanceProviderSyncRead)
async def submit_incident_medical_clearance_to_provider_route(
    clearance_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentMedicalClearanceProviderSyncRead:
    return await submit_incident_medical_clearance_to_provider(db, identity, clearance_id, authz)


@router.post("/medical-clearances/{clearance_id}/poll-provider-status", response_model=IncidentMedicalClearanceProviderSyncRead)
async def poll_incident_medical_clearance_provider_status_route(
    clearance_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> IncidentMedicalClearanceProviderSyncRead:
    return await poll_incident_medical_clearance_provider_status(db, identity, clearance_id, authz)


@router.post("/background-checks", response_model=BackgroundCheckRead, status_code=201)
async def create_background_check_route(
    payload: BackgroundCheckCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BackgroundCheckRead:
    return to_background_check_read(await create_background_check(db, identity, payload, authz))


@router.get("/background-checks", response_model=list[BackgroundCheckRead])
async def list_background_checks_route(
    organization_id: UUID = Query(),
    status_filter: BackgroundCheckStatus | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[BackgroundCheckRead]:
    await ensure_org_manage(authz, organization_id, identity)
    return [
        to_background_check_read(check)
        for check in await list_background_checks(db, organization_id, status_filter)
    ]


@router.post(
    "/background-checks/{check_id}/evidence",
    response_model=BackgroundCheckEvidenceDocumentRead,
    status_code=201,
)
async def upload_background_check_evidence_document_route(
    check_id: UUID,
    payload: BackgroundCheckEvidenceDocumentUploadCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BackgroundCheckEvidenceDocumentRead:
    return await upload_background_check_evidence_document(db, identity, check_id, payload, authz)


@router.get(
    "/background-checks/{check_id}/evidence",
    response_model=list[BackgroundCheckEvidenceDocumentRead],
)
async def list_background_check_evidence_documents_route(
    check_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[BackgroundCheckEvidenceDocumentRead]:
    return await list_background_check_evidence_documents(db, identity, check_id, authz)


@router.post(
    "/background-check-evidence/{document_id}/review",
    response_model=BackgroundCheckEvidenceDocumentRead,
)
async def review_background_check_evidence_document_route(
    document_id: UUID,
    payload: BackgroundCheckEvidenceDocumentReviewCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BackgroundCheckEvidenceDocumentRead:
    return await review_background_check_evidence_document(db, identity, document_id, payload, authz)


@router.post(
    "/background-check-evidence/{document_id}/link",
    response_model=BackgroundCheckEvidenceDocumentLinkRead,
)
async def create_background_check_evidence_document_link_route(
    document_id: UUID,
    payload: BackgroundCheckEvidenceDocumentLinkCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BackgroundCheckEvidenceDocumentLinkRead:
    return await create_signed_background_check_evidence_document_link(db, identity, document_id, payload, authz)


@router.get("/compliance-summary", response_model=ComplianceSummaryRead)
async def compliance_summary_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ComplianceSummaryRead:
    await ensure_org_manage(authz, organization_id, identity)
    return await compliance_summary(db, organization_id)


@router.post("/compliance-reconcile", response_model=ComplianceReconciliationRead)
async def reconcile_compliance_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ComplianceReconciliationRead:
    return await reconcile_compliance_statuses(db, identity, organization_id, authz)


@router.patch("/background-checks/{check_id}", response_model=BackgroundCheckRead)
async def update_background_check_route(
    check_id: UUID,
    payload: BackgroundCheckUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BackgroundCheckRead:
    return to_background_check_read(await update_background_check(db, identity, check_id, payload, authz))


@router.post("/background-checks/{check_id}/submit-provider", response_model=BackgroundCheckProviderSubmissionRead)
async def submit_background_check_to_screening_provider_route(
    check_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> BackgroundCheckProviderSubmissionRead:
    return await submit_background_check_to_screening_provider(db, identity, check_id, authz)


@router.post(
    "/background-check-provider-results",
    response_model=BackgroundCheckProviderResultRead,
)
async def ingest_background_check_provider_result_route(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> BackgroundCheckProviderResultRead:
    raw_body = await request.body()
    try:
        payload = BackgroundCheckProviderResultCreate.model_validate_json(raw_body)
    except (ValidationError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid screening provider payload",
        ) from exc
    return await ingest_background_check_provider_result(
        db,
        payload,
        raw_body,
        request.headers.get("X-Afrolete-Safeguarding-Timestamp"),
        request.headers.get("X-Afrolete-Safeguarding-Signature"),
    )


@router.post("/credentials", response_model=ComplianceCredentialRead, status_code=201)
async def create_compliance_credential_route(
    payload: ComplianceCredentialCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ComplianceCredentialRead:
    return to_credential_read(await create_compliance_credential(db, identity, payload, authz))


@router.get("/credentials", response_model=list[ComplianceCredentialRead])
async def list_compliance_credentials_route(
    organization_id: UUID = Query(),
    status_filter: ComplianceCredentialStatus | None = Query(default=None, alias="status"),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ComplianceCredentialRead]:
    await ensure_org_manage(authz, organization_id, identity)
    return [
        to_credential_read(credential)
        for credential in await list_compliance_credentials(db, organization_id, status_filter)
    ]


@router.patch("/credentials/{credential_id}", response_model=ComplianceCredentialRead)
async def update_compliance_credential_route(
    credential_id: UUID,
    payload: ComplianceCredentialUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ComplianceCredentialRead:
    return to_credential_read(
        await update_compliance_credential(db, identity, credential_id, payload, authz)
    )


@router.get("/my-family/events", response_model=list[FamilyEventSummaryRead])
async def list_my_family_events_route(
    organization_id: UUID = Query(),
    limit: int = Query(default=50, ge=1, le=200),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[FamilyEventSummaryRead]:
    return await list_my_family_events(db, identity, organization_id, limit)


@router.get("/my-family/consent-requests", response_model=list[FamilyConsentRequestRead])
async def list_my_family_consent_requests_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> list[FamilyConsentRequestRead]:
    return await list_my_family_consent_requests(db, identity, organization_id)


@router.post("/my-family/consent-requests/{request_id}/response", response_model=ActivityConsentRead)
async def respond_to_family_consent_request_route(
    request_id: UUID,
    payload: FamilyConsentResponseCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> ActivityConsentRead:
    return to_consent_read(await respond_to_family_consent_request(db, identity, request_id, payload))


@router.post(
    "/my-family/events/{event_id}/athletes/{athlete_person_id}/rsvp",
    response_model=FamilyEventSummaryRead,
)
async def respond_to_family_event_route(
    event_id: UUID,
    athlete_person_id: UUID,
    payload: FamilyEventRsvpCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> FamilyEventSummaryRead:
    return await respond_to_family_event(db, identity, event_id, athlete_person_id, payload)


@router.post("/consent-requests", response_model=ConsentRequestRead, status_code=201)
async def create_consent_request_route(
    payload: ConsentRequestCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ConsentRequestRead:
    request, token = await create_consent_request(db, identity, payload, authz)
    return to_request_read(request, token)


@router.post("/consents", response_model=ActivityConsentRead, status_code=201)
async def create_activity_consent_route(
    payload: ActivityConsentCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ActivityConsentRead:
    return to_consent_read(await create_activity_consent(db, identity, payload, authz))


@router.post("/consents/by-token", response_model=ActivityConsentRead)
async def capture_consent_by_token_route(
    payload: TokenConsentCapture,
    db: AsyncSession = Depends(get_db),
) -> ActivityConsentRead:
    return to_consent_read(await capture_consent_by_token(db, payload))


@router.post("/consents/by-known-channel", response_model=ActivityConsentRead)
async def capture_consent_by_known_channel_route(
    payload: KnownChannelConsentCapture,
    db: AsyncSession = Depends(get_db),
) -> ActivityConsentRead:
    return to_consent_read(await capture_consent_by_known_channel(db, payload))


@router.get(
    "/events/{event_id}/athletes/{athlete_person_id}/clearance",
    response_model=ParticipationClearanceRead,
)
async def participation_clearance_route(
    event_id: UUID,
    athlete_person_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ParticipationClearanceRead:
    clearance, is_minor, guardian_required, consent_id, reason = await clearance_for_event(
        db,
        event_id,
        athlete_person_id,
    )
    return ParticipationClearanceRead(
        event_id=event_id,
        athlete_person_id=athlete_person_id,
        is_minor=is_minor,
        guardian_required=guardian_required,
        status=clearance,
        consent_id=consent_id,
        reason=reason,
    )
