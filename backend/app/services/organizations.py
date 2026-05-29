import csv
import io
import json
import re
from base64 import b64decode
from binascii import Error as BinasciiError
from datetime import UTC, datetime
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
from app.models.organization import Committee, CommitteeMembership, Membership, Organization, RegistrationInquiry
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry
from app.schemas.organization import (
    CommitteeCreate,
    CommitteeMemberAdd,
    FamilyRegistrationInquiryRead,
    MemberAdd,
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
from app.services.communications import create_message
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
                country_code=payload.country_code.upper() if payload.country_code else None,
            )
            db.add(person)
            await db.flush()
        elif payload.country_code and person.country_code is None:
            person.country_code = payload.country_code.upper()
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
