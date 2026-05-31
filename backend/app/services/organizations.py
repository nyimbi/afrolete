import csv
import io
import json
import re
from base64 import b64decode
from binascii import Error as BinasciiError
from calendar import monthrange
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.agent import Agent, AgentTask
from app.models.communication import CommunicationMessage
from app.models.community import (
    FanChallengeProgress,
    FanEngagementChallenge,
    SupporterEngagementActivity,
    SupporterMembershipTier,
    SupporterProfile,
    SupporterReward,
)
from app.models.commercial import FundraisingCampaign, Sponsor, SponsorshipAgreement, TicketProduct
from app.models.enums import (
    AgentKind,
    AgentTaskStatus,
    CommercialStatus,
    CommunicationChannel,
    CommunicationMessageType,
    CommunicationScopeType,
    GuardianRelationshipKind,
    MemberSubjectType,
    MembershipRole,
    OrganizationType,
    RosterStatus,
    SportFormat,
    TeamRole,
)
from app.models.event import Event
from app.models.identity import AppUser, Person
from app.models.organization import (
    Committee,
    CommitteeMembership,
    MemberSubscription,
    MemberSubscriptionCharge,
    MemberSubscriptionPayment,
    MemberSubscriptionPlan,
    Membership,
    OrganizationAwardCategory,
    OrganizationAwardNomination,
    OrganizationAwardProgram,
    OrganizationAwardRecipient,
    OrganizationAwardVote,
    OrganizationComplianceDocument,
    OrganizationComplianceDocumentVersion,
    OrganizationDataMigrationProject,
    OrganizationDataMigrationRun,
    OrganizationExternalReport,
    OrganizationGroup,
    OrganizationGroupMembership,
    OrganizationMarketProfile,
    OrganizationProgram,
    OrganizationRecoveryDrill,
    OrganizationRecoveryPlan,
    OrganizationSeason,
    Organization,
    RegistrationInquiry,
)
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry
from app.schemas.organization import (
    CommitteeCreate,
    CommitteeMemberAdd,
    FamilyRegistrationInquiryRead,
    MemberAdd,
    MemberSubscriptionCheckoutLinkRead,
    MemberSubscriptionCheckoutSettlementCreate,
    MemberSubscriptionCheckoutSettlementRead,
    MemberSubscriptionChargeRunCreate,
    MemberSubscriptionChargeRunItemRead,
    MemberSubscriptionChargeRunRead,
    MemberSubscriptionCreate,
    MemberSubscriptionHostedCheckoutRead,
    MemberSubscriptionReminderItemRead,
    MemberSubscriptionReminderRunCreate,
    MemberSubscriptionReminderRunRead,
    MemberSubscriptionPaymentCreate,
    MemberSubscriptionPlanCreate,
    OrganizationAwardCategoryCreate,
    OrganizationAwardNominationCreate,
    OrganizationAwardProgramCreate,
    OrganizationAwardRecipientCreate,
    OrganizationAwardVoteCreate,
    OrganizationComplianceDocumentCreate,
    OrganizationComplianceDocumentVersionCreate,
    OrganizationComplianceDocumentSummaryRead,
    OrganizationDataMigrationProjectCreate,
    OrganizationDataMigrationRunCreate,
    OrganizationExternalReportCreate,
    OrganizationExternalReportRead,
    OrganizationExternalReportStatusUpdate,
    OrganizationExternalReportSummaryRead,
    OrganizationGroupCreate,
    OrganizationGroupMemberAdd,
    OrganizationMarketProfileCreate,
    OrganizationMarketProfileRead,
    OrganizationMarketProfileSummaryRead,
    OrganizationProgramCreate,
    OrganizationRecoveryDrillCreate,
    OrganizationRecoveryPlanCreate,
    OrganizationSeasonCreate,
    OrganizationHandleAvailabilityRead,
    OrganizationCreate,
    PublicRegistrationDocumentUpload,
    PublicRegistrationPacketUpdate,
    PublicRegistrationInquiryCreate,
    PublicSupporterChallengeProgressCreate,
    PublicSupporterChallengeProgressRead,
    PublicSupporterSignupCreate,
    PublicSupporterSignupRead,
    RegistrationLearningModuleRead,
    RegistrationLearningPathCreate,
    RegistrationLearningPathRead,
    RegistrationLaunchCommandCenterRead,
    RegistrationLaunchCopyRead,
    RegistrationLaunchLinkRead,
    RegistrationLaunchMetricRead,
    RegistrationLaunchReadinessCheckRead,
    RegistrationOnboardingMissionRead,
    RegistrationInquiryImportCreate,
    RegistrationInquiryImportPreviewRowRead,
    RegistrationInquiryImportRowErrorRead,
    RegistrationInquiryImportTemplateRead,
    RegistrationReadinessFamilyInquiryRead,
    RegistrationOnboardingPresetRead,
    RegistrationReadinessOrganizationRead,
    RegistrationReadinessRead,
    RegistrationReadinessStepRead,
    RegistrationInquiryAccountReadinessRead,
    RegistrationInquiryConversionCreate,
    RegistrationInquiryFollowUpCreate,
    RegistrationPaymentHostedCheckoutRead,
    RegistrationPaymentSessionCreate,
    RegistrationPaymentSettlementCreate,
    RegistrationPaymentSettlementRead,
    RegistrationInquiryUpdate,
)
from app.schemas.agent import AgentTaskCreate
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship
from app.services.agents import queue_agent_task
from app.services.communications import create_message, create_message_for_recipients, destination_for_channel
from app.schemas.communication import CommunicationMessageCreate
from app.services.storage.objects import put_object


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "organization"


def bounded_handle(value: str, max_length: int = 120) -> str:
    return slugify(value)[:max_length].strip("-") or "organization"


def handle_candidate(base: str, suffix: int | None = None, max_length: int = 120) -> str:
    clean_base = bounded_handle(base, max_length=max_length)
    if suffix is None:
        return clean_base
    suffix_text = f"-{suffix}"
    return f"{clean_base[: max_length - len(suffix_text)].strip('-')}{suffix_text}"


def organization_member_relation(subject_type: MemberSubjectType, role: MembershipRole) -> str:
    if subject_type == MemberSubjectType.ORGANIZATION:
        return "member_org"
    if subject_type == MemberSubjectType.TEAM:
        return "member_team"
    return role.value


INQUIRY_REVIEW_STATUSES = {"new", "reviewing", "contacted", "waitlisted", "rejected"}
REGISTRATION_PAYMENT_COMPLETE_STATUSES = {"paid", "waived", "not_required"}
REGISTRATION_PAYMENT_REVIEW_STATUSES = REGISTRATION_PAYMENT_COMPLETE_STATUSES | {
    "pending",
    "pending_verification",
    "failed",
    "cancelled",
}
DEFAULT_REGISTRATION_DOCUMENTS = ["proof_of_age", "medical_information"]


def public_site_path(organization: Organization) -> str:
    return f"/site/{organization.subdomain or organization.slug}"


def registration_page_path(organization: Organization) -> str:
    return f"/register?mode=player&site={organization.subdomain or organization.slug}"


def admissions_path(organization: Organization) -> str:
    return f"/admissions?organization_id={organization.id}"


def family_portal_path(organization: Organization) -> str:
    return f"/family?organization_id={organization.id}"


def dashboard_path(organization: Organization) -> str:
    return f"/?organization_id={organization.id}"


def absolute_launch_url(base_url: str, path: str) -> str:
    base = (base_url or "https://afrolete.lindela.io").rstrip("/")
    return f"{base}{path if path.startswith('/') else f'/{path}'}"


def onboarding_checklist(organization: Organization, launch_goal: str | None = None) -> list[str]:
    organization_label = "school" if organization.organization_type == OrganizationType.SCHOOL else "club"
    steps = [
        f"Invite the first {organization_label} administrators and coaches.",
        "Create teams, squads, or individual sport groups.",
        "Publish the branded public registration page.",
        "Collect player/family registration inquiries and convert accepted athletes.",
        "Send guardian portal invitations for minors and consent signers.",
        "Configure fees, payment links, and communication delivery channels.",
    ]
    if organization.organization_type == OrganizationType.SCHOOL:
        steps.insert(2, "Add school teams by sport, age group, season, and staff lead.")
    if launch_goal:
        steps.insert(0, f"Confirm launch goal: {launch_goal}")
    return steps


def registration_onboarding_presets(
    organization_type: OrganizationType | None = None,
) -> list[RegistrationOnboardingPresetRead]:
    presets = [
        RegistrationOnboardingPresetRead(
            key="school_term_athletics",
            label="School athletics term",
            organization_type=OrganizationType.SCHOOL,
            audience="School athletic director",
            description="Launch a term-based athletics program with guardian consent, medical notes, and school clearance ready from day one.",
            primary_sport="athletics",
            launch_goal="Open term registration, collect guardian packets, and prepare admissions review this week",
            starter_team_name="Term Athletics Squad",
            starter_team_sport_format=SportFormat.INDIVIDUAL,
            starter_team_age_group="U15",
            starter_team_gender_category="open",
            starter_team_season_label="Current term",
            registration_required_documents=[
                "proof_of_age",
                "medical_information",
                "guardian_consent",
                "photo_release",
                "school_clearance",
            ],
            registration_fee_currency="KES",
            registration_payment_instructions=(
                "Use the hosted checkout link or confirm payment with the school bursar before admissions conversion."
            ),
            checklist=[
                "Confirm term dates, school medical contact, and athletics staff lead.",
                "Publish the family registration link through school communication channels.",
                "Review packets for guardian consent, medical notes, and school clearance.",
            ],
        ),
        RegistrationOnboardingPresetRead(
            key="school_team_sport",
            label="School team sport",
            organization_type=OrganizationType.SCHOOL,
            audience="Teacher-coach or games master",
            description="Start a school team with age group, season, eligibility, and parent packet defaults already aligned.",
            primary_sport="football",
            launch_goal="Register the first school team and invite guardians for roster verification",
            starter_team_name="Junior Team",
            starter_team_sport_format=SportFormat.TEAM,
            starter_team_age_group="U17",
            starter_team_gender_category="open",
            starter_team_season_label="School season",
            registration_required_documents=[
                "proof_of_age",
                "medical_information",
                "guardian_consent",
                "photo_release",
                "academic_eligibility",
            ],
            registration_fee_currency="KES",
            registration_payment_instructions=(
                "Collect school activity fees through the approved school payment channel before final roster approval."
            ),
            checklist=[
                "Set the teacher-coach, captain, and team administrator roles.",
                "Confirm academic eligibility and guardian consent before fixtures.",
                "Create the first training schedule and attendance policy.",
            ],
        ),
        RegistrationOnboardingPresetRead(
            key="club_youth_team",
            label="Youth club team",
            organization_type=OrganizationType.CLUB,
            audience="Club manager",
            description="Open youth team registration with a branded public page, guardian packet, starter roster, and admissions queue.",
            primary_sport="football",
            launch_goal="Recruit the first youth team, complete family packets, and convert approved players",
            starter_team_name="U15 Development",
            starter_team_sport_format=SportFormat.TEAM,
            starter_team_age_group="U15",
            starter_team_gender_category="open",
            starter_team_season_label="2026",
            registration_required_documents=[
                "proof_of_age",
                "medical_information",
                "guardian_consent",
                "photo_release",
            ],
            registration_fee_currency="KES",
            registration_payment_instructions=(
                "Families can pay online after completing the registration packet; staff should verify settlement before conversion."
            ),
            checklist=[
                "Assign club administrators, head coach, and safeguarding contact.",
                "Publish the public registration page and share it with families.",
                "Review packet, payment, and consent readiness before admitting players.",
            ],
        ),
        RegistrationOnboardingPresetRead(
            key="club_individual_pathway",
            label="Individual pathway club",
            organization_type=OrganizationType.CLUB,
            audience="Performance club director",
            description="Launch an individual-sport pathway with athlete performance review, guardian consent, and first assessment defaults.",
            primary_sport="athletics",
            launch_goal="Register athletes for assessment, capture family packets, and start performance baselines",
            starter_team_name="Performance Pathway",
            starter_team_sport_format=SportFormat.INDIVIDUAL,
            starter_team_age_group="U18",
            starter_team_gender_category="open",
            starter_team_season_label="2026 season",
            registration_required_documents=[
                "proof_of_age",
                "medical_information",
                "guardian_consent",
                "photo_release",
                "performance_history",
            ],
            registration_fee_currency="KES",
            registration_payment_instructions=(
                "Use the hosted checkout link for assessment fees, then mark waivers or verified payments before admissions."
            ),
            checklist=[
                "Schedule first assessments and assign the performance coach.",
                "Collect medical notes and performance history before baseline testing.",
                "Convert accepted athletes into the pathway roster and performance dashboard.",
            ],
        ),
        RegistrationOnboardingPresetRead(
            key="academy_multi_sport",
            label="Multi-sport academy",
            organization_type=OrganizationType.ACADEMY,
            audience="Academy operator",
            description="Start a multi-sport academy intake with program selection, family onboarding, and flexible first group defaults.",
            primary_sport="multi-sport",
            launch_goal="Launch the first academy intake and route families into the right program",
            starter_team_name="Foundation Group",
            starter_team_sport_format=SportFormat.MIXED,
            starter_team_age_group="U13-U17",
            starter_team_gender_category="open",
            starter_team_season_label="Foundation cohort",
            registration_required_documents=[
                "proof_of_age",
                "medical_information",
                "guardian_consent",
                "photo_release",
                "program_interest",
            ],
            registration_fee_currency="KES",
            registration_payment_instructions=(
                "Collect intake fees through the hosted checkout link or record scholarship waivers during admissions review."
            ),
            checklist=[
                "Confirm program tracks and intake capacity.",
                "Review family packets and route athletes into first groups.",
                "Invite guardians and coaches into the first-week operating workspace.",
            ],
        ),
    ]
    if organization_type is None:
        return presets
    return [preset for preset in presets if preset.organization_type == organization_type]


def default_starter_team_name(organization: Organization) -> str:
    label = organization.primary_sport or "Multi-sport"
    if organization.organization_type == OrganizationType.SCHOOL:
        return f"{label.title()} Program"
    if organization.organization_type == OrganizationType.ACADEMY:
        return f"{label.title()} Academy Group"
    return f"{label.title()} Team"


async def get_public_site_organization(db: AsyncSession, site: str) -> Organization:
    organization = await db.scalar(
        select(Organization).where(
            (Organization.slug == site) | (Organization.subdomain == site)
        )
    )
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return organization


def normalize_registration_document_types(document_types: list[str]) -> list[str]:
    normalized: list[str] = []
    for document_type in document_types:
        safe = re.sub(r"[^a-z0-9_]+", "_", document_type.strip().lower()).strip("_")
        if safe and safe not in normalized:
            normalized.append(safe[:80])
    return normalized[:12]


def organization_registration_required_documents(organization: Organization) -> list[str]:
    raw = organization.registration_required_documents_json
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return normalize_registration_document_types([str(item) for item in parsed])


def organization_public_registration_documents(organization: Organization) -> list[str]:
    return organization_registration_required_documents(organization) or list(DEFAULT_REGISTRATION_DOCUMENTS)


async def create_onboarding_starter_team(
    db: AsyncSession,
    organization: Organization,
    payload_name: str | None,
    payload_sport: str | None,
    sport_format: SportFormat,
    age_group: str | None,
    gender_category: str | None,
    season_label: str | None,
    authz: AuthorizationService,
) -> Team:
    team = Team(
        organization_id=organization.id,
        name=payload_name or default_starter_team_name(organization),
        sport=payload_sport or organization.primary_sport or "multi-sport",
        sport_format=sport_format,
        age_group=age_group,
        gender_category=gender_category,
        season_label=season_label,
    )
    db.add(team)
    await db.flush()
    await authz.touch(
        Relationship(
            resource_type="organization",
            resource_id=str(organization.id),
            relation="member_team",
            subject_type="team",
            subject_id=str(team.id),
        )
    )
    await db.commit()
    await db.refresh(team)
    return team


async def queue_onboarding_concierge_agent_task(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization: Organization,
    starter_team: Team | None,
    launch_goal: str | None,
    authz: AuthorizationService,
) -> AgentTask:
    agent = await db.scalar(
        select(Agent)
        .where(
            Agent.organization_id == organization.id,
            Agent.kind == AgentKind.OPERATIONS,
            Agent.name == "Onboarding Concierge Agent",
        )
        .order_by(Agent.created_at)
        .limit(1)
    )
    if agent is None:
        agent = Agent(
            organization_id=organization.id,
            name="Onboarding Concierge Agent",
            kind=AgentKind.OPERATIONS,
            purpose=(
                "Guide newly launched clubs and schools through public registration, "
                "family onboarding, admissions setup, and first-week operating readiness."
            ),
            status="active",
            model_policy="human_review_required",
        )
        db.add(agent)
        await db.flush()
        await authz.touch(
            Relationship(
                resource_type="agent",
                resource_id=str(agent.id),
                relation="owner",
                subject_type="user",
                subject_id=str(identity.user_id),
            )
        )

    input_ref = (
        f"organization:{organization.id};"
        f"type:{organization.organization_type};"
        f"registration_open:{organization.registration_open};"
        f"starter_team:{starter_team.id if starter_team is not None else 'none'};"
        f"goal:{bounded_input_ref_segment(launch_goal or 'launch')}"
    )
    task = await queue_agent_task(
        db,
        identity,
        agent.id,
        AgentTaskCreate(
            organization_id=organization.id,
            task_type="organization_onboarding_concierge",
            title=f"Guide launch readiness for {organization.public_name or organization.name}",
            input_ref=input_ref,
        ),
        authz,
    )
    await db.refresh(task)
    return task


async def registration_launch_command_center(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    *,
    base_url: str = "https://afrolete.lindela.io",
    ensure_agent_task: bool = False,
) -> tuple[RegistrationLaunchCommandCenterRead, AgentTask | None]:
    if not await can_manage_registration_inquiries(identity, organization_id, authz):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    inquiries = list(
        (
            await db.scalars(
                select(RegistrationInquiry)
                .where(RegistrationInquiry.organization_id == organization_id)
                .order_by(RegistrationInquiry.created_at.desc())
                .limit(500)
            )
        ).all()
    )
    team_count = int(
        await db.scalar(select(func.count(Team.id)).where(Team.organization_id == organization_id))
        or 0
    )
    registration_docs = organization_public_registration_documents(organization)
    ready_packets = [inquiry for inquiry in inquiries if registration_packet_summary(inquiry)["packet_complete"]]
    incomplete_packets = [inquiry for inquiry in inquiries if not registration_packet_summary(inquiry)["packet_complete"]]
    pending_payments = [
        inquiry
        for inquiry in inquiries
        if inquiry.payment_status not in REGISTRATION_PAYMENT_COMPLETE_STATUSES
    ]
    linked_guardian_ids = {
        inquiry.guardian_person_id
        for inquiry in inquiries
        if inquiry.guardian_person_id is not None
    }
    converted_count = sum(1 for inquiry in inquiries if inquiry.status == "converted")

    checks = registration_launch_readiness_checks(
        organization=organization,
        team_count=team_count,
        inquiry_count=len(inquiries),
        ready_packet_count=len(ready_packets),
        registration_docs=registration_docs,
    )
    readiness_score = round(
        (sum(1 for check in checks if check.status == "ready") / max(len(checks), 1)) * 100
    )
    launch_status = "ready" if readiness_score >= 80 else "attention" if readiness_score >= 50 else "blocked"
    links = registration_launch_links(organization, base_url)
    channel_copies = registration_launch_channel_copies(
        organization=organization,
        registration_url=next(link.url for link in links if link.key == "registration"),
        public_site_url=next(link.url for link in links if link.key == "public_site"),
        registration_docs=registration_docs,
    )
    metrics = [
        RegistrationLaunchMetricRead(
            key="teams",
            label="Teams/programs",
            value=team_count,
            detail="Starter destinations families can choose during registration.",
            status="ready" if team_count else "action",
        ),
        RegistrationLaunchMetricRead(
            key="inquiries",
            label="Family inquiries",
            value=len(inquiries),
            detail="Public and imported registration intakes in the admissions queue.",
            status="ready" if inquiries else "action",
        ),
        RegistrationLaunchMetricRead(
            key="ready_packets",
            label="Ready packets",
            value=len(ready_packets),
            detail="Registrations ready for staff verification and conversion.",
            status="ready" if ready_packets else "todo",
        ),
        RegistrationLaunchMetricRead(
            key="incomplete_packets",
            label="Needs family action",
            value=len(incomplete_packets),
            detail="Families still missing documents, consent, emergency, medical, or payment evidence.",
            status="action" if incomplete_packets else "ready",
        ),
        RegistrationLaunchMetricRead(
            key="pending_payments",
            label="Pending payments",
            value=len(pending_payments),
            detail="Registration payments not yet paid, waived, or marked not required.",
            status="action" if pending_payments else "ready",
        ),
        RegistrationLaunchMetricRead(
            key="linked_guardians",
            label="Linked guardians",
            value=len(linked_guardian_ids),
            detail="Reusable guardian contacts connected to family registration records.",
            status="ready" if linked_guardian_ids else "todo",
        ),
        RegistrationLaunchMetricRead(
            key="converted",
            label="Converted athletes",
            value=converted_count,
            detail="Accepted registrations converted into athlete, guardian, and roster records.",
            status="ready" if converted_count else "todo",
        ),
    ]
    agent_task = await find_registration_launch_agent_task(db, organization_id)
    if ensure_agent_task and agent_task is None:
        agent_task = await queue_registration_launch_agent_task(
            db,
            identity,
            organization,
            authz,
            readiness_score=readiness_score,
            inquiry_count=len(inquiries),
            ready_packet_count=len(ready_packets),
            pending_payment_count=len(pending_payments),
        )
    return (
        RegistrationLaunchCommandCenterRead(
            organization_id=organization.id,
            organization_name=organization.name,
            organization_type=organization.organization_type,
            public_name=organization.public_name,
            launch_status=launch_status,
            readiness_score=readiness_score,
            public_site_path=public_site_path(organization),
            registration_page_path=registration_page_path(organization),
            admissions_path=admissions_path(organization),
            family_portal_path=family_portal_path(organization),
            dashboard_path=dashboard_path(organization),
            launch_links=links,
            channel_copies=channel_copies,
            metrics=metrics,
            readiness_checks=checks,
            staff_actions=registration_launch_staff_actions(
                organization=organization,
                checks=checks,
                inquiry_count=len(inquiries),
                ready_packet_count=len(ready_packets),
                pending_payment_count=len(pending_payments),
                agent_task=agent_task,
            ),
        ),
        agent_task,
    )


def registration_launch_readiness_checks(
    *,
    organization: Organization,
    team_count: int,
    inquiry_count: int,
    ready_packet_count: int,
    registration_docs: list[str],
) -> list[RegistrationLaunchReadinessCheckRead]:
    checks = [
        RegistrationLaunchReadinessCheckRead(
            key="workspace",
            label="Workspace ownership",
            status="ready",
            detail=f"{organization.organization_type.value.title()} workspace is created and manageable.",
            action_label="Open console",
            href=dashboard_path(organization),
        ),
        RegistrationLaunchReadinessCheckRead(
            key="public_profile",
            label="Public identity",
            status="ready" if organization.public_name and organization.contact_email else "action",
            detail=(
                f"{organization.public_name or organization.name} has contact details for families."
                if organization.public_name and organization.contact_email
                else "Add public name and contact email before broad family promotion."
            ),
            action_label="Review public page",
            href=public_site_path(organization),
        ),
        RegistrationLaunchReadinessCheckRead(
            key="public_address",
            label="Shareable address",
            status="ready" if organization.subdomain or organization.slug else "blocked",
            detail=f"Public handle: {organization.subdomain or organization.slug}.",
            action_label="Open public site",
            href=public_site_path(organization),
        ),
        RegistrationLaunchReadinessCheckRead(
            key="registration_window",
            label="Registration window",
            status="ready" if organization.registration_open else "blocked",
            detail="Public family registration is open." if organization.registration_open else "Open registration before sharing links.",
            action_label="Open registration",
            href=registration_page_path(organization),
        ),
        RegistrationLaunchReadinessCheckRead(
            key="document_policy",
            label="Document policy",
            status="ready" if registration_docs else "action",
            detail=(
                f"Required documents: {', '.join(registration_docs)}."
                if registration_docs
                else "Define required documents so families know what to upload."
            ),
            action_label="Review registration",
            href=registration_page_path(organization),
        ),
        RegistrationLaunchReadinessCheckRead(
            key="payment_policy",
            label="Payment policy",
            status=(
                "ready"
                if not organization.registration_fee_amount
                or (organization.registration_fee_currency and organization.registration_payment_instructions)
                else "action"
            ),
            detail=(
                "No registration fee configured."
                if not organization.registration_fee_amount
                else f"{organization.registration_fee_currency or 'Currency'} {organization.registration_fee_amount} fee policy is configured."
                if organization.registration_fee_currency and organization.registration_payment_instructions
                else "Add fee currency and payment instructions before collecting fees."
            ),
            action_label="Review packet",
            href=registration_page_path(organization),
        ),
        RegistrationLaunchReadinessCheckRead(
            key="starter_program",
            label="Starter team/program",
            status="ready" if team_count else "action",
            detail=(
                f"{team_count} team/program destination{'' if team_count == 1 else 's'} available."
                if team_count
                else "Create at least one team, squad, or individual sport program."
            ),
            action_label="Open console",
            href=dashboard_path(organization),
        ),
        RegistrationLaunchReadinessCheckRead(
            key="admissions_pipeline",
            label="Admissions pipeline",
            status="ready" if ready_packet_count else "action" if inquiry_count else "todo",
            detail=(
                f"{ready_packet_count} packet{'' if ready_packet_count == 1 else 's'} ready for review."
                if ready_packet_count
                else f"{inquiry_count} intake{'' if inquiry_count == 1 else 's'} waiting for family action."
                if inquiry_count
                else "Share the registration link to start the admissions queue."
            ),
            action_label="Review admissions",
            href=admissions_path(organization),
        ),
    ]
    return checks


def registration_launch_links(
    organization: Organization,
    base_url: str,
) -> list[RegistrationLaunchLinkRead]:
    paths = [
        ("public_site", "Public site", public_site_path(organization), "Families can inspect the branded organization page."),
        ("registration", "Registration form", registration_page_path(organization), "Primary share link for player and family onboarding."),
        ("admissions", "Admissions queue", admissions_path(organization), "Staff workspace for packet review and conversion."),
        ("family_portal", "Family portal", family_portal_path(organization), "Guardian workspace after account handoff or invite."),
        ("dashboard", "Operations console", dashboard_path(organization), "Owner and staff command surface."),
    ]
    return [
        RegistrationLaunchLinkRead(
            key=key,
            label=label,
            url=absolute_launch_url(base_url, path),
            qr_payload=absolute_launch_url(base_url, path),
            description=description,
        )
        for key, label, path, description in paths
    ]


def registration_launch_channel_copies(
    *,
    organization: Organization,
    registration_url: str,
    public_site_url: str,
    registration_docs: list[str],
) -> list[RegistrationLaunchCopyRead]:
    name = organization.public_name or organization.name
    sport = organization.primary_sport or "sports"
    fee_line = (
        f"Registration fee: {organization.registration_fee_currency or ''} {organization.registration_fee_amount}."
        if organization.registration_fee_amount
        else "Registration fee: not required."
    )
    document_line = (
        f"Please prepare: {', '.join(registration_docs)}."
        if registration_docs
        else "Please prepare age, medical, and guardian details."
    )
    email_body = "\n".join(
        [
            f"{name} is now accepting {sport} registrations on AfroLete.",
            document_line,
            fee_line,
            f"Start here: {registration_url}",
            f"Organization page: {public_site_url}",
        ]
    )
    sms_body = f"{name} registration is open. {document_line} Start: {registration_url}"
    whatsapp_body = "\n".join(
        [
            f"*{name} registration is open*",
            document_line,
            fee_line,
            f"Register: {registration_url}",
        ]
    )
    poster_body = "\n".join(
        [
            f"{name} {sport} registration",
            "Scan the QR code or open the link to complete athlete, guardian, consent, document, and payment details.",
            registration_url,
        ]
    )
    copies = [
        ("email", "Email announcement", f"{name} registration is open", email_body, registration_url),
        ("sms", "SMS nudge", None, sms_body, registration_url),
        ("whatsapp", "WhatsApp broadcast", None, whatsapp_body, registration_url),
        ("poster", "Noticeboard poster copy", f"{name} registration", poster_body, registration_url),
    ]
    return [
        RegistrationLaunchCopyRead(
            channel=channel,
            label=label,
            subject=subject,
            body=body,
            share_url=share_url,
            character_count=len(body),
        )
        for channel, label, subject, body, share_url in copies
    ]


def registration_launch_staff_actions(
    *,
    organization: Organization,
    checks: list[RegistrationLaunchReadinessCheckRead],
    inquiry_count: int,
    ready_packet_count: int,
    pending_payment_count: int,
    agent_task: AgentTask | None,
) -> list[str]:
    actions: list[str] = []
    for check in checks:
        if check.status in {"blocked", "action"}:
            actions.append(f"{check.label}: {check.detail}")
    if inquiry_count == 0:
        actions.append("Share the registration link through email, SMS, WhatsApp, school notices, and team chats.")
    if ready_packet_count:
        actions.append("Review ready packets and convert accepted athletes into rosters with guardian invites.")
    if pending_payment_count:
        actions.append("Reconcile pending registration payments or record approved waivers before conversion.")
    if agent_task is None:
        actions.append("Queue the Registration Growth Agent to draft the campaign and first-week operating plan.")
    else:
        actions.append(f"Review Registration Growth Agent task {agent_task.id} before broad outreach.")
    if organization.organization_type == OrganizationType.SCHOOL:
        actions.append("Confirm school clearance, academic eligibility, and term calendar ownership before fixtures.")
    elif organization.organization_type == OrganizationType.CLUB:
        actions.append("Confirm safeguarding contact, coach assignment, and first training schedule before publishing widely.")
    return actions[:10]


async def find_registration_launch_agent_task(
    db: AsyncSession,
    organization_id: UUID,
) -> AgentTask | None:
    return await db.scalar(
        select(AgentTask)
        .where(
            AgentTask.organization_id == organization_id,
            AgentTask.task_type == "registration_launch_campaign",
            AgentTask.input_ref.like(f"registration-launch:{organization_id};%"),
            AgentTask.status.not_in([AgentTaskStatus.FAILED, AgentTaskStatus.CANCELLED]),
        )
        .order_by(AgentTask.created_at.desc())
        .limit(1)
    )


async def queue_registration_launch_agent_task(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization: Organization,
    authz: AuthorizationService,
    *,
    readiness_score: int,
    inquiry_count: int,
    ready_packet_count: int,
    pending_payment_count: int,
) -> AgentTask:
    existing_task = await find_registration_launch_agent_task(db, organization.id)
    if existing_task is not None:
        return existing_task

    agent = await db.scalar(
        select(Agent)
        .where(
            Agent.organization_id == organization.id,
            Agent.kind == AgentKind.OPERATIONS,
            Agent.name == "Registration Growth Agent",
        )
        .order_by(Agent.created_at)
        .limit(1)
    )
    if agent is None:
        agent = Agent(
            organization_id=organization.id,
            name="Registration Growth Agent",
            kind=AgentKind.OPERATIONS,
            purpose=(
                "Turn club and school onboarding state into family outreach campaigns, "
                "admissions operating rhythm, and first-week conversion actions."
            ),
            status="active",
            model_policy="human_review_required",
        )
        db.add(agent)
        await db.flush()
        await authz.touch(
            Relationship(
                resource_type="agent",
                resource_id=str(agent.id),
                relation="owner",
                subject_type="user",
                subject_id=str(identity.user_id),
            )
        )

    input_ref = (
        f"registration-launch:{organization.id};"
        f"type:{organization.organization_type.value};"
        f"score:{readiness_score};"
        f"open:{organization.registration_open};"
        f"inquiries:{inquiry_count};"
        f"ready_packets:{ready_packet_count};"
        f"pending_payments:{pending_payment_count}"
    )
    return await queue_agent_task(
        db,
        identity,
        agent.id,
        AgentTaskCreate(
            organization_id=organization.id,
            task_type="registration_launch_campaign",
            title=f"Launch registration campaign for {organization.public_name or organization.name}",
            input_ref=input_ref,
        ),
        authz,
    )


def bounded_input_ref_segment(value: str, max_length: int = 160) -> str:
    return re.sub(r"\s+", " ", value).strip().replace(";", ",")[:max_length]


def registration_required_documents(inquiry: RegistrationInquiry) -> list[str]:
    configured = parse_registration_documents(inquiry.required_documents_json)
    if configured:
        return [str(item["document_type"]) for item in configured if item.get("document_type")]

    required = list(DEFAULT_REGISTRATION_DOCUMENTS)
    if inquiry.guardian_name or is_youth_age_group(inquiry.age_group):
        required.extend(["guardian_consent", "photo_release"])
    return required


def parse_registration_documents(raw: str | None) -> list[dict[str, object]]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    documents: list[dict[str, object]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        document_type = item.get("document_type")
        filename = item.get("filename")
        if not isinstance(document_type, str):
            continue
        documents.append(
            {
                "document_type": document_type,
                "filename": filename if isinstance(filename, str) else document_type,
                "storage_url": item.get("storage_url") if isinstance(item.get("storage_url"), str) else None,
                "checksum": item.get("checksum") if isinstance(item.get("checksum"), str) else None,
                "content_type": item.get("content_type") if isinstance(item.get("content_type"), str) else None,
                "size_bytes": item.get("size_bytes") if isinstance(item.get("size_bytes"), int) else None,
                "notes": item.get("notes") if isinstance(item.get("notes"), str) else None,
            }
        )
    return documents


def registration_packet_summary(inquiry: RegistrationInquiry) -> dict:
    required_documents = registration_required_documents(inquiry)
    submitted_documents = parse_registration_documents(inquiry.submitted_documents_json)
    submitted_types = {item["document_type"] for item in submitted_documents}
    missing_documents = [item for item in required_documents if item not in submitted_types]
    consent_complete = inquiry.privacy_acknowledged_at is not None and (
        not (inquiry.guardian_name or is_youth_age_group(inquiry.age_group))
        or inquiry.guardian_consent_acknowledged_at is not None
    )
    emergency_contact_complete = bool(inquiry.emergency_contact_name and inquiry.emergency_contact_phone)
    medical_complete = bool(inquiry.medical_notes or "medical_information" in submitted_types)
    payment_complete = inquiry.payment_status in REGISTRATION_PAYMENT_COMPLETE_STATUSES
    packet_complete = (
        consent_complete
        and emergency_contact_complete
        and medical_complete
        and not missing_documents
        and payment_complete
    )
    next_steps: list[str] = []
    if missing_documents:
        next_steps.append(f"Upload missing documents: {', '.join(missing_documents)}.")
    if not consent_complete:
        next_steps.append("Complete privacy and guardian consent acknowledgements.")
    if not emergency_contact_complete:
        next_steps.append("Add emergency contact name and phone.")
    if not medical_complete:
        next_steps.append("Add medical notes or a medical information document.")
    if not payment_complete:
        next_steps.append("Record payment, waiver, or not-required status.")
    if packet_complete:
        next_steps.append("Registration packet is ready for staff verification.")
    return {
        "required_documents": required_documents,
        "submitted_documents": submitted_documents,
        "missing_documents": missing_documents,
        "consent_complete": consent_complete,
        "medical_complete": medical_complete,
        "emergency_contact_complete": emergency_contact_complete,
        "payment_complete": payment_complete,
        "packet_complete": packet_complete,
        "next_steps": next_steps,
    }


def is_youth_age_group(age_group: str | None) -> bool:
    if not age_group:
        return False
    normalized = age_group.lower().replace(" ", "")
    return normalized.startswith("u") or "under" in normalized or "youth" in normalized


def safe_registration_filename(filename: str) -> str:
    name = Path(filename).name.strip().replace(" ", "-")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    return safe[:180] or "registration-document.bin"


async def get_public_registration_inquiry(
    db: AsyncSession,
    site: str,
    inquiry_id: UUID,
) -> tuple[Organization, RegistrationInquiry]:
    organization = await db.scalar(
        select(Organization).where(
            (Organization.slug == site) | (Organization.subdomain == site)
        )
    )
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    inquiry = await db.get(RegistrationInquiry, inquiry_id)
    if inquiry is None or inquiry.organization_id != organization.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    return organization, inquiry


async def can_manage_registration_inquiries(
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> bool:
    return await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage_roster",
        subject_type="user",
        subject_id=str(identity.user_id),
    ) or await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )


def append_review_note(existing: str | None, note: str) -> str:
    if not existing:
        return note
    return f"{existing.rstrip()}\n{note}"


def normalize_contact_email(email: str) -> str:
    return email.strip().lower()


async def find_person_by_email(db: AsyncSession, email: str) -> Person | None:
    normalized_email = normalize_contact_email(email)
    return await db.scalar(
        select(Person)
        .where(func.lower(Person.primary_email) == normalized_email)
        .order_by(Person.created_at)
        .limit(1)
    )


async def create_organization(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: OrganizationCreate,
    authz: AuthorizationService,
) -> tuple[Organization, list[MembershipRole]]:
    slug = bounded_handle(payload.slug or payload.name)
    existing = await db.scalar(select(Organization).where(Organization.slug == slug))
    if existing is not None:
        if payload.slug is None:
            slug = (await available_handle_suggestions(db, slug, Organization.slug, limit=1))[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Organization slug exists",
                    "slug_suggestions": await available_handle_suggestions(db, slug, Organization.slug),
                },
            )
    if payload.subdomain is not None:
        subdomain = bounded_handle(payload.subdomain)
        existing_subdomain = await db.scalar(
            select(Organization).where(Organization.subdomain == subdomain)
        )
        if existing_subdomain is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Organization subdomain exists",
                    "subdomain_suggestions": await available_handle_suggestions(db, subdomain, Organization.subdomain),
                },
            )
    else:
        subdomain = None

    organization = Organization(
        name=payload.name,
        slug=slug,
        organization_type=payload.organization_type,
        association_level=payload.association_level,
        country_code=payload.country_code,
        primary_sport=payload.primary_sport,
        mission=payload.mission,
        public_name=payload.public_name,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        website_url=payload.website_url,
        subdomain=subdomain,
        logo_url=payload.logo_url,
        brand_primary_color=payload.brand_primary_color,
        brand_secondary_color=payload.brand_secondary_color,
        registration_open=payload.registration_open,
        registration_fee_amount=payload.registration_fee_amount,
        registration_fee_currency=payload.registration_fee_currency.upper() if payload.registration_fee_currency else None,
        registration_payment_instructions=payload.registration_payment_instructions,
        registration_required_documents_json=json.dumps(
            normalize_registration_document_types(payload.registration_required_documents),
            sort_keys=True,
        )
        if payload.registration_required_documents
        else None,
    )
    db.add(organization)
    await db.flush()

    membership = Membership(
        organization_id=organization.id,
        subject_type=MemberSubjectType.PERSON,
        subject_id=identity.person_id,
        role=MembershipRole.OWNER,
        title="Owner",
    )
    db.add(membership)

    await authz.touch(
        Relationship(
            resource_type="organization",
            resource_id=str(organization.id),
            relation="owner",
            subject_type="user",
            subject_id=str(identity.user_id),
        )
    )
    await db.commit()
    await db.refresh(organization)
    return organization, [MembershipRole.OWNER]


async def organization_handle_availability(
    db: AsyncSession,
    name: str | None = None,
    slug: str | None = None,
    subdomain: str | None = None,
) -> OrganizationHandleAvailabilityRead:
    desired_slug = bounded_handle(slug or name or "organization")
    slug_available = not await organization_handle_exists(db, Organization.slug, desired_slug)
    desired_subdomain = bounded_handle(subdomain) if subdomain else None
    subdomain_available = (
        None
        if desired_subdomain is None
        else not await organization_handle_exists(db, Organization.subdomain, desired_subdomain)
    )
    return OrganizationHandleAvailabilityRead(
        desired_slug=desired_slug,
        slug_available=slug_available,
        slug_suggestions=[]
        if slug_available
        else await available_handle_suggestions(db, desired_slug, Organization.slug),
        desired_subdomain=desired_subdomain,
        subdomain_available=subdomain_available,
        subdomain_suggestions=[]
        if subdomain_available is not False or desired_subdomain is None
        else await available_handle_suggestions(db, desired_subdomain, Organization.subdomain),
    )


async def organization_handle_exists(db: AsyncSession, column, candidate: str) -> bool:
    return bool(await db.scalar(select(Organization.id).where(column == candidate).limit(1)))


async def available_handle_suggestions(db: AsyncSession, base: str, column, limit: int = 5) -> list[str]:
    candidates = [handle_candidate(base, suffix) for suffix in range(2, 80)]
    existing = {
        value
        for value in (await db.scalars(select(column).where(column.in_(candidates)))).all()
        if value is not None
    }
    suggestions = [candidate for candidate in candidates if candidate not in existing]
    return suggestions[:limit]


async def search_public_organizations(
    db: AsyncSession,
    query: str | None = None,
    organization_type: OrganizationType | None = None,
    sport: str | None = None,
    country_code: str | None = None,
    limit: int = 12,
) -> list[tuple[Organization, int, int]]:
    bounded_limit = max(1, min(limit, 50))
    statement = select(Organization).order_by(Organization.name).limit(bounded_limit)
    if organization_type is not None:
        statement = statement.where(Organization.organization_type == organization_type)
    if sport:
        statement = statement.where(func.lower(Organization.primary_sport).like(f"%{sport.lower()}%"))
    if country_code:
        statement = statement.where(func.lower(Organization.country_code) == country_code.lower())
    if query and query.strip():
        like = f"%{query.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(Organization.name).like(like),
                func.lower(Organization.public_name).like(like),
                func.lower(Organization.slug).like(like),
                func.lower(Organization.subdomain).like(like),
                func.lower(Organization.primary_sport).like(like),
            )
        )

    organizations = list((await db.scalars(statement)).all())
    now = datetime.now(UTC)
    results: list[tuple[Organization, int, int]] = []
    for organization in organizations:
        team_count = await db.scalar(
            select(func.count(Team.id)).where(Team.organization_id == organization.id)
        )
        upcoming_event_count = await db.scalar(
            select(func.count(Event.id))
            .where(Event.organization_id == organization.id)
            .where(Event.starts_at >= now)
        )
        results.append((organization, int(team_count or 0), int(upcoming_event_count or 0)))
    return results


async def list_organizations_for_identity(
    db: AsyncSession,
    identity: CurrentIdentity,
) -> list[tuple[Organization, list[MembershipRole]]]:
    rows = (
        await db.execute(
            select(Organization, Membership.role)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(Membership.subject_type == MemberSubjectType.PERSON)
            .where(Membership.subject_id == identity.person_id)
            .where(Membership.status == "active")
            .order_by(Organization.name)
        )
    ).all()

    grouped: dict[UUID, tuple[Organization, list[MembershipRole]]] = {}
    for organization, role in rows:
        if organization.id not in grouped:
            grouped[organization.id] = (organization, [])
        grouped[organization.id][1].append(role)
    return list(grouped.values())


async def registration_readiness(
    db: AsyncSession,
    identity: CurrentIdentity,
    settings: Settings | None = None,
) -> RegistrationReadinessRead:
    settings = settings or get_settings()
    manageable_roles = {MembershipRole.OWNER, MembershipRole.ADMIN, MembershipRole.STAFF}
    managed_items = [
        item
        for item in await list_organizations_for_identity(db, identity)
        if any(role in manageable_roles for role in item[1])
    ]
    managed_organizations = [organization for organization, _roles in managed_items]
    managed_ids = [organization.id for organization in managed_organizations]
    public_directory_count = int(
        await db.scalar(
            select(func.count(Organization.id)).where(Organization.registration_open.is_(True))
        )
        or 0
    )
    admissions_inquiries: list[RegistrationInquiry] = []
    if managed_ids:
        admissions_inquiries = list(
            (
                await db.scalars(
                    select(RegistrationInquiry)
                    .where(RegistrationInquiry.organization_id.in_(managed_ids))
                    .order_by(RegistrationInquiry.created_at.desc())
                    .limit(200)
                )
            ).all()
        )
    family_registrations = await list_family_registration_inquiries(db, identity)
    registration_open_count = sum(1 for organization in managed_organizations if organization.registration_open)
    admissions_ready_count = sum(
        1 for inquiry in admissions_inquiries if bool(registration_packet_summary(inquiry)["packet_complete"])
    )
    family_packet_complete_count = sum(1 for inquiry in family_registrations if inquiry.packet_complete)
    first_managed = managed_organizations[0] if managed_organizations else None
    first_family = family_registrations[0] if family_registrations else None
    steps = [
        RegistrationReadinessStepRead(
            key="identity",
            label="User account",
            status="ready",
            detail=f"{identity.display_name} <{identity.email}>",
            action_label="Signed in",
        ),
        RegistrationReadinessStepRead(
            key="workspace",
            label="Club or school workspace",
            status="ready" if managed_organizations else "action",
            detail=(
                f"{len(managed_organizations)} managed workspace"
                f"{'' if len(managed_organizations) == 1 else 's'}"
                if managed_organizations
                else "Create a club, school, or academy workspace"
            ),
            action_label="Open admissions" if first_managed is not None else "Create workspace",
            href=f"/admissions?organization_id={first_managed.id}" if first_managed is not None else "/register?mode=organization",
        ),
        RegistrationReadinessStepRead(
            key="public_registration",
            label="Public registration",
            status="ready" if registration_open_count else ("action" if managed_organizations else "blocked"),
            detail=(
                f"{registration_open_count} workspace"
                f"{'' if registration_open_count == 1 else 's'} accepting families"
                if registration_open_count
                else "Open registration settings after creating the workspace"
            ),
            action_label="Open public page" if first_managed is not None else "Create workspace first",
            href=public_site_path(first_managed) if first_managed is not None else "/register?mode=organization",
        ),
        RegistrationReadinessStepRead(
            key="admissions",
            label="Admissions queue",
            status="ready" if admissions_ready_count else ("action" if admissions_inquiries else "todo"),
            detail=(
                f"{admissions_ready_count} ready packet"
                f"{'' if admissions_ready_count == 1 else 's'} from {len(admissions_inquiries)} intake"
                f"{'' if len(admissions_inquiries) == 1 else 's'}"
                if admissions_inquiries
                else "No family intakes yet"
            ),
            action_label="Review admissions" if first_managed is not None else "Create workspace first",
            href=f"/admissions?organization_id={first_managed.id}" if first_managed is not None else "/register?mode=organization",
        ),
        RegistrationReadinessStepRead(
            key="family_registration",
            label="Family registration",
            status="ready" if family_packet_complete_count else ("action" if family_registrations else "todo"),
            detail=(
                f"{family_packet_complete_count} complete packet"
                f"{'' if family_packet_complete_count == 1 else 's'} from {len(family_registrations)} registration"
                f"{'' if len(family_registrations) == 1 else 's'}"
                if family_registrations
                else f"{public_directory_count} open organization"
                f"{'' if public_directory_count == 1 else 's'} available"
            ),
            action_label="Resume family registration" if first_family is not None else "Find organization",
            href=(
                f"{first_family.public_site_path}?inquiry_id={first_family.id}&email={quote(first_family.email)}"
                if first_family is not None
                else "/register?mode=player"
            ),
        ),
    ]
    return RegistrationReadinessRead(
        auth_mode=settings.auth_mode,
        identity_email=identity.email,
        identity_display_name=identity.display_name,
        managed_organization_count=len(managed_organizations),
        registration_open_count=registration_open_count,
        public_directory_count=public_directory_count,
        admissions_inquiry_count=len(admissions_inquiries),
        admissions_ready_count=admissions_ready_count,
        family_registration_count=len(family_registrations),
        family_packet_complete_count=family_packet_complete_count,
        steps=steps,
        missions=registration_onboarding_missions(
            managed_organizations=managed_organizations,
            registration_open_count=registration_open_count,
            admissions_inquiries=admissions_inquiries,
            admissions_ready_count=admissions_ready_count,
            family_registrations=family_registrations,
            family_packet_complete_count=family_packet_complete_count,
            public_directory_count=public_directory_count,
        ),
        organizations=[
            RegistrationReadinessOrganizationRead(
                id=organization.id,
                name=organization.name,
                public_name=organization.public_name,
                organization_type=organization.organization_type,
                registration_open=organization.registration_open,
                public_site_path=public_site_path(organization),
                registration_page_path=f"/register?mode=player&site={organization.subdomain or organization.slug}",
                admissions_path=f"/admissions?organization_id={organization.id}",
            )
            for organization in managed_organizations[:6]
        ],
        family_registrations=[
            RegistrationReadinessFamilyInquiryRead(
                id=inquiry.id,
                organization_id=inquiry.organization_id,
                organization_public_name=inquiry.organization_public_name,
                athlete_name=inquiry.athlete_name,
                packet_complete=inquiry.packet_complete,
                payment_status=inquiry.payment_status,
                next_steps=inquiry.next_steps,
                public_site_path=inquiry.public_site_path,
            )
            for inquiry in family_registrations[:6]
        ],
    )


def registration_onboarding_missions(
    *,
    managed_organizations: list[Organization],
    registration_open_count: int,
    admissions_inquiries: list[RegistrationInquiry],
    admissions_ready_count: int,
    family_registrations: list[FamilyRegistrationInquiryRead],
    family_packet_complete_count: int,
    public_directory_count: int,
) -> list[RegistrationOnboardingMissionRead]:
    first_managed = managed_organizations[0] if managed_organizations else None
    first_family = family_registrations[0] if family_registrations else None
    return [
        RegistrationOnboardingMissionRead(
            key="launch_workspace",
            audience="owner",
            title="Launch the operating workspace",
            status="complete" if managed_organizations else "active",
            progress_percent=100 if managed_organizations else 35,
            xp=150,
            detail=(
                f"{len(managed_organizations)} workspace"
                f"{'' if len(managed_organizations) == 1 else 's'} ready for setup."
                if managed_organizations
                else "Create the first club, school, or academy workspace with owner access."
            ),
            action_label="Open admissions" if first_managed is not None else "Create workspace",
            href=f"/admissions?organization_id={first_managed.id}" if first_managed is not None else "/register?mode=organization",
        ),
        RegistrationOnboardingMissionRead(
            key="publish_family_intake",
            audience="owner",
            title="Publish family registration",
            status="complete" if registration_open_count else ("active" if managed_organizations else "locked"),
            progress_percent=100 if registration_open_count else (55 if managed_organizations else 0),
            xp=120,
            detail=(
                f"{registration_open_count} workspace"
                f"{'' if registration_open_count == 1 else 's'} accepting public registration."
                if registration_open_count
                else "Open registration, documents, fees, and public site routing."
            ),
            action_label="Open public site" if first_managed is not None else "Create workspace first",
            href=public_site_path(first_managed) if first_managed is not None else "/register?mode=organization",
        ),
        RegistrationOnboardingMissionRead(
            key="complete_family_packet",
            audience="family",
            title="Complete an athlete packet",
            status="complete" if family_packet_complete_count else ("active" if family_registrations else "available"),
            progress_percent=100 if family_packet_complete_count else (60 if family_registrations else 20),
            xp=100,
            detail=(
                f"{family_packet_complete_count} complete packet"
                f"{'' if family_packet_complete_count == 1 else 's'} from {len(family_registrations)} registration"
                f"{'' if len(family_registrations) == 1 else 's'}."
                if family_registrations
                else f"{public_directory_count} open organization"
                f"{'' if public_directory_count == 1 else 's'} available for family registration."
            ),
            action_label="Resume packet" if first_family is not None else "Find organization",
            href=(
                f"{first_family.public_site_path}?inquiry_id={first_family.id}&email={quote(first_family.email)}"
                if first_family is not None
                else "/register?mode=player"
            ),
        ),
        RegistrationOnboardingMissionRead(
            key="review_admissions",
            audience="staff",
            title="Review admissions with AI support",
            status="complete" if admissions_ready_count else ("active" if admissions_inquiries else "locked"),
            progress_percent=100 if admissions_ready_count else (65 if admissions_inquiries else 0),
            xp=130,
            detail=(
                f"{admissions_ready_count} ready packet"
                f"{'' if admissions_ready_count == 1 else 's'} from {len(admissions_inquiries)} intake"
                f"{'' if len(admissions_inquiries) == 1 else 's'}."
                if admissions_inquiries
                else "Collect family intakes, then use admissions AI review and conversion."
            ),
            action_label="Review admissions" if first_managed is not None else "Create workspace first",
            href=f"/admissions?organization_id={first_managed.id}" if first_managed is not None else "/register?mode=organization",
        ),
    ]


def registration_learning_path(payload: RegistrationLearningPathCreate) -> RegistrationLearningPathRead:
    role = normalize_learning_key(payload.role)
    primary_goal = normalize_learning_key(payload.primary_goal)
    skill_level = normalize_learning_key(payload.skill_level)
    learning_style = normalize_learning_key(payload.learning_style)
    core_module = learning_core_module(role, primary_goal, learning_style)
    modules = [
        RegistrationLearningModuleRead(
            key="orientation",
            title=learning_orientation_title(role),
            duration_minutes=8 if skill_level in {"intermediate", "advanced"} else 12,
            format=learning_format(learning_style, fallback="guided walkthrough"),
            objective="Understand the AfroLete workspace, roles, data boundaries, and AI assistant handoffs.",
            practice_task="Open the registration readiness cockpit and identify the next unlocked mission.",
            completion_badge="Platform Ready",
        ),
        core_module,
        RegistrationLearningModuleRead(
            key="ai_assistant_practice",
            title="Practice with the AI assistant safely",
            duration_minutes=10,
            format=learning_format(learning_style, fallback="scenario"),
            objective="Use AI-generated drafts, recommendations, and review states without bypassing human approval.",
            practice_task="Run a deterministic concierge or admissions review draft and decide whether to accept it.",
            completion_badge="AI Review Steward",
        ),
    ]
    if primary_goal in {"track_performance", "analyze_video", "coach_athletes"}:
        modules.append(
            RegistrationLearningModuleRead(
                key="performance_practice",
                title="Analyze a performance scenario",
                duration_minutes=15 if skill_level == "beginner" else 10,
                format=learning_format(learning_style, fallback="sandbox exercise"),
                objective="Read performance trends, video-coaching cues, and readiness signals as one coaching story.",
                practice_task="Compare an athlete readiness score with a video coaching recommendation.",
                completion_badge="Performance Tracking Pro",
            )
        )
    if role in {"parent_guardian", "player"}:
        modules.append(
            RegistrationLearningModuleRead(
                key="family_portal_practice",
                title="Manage family follow-through",
                duration_minutes=9,
                format=learning_format(learning_style, fallback="checklist"),
                objective="Resume packets, review consent, track payments, and enter the family portal confidently.",
                practice_task="Find a pending registration card and name the next required packet action.",
                completion_badge="Family Portal Navigator",
            )
        )
    difficulty = {
        "beginner": "foundation",
        "intermediate": "applied",
        "advanced": "accelerated",
    }.get(skill_level, "foundation")
    accessibility_supports = ["keyboard navigation", "plain-language steps", "high contrast compatible"]
    if payload.accessibility_mode:
        accessibility_supports.insert(0, payload.accessibility_mode.strip())
    return RegistrationLearningPathRead(
        role=role,
        primary_goal=primary_goal,
        skill_level=skill_level,
        learning_style=learning_style,
        path_title=learning_path_title(role, primary_goal),
        estimated_minutes=sum(module.duration_minutes for module in modules),
        difficulty=difficulty,
        first_action=modules[0].practice_task,
        modules=modules,
        accessibility_supports=accessibility_supports,
    )


def normalize_learning_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_") or "general"


def learning_path_title(role: str, goal: str) -> str:
    role_label = role.replace("_", " ").title()
    goal_label = goal.replace("_", " ").title()
    return f"{role_label} path: {goal_label}"


def learning_orientation_title(role: str) -> str:
    if role in {"parent_guardian", "player"}:
        return "Find your family starting point"
    if role in {"head_coach", "assistant_coach", "coach"}:
        return "Set up the coaching workspace"
    return "Set up the operations workspace"


def learning_core_module(role: str, goal: str, learning_style: str) -> RegistrationLearningModuleRead:
    if goal in {"track_performance", "analyze_video", "coach_athletes"}:
        return RegistrationLearningModuleRead(
            key="performance_analytics",
            title="Read performance and video insights",
            duration_minutes=15,
            format=learning_format(learning_style, fallback="interactive demo"),
            objective="Connect athlete metrics, readiness, video coaching cues, and AI recommendations.",
            practice_task="Open a performance card and identify one strength, one risk, and one coaching cue.",
            completion_badge="Performance Analyst Starter",
        )
    if goal in {"manage_communications", "coordinate_families"} or role == "parent_guardian":
        return RegistrationLearningModuleRead(
            key="communications_and_family",
            title="Coordinate family communication",
            duration_minutes=12,
            format=learning_format(learning_style, fallback="guided checklist"),
            objective="Use inbox, consent, schedules, and follow-up messages without losing family context.",
            practice_task="Find the family portal link and identify the latest consent or packet action.",
            completion_badge="Family Coordination Starter",
        )
    if goal in {"schedule_training", "plan_sessions"}:
        return RegistrationLearningModuleRead(
            key="training_planning",
            title="Plan a safe training week",
            duration_minutes=14,
            format=learning_format(learning_style, fallback="practice scenario"),
            objective="Balance drills, readiness, schedule conflicts, and training load recommendations.",
            practice_task="Choose one drill and explain how readiness changes the session intensity.",
            completion_badge="Training Planner Starter",
        )
    return RegistrationLearningModuleRead(
        key="registration_launch",
        title="Launch registration and admissions",
        duration_minutes=12,
        format=learning_format(learning_style, fallback="hands-on setup"),
        objective="Create the workspace, publish public intake, collect packets, and review admissions.",
        practice_task="Create or inspect a starter program and follow the admissions link.",
        completion_badge="Registration Launch Starter",
    )


def learning_format(learning_style: str, fallback: str) -> str:
    return {
        "visual": "visual walkthrough",
        "hands_on": "hands-on exercise",
        "reading": "short reading and checklist",
        "audio": "audio-friendly script",
    }.get(learning_style, fallback)


async def get_organization_for_identity(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> tuple[Organization, list[MembershipRole]]:
    rows = (
        await db.execute(
            select(Organization, Membership.role)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(Organization.id == organization_id)
            .where(Membership.subject_type == MemberSubjectType.PERSON)
            .where(Membership.subject_id == identity.person_id)
            .where(Membership.status == "active")
        )
    ).all()
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    organization = rows[0][0]
    return organization, [role for _, role in rows]


async def get_public_site(
    db: AsyncSession,
    site: str,
) -> tuple[
    Organization,
    list[Team],
    list[Event],
    list[Sponsor],
    list[SponsorshipAgreement],
    list[FundraisingCampaign],
    list[TicketProduct],
    list[SupporterMembershipTier],
    list[FanEngagementChallenge],
    list[tuple[SupporterProfile, SupporterMembershipTier | None]],
    dict[UUID, int],
    dict[UUID, int],
]:
    organization = await db.scalar(
        select(Organization).where(
            (Organization.slug == site) | (Organization.subdomain == site)
        )
    )
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    teams = list(
        (
            await db.scalars(
                select(Team)
                .where(Team.organization_id == organization.id)
                .order_by(Team.sport, Team.name)
                .limit(12)
            )
        ).all()
    )
    upcoming_events = list(
        (
            await db.scalars(
                select(Event)
                .where(Event.organization_id == organization.id)
                .where(Event.starts_at >= datetime.now(UTC))
                .order_by(Event.starts_at)
                .limit(8)
            )
        ).all()
    )
    sponsors = list(
        (
            await db.scalars(
                select(Sponsor)
                .where(Sponsor.organization_id == organization.id)
                .order_by(Sponsor.name)
                .limit(12)
            )
        ).all()
    )
    sponsorships = list(
        (
            await db.scalars(
                select(SponsorshipAgreement)
                .where(SponsorshipAgreement.organization_id == organization.id)
                .where(SponsorshipAgreement.status == CommercialStatus.ACTIVE)
                .order_by(SponsorshipAgreement.value_amount.desc(), SponsorshipAgreement.name)
                .limit(24)
            )
        ).all()
    )
    campaigns = list(
        (
            await db.scalars(
                select(FundraisingCampaign)
                .where(FundraisingCampaign.organization_id == organization.id)
                .where(FundraisingCampaign.status == CommercialStatus.ACTIVE)
                .order_by(FundraisingCampaign.ends_on.is_(None), FundraisingCampaign.ends_on, FundraisingCampaign.name)
                .limit(6)
            )
        ).all()
    )
    ticket_products = list(
        (
            await db.scalars(
                select(TicketProduct)
                .where(TicketProduct.organization_id == organization.id)
                .where(TicketProduct.status == CommercialStatus.ACTIVE)
                .order_by(TicketProduct.name)
                .limit(8)
            )
        ).all()
    )
    supporter_tiers = list(
        (
            await db.scalars(
                select(SupporterMembershipTier)
                .where(SupporterMembershipTier.organization_id == organization.id)
                .where(SupporterMembershipTier.status == "active")
                .order_by(SupporterMembershipTier.monthly_price, SupporterMembershipTier.name)
                .limit(6)
            )
        ).all()
    )
    fan_challenges = list(
        (
            await db.scalars(
                select(FanEngagementChallenge)
                .where(FanEngagementChallenge.organization_id == organization.id)
                .where(FanEngagementChallenge.status == "active")
                .where(
                    or_(
                        FanEngagementChallenge.ends_at.is_(None),
                        FanEngagementChallenge.ends_at >= datetime.now(UTC),
                    )
                )
                .order_by(FanEngagementChallenge.starts_at.desc())
                .limit(6)
            )
        ).all()
    )
    fan_leaderboard = list(
        (
            await db.execute(
                select(SupporterProfile, SupporterMembershipTier)
                .outerjoin(SupporterMembershipTier, SupporterProfile.tier_id == SupporterMembershipTier.id)
                .where(SupporterProfile.organization_id == organization.id)
                .where(SupporterProfile.status == "active")
                .order_by(SupporterProfile.engagement_points.desc(), SupporterProfile.joined_at)
                .limit(8)
            )
        ).all()
    )
    challenge_completion_counts = await public_challenge_completion_counts(
        db,
        [challenge.id for challenge in fan_challenges],
    )
    supporter_completed_challenge_counts = await public_supporter_completed_challenge_counts(
        db,
        organization.id,
        [supporter.id for supporter, _tier in fan_leaderboard],
    )
    return (
        organization,
        teams,
        upcoming_events,
        sponsors,
        sponsorships,
        campaigns,
        ticket_products,
        supporter_tiers,
        fan_challenges,
        fan_leaderboard,
        challenge_completion_counts,
        supporter_completed_challenge_counts,
    )


async def public_supporter_signup(
    db: AsyncSession,
    site: str,
    payload: PublicSupporterSignupCreate,
) -> PublicSupporterSignupRead:
    organization = await get_public_site_organization(db, site)
    tier = None
    if payload.tier_id is not None:
        tier = await db.get(SupporterMembershipTier, payload.tier_id)
        if tier is None or tier.organization_id != organization.id or tier.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supporter tier not found")
    else:
        tier = await db.scalar(
            select(SupporterMembershipTier)
            .where(SupporterMembershipTier.organization_id == organization.id)
            .where(SupporterMembershipTier.status == "active")
            .order_by(SupporterMembershipTier.monthly_price, SupporterMembershipTier.name)
            .limit(1)
        )

    email = normalize_contact_email(payload.email)
    person = await find_person_by_email(db, email)
    if person is None:
        person = Person(display_name=payload.display_name, primary_email=email, primary_phone=payload.phone)
        db.add(person)
        await db.flush()
    else:
        if payload.display_name and person.display_name == person.primary_email:
            person.display_name = payload.display_name
        if payload.phone and not person.primary_phone:
            person.primary_phone = payload.phone

    supporter = await db.scalar(
        select(SupporterProfile).where(
            SupporterProfile.organization_id == organization.id,
            func.lower(SupporterProfile.email) == email.lower(),
        )
    )
    created = supporter is None
    points_awarded = 100 if created else 0
    notes = public_supporter_notes(payload)
    now = datetime.now(UTC)
    if supporter is None:
        supporter = SupporterProfile(
            organization_id=organization.id,
            person_id=person.id,
            tier_id=tier.id if tier else None,
            display_name=payload.display_name,
            email=email,
            engagement_points=points_awarded,
            lifetime_value=Decimal("0"),
            joined_at=now,
            last_engagement_at=now,
            notes=notes,
        )
        db.add(supporter)
        await db.flush()
        db.add(
            SupporterEngagementActivity(
                organization_id=organization.id,
                supporter_profile_id=supporter.id,
                activity_type="public_signup",
                source="public_site",
                description="Joined from branded public site.",
                points=points_awarded,
                value_amount=Decimal("0"),
                occurred_at=now,
            )
        )
    else:
        supporter.person_id = supporter.person_id or person.id
        supporter.display_name = payload.display_name
        if tier is not None:
            supporter.tier_id = tier.id
        supporter.last_engagement_at = supporter.last_engagement_at or now
        if notes:
            supporter.notes = f"{supporter.notes}\n{notes}" if supporter.notes else notes

    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == organization.id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == person.id,
            Membership.role == MembershipRole.VIEWER,
        )
    )
    if membership is None:
        db.add(
            Membership(
                organization_id=organization.id,
                subject_type=MemberSubjectType.PERSON,
                subject_id=person.id,
                role=MembershipRole.VIEWER,
            )
        )

    await db.commit()
    await db.refresh(supporter)
    if supporter.tier_id:
        tier = await db.get(SupporterMembershipTier, supporter.tier_id)
    return PublicSupporterSignupRead(
        supporter_profile_id=supporter.id,
        organization_id=organization.id,
        display_name=supporter.display_name,
        email=supporter.email,
        tier_id=supporter.tier_id,
        tier_name=tier.name if tier else None,
        engagement_points=supporter.engagement_points,
        status=supporter.status,
        signup_status="created" if created else "updated",
        points_awarded=points_awarded,
        next_actions=public_supporter_next_actions(organization, tier),
    )


async def public_supporter_challenge_progress(
    db: AsyncSession,
    site: str,
    challenge_id: UUID,
    payload: PublicSupporterChallengeProgressCreate,
) -> PublicSupporterChallengeProgressRead:
    organization = await get_public_site_organization(db, site)
    challenge = await db.get(FanEngagementChallenge, challenge_id)
    if challenge is None or challenge.organization_id != organization.id or challenge.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fan challenge not found")
    if challenge.ends_at is not None and challenge.ends_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Fan challenge has ended")

    email = normalize_contact_email(payload.email)
    supporter = await db.scalar(
        select(SupporterProfile).where(
            SupporterProfile.organization_id == organization.id,
            func.lower(SupporterProfile.email) == email.lower(),
        )
    )
    if supporter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supporter profile not found")

    progress = await db.scalar(
        select(FanChallengeProgress).where(
            FanChallengeProgress.challenge_id == challenge.id,
            FanChallengeProgress.supporter_profile_id == supporter.id,
        )
    )
    if progress is None:
        progress = FanChallengeProgress(
            organization_id=organization.id,
            challenge_id=challenge.id,
            supporter_profile_id=supporter.id,
            progress_count=0,
            points_awarded=0,
            status="in_progress",
        )
        db.add(progress)
    progress.progress_count += payload.progress_count
    if progress.progress_count >= challenge.target_count and progress.status != "completed":
        now = datetime.now(UTC)
        progress.status = "completed"
        progress.completed_at = now
        progress.points_awarded = challenge.points_reward
        supporter.engagement_points += challenge.points_reward
        supporter.last_engagement_at = now
        db.add(
            SupporterEngagementActivity(
                organization_id=organization.id,
                supporter_profile_id=supporter.id,
                activity_type=challenge.target_activity_type,
                source="public_challenge",
                description=f"Completed fan challenge: {challenge.title}",
                points=challenge.points_reward,
                value_amount=Decimal("0"),
                occurred_at=now,
            )
        )
        if challenge.badge_name:
            db.add(
                SupporterReward(
                    organization_id=organization.id,
                    supporter_profile_id=supporter.id,
                    title=challenge.badge_name,
                    reward_type="badge",
                    threshold_points=challenge.points_reward,
                )
            )

    await db.commit()
    await db.refresh(progress)
    return PublicSupporterChallengeProgressRead(
        supporter_profile_id=supporter.id,
        supporter_name=supporter.display_name,
        challenge_id=challenge.id,
        challenge_title=challenge.title,
        progress_count=progress.progress_count,
        target_count=challenge.target_count,
        points_awarded=progress.points_awarded,
        status=progress.status,
        completed_at=progress.completed_at,
    )


async def public_challenge_completion_counts(db: AsyncSession, challenge_ids: list[UUID]) -> dict[UUID, int]:
    if not challenge_ids:
        return {}
    rows = (
        await db.execute(
            select(FanChallengeProgress.challenge_id, func.count(FanChallengeProgress.id))
            .where(
                FanChallengeProgress.challenge_id.in_(challenge_ids),
                FanChallengeProgress.status == "completed",
            )
            .group_by(FanChallengeProgress.challenge_id)
        )
    ).all()
    return {challenge_id: count for challenge_id, count in rows}


async def public_supporter_completed_challenge_counts(
    db: AsyncSession,
    organization_id: UUID,
    supporter_ids: list[UUID],
) -> dict[UUID, int]:
    if not supporter_ids:
        return {}
    rows = (
        await db.execute(
            select(FanChallengeProgress.supporter_profile_id, func.count(FanChallengeProgress.id))
            .where(
                FanChallengeProgress.organization_id == organization_id,
                FanChallengeProgress.supporter_profile_id.in_(supporter_ids),
                FanChallengeProgress.status == "completed",
            )
            .group_by(FanChallengeProgress.supporter_profile_id)
        )
    ).all()
    return {supporter_id: count for supporter_id, count in rows}


def public_supporter_notes(payload: PublicSupporterSignupCreate) -> str:
    parts = ["Public supporter signup"]
    if payload.interests:
        parts.append(f"Interests: {', '.join(payload.interests[:12])}")
    if payload.message:
        parts.append(f"Message: {payload.message}")
    if payload.source_url:
        parts.append(f"Source: {payload.source_url}")
    return " | ".join(parts)


def public_supporter_next_actions(
    organization: Organization,
    tier: SupporterMembershipTier | None,
) -> list[str]:
    actions = [
        f"Follow {organization.public_name or organization.name} events and polls from this public site.",
        "Join an open fan challenge to earn points and badges.",
    ]
    if tier is not None and tier.monthly_price > 0:
        actions.append(f"Staff can connect payment fulfillment for the {tier.name} membership tier.")
    return actions


async def create_public_registration_inquiry(
    db: AsyncSession,
    site: str,
    payload: PublicRegistrationInquiryCreate,
) -> RegistrationInquiry:
    organization = await get_public_site_organization(db, site)
    if not organization.registration_open:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Registration is closed")
    if payload.team_id is not None:
        team = await db.get(Team, payload.team_id)
        if team is None or team.organization_id != organization.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    guardian = await ensure_registration_guardian_contact(db, organization.id, payload)

    required_documents = organization_registration_required_documents(organization)
    if not required_documents:
        required_documents = list(DEFAULT_REGISTRATION_DOCUMENTS)
        if payload.guardian_name or is_youth_age_group(payload.age_group):
            required_documents.extend(["guardian_consent", "photo_release"])

    inquiry_payload = payload.model_dump()
    inquiry_payload["email"] = normalize_contact_email(payload.email)
    inquiry = RegistrationInquiry(
        organization_id=organization.id,
        **inquiry_payload,
        guardian_person_id=guardian.id,
        guardian_contact_status="pending_account",
        required_documents_json=json.dumps(
            [{"document_type": document_type, "filename": document_type} for document_type in required_documents],
            sort_keys=True,
        ),
        payment_amount=organization.registration_fee_amount,
        payment_currency=organization.registration_fee_currency,
        payment_status="pending" if organization.registration_fee_amount else "not_required",
        payment_method="registration_checkout" if organization.registration_fee_amount else None,
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)
    return inquiry


async def ensure_registration_guardian_contact(
    db: AsyncSession,
    organization_id: UUID,
    payload: PublicRegistrationInquiryCreate,
) -> Person:
    guardian_email = normalize_contact_email(payload.email)
    guardian = await find_person_by_email(db, guardian_email)
    if guardian is None:
        guardian = Person(
            display_name=payload.guardian_name or guardian_email,
            primary_email=guardian_email,
            primary_phone=payload.phone,
        )
        db.add(guardian)
        await db.flush()
    else:
        if payload.guardian_name and guardian.display_name == guardian.primary_email:
            guardian.display_name = payload.guardian_name
        if payload.phone and not guardian.primary_phone:
            guardian.primary_phone = payload.phone

    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == guardian.id,
            Membership.role == MembershipRole.GUARDIAN,
        )
    )
    if membership is None:
        db.add(
            Membership(
                organization_id=organization_id,
                subject_type=MemberSubjectType.PERSON,
                subject_id=guardian.id,
                role=MembershipRole.GUARDIAN,
                title="Registration guardian",
            )
        )
    return guardian


async def get_public_registration_account_readiness(
    db: AsyncSession,
    site: str,
    inquiry_id: UUID,
    email: str,
) -> RegistrationInquiryAccountReadinessRead:
    _organization, inquiry = await get_public_registration_inquiry(db, site, inquiry_id)
    if normalize_contact_email(inquiry.email) != normalize_contact_email(email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inquiry email mismatch")

    guardian = await db.get(Person, inquiry.guardian_person_id) if inquiry.guardian_person_id else None
    linked_user = None
    email_user = None
    guardian_email = guardian.primary_email if guardian is not None else inquiry.email
    if guardian is not None:
        linked_user = await db.scalar(
            select(AppUser)
            .where(AppUser.person_id == guardian.id)
            .order_by(AppUser.created_at.desc())
            .limit(1)
        )
    if guardian_email:
        email_user = await db.scalar(
            select(AppUser)
            .where(func.lower(AppUser.email) == normalize_contact_email(guardian_email))
            .order_by(AppUser.created_at.desc())
            .limit(1)
        )
    account_status, recommended_action = registration_guardian_account_status(
        guardian,
        linked_user,
        email_user,
    )
    return RegistrationInquiryAccountReadinessRead(
        inquiry_id=inquiry.id,
        guardian_person_id=guardian.id if guardian else inquiry.guardian_person_id,
        guardian_email=guardian_email,
        guardian_contact_status=inquiry.guardian_contact_status,
        account_status=account_status,
        can_create_account=account_status == "invite_ready",
        can_sign_in=account_status in {"linked", "pending_link", "invite_ready"},
        recommended_action=recommended_action,
    )


async def list_family_registration_inquiries(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID | None = None,
) -> list[FamilyRegistrationInquiryRead]:
    email_key = normalize_contact_email(identity.email)
    statement = (
        select(RegistrationInquiry, Organization)
        .join(Organization, Organization.id == RegistrationInquiry.organization_id)
        .where(
            or_(
                RegistrationInquiry.guardian_person_id == identity.person_id,
                func.lower(RegistrationInquiry.email) == email_key,
            )
        )
        .order_by(RegistrationInquiry.created_at.desc())
        .limit(50)
    )
    if organization_id is not None:
        statement = statement.where(RegistrationInquiry.organization_id == organization_id)

    rows = (await db.execute(statement)).all()
    current_user = await db.get(AppUser, identity.user_id)
    results: list[FamilyRegistrationInquiryRead] = []
    for inquiry, organization in rows:
        guardian = await db.get(Person, inquiry.guardian_person_id) if inquiry.guardian_person_id else None
        linked_user = current_user if guardian is not None and current_user and current_user.person_id == guardian.id else None
        email_user = (
            current_user
            if current_user is not None and normalize_contact_email(current_user.email) == normalize_contact_email(inquiry.email)
            else None
        )
        account_status, _recommended_action = registration_guardian_account_status(
            guardian,
            linked_user,
            email_user,
        )
        packet = registration_packet_summary(inquiry)
        results.append(
            FamilyRegistrationInquiryRead(
                id=inquiry.id,
                organization_id=inquiry.organization_id,
                organization_name=organization.name,
                organization_public_name=organization.public_name,
                organization_slug=organization.slug,
                public_site_path=public_site_path(organization),
                athlete_name=inquiry.athlete_name,
                guardian_name=inquiry.guardian_name,
                email=inquiry.email,
                status=inquiry.status,
                verification_status=inquiry.verification_status,
                guardian_contact_status=inquiry.guardian_contact_status,
                account_status=account_status,
                payment_status=inquiry.payment_status,
                packet_complete=bool(packet["packet_complete"]),
                missing_documents=[str(item) for item in packet["missing_documents"]],
                next_steps=[str(item) for item in packet["next_steps"]],
                created_at=inquiry.created_at,
                packet_submitted_at=inquiry.packet_submitted_at,
            )
        )
    return results


def registration_guardian_account_status(
    guardian: Person | None,
    linked_user: AppUser | None,
    email_user: AppUser | None,
) -> tuple[str, str]:
    if guardian is None:
        return (
            "missing_contact",
            "Submit guardian contact details before creating a family account.",
        )
    if linked_user is not None:
        return (
            "linked",
            "This guardian contact is linked to an AfroLete account; sign in to continue family onboarding.",
        )
    if email_user is not None and email_user.person_id is None:
        return (
            "pending_link",
            "Sign in once with this email so AfroLete can attach the existing account to the guardian contact.",
        )
    if email_user is not None and email_user.person_id != guardian.id:
        return (
            "account_review_required",
            "This email is already attached to another account; staff should review the account link before onboarding.",
        )
    if guardian.primary_email:
        return (
            "invite_ready",
            "Create an account or sign in with this email; AfroLete will link it to the guardian contact.",
        )
    if guardian.primary_phone:
        return (
            "phone_only",
            "Add an email address before Keycloak account onboarding.",
        )
    return (
        "missing_contact",
        "Add guardian email or phone contact details before creating a family account.",
    )


async def update_public_registration_packet(
    db: AsyncSession,
    site: str,
    inquiry_id: UUID,
    payload: PublicRegistrationPacketUpdate,
) -> RegistrationInquiry:
    organization = await db.scalar(
        select(Organization).where(
            (Organization.slug == site) | (Organization.subdomain == site)
        )
    )
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    inquiry = await db.get(RegistrationInquiry, inquiry_id)
    if inquiry is None or inquiry.organization_id != organization.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    if normalize_contact_email(inquiry.email) != normalize_contact_email(payload.email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inquiry email mismatch")
    if inquiry.status == "converted":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Converted inquiry cannot be updated")

    now = datetime.now(UTC)
    inquiry.date_of_birth = payload.date_of_birth
    inquiry.emergency_contact_name = payload.emergency_contact_name
    inquiry.emergency_contact_phone = payload.emergency_contact_phone
    inquiry.medical_notes = payload.medical_notes
    inquiry.consent_signer_name = payload.consent_signer_name
    if payload.guardian_consent_acknowledged:
        inquiry.guardian_consent_acknowledged_at = inquiry.guardian_consent_acknowledged_at or now
    if payload.privacy_acknowledged:
        inquiry.privacy_acknowledged_at = inquiry.privacy_acknowledged_at or now

    required_documents = registration_required_documents(inquiry)
    inquiry.required_documents_json = json.dumps(
        [{"document_type": document_type, "filename": document_type} for document_type in required_documents],
        sort_keys=True,
    )
    inquiry.submitted_documents_json = json.dumps(
        merge_registration_documents(
            parse_registration_documents(inquiry.submitted_documents_json),
            [document.model_dump() for document in payload.documents],
        ),
        sort_keys=True,
    )
    inquiry.payment_amount = payload.payment_amount
    inquiry.payment_currency = payload.payment_currency.upper() if payload.payment_currency else None
    inquiry.payment_method = payload.payment_method
    inquiry.payment_reference = payload.payment_reference
    inquiry.payment_status = normalized_registration_payment_status(payload, inquiry)

    summary = registration_packet_summary(inquiry)
    inquiry.verification_status = "ready_for_review" if summary["packet_complete"] else "packet_incomplete"
    inquiry.packet_submitted_at = now
    if inquiry.status == "new":
        inquiry.status = "reviewing"

    await db.commit()
    await db.refresh(inquiry)
    return inquiry


async def upload_public_registration_document(
    db: AsyncSession,
    site: str,
    inquiry_id: UUID,
    payload: PublicRegistrationDocumentUpload,
    settings: Settings | None = None,
) -> RegistrationInquiry:
    selected_settings = settings or get_settings()
    organization = await db.scalar(
        select(Organization).where(
            (Organization.slug == site) | (Organization.subdomain == site)
        )
    )
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    inquiry = await db.get(RegistrationInquiry, inquiry_id)
    if inquiry is None or inquiry.organization_id != organization.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    if normalize_contact_email(inquiry.email) != normalize_contact_email(payload.email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inquiry email mismatch")
    if inquiry.status == "converted":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Converted inquiry cannot be updated")

    try:
        content = b64decode(payload.content_base64, validate=True)
    except (BinasciiError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid base64 document content") from exc
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document content is empty")
    if len(content) > selected_settings.registration_document_max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Document is too large")

    checksum = sha256(content).hexdigest()
    filename = safe_registration_filename(payload.filename)
    storage_name = f"{checksum[:16]}-{filename}"
    key = (Path("registration-documents") / str(organization.id) / str(inquiry.id) / storage_name).as_posix()
    stored = put_object(
        selected_settings,
        local_root=selected_settings.registration_document_file_dir,
        local_url_prefix=selected_settings.registration_document_file_url_prefix,
        key=key,
        content=content,
        content_type=payload.content_type,
    )
    documents = [
        item
        for item in parse_registration_documents(inquiry.submitted_documents_json)
        if item.get("document_type") != payload.document_type
    ]
    documents.append(
        {
            "document_type": payload.document_type,
            "filename": filename,
            "storage_url": stored.url,
            "checksum": checksum,
            "content_type": payload.content_type,
            "size_bytes": len(content),
            "notes": payload.notes,
        }
    )
    inquiry.required_documents_json = json.dumps(
        [{"document_type": document_type, "filename": document_type} for document_type in registration_required_documents(inquiry)],
        sort_keys=True,
    )
    inquiry.submitted_documents_json = json.dumps(documents, sort_keys=True)
    summary = registration_packet_summary(inquiry)
    inquiry.verification_status = "ready_for_review" if summary["packet_complete"] else "packet_incomplete"
    inquiry.packet_submitted_at = inquiry.packet_submitted_at or datetime.now(UTC)
    if inquiry.status == "new":
        inquiry.status = "reviewing"

    await db.commit()
    await db.refresh(inquiry)
    return inquiry


def normalized_registration_payment_status(
    payload: PublicRegistrationPacketUpdate,
    inquiry: RegistrationInquiry,
) -> str:
    if payload.payment_status:
        return payload.payment_status
    if payload.payment_amount is None:
        return "not_required"
    if payload.payment_reference:
        return "pending_verification"
    return inquiry.payment_status if inquiry.payment_status != "not_required" else "pending"


def registration_payment_session_id(inquiry: RegistrationInquiry, provider: str) -> str:
    token = sha256(
        (
            f"registration-payment:{inquiry.id}:{inquiry.email.casefold()}:"
            f"{inquiry.payment_amount}:{inquiry.created_at}:{provider.casefold()}"
        ).encode()
    ).hexdigest()
    provider_token = re.sub(r"[^a-z0-9]+", "-", provider.lower()).strip("-")[:24] or "processor"
    return f"rpay_{provider_token}_{token[:24]}"


def registration_payment_session_url(
    base_url: str,
    session_id: str,
    site: str,
    inquiry: RegistrationInquiry,
    provider: str,
) -> str:
    return (
        f"{base_url.rstrip('/')}/{session_id}"
        f"?kind=registration&site={quote(site, safe='')}"
        f"&inquiry_id={inquiry.id}&provider={quote(provider, safe='')}"
    )


def registration_payment_open_amount(inquiry: RegistrationInquiry) -> Decimal:
    amount_due = inquiry.payment_amount or Decimal("0.00")
    amount_paid = amount_due if inquiry.payment_status in REGISTRATION_PAYMENT_COMPLETE_STATUSES else Decimal("0.00")
    return max(amount_due - amount_paid, Decimal("0.00")).quantize(Decimal("0.01"))


def registration_payment_session_status(inquiry: RegistrationInquiry) -> str:
    if registration_payment_open_amount(inquiry) <= 0:
        return "paid" if inquiry.payment_amount else "not_required"
    if inquiry.payment_status in {"failed", "cancelled"}:
        return inquiry.payment_status
    return "ready"


def registration_payment_hosted_checkout_read(
    inquiry: RegistrationInquiry,
    provider: str,
    session_id: str,
    site: str,
) -> RegistrationPaymentHostedCheckoutRead:
    amount_due = (inquiry.payment_amount or Decimal("0.00")).quantize(Decimal("0.01"))
    amount_paid = amount_due if inquiry.payment_status in REGISTRATION_PAYMENT_COMPLETE_STATUSES else Decimal("0.00")
    open_amount = registration_payment_open_amount(inquiry)
    registration_reference = f"REG-{str(inquiry.id).split('-')[0].upper()}"
    title = f"Registration fee for {inquiry.athlete_name}"
    return RegistrationPaymentHostedCheckoutRead(
        inquiry_id=inquiry.id,
        organization_id=inquiry.organization_id,
        athlete_name=inquiry.athlete_name,
        guardian_name=inquiry.guardian_name,
        guardian_email=inquiry.email,
        registration_reference=registration_reference,
        title=title,
        memo=inquiry.message,
        due_on=None,
        amount_due=amount_due,
        amount_paid=amount_paid.quantize(Decimal("0.01")),
        open_amount=open_amount,
        currency=(inquiry.payment_currency or "USD").upper(),
        status=inquiry.payment_status,
        provider=provider,
        session_id=session_id,
        session_status=registration_payment_session_status(inquiry),
        client_reference=f"registration-payment:{inquiry.id}",
        payment_methods=["mobile_money", "card", "bank_transfer", "cash_office"],
        settlement_endpoint=f"/api/v1/organizations/registration-checkout-sessions/{session_id}/settle",
        checkout_summary=(
            f"{title} has {open_amount} {(inquiry.payment_currency or 'USD').upper()} outstanding."
            if open_amount > 0
            else f"{title} is fully paid."
        ),
        public_registration_path=registration_resume_path(site, inquiry),
        family_portal_path=registration_family_portal_path(inquiry),
    )


def registration_resume_path(site: str, inquiry: RegistrationInquiry) -> str:
    return "/register?" + urlencode(
        {
            "mode": "player",
            "site": site,
            "inquiry_id": str(inquiry.id),
            "email": inquiry.email,
        }
    )


def registration_family_portal_path(inquiry: RegistrationInquiry) -> str:
    return "/family?" + urlencode(
        {
            "organization_id": str(inquiry.organization_id),
            "inquiry_id": str(inquiry.id),
            "guardian_email": inquiry.email,
            "guardian_name": inquiry.guardian_name or inquiry.email,
            "athlete_name": inquiry.athlete_name,
            "autoload": "1",
        }
    )


async def create_registration_payment_session(
    db: AsyncSession,
    site: str,
    inquiry_id: UUID,
    payload: RegistrationPaymentSessionCreate,
) -> tuple[RegistrationInquiry, str, str, str, RegistrationPaymentHostedCheckoutRead]:
    _organization, inquiry = await get_public_registration_inquiry(db, site, inquiry_id)
    if normalize_contact_email(inquiry.email) != normalize_contact_email(payload.email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inquiry email mismatch")
    if inquiry.status == "converted":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Converted inquiry cannot be updated")
    if inquiry.payment_amount is None or inquiry.payment_amount <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Registration fee amount is required")

    provider = payload.provider.strip().lower() or "manual_gateway"
    session_id = registration_payment_session_id(inquiry, provider)
    if inquiry.payment_status not in REGISTRATION_PAYMENT_COMPLETE_STATUSES:
        inquiry.payment_status = "pending"
    inquiry.payment_reference = inquiry.payment_reference or session_id
    inquiry.payment_method = payload.payment_method or inquiry.payment_method or provider
    inquiry.payment_currency = (inquiry.payment_currency or "USD").upper()
    inquiry.packet_submitted_at = inquiry.packet_submitted_at or datetime.now(UTC)
    inquiry.verification_status = (
        "ready_for_review"
        if registration_packet_summary(inquiry)["packet_complete"]
        else "packet_incomplete"
    )
    await db.commit()
    await db.refresh(inquiry)

    hosted_checkout = registration_payment_hosted_checkout_read(inquiry, provider, session_id, site)
    return (
        inquiry,
        session_id,
        registration_payment_session_url(
            payload.checkout_base_url,
            session_id,
            site,
            inquiry,
            provider,
        ),
        provider,
        hosted_checkout,
    )


async def get_registration_payment_hosted_checkout(
    db: AsyncSession,
    session_id: str,
    site: str,
    inquiry_id: UUID,
    provider: str,
) -> RegistrationPaymentHostedCheckoutRead:
    _organization, inquiry = await get_public_registration_inquiry(db, site, inquiry_id)
    expected_session_id = registration_payment_session_id(inquiry, provider)
    if session_id != expected_session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration payment session not found")
    if inquiry.payment_amount is None or inquiry.payment_amount <= 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration payment session not found")
    return registration_payment_hosted_checkout_read(inquiry, provider, session_id, site)


async def settle_registration_payment_checkout(
    db: AsyncSession,
    session_id: str,
    site: str,
    payload: RegistrationPaymentSettlementCreate,
) -> RegistrationPaymentSettlementRead:
    _organization, inquiry = await get_public_registration_inquiry(db, site, payload.inquiry_id)
    expected_session_id = registration_payment_session_id(inquiry, payload.provider)
    if session_id != expected_session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration payment session not found")
    if inquiry.payment_amount is None or inquiry.payment_amount <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Registration fee amount is required")
    if payload.currency and payload.currency.upper() != (inquiry.payment_currency or "USD").upper():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Currency mismatch")
    amount = payload.amount or inquiry.payment_amount
    if amount > inquiry.payment_amount:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Payment exceeds registration fee")

    accepted = payload.status == "succeeded"
    if accepted:
        inquiry.payment_status = "paid" if amount >= inquiry.payment_amount else "pending_verification"
        inquiry.payment_reference = payload.external_payment_id or inquiry.payment_reference or session_id
    elif payload.status == "pending":
        inquiry.payment_status = "pending_verification"
        inquiry.payment_reference = payload.external_payment_id or inquiry.payment_reference or session_id
    else:
        inquiry.payment_status = payload.status
        inquiry.payment_reference = payload.external_payment_id or inquiry.payment_reference or session_id
    inquiry.payment_method = payload.method
    inquiry.payment_currency = (payload.currency or inquiry.payment_currency or "USD").upper()
    inquiry.packet_submitted_at = inquiry.packet_submitted_at or datetime.now(UTC)
    inquiry.verification_status = (
        "ready_for_review"
        if registration_packet_summary(inquiry)["packet_complete"]
        else "packet_incomplete"
    )
    if inquiry.status == "new":
        inquiry.status = "reviewing"

    await db.commit()
    await db.refresh(inquiry)
    open_amount = registration_payment_open_amount(inquiry)
    return RegistrationPaymentSettlementRead(
        inquiry_id=inquiry.id,
        provider=payload.provider,
        accepted=accepted,
        payment_reference=inquiry.payment_reference,
        payment_status=inquiry.payment_status,
        amount_paid=(inquiry.payment_amount - open_amount).quantize(Decimal("0.01")),
        open_amount=open_amount,
        session_status=registration_payment_session_status(inquiry),
        message=(
            "Registration payment recorded."
            if accepted
            else f"Registration payment marked {payload.status}."
        ),
    )


def merge_registration_documents(
    existing_documents: list[dict[str, object]],
    incoming_documents: list[dict[str, object]],
) -> list[dict[str, object]]:
    existing_by_type = {
        str(document.get("document_type")): document
        for document in existing_documents
        if document.get("document_type")
    }
    merged: list[dict[str, object]] = []
    seen: set[str] = set()
    for document in incoming_documents:
        document_type = str(document.get("document_type", ""))
        if not document_type:
            continue
        existing = existing_by_type.get(document_type, {})
        next_document = {**existing, **{key: value for key, value in document.items() if value is not None}}
        merged.append(next_document)
        seen.add(document_type)
    merged.extend(
        document
        for document in existing_documents
        if str(document.get("document_type", "")) not in seen
    )
    return merged


async def list_registration_inquiries(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[RegistrationInquiry]:
    if not await can_manage_registration_inquiries(identity, organization_id, authz):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return list(
        (
            await db.scalars(
                select(RegistrationInquiry)
                .where(RegistrationInquiry.organization_id == organization_id)
                .order_by(RegistrationInquiry.created_at.desc())
                .limit(200)
            )
        ).all()
    )


async def registration_inquiry_import_template(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> RegistrationInquiryImportTemplateRead:
    if not await can_manage_registration_inquiries(identity, organization_id, authz):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    teams = list(
        (
            await db.scalars(
                select(Team)
                .where(Team.organization_id == organization_id)
                .order_by(Team.name)
                .limit(3)
            )
        ).all()
    )
    columns = [
        "athlete_name",
        "guardian_name",
        "email",
        "phone",
        "age_group",
        "sport_interest",
        "team",
        "message",
    ]
    sample_team = teams[0].name if teams else ""
    sample_sport = organization.primary_sport or "football"
    rows = [
        {
            "athlete_name": "Amina Example",
            "guardian_name": "Parent Example",
            "email": "parent.example@example.com",
            "phone": "+254700000000",
            "age_group": "U15",
            "sport_interest": sample_sport,
            "team": sample_team,
            "message": "Imported from spreadsheet.",
        }
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return RegistrationInquiryImportTemplateRead(
        organization_id=organization_id,
        filename=f"{organization.slug}-registration-import-template.csv",
        columns=columns,
        csv_text=buffer.getvalue(),
    )


async def import_registration_inquiries(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: RegistrationInquiryImportCreate,
    authz: AuthorizationService,
) -> tuple[
    list[RegistrationInquiry],
    list[RegistrationInquiryImportPreviewRowRead],
    list[RegistrationInquiryImportRowErrorRead],
]:
    if not await can_manage_registration_inquiries(identity, organization_id, authz):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    rows = list(csv.DictReader(io.StringIO(payload.csv_text.strip())))
    if not rows or not rows[0]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="CSV headers are required")

    teams_by_id = {
        str(team.id): team
        for team in (
            await db.scalars(select(Team).where(Team.organization_id == organization_id))
        ).all()
    }
    teams_by_name = {team.name.strip().lower(): team for team in teams_by_id.values()}
    created: list[RegistrationInquiry] = []
    preview_rows: list[RegistrationInquiryImportPreviewRowRead] = []
    errors: list[RegistrationInquiryImportRowErrorRead] = []
    required_documents = organization_public_registration_documents(organization)

    for row_number, raw_row in enumerate(rows, start=2):
        row = normalize_import_row(raw_row)
        try:
            team_id = imported_team_id(row, teams_by_id, teams_by_name)
            inquiry_payload = PublicRegistrationInquiryCreate.model_validate(
                {
                    "athlete_name": row.get("athlete_name") or row.get("player_name"),
                    "guardian_name": row.get("guardian_name") or row.get("parent_name"),
                    "email": row.get("email") or row.get("guardian_email"),
                    "phone": row.get("phone") or row.get("guardian_phone"),
                    "age_group": row.get("age_group"),
                    "sport_interest": row.get("sport_interest") or row.get("sport"),
                    "team_id": team_id,
                    "message": row.get("message") or row.get("notes"),
                    "source_url": payload.source_url or row.get("source_url") or "csv-import",
                }
            )
        except (HTTPException, ValidationError, ValueError) as error:
            errors.append(
                RegistrationInquiryImportRowErrorRead(
                    row_number=row_number,
                    message=import_error_message(error),
                    row=row,
                )
            )
            continue

        team = teams_by_id.get(str(inquiry_payload.team_id)) if inquiry_payload.team_id else None
        preview_rows.append(
            RegistrationInquiryImportPreviewRowRead(
                row_number=row_number,
                athlete_name=inquiry_payload.athlete_name,
                guardian_name=inquiry_payload.guardian_name,
                email=normalize_contact_email(inquiry_payload.email),
                phone=inquiry_payload.phone,
                age_group=inquiry_payload.age_group,
                sport_interest=inquiry_payload.sport_interest,
                team_id=inquiry_payload.team_id,
                team_name=team.name if team is not None else None,
                payment_status="pending" if organization.registration_fee_amount else "not_required",
                required_documents=required_documents,
            )
        )
        if payload.dry_run:
            continue

        guardian = await ensure_registration_guardian_contact(db, organization_id, inquiry_payload)
        inquiry_dict = inquiry_payload.model_dump()
        inquiry_dict["email"] = normalize_contact_email(inquiry_payload.email)
        inquiry = RegistrationInquiry(
            organization_id=organization_id,
            **inquiry_dict,
            guardian_person_id=guardian.id,
            guardian_contact_status="pending_account",
            required_documents_json=json.dumps(
                [{"document_type": document_type, "filename": document_type} for document_type in required_documents],
                sort_keys=True,
            ),
            payment_amount=organization.registration_fee_amount,
            payment_currency=organization.registration_fee_currency,
            payment_status="pending" if organization.registration_fee_amount else "not_required",
            payment_method="registration_checkout" if organization.registration_fee_amount else None,
            review_notes=f"Imported from CSV row {row_number}.",
            reviewed_by_person_id=identity.person_id,
            reviewed_at=datetime.now(UTC),
        )
        db.add(inquiry)
        created.append(inquiry)

    if created:
        await db.commit()
        for inquiry in created:
            await db.refresh(inquiry)
    return created, preview_rows, errors


def normalize_import_row(row: dict[str, str | None]) -> dict[str, str | None]:
    return {
        (key or "").strip().lower().replace(" ", "_"): value.strip() if isinstance(value, str) and value.strip() else None
        for key, value in row.items()
        if key is not None
    }


def imported_team_id(
    row: dict[str, str | None],
    teams_by_id: dict[str, Team],
    teams_by_name: dict[str, Team],
) -> UUID | None:
    raw_team_id = row.get("team_id")
    if raw_team_id:
        if raw_team_id not in teams_by_id:
            raise ValueError(f"Team id {raw_team_id} does not belong to this organization")
        return UUID(raw_team_id)
    raw_team_name = row.get("team") or row.get("team_name")
    if raw_team_name:
        team = teams_by_name.get(raw_team_name.strip().lower())
        if team is None:
            raise ValueError(f"Team {raw_team_name} was not found")
        return team.id
    return None


def import_error_message(error: HTTPException | ValidationError | ValueError) -> str:
    if isinstance(error, HTTPException):
        return str(error.detail)
    if isinstance(error, ValidationError):
        return "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors()
        )
    return str(error)


async def update_registration_inquiry(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    inquiry_id: UUID,
    payload: RegistrationInquiryUpdate,
    authz: AuthorizationService,
) -> RegistrationInquiry:
    if not await can_manage_registration_inquiries(identity, organization_id, authz):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    inquiry = await db.get(RegistrationInquiry, inquiry_id)
    if inquiry is None or inquiry.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")

    changed = False
    payment_fields = {"payment_status", "payment_method", "payment_reference"}
    if inquiry.status == "converted" and payload.model_fields_set.intersection(payment_fields):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Converted inquiries cannot be modified",
        )

    if "status" in payload.model_fields_set:
        if payload.status is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Inquiry status cannot be empty",
            )
        normalized_status = payload.status.strip().lower()
        if normalized_status == "converted":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Use the conversion workflow to mark inquiries converted",
            )
        if normalized_status not in INQUIRY_REVIEW_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Status must be one of: {', '.join(sorted(INQUIRY_REVIEW_STATUSES))}",
            )
        if inquiry.status == "converted" and normalized_status != "converted":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Converted inquiries cannot be reopened",
            )
        inquiry.status = normalized_status
        changed = True

    if "review_notes" in payload.model_fields_set:
        inquiry.review_notes = payload.review_notes
        changed = True
    if "follow_up_at" in payload.model_fields_set:
        inquiry.follow_up_at = payload.follow_up_at
        changed = True
    payment_changed = False
    if "payment_status" in payload.model_fields_set:
        if payload.payment_status is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Payment status cannot be empty",
            )
        normalized_payment_status = payload.payment_status.strip().lower()
        if normalized_payment_status not in REGISTRATION_PAYMENT_REVIEW_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Payment status must be one of: {', '.join(sorted(REGISTRATION_PAYMENT_REVIEW_STATUSES))}",
            )
        inquiry.payment_status = normalized_payment_status
        payment_changed = True
        changed = True
    if "payment_method" in payload.model_fields_set:
        inquiry.payment_method = payload.payment_method.strip() if payload.payment_method else None
        payment_changed = True
        changed = True
    if "payment_reference" in payload.model_fields_set:
        inquiry.payment_reference = payload.payment_reference.strip() if payload.payment_reference else None
        payment_changed = True
        changed = True
    if payment_changed:
        inquiry.verification_status = (
            "ready_for_review" if registration_packet_summary(inquiry)["packet_complete"] else "packet_incomplete"
        )
        if inquiry.status == "new":
            inquiry.status = "reviewing"

    if changed:
        inquiry.reviewed_by_person_id = identity.person_id
        inquiry.reviewed_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(inquiry)
    return inquiry


async def queue_registration_inquiry_agent_review(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    inquiry_id: UUID,
    authz: AuthorizationService,
) -> AgentTask:
    if not await can_manage_registration_inquiries(identity, organization_id, authz):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    inquiry = await db.get(RegistrationInquiry, inquiry_id)
    if inquiry is None or inquiry.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    if inquiry.status == "converted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Converted inquiries no longer need admissions AI review",
        )

    agent = await db.scalar(
        select(Agent)
        .where(
            Agent.organization_id == organization_id,
            Agent.kind == AgentKind.OPERATIONS,
            Agent.name == "Admissions Intake Agent",
        )
        .order_by(Agent.created_at)
        .limit(1)
    )
    if agent is None:
        agent = Agent(
            organization_id=organization_id,
            name="Admissions Intake Agent",
            kind=AgentKind.OPERATIONS,
            purpose=(
                "Review registration inquiries for packet readiness, consent gaps, "
                "payment blockers, and family handoff risks before staff conversion."
            ),
            status="active",
            model_policy="human_review_required",
        )
        db.add(agent)
        await db.flush()
        await authz.touch(
            Relationship(
                resource_type="agent",
                resource_id=str(agent.id),
                relation="owner",
                subject_type="user",
                subject_id=str(identity.user_id),
            )
        )

    packet = registration_packet_summary(inquiry)
    input_ref = (
        f"registration-inquiry:{inquiry.id};"
        f"status:{inquiry.status};"
        f"verification:{inquiry.verification_status};"
        f"payment:{inquiry.payment_status};"
        f"packet_complete:{packet['packet_complete']}"
    )
    existing_task = await db.scalar(
        select(AgentTask)
        .where(
            AgentTask.organization_id == organization_id,
            AgentTask.task_type == "registration_inquiry_review",
            AgentTask.input_ref.like(f"registration-inquiry:{inquiry.id};%"),
            AgentTask.status.not_in([AgentTaskStatus.FAILED, AgentTaskStatus.CANCELLED]),
        )
        .order_by(AgentTask.created_at.desc())
        .limit(1)
    )
    if existing_task is not None:
        return existing_task

    task = await queue_agent_task(
        db,
        identity,
        agent.id,
        AgentTaskCreate(
            organization_id=organization_id,
            task_type="registration_inquiry_review",
            title=f"Review registration packet for {inquiry.athlete_name}",
            input_ref=input_ref,
        ),
        authz,
    )
    inquiry.review_notes = append_review_note(
        inquiry.review_notes,
        f"AI admissions review queued for {inquiry.athlete_name}: agent task {task.id}",
    )
    inquiry.reviewed_by_person_id = identity.person_id
    inquiry.reviewed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(task)
    return task


async def create_registration_inquiry_follow_up(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    inquiry_id: UUID,
    payload: RegistrationInquiryFollowUpCreate,
    authz: AuthorizationService,
) -> tuple[RegistrationInquiry, CommunicationMessage, Person]:
    if not await can_manage_registration_inquiries(identity, organization_id, authz):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    inquiry = await db.get(RegistrationInquiry, inquiry_id)
    if inquiry is None or inquiry.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")

    recipient = await db.get(Person, inquiry.guardian_person_id) if inquiry.guardian_person_id else None
    recipient = recipient or await find_person_by_email(db, inquiry.email)
    if recipient is None:
        recipient = Person(
            display_name=inquiry.guardian_name or inquiry.email,
            primary_email=normalize_contact_email(inquiry.email),
            primary_phone=inquiry.phone,
        )
        db.add(recipient)
        await db.flush()
    elif inquiry.phone and not recipient.primary_phone:
        recipient.primary_phone = inquiry.phone
        await db.flush()
    inquiry.guardian_person_id = recipient.id

    message = await create_message(
        db,
        identity,
        CommunicationMessageCreate(
            organization_id=organization_id,
            message_type=CommunicationMessageType.REMINDER,
            channel=payload.channel,
            scope_type=CommunicationScopeType.PERSON,
            scope_id=recipient.id,
            recipient_person_ids=[recipient.id],
            subject=payload.subject,
            body=payload.body,
            urgent=payload.urgent,
            quiet_hours_override=payload.quiet_hours_override,
            copy_guardians_for_minors=False,
        ),
        authz,
    )

    inquiry.status = "contacted"
    inquiry.review_notes = append_review_note(
        inquiry.review_notes,
        f"Follow-up queued via {payload.channel.value}: {payload.subject}",
    )
    inquiry.reviewed_by_person_id = identity.person_id
    inquiry.reviewed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(inquiry)
    await db.refresh(message)
    await db.refresh(recipient)
    return inquiry, message, recipient


async def convert_registration_inquiry(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    inquiry_id: UUID,
    payload: RegistrationInquiryConversionCreate,
    authz: AuthorizationService,
) -> tuple[
    RegistrationInquiry,
    Person,
    AthleteProfile,
    TeamRosterEntry | None,
    Person | None,
    CommunicationMessage | None,
    str | None,
]:
    if not await can_manage_registration_inquiries(identity, organization_id, authz):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    inquiry = await db.get(RegistrationInquiry, inquiry_id)
    if inquiry is None or inquiry.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
    if inquiry.status == "converted":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inquiry already converted")
    packet = registration_packet_summary(inquiry)
    if not packet["packet_complete"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Registration packet is not ready for conversion",
                "next_steps": packet["next_steps"],
                "missing_documents": packet["missing_documents"],
            },
        )

    target_team_id = payload.team_id or inquiry.team_id
    team = None
    if target_team_id is not None:
        team = await db.get(Team, target_team_id)
        if team is None or team.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    athlete = Person(display_name=inquiry.athlete_name)
    db.add(athlete)
    await db.flush()

    athlete_membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.subject_type == MemberSubjectType.PERSON,
            Membership.subject_id == athlete.id,
            Membership.role == MembershipRole.ATHLETE,
        )
    )
    if athlete_membership is None:
        db.add(
            Membership(
                organization_id=organization_id,
                subject_type=MemberSubjectType.PERSON,
                subject_id=athlete.id,
                role=MembershipRole.ATHLETE,
                title="Athlete",
            )
        )

    athlete_profile = AthleteProfile(
        organization_id=organization_id,
        person_id=athlete.id,
        development_notes=f"Converted from registration inquiry {inquiry.id}",
    )
    db.add(athlete_profile)
    await db.flush()

    roster_entry = None
    if team is not None:
        roster_entry = TeamRosterEntry(
            team_id=team.id,
            athlete_profile_id=athlete_profile.id,
            role=payload.role,
            status=RosterStatus.ACTIVE,
            jersey_number=payload.jersey_number,
            primary_position=payload.primary_position,
        )
        db.add(roster_entry)
        await authz.touch(
            Relationship(
                resource_type="team",
                resource_id=str(team.id),
                relation="athlete" if payload.role == TeamRole.PLAYER else payload.role.value,
                subject_type="person",
                subject_id=str(athlete.id),
            )
        )

    guardian = None
    guardian_relationship = None
    if payload.create_guardian:
        guardian = await db.get(Person, inquiry.guardian_person_id) if inquiry.guardian_person_id else None
        guardian = guardian or await find_person_by_email(db, inquiry.email)
        if guardian is None:
            guardian = Person(
                display_name=inquiry.guardian_name or inquiry.email,
                primary_email=normalize_contact_email(inquiry.email),
                primary_phone=inquiry.phone,
            )
            db.add(guardian)
            await db.flush()
        elif inquiry.phone and not guardian.primary_phone:
            guardian.primary_phone = inquiry.phone
        inquiry.guardian_person_id = guardian.id
        inquiry.guardian_contact_status = "linked_to_athlete"

        existing_guardian = await db.scalar(
            select(GuardianRelationship).where(
                GuardianRelationship.athlete_person_id == athlete.id,
                GuardianRelationship.guardian_person_id == guardian.id,
            )
        )
        if existing_guardian is None:
            guardian_relationship = GuardianRelationship(
                athlete_person_id=athlete.id,
                guardian_person_id=guardian.id,
                relationship_kind=GuardianRelationshipKind.PARENT,
                relationship="parent",
                can_sign_consent=True,
                emergency_contact=True,
                is_primary=True,
            )
            db.add(guardian_relationship)
            await db.flush()
        else:
            guardian_relationship = existing_guardian

    inquiry.status = "converted"
    inquiry.reviewed_by_person_id = identity.person_id
    inquiry.reviewed_at = datetime.now(UTC)
    await authz.touch(
        Relationship(
            resource_type="organization",
            resource_id=str(organization_id),
            relation="athlete",
            subject_type="person",
            subject_id=str(athlete.id),
        )
    )
    await db.commit()
    await db.refresh(inquiry)
    await db.refresh(athlete)
    await db.refresh(athlete_profile)
    if roster_entry is not None:
        await db.refresh(roster_entry)
    if guardian is not None:
        await db.refresh(guardian)
    guardian_invite = None
    guardian_invite_url = None
    if guardian is not None and guardian_relationship is not None and payload.send_guardian_invite:
        organization = await db.get(Organization, organization_id)
        if organization is not None:
            guardian_invite_url = registration_guardian_portal_invite_url(
                payload.guardian_portal_url,
                organization_id,
                guardian_relationship.id,
                athlete.id,
                guardian,
            )
            guardian_invite = await create_registration_guardian_invite(
                db,
                identity,
                organization,
                athlete,
                guardian,
                payload.guardian_invite_channel,
                guardian_invite_url,
                authz,
            )
            inquiry.review_notes = append_review_note(
                inquiry.review_notes,
                f"Guardian portal invite queued via {payload.guardian_invite_channel.value}: {guardian_invite_url}",
            )
            await db.commit()
            await db.refresh(inquiry)
            await db.refresh(guardian_invite)
    return inquiry, athlete, athlete_profile, roster_entry, guardian, guardian_invite, guardian_invite_url


def registration_guardian_portal_invite_url(
    base_url: str,
    organization_id: UUID,
    relationship_id: UUID,
    athlete_id: UUID,
    guardian: Person,
) -> str:
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault("organization_id", str(organization_id))
    query.setdefault("relationship_id", str(relationship_id))
    query.setdefault("athlete_id", str(athlete_id))
    query.setdefault("autoload", "1")
    query.setdefault("guardian_sub", f"guardian-{relationship_id}")
    query.setdefault("guardian_name", guardian.display_name)
    if guardian.primary_email:
        query.setdefault("guardian_email", guardian.primary_email)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


async def create_registration_guardian_invite(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization: Organization,
    athlete: Person,
    guardian: Person,
    channel: CommunicationChannel,
    portal_url: str,
    authz: AuthorizationService,
) -> CommunicationMessage:
    organization_name = organization.public_name or organization.name
    return await create_message(
        db,
        identity,
        CommunicationMessageCreate(
            organization_id=organization.id,
            message_type=CommunicationMessageType.REQUEST,
            channel=channel,
            scope_type=CommunicationScopeType.PERSON,
            scope_id=guardian.id,
            recipient_person_ids=[guardian.id],
            subject=f"{organization_name} family portal invitation",
            body=registration_guardian_invite_body(organization_name, athlete, guardian, portal_url),
            urgent=False,
            quiet_hours_override=False,
            copy_guardians_for_minors=False,
        ),
        authz,
        enforce_manage_communications_scope=False,
    )


def registration_guardian_invite_body(
    organization_name: str,
    athlete: Person,
    guardian: Person,
    portal_url: str,
) -> str:
    return "\n\n".join(
        [
            f"Hello {guardian.display_name},",
            f"{organization_name} has accepted {athlete.display_name}'s registration inquiry and created your AfroLete family portal access.",
            "Sign in with the email address where you received this message so AfroLete can link your guardian account automatically.",
            f"Open the family portal: {portal_url}",
            "From the portal you can review consent requests, RSVP for events, monitor schedules, and see family-visible athlete development updates.",
        ]
    )


async def add_member(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: MemberAdd,
    authz: AuthorizationService,
) -> Membership:
    can_manage = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    subject_id = payload.subject_id
    if payload.subject_type == MemberSubjectType.PERSON:
        if not payload.email and subject_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Person members require email or subject_id",
            )
        person = None
        if subject_id is not None:
            person = await db.get(Person, subject_id)
            if person is None:
                raise HTTPException(status_code=404, detail="Person not found")
        elif payload.email:
            person = await db.scalar(select(Person).where(Person.primary_email == payload.email))
        if person is None:
            person = Person(
                display_name=payload.display_name or payload.email or "Member",
                primary_email=payload.email,
                date_of_birth=payload.date_of_birth,
                country_code=payload.country_code.upper() if payload.country_code else None,
            )
            db.add(person)
            await db.flush()
        elif payload.country_code and person.country_code is None:
            person.country_code = payload.country_code.upper()
        if payload.date_of_birth is not None and person.date_of_birth is None:
            person.date_of_birth = payload.date_of_birth
        subject_id = person.id
    else:
        if subject_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Organization and team members require subject_id",
            )
        if payload.subject_type == MemberSubjectType.ORGANIZATION:
            subject_exists = await db.get(Organization, subject_id)
            if subject_exists is None:
                raise HTTPException(status_code=404, detail="Organization member not found")
        if payload.subject_type == MemberSubjectType.TEAM:
            subject_exists = await db.get(Team, subject_id)
            if subject_exists is None:
                raise HTTPException(status_code=404, detail="Team member not found")

    if subject_id is None:
        raise HTTPException(status_code=422, detail="Missing member subject")

    existing = await db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.subject_type == payload.subject_type,
            Membership.subject_id == subject_id,
            Membership.role == payload.role,
        )
    )
    if existing is not None:
        return existing

    membership = Membership(
        organization_id=organization_id,
        subject_type=payload.subject_type,
        subject_id=subject_id,
        role=payload.role,
        title=payload.title,
    )
    db.add(membership)

    await authz.touch(
        Relationship(
            resource_type="organization",
            resource_id=str(organization_id),
            relation=organization_member_relation(payload.subject_type, payload.role),
            subject_type=payload.subject_type.value,
            subject_id=str(subject_id),
        )
    )
    await db.commit()
    await db.refresh(membership)
    return membership


async def ensure_manage_organization(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> Organization:
    can_manage = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def create_organization_program(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: OrganizationProgramCreate,
    authz: AuthorizationService,
) -> OrganizationProgram:
    await ensure_manage_organization(db, identity, organization_id, authz)
    program = OrganizationProgram(
        organization_id=organization_id,
        name=payload.name,
        program_type=payload.program_type,
        sport=payload.sport,
        age_group=payload.age_group,
        gender_category=payload.gender_category,
        description=payload.description,
        capacity=payload.capacity,
        starts_on=payload.starts_on,
        ends_on=payload.ends_on,
        status=payload.status,
    )
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return program


async def list_organization_programs(db: AsyncSession, organization_id: UUID) -> list[OrganizationProgram]:
    return list(
        (
            await db.scalars(
                select(OrganizationProgram)
                .where(OrganizationProgram.organization_id == organization_id)
                .order_by(OrganizationProgram.status, OrganizationProgram.name)
            )
        ).all()
    )


async def create_organization_season(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: OrganizationSeasonCreate,
    authz: AuthorizationService,
) -> OrganizationSeason:
    await ensure_manage_organization(db, identity, organization_id, authz)
    if payload.ends_on < payload.starts_on:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Season end must be on or after start")
    season = OrganizationSeason(
        organization_id=organization_id,
        name=payload.name,
        sport=payload.sport,
        starts_on=payload.starts_on,
        ends_on=payload.ends_on,
        registration_opens_on=payload.registration_opens_on,
        registration_closes_on=payload.registration_closes_on,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(season)
    await db.commit()
    await db.refresh(season)
    return season


async def list_organization_seasons(db: AsyncSession, organization_id: UUID) -> list[OrganizationSeason]:
    return list(
        (
            await db.scalars(
                select(OrganizationSeason)
                .where(OrganizationSeason.organization_id == organization_id)
                .order_by(OrganizationSeason.starts_on.desc(), OrganizationSeason.name)
            )
        ).all()
    )


async def create_organization_group(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: OrganizationGroupCreate,
    authz: AuthorizationService,
) -> OrganizationGroup:
    await ensure_manage_organization(db, identity, organization_id, authz)
    await ensure_group_links_match_organization(db, organization_id, payload)
    group = OrganizationGroup(
        organization_id=organization_id,
        program_id=payload.program_id,
        season_id=payload.season_id,
        team_id=payload.team_id,
        lead_person_id=payload.lead_person_id,
        name=payload.name,
        group_type=payload.group_type,
        sport=payload.sport,
        age_group=payload.age_group,
        description=payload.description,
        capacity=payload.capacity,
        status=payload.status,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def list_organization_groups(
    db: AsyncSession,
    organization_id: UUID,
) -> list[tuple[OrganizationGroup, int]]:
    rows = (
        await db.execute(
            select(OrganizationGroup, func.count(OrganizationGroupMembership.id))
            .outerjoin(OrganizationGroupMembership, OrganizationGroupMembership.group_id == OrganizationGroup.id)
            .where(OrganizationGroup.organization_id == organization_id)
            .group_by(OrganizationGroup.id)
            .order_by(OrganizationGroup.status, OrganizationGroup.name)
        )
    ).all()
    return [(group, int(member_count or 0)) for group, member_count in rows]


async def add_organization_group_member(
    db: AsyncSession,
    identity: CurrentIdentity,
    group_id: UUID,
    payload: OrganizationGroupMemberAdd,
    authz: AuthorizationService,
) -> OrganizationGroupMembership:
    group = await db.get(OrganizationGroup, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization group not found")
    await ensure_manage_organization(db, identity, group.organization_id, authz)
    await ensure_member_subject_exists(db, payload.subject_type, payload.subject_id)
    existing = await db.scalar(
        select(OrganizationGroupMembership).where(
            OrganizationGroupMembership.group_id == group_id,
            OrganizationGroupMembership.subject_type == payload.subject_type,
            OrganizationGroupMembership.subject_id == payload.subject_id,
            OrganizationGroupMembership.role == payload.role,
        )
    )
    if existing is not None:
        return existing
    membership = OrganizationGroupMembership(
        group_id=group_id,
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        role=payload.role,
        notes=payload.notes,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


async def list_organization_group_members(
    db: AsyncSession,
    identity: CurrentIdentity,
    group_id: UUID,
    authz: AuthorizationService,
) -> list[tuple[OrganizationGroupMembership, str | None]]:
    group = await db.get(OrganizationGroup, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization group not found")
    await ensure_manage_organization(db, identity, group.organization_id, authz)
    memberships = list(
        (
            await db.scalars(
                select(OrganizationGroupMembership)
                .where(OrganizationGroupMembership.group_id == group_id)
                .order_by(OrganizationGroupMembership.role, OrganizationGroupMembership.created_at)
            )
        ).all()
    )
    return [
        (membership, await member_subject_label(db, membership.subject_type, membership.subject_id))
        for membership in memberships
    ]


async def ensure_group_links_match_organization(
    db: AsyncSession,
    organization_id: UUID,
    payload: OrganizationGroupCreate,
) -> None:
    if payload.program_id is not None:
        program = await db.get(OrganizationProgram, payload.program_id)
        if program is None or program.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    if payload.season_id is not None:
        season = await db.get(OrganizationSeason, payload.season_id)
        if season is None or season.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Season not found")
    if payload.team_id is not None:
        team = await db.get(Team, payload.team_id)
        if team is None or team.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if payload.lead_person_id is not None and await db.get(Person, payload.lead_person_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead person not found")


async def create_organization_award_program(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: OrganizationAwardProgramCreate,
    authz: AuthorizationService,
) -> OrganizationAwardProgram:
    await ensure_manage_organization(db, identity, organization_id, authz)
    program = OrganizationAwardProgram(
        organization_id=organization_id,
        name=payload.name,
        season_label=payload.season_label,
        level=payload.level,
        frequency=payload.frequency,
        nomination_opens_at=payload.nomination_opens_at,
        nomination_closes_at=payload.nomination_closes_at,
        voting_opens_at=payload.voting_opens_at,
        voting_closes_at=payload.voting_closes_at,
        eligibility_summary=payload.eligibility_summary,
        ceremony_name=payload.ceremony_name,
        ceremony_at=payload.ceremony_at,
        ceremony_venue=payload.ceremony_venue,
        certificate_template=payload.certificate_template,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return program


async def list_organization_award_programs(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[tuple[OrganizationAwardProgram, int, int, int]]:
    await ensure_manage_organization(db, identity, organization_id, authz)
    programs = list(
        (
            await db.scalars(
                select(OrganizationAwardProgram)
                .where(OrganizationAwardProgram.organization_id == organization_id)
                .order_by(OrganizationAwardProgram.created_at.desc())
            )
        ).all()
    )
    rows: list[tuple[OrganizationAwardProgram, int, int, int]] = []
    for program in programs:
        category_count = await scalar_count_for(db, OrganizationAwardCategory.program_id, program.id)
        nomination_count = await scalar_count_for(db, OrganizationAwardNomination.program_id, program.id)
        recipient_count = await scalar_count_for(db, OrganizationAwardRecipient.program_id, program.id)
        rows.append((program, category_count, nomination_count, recipient_count))
    return rows


async def create_organization_award_category(
    db: AsyncSession,
    identity: CurrentIdentity,
    program_id: UUID,
    payload: OrganizationAwardCategoryCreate,
    authz: AuthorizationService,
) -> OrganizationAwardCategory:
    program = await get_award_program_for_manage(db, identity, program_id, authz)
    category = OrganizationAwardCategory(
        organization_id=program.organization_id,
        program_id=program.id,
        name=payload.name,
        award_type=payload.award_type,
        judging_method=payload.judging_method,
        criteria=payload.criteria,
        max_recipients=payload.max_recipients,
        voter_roles=payload.voter_roles,
        status=payload.status,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def list_organization_award_categories(
    db: AsyncSession,
    identity: CurrentIdentity,
    program_id: UUID,
    authz: AuthorizationService,
) -> list[tuple[OrganizationAwardCategory, int, int]]:
    await get_award_program_for_manage(db, identity, program_id, authz)
    categories = list(
        (
            await db.scalars(
                select(OrganizationAwardCategory)
                .where(OrganizationAwardCategory.program_id == program_id)
                .order_by(OrganizationAwardCategory.status, OrganizationAwardCategory.name)
            )
        ).all()
    )
    rows: list[tuple[OrganizationAwardCategory, int, int]] = []
    for category in categories:
        nomination_count = await scalar_count_for(db, OrganizationAwardNomination.category_id, category.id)
        recipient_count = await scalar_count_for(db, OrganizationAwardRecipient.category_id, category.id)
        rows.append((category, nomination_count, recipient_count))
    return rows


async def create_organization_award_nomination(
    db: AsyncSession,
    identity: CurrentIdentity,
    category_id: UUID,
    payload: OrganizationAwardNominationCreate,
    authz: AuthorizationService,
) -> OrganizationAwardNomination:
    category = await get_award_category_for_manage(db, identity, category_id, authz)
    await ensure_member_subject_exists(db, payload.nominee_subject_type, payload.nominee_subject_id)
    nomination = OrganizationAwardNomination(
        organization_id=category.organization_id,
        program_id=category.program_id,
        category_id=category.id,
        nominee_subject_type=payload.nominee_subject_type,
        nominee_subject_id=payload.nominee_subject_id,
        nominated_by_person_id=identity.person_id,
        title=payload.title,
        nomination_summary=payload.nomination_summary,
        evidence_url=payload.evidence_url,
        status=payload.status,
        finalist=payload.finalist,
        score=payload.score,
    )
    db.add(nomination)
    await db.commit()
    await db.refresh(nomination)
    return nomination


async def list_organization_award_nominations(
    db: AsyncSession,
    identity: CurrentIdentity,
    category_id: UUID,
    authz: AuthorizationService,
) -> list[tuple[OrganizationAwardNomination, str | None, int, Decimal]]:
    await get_award_category_for_manage(db, identity, category_id, authz)
    nominations = list(
        (
            await db.scalars(
                select(OrganizationAwardNomination)
                .where(OrganizationAwardNomination.category_id == category_id)
                .order_by(
                    OrganizationAwardNomination.finalist.desc(),
                    OrganizationAwardNomination.status,
                    OrganizationAwardNomination.created_at.desc(),
                )
            )
        ).all()
    )
    rows: list[tuple[OrganizationAwardNomination, str | None, int, Decimal]] = []
    for nomination in nominations:
        votes = list(
            (
                await db.scalars(
                    select(OrganizationAwardVote).where(
                        OrganizationAwardVote.nomination_id == nomination.id
                    )
                )
            ).all()
        )
        weighted_score = sum((vote.score * vote.weight for vote in votes), Decimal("0")).quantize(
            Decimal("0.01")
        )
        nominee_label = await member_subject_label(
            db,
            nomination.nominee_subject_type,
            nomination.nominee_subject_id,
        )
        rows.append((nomination, nominee_label, len(votes), weighted_score))
    return rows


async def create_or_update_organization_award_vote(
    db: AsyncSession,
    identity: CurrentIdentity,
    nomination_id: UUID,
    payload: OrganizationAwardVoteCreate,
    authz: AuthorizationService,
) -> OrganizationAwardVote:
    nomination = await get_award_nomination_for_manage(db, identity, nomination_id, authz)
    voter_person_id = payload.voter_person_id or identity.person_id
    voter = await db.get(Person, voter_person_id)
    if voter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voter not found")
    vote = await db.scalar(
        select(OrganizationAwardVote).where(
            OrganizationAwardVote.nomination_id == nomination.id,
            OrganizationAwardVote.voter_person_id == voter_person_id,
        )
    )
    if vote is None:
        vote = OrganizationAwardVote(
            organization_id=nomination.organization_id,
            nomination_id=nomination.id,
            voter_person_id=voter_person_id,
            score=payload.score,
            weight=payload.weight,
            comment=payload.comment,
        )
        db.add(vote)
    else:
        vote.score = payload.score
        vote.weight = payload.weight
        vote.comment = payload.comment
    await db.commit()
    await db.refresh(vote)
    return vote


async def create_organization_award_recipient(
    db: AsyncSession,
    identity: CurrentIdentity,
    category_id: UUID,
    payload: OrganizationAwardRecipientCreate,
    authz: AuthorizationService,
) -> OrganizationAwardRecipient:
    category = await get_award_category_for_manage(db, identity, category_id, authz)
    await ensure_member_subject_exists(db, payload.recipient_subject_type, payload.recipient_subject_id)
    nomination: OrganizationAwardNomination | None = None
    if payload.nomination_id is not None:
        nomination = await db.get(OrganizationAwardNomination, payload.nomination_id)
        if nomination is None or nomination.category_id != category.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Award nomination not found")
    recipient = OrganizationAwardRecipient(
        organization_id=category.organization_id,
        program_id=category.program_id,
        category_id=category.id,
        nomination_id=nomination.id if nomination else None,
        recipient_subject_type=payload.recipient_subject_type,
        recipient_subject_id=payload.recipient_subject_id,
        certificate_number=await next_award_certificate_number(db, category.organization_id),
        awarded_on=payload.awarded_on,
        public_citation=payload.public_citation,
        certificate_url=payload.certificate_url,
        status=payload.status,
    )
    db.add(recipient)
    if nomination is not None:
        nomination.status = "accepted"
        nomination.finalist = True
    await db.commit()
    await db.refresh(recipient)
    return recipient


async def list_organization_award_recipients(
    db: AsyncSession,
    identity: CurrentIdentity,
    program_id: UUID,
    authz: AuthorizationService,
) -> list[tuple[OrganizationAwardRecipient, str | None]]:
    await get_award_program_for_manage(db, identity, program_id, authz)
    recipients = list(
        (
            await db.scalars(
                select(OrganizationAwardRecipient)
                .where(OrganizationAwardRecipient.program_id == program_id)
                .order_by(
                    OrganizationAwardRecipient.awarded_on.desc(),
                    OrganizationAwardRecipient.created_at.desc(),
                )
            )
        ).all()
    )
    return [
        (
            recipient,
            await member_subject_label(
                db,
                recipient.recipient_subject_type,
                recipient.recipient_subject_id,
            ),
        )
        for recipient in recipients
    ]


async def get_award_program_for_manage(
    db: AsyncSession,
    identity: CurrentIdentity,
    program_id: UUID,
    authz: AuthorizationService,
) -> OrganizationAwardProgram:
    program = await db.get(OrganizationAwardProgram, program_id)
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Award program not found")
    await ensure_manage_organization(db, identity, program.organization_id, authz)
    return program


async def get_award_category_for_manage(
    db: AsyncSession,
    identity: CurrentIdentity,
    category_id: UUID,
    authz: AuthorizationService,
) -> OrganizationAwardCategory:
    category = await db.get(OrganizationAwardCategory, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Award category not found")
    await ensure_manage_organization(db, identity, category.organization_id, authz)
    return category


async def get_award_nomination_for_manage(
    db: AsyncSession,
    identity: CurrentIdentity,
    nomination_id: UUID,
    authz: AuthorizationService,
) -> OrganizationAwardNomination:
    nomination = await db.get(OrganizationAwardNomination, nomination_id)
    if nomination is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Award nomination not found")
    await ensure_manage_organization(db, identity, nomination.organization_id, authz)
    return nomination


async def scalar_count_for(db: AsyncSession, column, value: UUID) -> int:
    return int(await db.scalar(select(func.count()).where(column == value)) or 0)


async def next_award_certificate_number(db: AsyncSession, organization_id: UUID) -> str:
    count = await scalar_count_for(db, OrganizationAwardRecipient.organization_id, organization_id)
    return f"AFROLETE-AWARD-{str(organization_id)[:8].upper()}-{count + 1:04d}"


async def create_data_migration_project(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: OrganizationDataMigrationProjectCreate,
    authz: AuthorizationService,
) -> OrganizationDataMigrationProject:
    await ensure_manage_organization(db, identity, organization_id, authz)
    if payload.owner_person_id is not None and await db.get(Person, payload.owner_person_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Migration owner not found")
    project = OrganizationDataMigrationProject(
        organization_id=organization_id,
        **payload.model_dump(),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def list_data_migration_projects(
    db: AsyncSession,
    organization_id: UUID,
) -> list[tuple[OrganizationDataMigrationProject, int]]:
    projects = list(
        (
            await db.scalars(
                select(OrganizationDataMigrationProject)
                .where(OrganizationDataMigrationProject.organization_id == organization_id)
                .order_by(
                    OrganizationDataMigrationProject.status,
                    OrganizationDataMigrationProject.created_at.desc(),
                )
            )
        ).all()
    )
    return [
        (project, await scalar_count_for(db, OrganizationDataMigrationRun.project_id, project.id))
        for project in projects
    ]


async def get_data_migration_project_for_manage(
    db: AsyncSession,
    identity: CurrentIdentity,
    project_id: UUID,
    authz: AuthorizationService,
) -> OrganizationDataMigrationProject:
    project = await db.get(OrganizationDataMigrationProject, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data migration project not found")
    await ensure_manage_organization(db, identity, project.organization_id, authz)
    return project


async def create_data_migration_run(
    db: AsyncSession,
    identity: CurrentIdentity,
    project_id: UUID,
    payload: OrganizationDataMigrationRunCreate,
    authz: AuthorizationService,
) -> tuple[OrganizationDataMigrationRun, OrganizationDataMigrationProject]:
    project = await get_data_migration_project_for_manage(db, identity, project_id, authz)
    run = OrganizationDataMigrationRun(
        organization_id=project.organization_id,
        project_id=project.id,
        **payload.model_dump(),
    )
    db.add(run)
    project.error_count += payload.error_count
    if payload.status in {"succeeded", "partial"} and payload.run_type in {"import", "reconciliation"}:
        project.records_imported += payload.records_created + payload.records_updated
    if payload.status == "running":
        project.status = "importing" if payload.run_type == "import" else "validating"
        project.started_at = project.started_at or payload.started_at or datetime.now(UTC)
    elif payload.status == "failed":
        project.status = "blocked"
    elif payload.status == "succeeded" and payload.run_type == "reconciliation":
        project.status = "completed"
        project.completed_at = payload.finished_at or datetime.now(UTC)
    elif payload.status in {"succeeded", "partial"} and payload.run_type == "import":
        project.status = "reconciled" if payload.status == "succeeded" and payload.error_count == 0 else "validating"
    elif payload.run_type in {"mapping_preview", "validation", "dry_run"} and payload.status in {"succeeded", "partial"}:
        project.status = "validating"
    await db.commit()
    await db.refresh(run)
    await db.refresh(project)
    return run, project


async def list_data_migration_runs(
    db: AsyncSession,
    identity: CurrentIdentity,
    project_id: UUID,
    authz: AuthorizationService,
) -> list[OrganizationDataMigrationRun]:
    project = await get_data_migration_project_for_manage(db, identity, project_id, authz)
    return list(
        (
            await db.scalars(
                select(OrganizationDataMigrationRun)
                .where(OrganizationDataMigrationRun.project_id == project.id)
                .order_by(OrganizationDataMigrationRun.created_at.desc())
            )
        ).all()
    )


async def create_recovery_plan(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: OrganizationRecoveryPlanCreate,
    authz: AuthorizationService,
) -> OrganizationRecoveryPlan:
    await ensure_manage_organization(db, identity, organization_id, authz)
    plan = OrganizationRecoveryPlan(
        organization_id=organization_id,
        **payload.model_dump(),
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def list_recovery_plans(
    db: AsyncSession,
    organization_id: UUID,
) -> list[tuple[OrganizationRecoveryPlan, int]]:
    plans = list(
        (
            await db.scalars(
                select(OrganizationRecoveryPlan)
                .where(OrganizationRecoveryPlan.organization_id == organization_id)
                .order_by(OrganizationRecoveryPlan.status, OrganizationRecoveryPlan.name)
            )
        ).all()
    )
    return [
        (plan, await scalar_count_for(db, OrganizationRecoveryDrill.recovery_plan_id, plan.id))
        for plan in plans
    ]


async def get_recovery_plan_for_manage(
    db: AsyncSession,
    identity: CurrentIdentity,
    recovery_plan_id: UUID,
    authz: AuthorizationService,
) -> OrganizationRecoveryPlan:
    plan = await db.get(OrganizationRecoveryPlan, recovery_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recovery plan not found")
    await ensure_manage_organization(db, identity, plan.organization_id, authz)
    return plan


async def create_recovery_drill(
    db: AsyncSession,
    identity: CurrentIdentity,
    recovery_plan_id: UUID,
    payload: OrganizationRecoveryDrillCreate,
    authz: AuthorizationService,
) -> tuple[OrganizationRecoveryDrill, OrganizationRecoveryPlan]:
    plan = await get_recovery_plan_for_manage(db, identity, recovery_plan_id, authz)
    drill = OrganizationRecoveryDrill(
        organization_id=plan.organization_id,
        recovery_plan_id=plan.id,
        **payload.model_dump(),
    )
    db.add(drill)
    if payload.status in {"passed", "failed", "blocked"}:
        plan.last_tested_at = payload.finished_at or datetime.now(UTC)
        plan.status = "active" if payload.status == "passed" else "failed"
    elif payload.status == "running":
        plan.status = "testing"
    await db.commit()
    await db.refresh(drill)
    await db.refresh(plan)
    return drill, plan


async def list_recovery_drills(
    db: AsyncSession,
    identity: CurrentIdentity,
    recovery_plan_id: UUID,
    authz: AuthorizationService,
) -> list[OrganizationRecoveryDrill]:
    plan = await get_recovery_plan_for_manage(db, identity, recovery_plan_id, authz)
    return list(
        (
            await db.scalars(
                select(OrganizationRecoveryDrill)
                .where(OrganizationRecoveryDrill.recovery_plan_id == plan.id)
                .order_by(OrganizationRecoveryDrill.created_at.desc())
            )
        ).all()
    )


def document_days_until_expiry(document: OrganizationComplianceDocument, today: date | None = None) -> int | None:
    if document.expires_on is None:
        return None
    return (document.expires_on - (today or date.today())).days


async def create_compliance_document(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: OrganizationComplianceDocumentCreate,
    authz: AuthorizationService,
) -> OrganizationComplianceDocument:
    await ensure_manage_organization(db, identity, organization_id, authz)
    if payload.owner_person_id is not None and await db.get(Person, payload.owner_person_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document owner not found")
    document = OrganizationComplianceDocument(
        organization_id=organization_id,
        **payload.model_dump(),
    )
    if payload.expires_on is not None and payload.expires_on < date.today():
        document.status = "expired"
    db.add(document)
    await db.flush()
    if payload.storage_url or payload.checksum:
        db.add(
            OrganizationComplianceDocumentVersion(
                organization_id=organization_id,
                document_id=document.id,
                version_number=1,
                storage_url=payload.storage_url,
                checksum=payload.checksum,
                change_summary="Initial document registration.",
                uploaded_by_person_id=identity.person_id,
                verified_by_person_id=identity.person_id if document.status == "verified" else None,
                verified_at=datetime.now(UTC) if document.status == "verified" else None,
                status="current",
            )
        )
    await db.commit()
    await db.refresh(document)
    return document


async def list_compliance_documents(
    db: AsyncSession,
    organization_id: UUID,
) -> list[tuple[OrganizationComplianceDocument, int]]:
    documents = list(
        (
            await db.scalars(
                select(OrganizationComplianceDocument)
                .where(OrganizationComplianceDocument.organization_id == organization_id)
                .order_by(
                    OrganizationComplianceDocument.status,
                    OrganizationComplianceDocument.expires_on,
                    OrganizationComplianceDocument.title,
                )
            )
        ).all()
    )
    return [
        (
            document,
            await scalar_count_for(db, OrganizationComplianceDocumentVersion.document_id, document.id),
        )
        for document in documents
    ]


async def get_compliance_document_for_manage(
    db: AsyncSession,
    identity: CurrentIdentity,
    document_id: UUID,
    authz: AuthorizationService,
) -> OrganizationComplianceDocument:
    document = await db.get(OrganizationComplianceDocument, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance document not found")
    await ensure_manage_organization(db, identity, document.organization_id, authz)
    return document


async def create_compliance_document_version(
    db: AsyncSession,
    identity: CurrentIdentity,
    document_id: UUID,
    payload: OrganizationComplianceDocumentVersionCreate,
    authz: AuthorizationService,
) -> tuple[OrganizationComplianceDocumentVersion, OrganizationComplianceDocument]:
    document = await get_compliance_document_for_manage(db, identity, document_id, authz)
    current_versions = list(
        (
            await db.scalars(
                select(OrganizationComplianceDocumentVersion).where(
                    OrganizationComplianceDocumentVersion.document_id == document.id
                )
            )
        ).all()
    )
    next_version = max((version.version_number for version in current_versions), default=0) + 1
    for version in current_versions:
        if version.status == "current":
            version.status = "superseded"
    version = OrganizationComplianceDocumentVersion(
        organization_id=document.organization_id,
        document_id=document.id,
        version_number=next_version,
        uploaded_by_person_id=identity.person_id,
        verified_by_person_id=identity.person_id if payload.status == "current" and document.status == "verified" else None,
        verified_at=datetime.now(UTC) if payload.status == "current" and document.status == "verified" else None,
        **payload.model_dump(),
    )
    db.add(version)
    document.current_version = next_version
    if payload.storage_url:
        document.storage_url = payload.storage_url
    if payload.checksum:
        document.checksum = payload.checksum
    if payload.status == "current" and document.status == "draft":
        document.status = "pending_review"
    await db.commit()
    await db.refresh(version)
    await db.refresh(document)
    return version, document


async def list_compliance_document_versions(
    db: AsyncSession,
    identity: CurrentIdentity,
    document_id: UUID,
    authz: AuthorizationService,
) -> list[OrganizationComplianceDocumentVersion]:
    document = await get_compliance_document_for_manage(db, identity, document_id, authz)
    return list(
        (
            await db.scalars(
                select(OrganizationComplianceDocumentVersion)
                .where(OrganizationComplianceDocumentVersion.document_id == document.id)
                .order_by(OrganizationComplianceDocumentVersion.version_number.desc())
            )
        ).all()
    )


async def compliance_document_summary(
    db: AsyncSession,
    organization_id: UUID,
) -> OrganizationComplianceDocumentSummaryRead:
    today = date.today()
    documents = [document for document, _ in await list_compliance_documents(db, organization_id)]
    category_counts: dict[str, int] = {}
    renewal_status_counts: dict[str, int] = {}
    for document in documents:
        category_counts[document.category] = category_counts.get(document.category, 0) + 1
        renewal_status_counts[document.renewal_status] = renewal_status_counts.get(document.renewal_status, 0) + 1
    return OrganizationComplianceDocumentSummaryRead(
        organization_id=organization_id,
        total_documents=len(documents),
        verified_documents=sum(1 for document in documents if document.status == "verified"),
        expired_documents=sum(
            1
            for document in documents
            if document.status == "expired" or (document.expires_on is not None and document.expires_on < today)
        ),
        expiring_soon_documents=sum(
            1
            for document in documents
            if document.expires_on is not None and 0 <= (document.expires_on - today).days <= 90
        ),
        auto_renewal_documents=sum(1 for document in documents if document.auto_renewal_enabled),
        category_counts=category_counts,
        renewal_status_counts=renewal_status_counts,
    )


async def create_member_subscription_plan(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: MemberSubscriptionPlanCreate,
    authz: AuthorizationService,
) -> MemberSubscriptionPlan:
    await ensure_manage_organization(db, identity, organization_id, authz)
    plan = MemberSubscriptionPlan(
        organization_id=organization_id,
        name=payload.name,
        description=payload.description,
        member_role=payload.member_role,
        amount=payload.amount,
        currency=payload.currency.upper(),
        billing_interval=payload.billing_interval,
        due_day=payload.due_day,
        grace_period_days=payload.grace_period_days,
        benefits=payload.benefits,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def list_member_subscription_plans(
    db: AsyncSession,
    organization_id: UUID,
) -> list[MemberSubscriptionPlan]:
    return list(
        (
            await db.scalars(
                select(MemberSubscriptionPlan)
                .where(MemberSubscriptionPlan.organization_id == organization_id)
                .order_by(MemberSubscriptionPlan.status, MemberSubscriptionPlan.name)
            )
        ).all()
    )


async def create_member_subscription(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: MemberSubscriptionCreate,
    authz: AuthorizationService,
) -> MemberSubscription:
    await ensure_manage_organization(db, identity, organization_id, authz)
    plan = await db.get(MemberSubscriptionPlan, payload.plan_id)
    if plan is None or plan.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member subscription plan not found")

    membership_id = payload.membership_id
    subject_type = payload.subject_type
    subject_id = payload.subject_id
    if membership_id is not None:
        membership = await db.get(Membership, membership_id)
        if membership is None or membership.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
        subject_type = membership.subject_type
        subject_id = membership.subject_id
    else:
        if subject_type is None or subject_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Member subscription requires membership_id or subject_type and subject_id",
            )
        membership = await db.scalar(
            select(Membership).where(
                Membership.organization_id == organization_id,
                Membership.subject_type == subject_type,
                Membership.subject_id == subject_id,
                Membership.status == "active",
            )
        )
        membership_id = membership.id if membership else None

    if subject_type is None or subject_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Missing subscription subject")
    await ensure_member_subject_exists(db, subject_type, subject_id)

    subscription = MemberSubscription(
        organization_id=organization_id,
        plan_id=plan.id,
        membership_id=membership_id,
        subject_type=subject_type,
        subject_id=subject_id,
        starts_on=payload.starts_on,
        current_period_start=payload.current_period_start,
        current_period_end=payload.current_period_end,
        next_due_on=payload.next_due_on,
        status=payload.status,
        balance_amount=payload.balance_amount if payload.balance_amount is not None else plan.amount,
        external_reference=payload.external_reference,
        notes=payload.notes,
    )
    db.add(subscription)
    await db.flush()
    initial_balance = subscription.balance_amount.quantize(Decimal("0.01"))
    if initial_balance > 0:
        db.add(
            MemberSubscriptionCharge(
                organization_id=organization_id,
                subscription_id=subscription.id,
                plan_id=plan.id,
                period_start=subscription.current_period_start,
                period_end=subscription.current_period_end,
                due_on=subscription.next_due_on,
                amount=initial_balance,
                amount_paid=Decimal("0.00"),
                balance_amount=initial_balance,
                currency=plan.currency.upper(),
                status="open",
                source="initial_subscription",
                description=f"Initial member dues charge for {plan.name}",
                created_by_person_id=identity.person_id,
            )
        )
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def list_member_subscriptions(
    db: AsyncSession,
    organization_id: UUID,
) -> list[tuple[MemberSubscription, MemberSubscriptionPlan, str | None]]:
    rows = (
        await db.execute(
            select(MemberSubscription, MemberSubscriptionPlan)
            .join(MemberSubscriptionPlan, MemberSubscriptionPlan.id == MemberSubscription.plan_id)
            .where(MemberSubscription.organization_id == organization_id)
            .order_by(MemberSubscription.status, MemberSubscription.next_due_on, MemberSubscription.created_at.desc())
        )
    ).all()
    result: list[tuple[MemberSubscription, MemberSubscriptionPlan, str | None]] = []
    for subscription, plan in rows:
        result.append((subscription, plan, await member_subject_label(db, subscription.subject_type, subscription.subject_id)))
    return result


async def list_member_subscription_charges(
    db: AsyncSession,
    organization_id: UUID,
    subscription_id: UUID | None = None,
) -> list[tuple[MemberSubscriptionCharge, MemberSubscription, MemberSubscriptionPlan, str | None]]:
    statement = (
        select(MemberSubscriptionCharge, MemberSubscription, MemberSubscriptionPlan)
        .join(MemberSubscription, MemberSubscription.id == MemberSubscriptionCharge.subscription_id)
        .join(MemberSubscriptionPlan, MemberSubscriptionPlan.id == MemberSubscriptionCharge.plan_id)
        .where(MemberSubscriptionCharge.organization_id == organization_id)
        .order_by(MemberSubscriptionCharge.due_on.desc(), MemberSubscriptionCharge.created_at.desc())
    )
    if subscription_id is not None:
        statement = statement.where(MemberSubscriptionCharge.subscription_id == subscription_id)
    rows = (await db.execute(statement)).all()
    result: list[tuple[MemberSubscriptionCharge, MemberSubscription, MemberSubscriptionPlan, str | None]] = []
    for charge, subscription, plan in rows:
        result.append(
            (
                charge,
                subscription,
                plan,
                await member_subject_label(db, subscription.subject_type, subscription.subject_id),
            )
        )
    return result


async def record_member_subscription_payment(
    db: AsyncSession,
    identity: CurrentIdentity,
    subscription_id: UUID,
    payload: MemberSubscriptionPaymentCreate,
    authz: AuthorizationService,
) -> tuple[MemberSubscriptionPayment, MemberSubscription]:
    subscription = await db.get(MemberSubscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member subscription not found")
    await ensure_manage_organization(db, identity, subscription.organization_id, authz)
    plan = await db.get(MemberSubscriptionPlan, subscription.plan_id)
    currency = (payload.currency or (plan.currency if plan else "KES")).upper()
    payment = MemberSubscriptionPayment(
        organization_id=subscription.organization_id,
        subscription_id=subscription.id,
        amount=payload.amount,
        currency=currency,
        provider=payload.provider,
        method=payload.method,
        external_payment_id=payload.external_payment_id,
        received_at=payload.received_at or datetime.now(UTC),
        status=payload.status,
        raw_reference=payload.raw_reference,
        notes=payload.notes,
    )
    db.add(payment)
    if payload.status == "succeeded":
        await db.flush()
        await apply_member_subscription_payment_to_charges(
            db,
            subscription,
            payload.amount,
            payment.id,
            payment.received_at,
        )
        subscription.balance_amount = max(Decimal("0"), subscription.balance_amount - payload.amount)
        if subscription.balance_amount == Decimal("0") and subscription.status == "past_due":
            subscription.status = "active"
        await mark_member_subscription_charges_paid_if_settled(db, subscription, payment.id, payment.received_at)
    await db.commit()
    await db.refresh(payment)
    await db.refresh(subscription)
    return payment, subscription


async def create_member_subscription_checkout_link(
    db: AsyncSession,
    identity: CurrentIdentity,
    subscription_id: UUID,
    provider: str,
    checkout_base_url: str,
    authz: AuthorizationService,
) -> MemberSubscriptionCheckoutLinkRead:
    subscription, plan, subject_label = await get_member_subscription_checkout_subject(db, subscription_id)
    await ensure_manage_organization(db, identity, subscription.organization_id, authz)
    normalized_provider = normalize_payment_provider(provider)
    session_id = member_subscription_checkout_session_id(subscription, normalized_provider)
    return MemberSubscriptionCheckoutLinkRead(
        subscription_id=subscription.id,
        provider=normalized_provider,
        session_id=session_id,
        checkout_url=member_subscription_checkout_session_url(
            checkout_base_url,
            session_id,
            subscription,
            normalized_provider,
        ),
        hosted_checkout=member_subscription_hosted_checkout_read(
            subscription,
            plan,
            subject_label,
            normalized_provider,
            session_id,
        ),
    )


async def get_member_subscription_hosted_checkout(
    db: AsyncSession,
    session_id: str,
    subscription_id: UUID,
    provider: str,
) -> MemberSubscriptionHostedCheckoutRead:
    subscription, plan, subject_label = await get_member_subscription_checkout_subject(db, subscription_id)
    normalized_provider = normalize_payment_provider(provider)
    expected_session_id = member_subscription_checkout_session_id(subscription, normalized_provider)
    if session_id != expected_session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member dues checkout session not found")
    return member_subscription_hosted_checkout_read(
        subscription,
        plan,
        subject_label,
        normalized_provider,
        session_id,
    )


async def settle_member_subscription_checkout(
    db: AsyncSession,
    session_id: str,
    payload: MemberSubscriptionCheckoutSettlementCreate,
) -> MemberSubscriptionCheckoutSettlementRead:
    subscription, plan, _subject_label = await get_member_subscription_checkout_subject(db, payload.subscription_id)
    normalized_provider = normalize_payment_provider(payload.provider)
    expected_session_id = member_subscription_checkout_session_id(subscription, normalized_provider)
    if session_id != expected_session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member dues checkout session not found")
    currency = (payload.currency or plan.currency or "KES").upper()
    if currency != plan.currency.upper():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Currency mismatch")
    open_amount = member_subscription_open_amount(subscription)
    if open_amount <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member dues subscription is already paid")
    amount = (payload.amount or open_amount).quantize(Decimal("0.01"))
    if amount <= 0 or amount > open_amount:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Payment exceeds dues balance")

    payment_id: UUID | None = None
    accepted = payload.status == "succeeded"
    payment = MemberSubscriptionPayment(
        organization_id=subscription.organization_id,
        subscription_id=subscription.id,
        amount=amount,
        currency=currency,
        provider=normalized_provider,
        method=payload.method,
        external_payment_id=payload.external_payment_id or f"{normalized_provider}:{session_id}",
        received_at=datetime.now(UTC),
        status=payload.status,
        raw_reference=payload.raw_reference,
        notes=f"Hosted member dues checkout {session_id}",
    )
    db.add(payment)
    if accepted:
        await db.flush()
        await apply_member_subscription_payment_to_charges(
            db,
            subscription,
            amount,
            payment.id,
            payment.received_at,
        )
        subscription.balance_amount = member_subscription_open_amount(subscription) - amount
        if subscription.balance_amount <= 0:
            subscription.balance_amount = Decimal("0.00")
            if subscription.status == "past_due":
                subscription.status = "active"
            await mark_member_subscription_charges_paid_if_settled(db, subscription, payment.id, payment.received_at)
    elif payload.status == "pending" and subscription.status == "active":
        subscription.notes = append_member_dues_note(subscription.notes, f"Pending hosted dues payment {session_id}.")
    await db.commit()
    await db.refresh(payment)
    await db.refresh(subscription)
    payment_id = payment.id
    return MemberSubscriptionCheckoutSettlementRead(
        subscription_id=subscription.id,
        provider=normalized_provider,
        accepted=accepted,
        payment_id=payment_id,
        subscription_status=subscription.status,
        amount_paid=(plan.amount - member_subscription_open_amount(subscription)).quantize(Decimal("0.01")),
        open_amount=member_subscription_open_amount(subscription),
        session_status=member_subscription_checkout_session_status(subscription),
        message=(
            "Member dues payment recorded for the club."
            if accepted
            else f"Member dues payment marked {payload.status}."
        ),
    )


async def run_member_subscription_charge_generation(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: MemberSubscriptionChargeRunCreate,
    authz: AuthorizationService,
) -> MemberSubscriptionChargeRunRead:
    await ensure_manage_organization(db, identity, payload.organization_id, authz)
    return await run_member_subscription_charge_worker(
        db,
        organization_id=payload.organization_id,
        charge_on=payload.charge_on,
        limit=payload.limit,
        dry_run=payload.dry_run,
        created_by_person_id=identity.person_id,
    )


async def run_member_subscription_charge_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    charge_on: date | None = None,
    limit: int = 100,
    dry_run: bool = False,
    created_by_person_id: UUID | None = None,
) -> MemberSubscriptionChargeRunRead:
    effective_charge_on = charge_on or date.today()
    rows = await member_subscriptions_due_for_charge(
        db,
        organization_id=organization_id,
        charge_on=effective_charge_on,
        limit=limit,
    )
    items: list[MemberSubscriptionChargeRunItemRead] = []
    subscription_ids: list[UUID] = []
    charge_ids: list[UUID] = []
    total_charged = Decimal("0.00")
    executed_count = 0
    skipped_count = 0
    failed_count = 0

    for subscription, plan in rows:
        executed_count += 1
        subject_label = await member_subject_label(db, subscription.subject_type, subscription.subject_id)
        if plan.billing_interval == "one_time":
            skipped_count += 1
            items.append(
                member_subscription_charge_run_item(
                    subscription,
                    plan,
                    subject_label,
                    None,
                    action="skipped",
                    reason="One-time member dues plans do not generate recurring charges.",
                )
            )
            continue
        period_start, period_end = next_member_subscription_period(subscription, plan)
        due_on = member_subscription_charge_due_on(plan, period_start, period_end)
        existing = await db.scalar(
            select(MemberSubscriptionCharge).where(
                MemberSubscriptionCharge.subscription_id == subscription.id,
                MemberSubscriptionCharge.period_start == period_start,
                MemberSubscriptionCharge.period_end == period_end,
            )
        )
        if existing is not None:
            skipped_count += 1
            items.append(
                member_subscription_charge_run_item(
                    subscription,
                    plan,
                    subject_label,
                    existing,
                    action="skipped",
                    reason="Charge already exists for this member dues period.",
                )
            )
            continue
        if dry_run:
            skipped_count += 1
            items.append(
                MemberSubscriptionChargeRunItemRead(
                    subscription_id=subscription.id,
                    charge_id=None,
                    plan_name=plan.name,
                    subject_label=subject_label,
                    period_start=period_start,
                    period_end=period_end,
                    due_on=due_on,
                    amount=plan.amount.quantize(Decimal("0.01")),
                    currency=plan.currency.upper(),
                    action="dry_run",
                    reason="Would create a club-managed member dues charge.",
                )
            )
            continue
        try:
            charge = MemberSubscriptionCharge(
                organization_id=subscription.organization_id,
                subscription_id=subscription.id,
                plan_id=plan.id,
                period_start=period_start,
                period_end=period_end,
                due_on=due_on,
                amount=plan.amount,
                amount_paid=Decimal("0.00"),
                balance_amount=plan.amount,
                currency=plan.currency.upper(),
                status="open",
                source="recurring_cycle",
                description=f"Recurring member dues charge for {plan.name}",
                created_by_person_id=created_by_person_id,
            )
            db.add(charge)
            open_before = member_subscription_open_amount(subscription)
            subscription.current_period_start = period_start
            subscription.current_period_end = period_end
            subscription.next_due_on = due_on
            subscription.balance_amount = (open_before + plan.amount).quantize(Decimal("0.01"))
            if subscription.status == "past_due" and open_before > 0:
                subscription.status = "past_due"
            else:
                subscription.status = "active"
            await db.commit()
            await db.refresh(charge)
            await db.refresh(subscription)
            subscription_ids.append(subscription.id)
            charge_ids.append(charge.id)
            total_charged += charge.amount
            items.append(
                member_subscription_charge_run_item(
                    subscription,
                    plan,
                    subject_label,
                    charge,
                    action="charged",
                    reason="Recurring club member dues charge created.",
                )
            )
        except Exception:
            failed_count += 1
            await db.rollback()
            items.append(
                MemberSubscriptionChargeRunItemRead(
                    subscription_id=subscription.id,
                    charge_id=None,
                    plan_name=plan.name,
                    subject_label=subject_label,
                    period_start=period_start,
                    period_end=period_end,
                    due_on=due_on,
                    amount=plan.amount.quantize(Decimal("0.01")),
                    currency=plan.currency.upper(),
                    action="failed",
                    reason="Failed to create member dues charge.",
                )
            )

    return MemberSubscriptionChargeRunRead(
        organization_id=organization_id,
        charge_on=effective_charge_on,
        eligible_count=len(rows),
        executed_count=executed_count,
        charged_count=len(charge_ids),
        skipped_count=skipped_count,
        failed_count=failed_count,
        dry_run=dry_run,
        subscription_ids=subscription_ids,
        charge_ids=charge_ids,
        total_charged=total_charged.quantize(Decimal("0.01")),
        items=items,
    )


async def member_subscriptions_due_for_charge(
    db: AsyncSession,
    *,
    organization_id: UUID | None,
    charge_on: date,
    limit: int,
) -> list[tuple[MemberSubscription, MemberSubscriptionPlan]]:
    statement = (
        select(MemberSubscription, MemberSubscriptionPlan)
        .join(MemberSubscriptionPlan, MemberSubscriptionPlan.id == MemberSubscription.plan_id)
        .where(MemberSubscription.status.in_(["trialing", "active", "past_due"]))
        .where(MemberSubscriptionPlan.billing_interval != "one_time")
        .where(MemberSubscription.current_period_end < charge_on)
        .order_by(MemberSubscription.current_period_end.asc(), MemberSubscription.created_at.asc())
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(MemberSubscription.organization_id == organization_id)
    return list((await db.execute(statement)).all())


def next_member_subscription_period(
    subscription: MemberSubscription,
    plan: MemberSubscriptionPlan,
) -> tuple[date, date]:
    period_start = subscription.current_period_end + timedelta(days=1)
    interval = plan.billing_interval
    if interval == "weekly":
        return period_start, period_start + timedelta(days=6)
    months = {
        "monthly": 1,
        "quarterly": 3,
        "term": 3,
        "season": 12,
        "annual": 12,
    }.get(interval, 1)
    return period_start, add_months(period_start, months) - timedelta(days=1)


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def member_subscription_charge_due_on(
    plan: MemberSubscriptionPlan,
    period_start: date,
    period_end: date,
) -> date:
    if plan.due_day is None:
        return period_start
    due_day = min(plan.due_day, monthrange(period_start.year, period_start.month)[1])
    due_on = date(period_start.year, period_start.month, due_day)
    if due_on < period_start:
        return period_start
    if due_on > period_end:
        return period_end
    return due_on


async def apply_member_subscription_payment_to_charges(
    db: AsyncSession,
    subscription: MemberSubscription,
    amount: Decimal,
    payment_id: UUID,
    paid_at: datetime,
) -> Decimal:
    remaining = amount.quantize(Decimal("0.01"))
    allocated = Decimal("0.00")
    if remaining <= 0:
        return allocated
    charges = (
        await db.scalars(
            select(MemberSubscriptionCharge)
            .where(MemberSubscriptionCharge.subscription_id == subscription.id)
            .where(MemberSubscriptionCharge.status.in_(["open", "partial"]))
            .where(MemberSubscriptionCharge.balance_amount > Decimal("0"))
            .order_by(MemberSubscriptionCharge.due_on.asc().nulls_last(), MemberSubscriptionCharge.created_at.asc())
        )
    ).all()
    for charge in charges:
        if remaining <= 0:
            break
        charge_balance = max(charge.balance_amount, Decimal("0.00")).quantize(Decimal("0.01"))
        if charge_balance <= 0:
            continue
        applied = min(charge_balance, remaining).quantize(Decimal("0.01"))
        charge.amount_paid = (charge.amount_paid + applied).quantize(Decimal("0.01"))
        charge.balance_amount = (charge_balance - applied).quantize(Decimal("0.01"))
        charge.last_payment_id = payment_id
        if charge.balance_amount <= 0:
            charge.balance_amount = Decimal("0.00")
            charge.status = "paid"
            charge.paid_at = paid_at
        else:
            charge.status = "partial"
        remaining = (remaining - applied).quantize(Decimal("0.01"))
        allocated = (allocated + applied).quantize(Decimal("0.01"))
    return allocated


async def mark_member_subscription_charges_paid_if_settled(
    db: AsyncSession,
    subscription: MemberSubscription,
    payment_id: UUID | None = None,
    paid_at: datetime | None = None,
) -> None:
    if member_subscription_open_amount(subscription) > 0:
        return
    charges = (
        await db.scalars(
            select(MemberSubscriptionCharge)
            .where(MemberSubscriptionCharge.subscription_id == subscription.id)
            .where(MemberSubscriptionCharge.status.in_(["open", "partial"]))
        )
    ).all()
    for charge in charges:
        charge.amount_paid = charge.amount
        charge.balance_amount = Decimal("0.00")
        charge.status = "paid"
        charge.last_payment_id = payment_id or charge.last_payment_id
        charge.paid_at = paid_at or charge.paid_at


def member_subscription_charge_run_item(
    subscription: MemberSubscription,
    plan: MemberSubscriptionPlan,
    subject_label: str | None,
    charge: MemberSubscriptionCharge | None,
    *,
    action: str,
    reason: str,
) -> MemberSubscriptionChargeRunItemRead:
    return MemberSubscriptionChargeRunItemRead(
        subscription_id=subscription.id,
        charge_id=charge.id if charge else None,
        plan_name=plan.name,
        subject_label=subject_label,
        period_start=charge.period_start if charge else None,
        period_end=charge.period_end if charge else None,
        due_on=charge.due_on if charge else None,
        amount=(charge.amount if charge else plan.amount).quantize(Decimal("0.01")),
        currency=(charge.currency if charge else plan.currency).upper(),
        action=action,
        reason=reason,
    )


async def get_member_subscription_checkout_subject(
    db: AsyncSession,
    subscription_id: UUID,
) -> tuple[MemberSubscription, MemberSubscriptionPlan, str | None]:
    subscription = await db.get(MemberSubscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member subscription not found")
    plan = await db.get(MemberSubscriptionPlan, subscription.plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member subscription plan not found")
    return (
        subscription,
        plan,
        await member_subject_label(db, subscription.subject_type, subscription.subject_id),
    )


def member_subscription_checkout_session_id(subscription: MemberSubscription, provider: str) -> str:
    token = sha256(
        (
            f"member-dues:{subscription.id}:{subscription.organization_id}:"
            f"{subscription.current_period_end}:{provider.casefold()}"
        ).encode()
    ).hexdigest()
    provider_token = re.sub(r"[^a-z0-9]+", "-", provider.lower()).strip("-")[:24] or "processor"
    return f"mdues_{provider_token}_{token[:24]}"


def member_subscription_checkout_session_url(
    base_url: str,
    session_id: str,
    subscription: MemberSubscription,
    provider: str,
) -> str:
    return (
        f"{base_url.rstrip('/')}/{session_id}"
        f"?kind=member_dues&subscription_id={subscription.id}&provider={quote(provider, safe='')}"
    )


def member_subscription_open_amount(subscription: MemberSubscription) -> Decimal:
    return max(subscription.balance_amount, Decimal("0.00")).quantize(Decimal("0.01"))


def member_subscription_checkout_session_status(subscription: MemberSubscription) -> str:
    return "paid" if member_subscription_open_amount(subscription) <= 0 else "ready"


def member_subscription_hosted_checkout_read(
    subscription: MemberSubscription,
    plan: MemberSubscriptionPlan,
    subject_label: str | None,
    provider: str,
    session_id: str,
) -> MemberSubscriptionHostedCheckoutRead:
    open_amount = member_subscription_open_amount(subscription)
    paid_amount = max(plan.amount - open_amount, Decimal("0.00")).quantize(Decimal("0.01"))
    display_subject = subject_label or f"{subscription.subject_type.value}:{subscription.subject_id}"
    title = f"{plan.name} for {display_subject}"
    return MemberSubscriptionHostedCheckoutRead(
        subscription_id=subscription.id,
        organization_id=subscription.organization_id,
        plan_id=plan.id,
        plan_name=plan.name,
        receivable_owner_type="tenant_organization",
        receivable_note=(
            "This is a club-managed member dues receivable collected for the tenant organization; "
            "it does not pay AfroLete platform hosting."
        ),
        platform_hosting_charge=False,
        subject_label=subject_label,
        dues_reference=subscription.external_reference or f"DUES-{str(subscription.id).split('-')[0].upper()}",
        title=title,
        memo=subscription.notes or plan.description or plan.benefits,
        due_on=subscription.next_due_on,
        amount_due=plan.amount.quantize(Decimal("0.01")),
        amount_paid=paid_amount,
        open_amount=open_amount,
        currency=plan.currency.upper(),
        status=subscription.status,
        provider=provider,
        session_id=session_id,
        session_status=member_subscription_checkout_session_status(subscription),
        client_reference=f"member-dues:{subscription.id}",
        payment_methods=["mobile_money", "mpesa_stk", "bank_transfer", "cash_office"],
        settlement_endpoint=f"/api/v1/organizations/member-subscription-checkout-sessions/{session_id}/settle",
        checkout_summary=(
            f"{title} has {open_amount} {plan.currency.upper()} outstanding for the club."
            if open_amount > 0
            else f"{title} is fully paid."
        ),
    )


def normalize_payment_provider(provider: str) -> str:
    return provider.strip().lower() or "mpesa"


def append_member_dues_note(existing: str | None, note: str) -> str:
    return f"{existing}\n{note}" if existing else note


async def run_member_subscription_reminders(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: MemberSubscriptionReminderRunCreate,
    authz: AuthorizationService,
) -> MemberSubscriptionReminderRunRead:
    await ensure_manage_organization(db, identity, payload.organization_id, authz)
    return await run_member_subscription_reminder_worker(
        db,
        organization_id=payload.organization_id,
        channel=payload.channel,
        as_of=payload.as_of,
        due_within_days=payload.due_within_days,
        repeat_after_days=payload.repeat_after_days,
        limit=payload.limit,
        dry_run=payload.dry_run,
    )


async def run_member_subscription_reminder_worker(
    db: AsyncSession,
    organization_id: UUID | None = None,
    *,
    channel: CommunicationChannel = CommunicationChannel.EMAIL,
    as_of: date | None = None,
    due_within_days: int = 7,
    repeat_after_days: int = 7,
    limit: int = 100,
    dry_run: bool = False,
) -> MemberSubscriptionReminderRunRead:
    effective_as_of = as_of or date.today()
    rows = await member_subscriptions_due_for_reminder(
        db,
        organization_id=organization_id,
        due_on_or_before=effective_as_of + timedelta(days=due_within_days),
        limit=limit,
    )
    items: list[MemberSubscriptionReminderItemRead] = []
    subscription_ids: list[UUID] = []
    message_ids: list[UUID] = []
    executed_count = 0
    skipped_count = 0
    failed_count = 0
    marked_past_due_count = 0

    for subscription, plan in rows:
        executed_count += 1
        subject_label = await member_subject_label(db, subscription.subject_type, subscription.subject_id)
        if member_subscription_recently_reminded(subscription, repeat_after_days):
            skipped_count += 1
            items.append(
                member_subscription_reminder_item(
                    subscription,
                    plan,
                    subject_label,
                    effective_as_of,
                    action="skipped",
                    reason=f"Dues reminder already sent within {repeat_after_days} days.",
                    message_id=subscription.dues_reminder_message_id,
                )
            )
            continue
        recipients = await member_subscription_reminder_recipients(db, subscription, channel)
        if not recipients:
            skipped_count += 1
            items.append(
                member_subscription_reminder_item(
                    subscription,
                    plan,
                    subject_label,
                    effective_as_of,
                    action="skipped",
                    reason=f"No dues reminder recipient has a destination for {channel.value}.",
                )
            )
            continue
        should_mark_past_due = member_subscription_should_mark_past_due(subscription, plan, effective_as_of)
        if dry_run:
            skipped_count += 1
            reason = f"Would remind {len(recipients)} recipient(s)."
            if should_mark_past_due:
                reason += " Would mark account past due."
            items.append(
                member_subscription_reminder_item(
                    subscription,
                    plan,
                    subject_label,
                    effective_as_of,
                    action="dry_run",
                    reason=reason,
                    recipient_count=len(recipients),
                )
            )
            continue
        try:
            message = await create_message_for_recipients(
                db,
                organization_id=subscription.organization_id,
                message_type=CommunicationMessageType.REMINDER,
                channel=channel,
                scope_type=CommunicationScopeType.PERSON
                if subscription.subject_type == MemberSubjectType.PERSON
                else CommunicationScopeType.ORGANIZATION,
                scope_id=subscription.subject_id
                if subscription.subject_type == MemberSubjectType.PERSON
                else subscription.organization_id,
                recipient_person_ids=[person.id for person in recipients],
                subject=f"Member dues reminder: {plan.name}",
                body=member_subscription_reminder_body(subscription, plan, subject_label, effective_as_of),
                urgent=(subscription.next_due_on is not None and subscription.next_due_on < effective_as_of),
                created_by_person_id=None,
            )
            if should_mark_past_due and subscription.status != "past_due":
                subscription.status = "past_due"
                marked_past_due_count += 1
            subscription.dues_last_reminded_at = datetime.now(UTC)
            subscription.dues_reminder_message_id = message.id
            subscription.dues_reminder_count = int(subscription.dues_reminder_count or 0) + 1
            await db.commit()
            await db.refresh(subscription)
            subscription_ids.append(subscription.id)
            message_ids.append(message.id)
            items.append(
                member_subscription_reminder_item(
                    subscription,
                    plan,
                    subject_label,
                    effective_as_of,
                    action="reminded",
                    reason=f"Dues reminder sent to {len(recipients)} recipient(s).",
                    recipient_count=len(recipients),
                    message_id=message.id,
                )
            )
        except Exception:
            failed_count += 1
            await db.rollback()
            items.append(
                member_subscription_reminder_item(
                    subscription,
                    plan,
                    subject_label,
                    effective_as_of,
                    action="failed",
                    reason="Failed to create dues reminder message.",
                    recipient_count=len(recipients),
                )
            )

    return MemberSubscriptionReminderRunRead(
        organization_id=organization_id,
        channel=channel,
        as_of=effective_as_of,
        due_within_days=due_within_days,
        repeat_after_days=repeat_after_days,
        eligible_count=len(rows),
        executed_count=executed_count,
        reminded_count=len(message_ids),
        skipped_count=skipped_count,
        failed_count=failed_count,
        marked_past_due_count=marked_past_due_count,
        dry_run=dry_run,
        subscription_ids=subscription_ids,
        message_ids=message_ids,
        items=items,
    )


async def member_subscriptions_due_for_reminder(
    db: AsyncSession,
    *,
    organization_id: UUID | None,
    due_on_or_before: date,
    limit: int,
) -> list[tuple[MemberSubscription, MemberSubscriptionPlan]]:
    statement = (
        select(MemberSubscription, MemberSubscriptionPlan)
        .join(MemberSubscriptionPlan, MemberSubscriptionPlan.id == MemberSubscription.plan_id)
        .where(MemberSubscription.status.in_(["trialing", "active", "past_due"]))
        .where(MemberSubscription.balance_amount > Decimal("0"))
        .where(MemberSubscription.next_due_on.is_not(None))
        .where(MemberSubscription.next_due_on <= due_on_or_before)
        .order_by(MemberSubscription.next_due_on.asc(), MemberSubscription.created_at.asc())
        .limit(limit)
    )
    if organization_id is not None:
        statement = statement.where(MemberSubscription.organization_id == organization_id)
    return list((await db.execute(statement)).all())


def member_subscription_recently_reminded(subscription: MemberSubscription, repeat_after_days: int) -> bool:
    if subscription.dues_last_reminded_at is None:
        return False
    if repeat_after_days <= 0:
        return False
    last_reminded = (
        subscription.dues_last_reminded_at.replace(tzinfo=UTC)
        if subscription.dues_last_reminded_at.tzinfo is None
        else subscription.dues_last_reminded_at.astimezone(UTC)
    )
    return last_reminded >= datetime.now(UTC) - timedelta(days=repeat_after_days)


def member_subscription_should_mark_past_due(
    subscription: MemberSubscription,
    plan: MemberSubscriptionPlan,
    as_of: date,
) -> bool:
    if subscription.next_due_on is None:
        return False
    return subscription.next_due_on + timedelta(days=plan.grace_period_days) < as_of


async def member_subscription_reminder_recipients(
    db: AsyncSession,
    subscription: MemberSubscription,
    channel: CommunicationChannel,
) -> list[Person]:
    recipients: list[Person] = []
    if subscription.subject_type == MemberSubjectType.PERSON:
        person = await db.get(Person, subscription.subject_id)
        if person is not None and (
            channel == CommunicationChannel.IN_APP or destination_for_channel(person, channel) is not None
        ):
            recipients.append(person)
    if recipients:
        return recipients
    managers = (
        await db.scalars(
            select(Person)
            .join(Membership, Membership.subject_id == Person.id)
            .where(Membership.organization_id == subscription.organization_id)
            .where(Membership.subject_type == MemberSubjectType.PERSON)
            .where(Membership.role.in_([MembershipRole.OWNER, MembershipRole.ADMIN, MembershipRole.STAFF]))
            .where(Membership.status == "active")
            .order_by(Membership.role.asc(), Person.display_name.asc())
        )
    ).all()
    for person in managers:
        if channel == CommunicationChannel.IN_APP or destination_for_channel(person, channel) is not None:
            recipients.append(person)
    unique: dict[UUID, Person] = {}
    for person in recipients:
        unique.setdefault(person.id, person)
    return list(unique.values())


def member_subscription_reminder_body(
    subscription: MemberSubscription,
    plan: MemberSubscriptionPlan,
    subject_label: str | None,
    as_of: date,
) -> str:
    open_amount = member_subscription_open_amount(subscription)
    due_line = (
        f"Due date: {subscription.next_due_on.isoformat()}."
        if subscription.next_due_on is not None
        else "No due date is currently recorded."
    )
    days_line = (
        f"Days until due: {(subscription.next_due_on - as_of).days}."
        if subscription.next_due_on is not None
        else "Days until due: not available."
    )
    dues_reference = subscription.external_reference or f"DUES-{str(subscription.id).split('-')[0].upper()}"
    return "\n".join(
        [
            f"{plan.name} has {open_amount} {plan.currency.upper()} outstanding for {subject_label or subscription.subject_id}.",
            due_line,
            days_line,
            f"Reference: {dues_reference}. This is a club-managed dues account, not an AfroLete hosting invoice.",
            "Use the member dues payment link, M-Pesa, bank transfer, or the club office to settle the balance.",
        ]
    )


def member_subscription_reminder_item(
    subscription: MemberSubscription,
    plan: MemberSubscriptionPlan,
    subject_label: str | None,
    as_of: date,
    *,
    action: str,
    reason: str,
    recipient_count: int = 0,
    message_id: UUID | None = None,
) -> MemberSubscriptionReminderItemRead:
    return MemberSubscriptionReminderItemRead(
        subscription_id=subscription.id,
        plan_name=plan.name,
        subject_label=subject_label,
        next_due_on=subscription.next_due_on,
        days_until_due=(subscription.next_due_on - as_of).days if subscription.next_due_on is not None else None,
        balance_amount=subscription.balance_amount,
        currency=plan.currency.upper(),
        recipient_count=recipient_count,
        action=action,
        reason=reason,
        message_id=message_id,
    )


async def create_organization_market_profile(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: OrganizationMarketProfileCreate,
    authz: AuthorizationService,
) -> OrganizationMarketProfileRead:
    await ensure_manage_organization(db, identity, organization_id, authz)
    profile = await db.scalar(
        select(OrganizationMarketProfile).where(
            OrganizationMarketProfile.organization_id == organization_id,
            OrganizationMarketProfile.country_code == payload.country_code.upper(),
            OrganizationMarketProfile.region_code == payload.region_code,
        )
    )
    values = organization_market_profile_values(payload)
    if profile is None:
        profile = OrganizationMarketProfile(organization_id=organization_id, **values)
        db.add(profile)
    else:
        for field, value in values.items():
            setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return organization_market_profile_read(profile)


async def list_organization_market_profiles(
    db: AsyncSession,
    organization_id: UUID,
) -> list[OrganizationMarketProfileRead]:
    profiles = (
        await db.scalars(
            select(OrganizationMarketProfile)
            .where(OrganizationMarketProfile.organization_id == organization_id)
            .order_by(
                OrganizationMarketProfile.status,
                OrganizationMarketProfile.country_code,
                OrganizationMarketProfile.region_code,
                OrganizationMarketProfile.name,
            )
        )
    ).all()
    return [organization_market_profile_read(profile) for profile in profiles]


async def organization_market_profile_summary(
    db: AsyncSession,
    organization_id: UUID,
) -> OrganizationMarketProfileSummaryRead:
    profiles = await list_organization_market_profiles(db, organization_id)
    active_profiles = [profile for profile in profiles if profile.status == "active"]
    payment_methods = sorted({method for profile in profiles for method in profile.supported_payment_methods})
    mobile_money_providers = sorted({provider for profile in profiles for provider in profile.mobile_money_providers})
    tax_authorities = sorted({profile.tax_authority for profile in profiles if profile.tax_authority})
    government_agencies = sorted(
        {agency for profile in profiles for agency in profile.government_reporting_agencies}
    )
    federation_templates = sorted(
        {template for profile in profiles for template in profile.federation_reporting_templates}
    )
    next_actions: list[str] = []
    if not active_profiles:
        next_actions.append("Activate at least one country or regional market profile.")
    if not payment_methods:
        next_actions.append("Configure local payment methods for dues, registration, ticketing, and invoices.")
    if not tax_authorities:
        next_actions.append("Record local tax authority and tax profile requirements.")
    if not government_agencies and not federation_templates:
        next_actions.append("Add government or federation reporting templates for compliance packages.")
    if not mobile_money_providers:
        next_actions.append("Add mobile-money or local bank rails for markets where cards are not primary.")
    return OrganizationMarketProfileSummaryRead(
        organization_id=organization_id,
        profile_count=len(profiles),
        active_profile_count=len(active_profiles),
        country_count=len({profile.country_code for profile in profiles}),
        primary_currencies=sorted({profile.default_currency for profile in profiles}),
        payment_methods=payment_methods,
        mobile_money_providers=mobile_money_providers,
        tax_authorities=tax_authorities,
        government_reporting_agencies=government_agencies,
        federation_reporting_templates=federation_templates,
        compliance_ready=bool(active_profiles and payment_methods and tax_authorities and (government_agencies or federation_templates)),
        next_actions=next_actions or ["Market localization profile is operationally ready."],
    )


def organization_market_profile_values(payload: OrganizationMarketProfileCreate) -> dict:
    return {
        "name": payload.name,
        "country_code": payload.country_code.upper(),
        "region_code": payload.region_code,
        "locale": payload.locale,
        "timezone": payload.timezone,
        "default_currency": payload.default_currency.upper(),
        "reporting_currency": payload.reporting_currency.upper(),
        "exchange_rate_source": payload.exchange_rate_source,
        "exchange_rate_margin_bps": payload.exchange_rate_margin_bps,
        "season_rate_lock": payload.season_rate_lock,
        "primary_payment_method": payload.primary_payment_method,
        "supported_payment_methods_json": json_dumps_list(payload.supported_payment_methods),
        "mobile_money_providers_json": json_dumps_list(payload.mobile_money_providers),
        "cash_collection_points_json": json_dumps_list(payload.cash_collection_points),
        "bank_integrations_json": json_dumps_list(payload.bank_integrations),
        "tax_authority": payload.tax_authority,
        "tax_registration_number": payload.tax_registration_number,
        "tax_profile": payload.tax_profile,
        "tax_rate": payload.tax_rate,
        "tax_exempt_categories_json": json_dumps_list(payload.tax_exempt_categories),
        "government_reporting_agencies_json": json_dumps_list(payload.government_reporting_agencies),
        "federation_reporting_templates_json": json_dumps_list(payload.federation_reporting_templates),
        "compliance_notes": payload.compliance_notes,
        "status": payload.status,
    }


def organization_market_profile_read(profile: OrganizationMarketProfile) -> OrganizationMarketProfileRead:
    return OrganizationMarketProfileRead(
        id=profile.id,
        organization_id=profile.organization_id,
        name=profile.name,
        country_code=profile.country_code,
        region_code=profile.region_code,
        locale=profile.locale,
        timezone=profile.timezone,
        default_currency=profile.default_currency,
        reporting_currency=profile.reporting_currency,
        exchange_rate_source=profile.exchange_rate_source,
        exchange_rate_margin_bps=profile.exchange_rate_margin_bps,
        season_rate_lock=profile.season_rate_lock,
        primary_payment_method=profile.primary_payment_method,
        supported_payment_methods=json_loads_list(profile.supported_payment_methods_json),
        mobile_money_providers=json_loads_list(profile.mobile_money_providers_json),
        cash_collection_points=json_loads_list(profile.cash_collection_points_json),
        bank_integrations=json_loads_list(profile.bank_integrations_json),
        tax_authority=profile.tax_authority,
        tax_registration_number=profile.tax_registration_number,
        tax_profile=profile.tax_profile,
        tax_rate=profile.tax_rate,
        tax_exempt_categories=json_loads_list(profile.tax_exempt_categories_json),
        government_reporting_agencies=json_loads_list(profile.government_reporting_agencies_json),
        federation_reporting_templates=json_loads_list(profile.federation_reporting_templates_json),
        compliance_notes=profile.compliance_notes,
        status=profile.status,
    )


async def create_organization_external_report(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: OrganizationExternalReportCreate,
    authz: AuthorizationService,
) -> OrganizationExternalReportRead:
    await ensure_manage_organization(db, identity, organization_id, authz)
    market_profile = await organization_external_report_market_profile(db, organization_id, payload.market_profile_id)
    report = OrganizationExternalReport(
        organization_id=organization_id,
        market_profile_id=market_profile.id if market_profile else None,
        name=payload.name,
        report_code=payload.report_code,
        report_type=payload.report_type,
        target_agency=payload.target_agency,
        target_type=payload.target_type,
        reporting_period_start=payload.reporting_period_start,
        reporting_period_end=payload.reporting_period_end,
        due_on=payload.due_on,
        submission_format=payload.submission_format,
        data_elements_json=json_dumps_list(payload.data_elements),
        source_summary=payload.source_summary
        or "External report generated from tenant registrations, rosters, finance, safety, and compliance records.",
        generated_payload=payload.generated_payload
        or organization_external_report_generated_payload(payload, organization_id, market_profile),
        submission_payload=payload.submission_payload,
        status=payload.status,
        external_reference=payload.external_reference,
        submitted_at=payload.submitted_at,
        accepted_at=payload.accepted_at,
        rejection_reason=payload.rejection_reason,
        notes=payload.notes,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return organization_external_report_read(report, market_profile.name if market_profile else None)


async def list_organization_external_reports(
    db: AsyncSession,
    organization_id: UUID,
    status_filter: str | None = None,
    target_type: str | None = None,
) -> list[OrganizationExternalReportRead]:
    statement = (
        select(OrganizationExternalReport, OrganizationMarketProfile.name)
        .outerjoin(
            OrganizationMarketProfile,
            OrganizationMarketProfile.id == OrganizationExternalReport.market_profile_id,
        )
        .where(OrganizationExternalReport.organization_id == organization_id)
        .order_by(
            OrganizationExternalReport.status,
            OrganizationExternalReport.due_on.asc(),
            OrganizationExternalReport.target_agency,
        )
    )
    if status_filter:
        statement = statement.where(OrganizationExternalReport.status == status_filter)
    if target_type:
        statement = statement.where(OrganizationExternalReport.target_type == target_type)
    return [
        organization_external_report_read(report, market_profile_name)
        for report, market_profile_name in (await db.execute(statement)).all()
    ]


async def update_organization_external_report_status(
    db: AsyncSession,
    identity: CurrentIdentity,
    report_id: UUID,
    payload: OrganizationExternalReportStatusUpdate,
    authz: AuthorizationService,
) -> OrganizationExternalReportRead:
    report = await db.get(OrganizationExternalReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="External report not found")
    await ensure_manage_organization(db, identity, report.organization_id, authz)
    report.status = payload.status
    for field in ("external_reference", "rejection_reason", "submission_payload", "notes"):
        value = getattr(payload, field)
        if value is not None:
            setattr(report, field, value)
    now = datetime.now(UTC)
    if payload.submitted_at is not None:
        report.submitted_at = payload.submitted_at
    elif payload.status in {"submitted", "accepted"} and report.submitted_at is None:
        report.submitted_at = now
    if payload.accepted_at is not None:
        report.accepted_at = payload.accepted_at
    elif payload.status == "accepted" and report.accepted_at is None:
        report.accepted_at = now
    await db.commit()
    await db.refresh(report)
    market_profile = await db.get(OrganizationMarketProfile, report.market_profile_id) if report.market_profile_id else None
    return organization_external_report_read(report, market_profile.name if market_profile else None)


async def organization_external_report_summary(
    db: AsyncSession,
    organization_id: UUID,
) -> OrganizationExternalReportSummaryRead:
    reports = await list_organization_external_reports(db, organization_id)
    today = date.today()
    target_type_counts: dict[str, int] = {}
    for report in reports:
        target_type_counts[report.target_type] = target_type_counts.get(report.target_type, 0) + 1
    overdue_reports = [
        report
        for report in reports
        if report.due_on < today and report.status not in {"submitted", "accepted", "cancelled"}
    ]
    upcoming_reports = [
        report
        for report in reports
        if 0 <= (report.due_on - today).days <= 14 and report.status in {"draft", "ready"}
    ]
    next_actions: list[str] = []
    if not reports:
        next_actions.append("Create government and federation reporting obligations for this tenant.")
    if overdue_reports:
        next_actions.append(f"Resolve {len(overdue_reports)} overdue external reporting submission(s).")
    if upcoming_reports:
        next_actions.append(f"Prepare {len(upcoming_reports)} report(s) due in the next 14 days.")
    if not any(report.target_type == "federation" for report in reports):
        next_actions.append("Add federation reporting templates for club licensing and competition eligibility.")
    if not any(report.target_type == "government" for report in reports):
        next_actions.append("Add government reporting templates for statutory compliance.")
    return OrganizationExternalReportSummaryRead(
        organization_id=organization_id,
        total_reports=len(reports),
        submitted_reports=sum(1 for report in reports if report.status == "submitted"),
        accepted_reports=sum(1 for report in reports if report.status == "accepted"),
        rejected_reports=sum(1 for report in reports if report.status == "rejected"),
        overdue_reports=len(overdue_reports),
        upcoming_reports=len(upcoming_reports),
        target_type_counts=target_type_counts,
        next_actions=next_actions or ["External reporting register is current."],
    )


async def organization_external_report_market_profile(
    db: AsyncSession,
    organization_id: UUID,
    market_profile_id: UUID | None,
) -> OrganizationMarketProfile | None:
    if market_profile_id is None:
        return None
    market_profile = await db.get(OrganizationMarketProfile, market_profile_id)
    if market_profile is None or market_profile.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market profile not found")
    return market_profile


def organization_external_report_generated_payload(
    payload: OrganizationExternalReportCreate,
    organization_id: UUID,
    market_profile: OrganizationMarketProfile | None,
) -> str:
    return json.dumps(
        {
            "organization_id": str(organization_id),
            "report": {
                "name": payload.name,
                "report_code": payload.report_code,
                "report_type": payload.report_type,
                "target_agency": payload.target_agency,
                "target_type": payload.target_type,
                "period_start": payload.reporting_period_start.isoformat(),
                "period_end": payload.reporting_period_end.isoformat(),
                "due_on": payload.due_on.isoformat(),
                "submission_format": payload.submission_format,
                "data_elements": payload.data_elements,
            },
            "market": None
            if market_profile is None
            else {
                "name": market_profile.name,
                "country_code": market_profile.country_code,
                "region_code": market_profile.region_code,
                "timezone": market_profile.timezone,
                "currency": market_profile.reporting_currency,
                "payment_methods": json_loads_list(market_profile.supported_payment_methods_json),
                "government_reporting_agencies": json_loads_list(
                    market_profile.government_reporting_agencies_json
                ),
                "federation_reporting_templates": json_loads_list(
                    market_profile.federation_reporting_templates_json
                ),
            },
        },
        sort_keys=True,
    )


def organization_external_report_read(
    report: OrganizationExternalReport,
    market_profile_name: str | None = None,
) -> OrganizationExternalReportRead:
    return OrganizationExternalReportRead(
        id=report.id,
        organization_id=report.organization_id,
        market_profile_id=report.market_profile_id,
        market_profile_name=market_profile_name,
        name=report.name,
        report_code=report.report_code,
        report_type=report.report_type,
        target_agency=report.target_agency,
        target_type=report.target_type,
        reporting_period_start=report.reporting_period_start,
        reporting_period_end=report.reporting_period_end,
        due_on=report.due_on,
        submission_format=report.submission_format,
        data_elements=json_loads_list(report.data_elements_json),
        source_summary=report.source_summary,
        generated_payload=report.generated_payload,
        submission_payload=report.submission_payload,
        status=report.status,
        external_reference=report.external_reference,
        submitted_at=report.submitted_at,
        accepted_at=report.accepted_at,
        rejection_reason=report.rejection_reason,
        notes=report.notes,
        days_until_due=(report.due_on - date.today()).days,
    )


def json_dumps_list(values: list[str]) -> str:
    normalized = [value.strip() for value in values if value.strip()]
    return json.dumps(normalized)


def json_loads_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()]


async def ensure_member_subject_exists(db: AsyncSession, subject_type: MemberSubjectType, subject_id: UUID) -> None:
    model = Person
    if subject_type == MemberSubjectType.ORGANIZATION:
        model = Organization
    elif subject_type == MemberSubjectType.TEAM:
        model = Team
    if await db.get(model, subject_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{subject_type.value.title()} subject not found")


async def member_subject_label(db: AsyncSession, subject_type: MemberSubjectType, subject_id: UUID) -> str | None:
    if subject_type == MemberSubjectType.PERSON:
        person = await db.get(Person, subject_id)
        return person.display_name if person else None
    if subject_type == MemberSubjectType.ORGANIZATION:
        organization = await db.get(Organization, subject_id)
        return organization.public_name or organization.name if organization else None
    team = await db.get(Team, subject_id)
    return team.name if team else None


async def create_committee(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    payload: CommitteeCreate,
    authz: AuthorizationService,
) -> Committee:
    can_manage = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    committee = Committee(
        organization_id=organization_id,
        name=payload.name,
        level=payload.level,
        mandate=payload.mandate,
    )
    db.add(committee)
    await db.flush()
    await authz.touch(
        Relationship(
            resource_type="organization",
            resource_id=str(organization_id),
            relation="committee",
            subject_type="committee",
            subject_id=str(committee.id),
        )
    )
    await db.commit()
    await db.refresh(committee)
    return committee


async def list_committees(db: AsyncSession, organization_id: UUID) -> list[Committee]:
    return list(
        (
            await db.scalars(
                select(Committee)
                .where(Committee.organization_id == organization_id)
                .order_by(Committee.name)
            )
        ).all()
    )


async def add_committee_member(
    db: AsyncSession,
    identity: CurrentIdentity,
    committee_id: UUID,
    payload: CommitteeMemberAdd,
    authz: AuthorizationService,
) -> CommitteeMembership:
    committee = await db.get(Committee, committee_id)
    if committee is None:
        raise HTTPException(status_code=404, detail="Committee not found")

    can_manage = await authz.check(
        resource_type="organization",
        resource_id=str(committee.organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not can_manage:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    person_id = payload.person_id
    if person_id is not None:
        person = await db.get(Person, person_id)
        if person is None:
            raise HTTPException(status_code=404, detail="Person not found")
    else:
        if not payload.email:
            raise HTTPException(
                status_code=422, detail="Committee member requires email or person_id"
            )
        person = await db.scalar(select(Person).where(Person.primary_email == payload.email))
        if person is None:
            person = Person(
                display_name=payload.display_name or payload.email,
                primary_email=payload.email,
            )
            db.add(person)
            await db.flush()
        person_id = person.id

    existing = await db.scalar(
        select(CommitteeMembership).where(
            CommitteeMembership.committee_id == committee_id,
            CommitteeMembership.person_id == person_id,
            CommitteeMembership.role == payload.role,
        )
    )
    if existing is not None:
        return existing

    membership = CommitteeMembership(
        committee_id=committee_id,
        person_id=person_id,
        role=payload.role,
        title=payload.title,
    )
    db.add(membership)
    await authz.touch(
        Relationship(
            resource_type="committee",
            resource_id=str(committee_id),
            relation=payload.role.value,
            subject_type="person",
            subject_id=str(person_id),
        )
    )
    await db.commit()
    await db.refresh(membership)
    return membership
