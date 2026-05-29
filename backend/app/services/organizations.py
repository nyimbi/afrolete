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
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.communication import CommunicationMessage
from app.models.commercial import FundraisingCampaign, Sponsor, SponsorshipAgreement, TicketProduct
from app.models.enums import (
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
from app.models.identity import Person
from app.models.organization import Committee, CommitteeMembership, Membership, Organization, RegistrationInquiry
from app.models.team import AthleteProfile, GuardianRelationship, Team, TeamRosterEntry
from app.schemas.organization import (
    CommitteeCreate,
    CommitteeMemberAdd,
    MemberAdd,
    OrganizationHandleAvailabilityRead,
    OrganizationCreate,
    PublicRegistrationDocumentUpload,
    PublicRegistrationPacketUpdate,
    PublicRegistrationInquiryCreate,
    RegistrationInquiryConversionCreate,
    RegistrationInquiryFollowUpCreate,
    RegistrationPaymentHostedCheckoutRead,
    RegistrationPaymentSessionCreate,
    RegistrationPaymentSettlementCreate,
    RegistrationPaymentSettlementRead,
    RegistrationInquiryUpdate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship
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
DEFAULT_REGISTRATION_DOCUMENTS = ["proof_of_age", "medical_information"]


def public_site_path(organization: Organization) -> str:
    return f"/site/{organization.subdomain or organization.slug}"


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


def default_starter_team_name(organization: Organization) -> str:
    label = organization.primary_sport or "Multi-sport"
    if organization.organization_type == OrganizationType.SCHOOL:
        return f"{label.title()} Program"
    if organization.organization_type == OrganizationType.ACADEMY:
        return f"{label.title()} Academy Group"
    return f"{label.title()} Team"


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
    return organization, teams, upcoming_events, sponsors, sponsorships, campaigns, ticket_products


async def create_public_registration_inquiry(
    db: AsyncSession,
    site: str,
    payload: PublicRegistrationInquiryCreate,
) -> RegistrationInquiry:
    organization = await db.scalar(
        select(Organization).where(
            (Organization.slug == site) | (Organization.subdomain == site)
        )
    )
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    if not organization.registration_open:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Registration is closed")
    if payload.team_id is not None:
        team = await db.get(Team, payload.team_id)
        if team is None or team.organization_id != organization.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    required_documents = organization_registration_required_documents(organization)
    if not required_documents:
        required_documents = list(DEFAULT_REGISTRATION_DOCUMENTS)
        if payload.guardian_name or is_youth_age_group(payload.age_group):
            required_documents.extend(["guardian_consent", "photo_release"])

    inquiry = RegistrationInquiry(
        organization_id=organization.id,
        **payload.model_dump(),
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
    if inquiry.email.lower() != payload.email.lower():
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
    if inquiry.email.lower() != payload.email.lower():
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
) -> RegistrationPaymentHostedCheckoutRead:
    amount_due = (inquiry.payment_amount or Decimal("0.00")).quantize(Decimal("0.01"))
    amount_paid = amount_due if inquiry.payment_status in REGISTRATION_PAYMENT_COMPLETE_STATUSES else Decimal("0.00")
    open_amount = registration_payment_open_amount(inquiry)
    registration_reference = f"REG-{str(inquiry.id).split('-')[0].upper()}"
    title = f"Registration fee for {inquiry.athlete_name}"
    return RegistrationPaymentHostedCheckoutRead(
        inquiry_id=inquiry.id,
        organization_id=inquiry.organization_id,
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
    )


async def create_registration_payment_session(
    db: AsyncSession,
    site: str,
    inquiry_id: UUID,
    payload: RegistrationPaymentSessionCreate,
) -> tuple[RegistrationInquiry, str, str, str, RegistrationPaymentHostedCheckoutRead]:
    _organization, inquiry = await get_public_registration_inquiry(db, site, inquiry_id)
    if inquiry.email.lower() != payload.email.lower():
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

    hosted_checkout = registration_payment_hosted_checkout_read(inquiry, provider, session_id)
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
    return registration_payment_hosted_checkout_read(inquiry, provider, session_id)


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

    if changed:
        inquiry.reviewed_by_person_id = identity.person_id
        inquiry.reviewed_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(inquiry)
    return inquiry


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

    recipient = await db.scalar(select(Person).where(Person.primary_email == inquiry.email))
    if recipient is None:
        recipient = Person(
            display_name=inquiry.guardian_name or inquiry.email,
            primary_email=inquiry.email,
            primary_phone=inquiry.phone,
        )
        db.add(recipient)
        await db.flush()
    elif inquiry.phone and not recipient.primary_phone:
        recipient.primary_phone = inquiry.phone
        await db.flush()

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
        guardian = await db.scalar(select(Person).where(Person.primary_email == inquiry.email))
        if guardian is None:
            guardian = Person(
                display_name=inquiry.guardian_name or inquiry.email,
                primary_email=inquiry.email,
                primary_phone=inquiry.phone,
            )
            db.add(guardian)
            await db.flush()
        elif inquiry.phone and not guardian.primary_phone:
            guardian.primary_phone = inquiry.phone

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
