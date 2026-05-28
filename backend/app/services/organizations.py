import re
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import CommunicationMessage
from app.models.commercial import FundraisingCampaign, Sponsor, SponsorshipAgreement, TicketProduct
from app.models.enums import (
    CommercialStatus,
    CommunicationMessageType,
    CommunicationScopeType,
    GuardianRelationshipKind,
    MemberSubjectType,
    MembershipRole,
    RosterStatus,
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
    OrganizationCreate,
    PublicRegistrationInquiryCreate,
    RegistrationInquiryConversionCreate,
    RegistrationInquiryFollowUpCreate,
    RegistrationInquiryUpdate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship
from app.services.communications import create_message
from app.schemas.communication import CommunicationMessageCreate


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "organization"


def organization_member_relation(subject_type: MemberSubjectType, role: MembershipRole) -> str:
    if subject_type == MemberSubjectType.ORGANIZATION:
        return "member_org"
    if subject_type == MemberSubjectType.TEAM:
        return "member_team"
    return role.value


INQUIRY_REVIEW_STATUSES = {"new", "reviewing", "contacted", "waitlisted", "rejected"}


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
    slug = payload.slug or slugify(payload.name)
    existing = await db.scalar(select(Organization).where(Organization.slug == slug))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization slug exists")
    if payload.subdomain is not None:
        existing_subdomain = await db.scalar(
            select(Organization).where(Organization.subdomain == payload.subdomain)
        )
        if existing_subdomain is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization subdomain exists",
            )

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
        subdomain=payload.subdomain,
        logo_url=payload.logo_url,
        brand_primary_color=payload.brand_primary_color,
        brand_secondary_color=payload.brand_secondary_color,
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
    if payload.team_id is not None:
        team = await db.get(Team, payload.team_id)
        if team is None or team.organization_id != organization.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    inquiry = RegistrationInquiry(
        organization_id=organization.id,
        **payload.model_dump(),
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)
    return inquiry


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
) -> tuple[RegistrationInquiry, Person, AthleteProfile, TeamRosterEntry | None, Person | None]:
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
            db.add(
                GuardianRelationship(
                    athlete_person_id=athlete.id,
                    guardian_person_id=guardian.id,
                    relationship_kind=GuardianRelationshipKind.PARENT,
                    relationship="parent",
                    can_sign_consent=True,
                    emergency_contact=True,
                    is_primary=True,
                )
            )

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
    return inquiry, athlete, athlete_profile, roster_entry, guardian


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
