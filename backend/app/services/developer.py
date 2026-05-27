from datetime import UTC, datetime
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.developer import (
    DeveloperApplication,
    DeveloperMarketplaceListing,
    DeveloperWebhookSubscription,
)
from app.models.organization import Organization
from app.schemas.developer import (
    DeveloperApplicationCreate,
    DeveloperMarketplaceListingCreate,
    DeveloperMarketplaceListingReview,
    DeveloperPortalSummaryRead,
    DeveloperWebhookSubscriptionCreate,
    DeveloperWebhookSubscriptionUpdate,
)
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, Relationship


async def ensure_manage_developer_platform(
    authz: AuthorizationService,
    identity: CurrentIdentity,
    organization_id: UUID,
) -> None:
    allowed = await authz.check(
        resource_type="organization",
        resource_id=str(organization_id),
        permission="manage",
        subject_type="user",
        subject_id=str(identity.user_id),
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def create_developer_application(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: DeveloperApplicationCreate,
    authz: AuthorizationService,
) -> tuple[DeveloperApplication, str]:
    await get_organization(db, payload.organization_id)
    await ensure_manage_developer_platform(authz, identity, payload.organization_id)
    secret = token_urlsafe(32)
    application = DeveloperApplication(
        organization_id=payload.organization_id,
        owner_person_id=identity.person_id,
        name=payload.name,
        app_type=payload.app_type,
        client_id=f"afrolete_{token_urlsafe(18)}",
        client_secret_hash=hash_secret(secret),
        redirect_uris=pack_list(payload.redirect_uris),
        scopes=pack_list(payload.scopes),
        contact_email=payload.contact_email,
        notes=payload.notes,
        last_rotated_at=datetime.now(UTC),
    )
    db.add(application)
    await db.flush()
    await authz.touch(
        Relationship(
            resource_type="developer_application",
            resource_id=str(application.id),
            relation="owner",
            subject_type="user",
            subject_id=str(identity.user_id),
        )
    )
    await db.commit()
    await db.refresh(application)
    return application, secret


async def rotate_developer_application_secret(
    db: AsyncSession,
    identity: CurrentIdentity,
    application_id: UUID,
    authz: AuthorizationService,
) -> tuple[DeveloperApplication, str]:
    application = await get_developer_application(db, application_id)
    await ensure_manage_developer_platform(authz, identity, application.organization_id)
    secret = token_urlsafe(32)
    application.client_secret_hash = hash_secret(secret)
    application.last_rotated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(application)
    return application, secret


async def list_developer_applications(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[DeveloperApplication]:
    await ensure_manage_developer_platform(authz, identity, organization_id)
    return list(
        (
            await db.scalars(
                select(DeveloperApplication)
                .where(DeveloperApplication.organization_id == organization_id)
                .order_by(DeveloperApplication.created_at.desc())
            )
        ).all()
    )


async def create_developer_webhook_subscription(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: DeveloperWebhookSubscriptionCreate,
    authz: AuthorizationService,
) -> tuple[DeveloperWebhookSubscription, str]:
    await get_organization(db, payload.organization_id)
    await ensure_manage_developer_platform(authz, identity, payload.organization_id)
    if payload.application_id is not None:
        await get_developer_application_for_organization(db, payload.application_id, payload.organization_id)
    secret = token_urlsafe(32)
    subscription = DeveloperWebhookSubscription(
        organization_id=payload.organization_id,
        application_id=payload.application_id,
        name=payload.name,
        target_url=payload.target_url,
        event_types=pack_list(payload.event_types),
        signing_secret_hash=hash_secret(secret),
        delivery_mode=payload.delivery_mode,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription, secret


async def list_developer_webhook_subscriptions(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[DeveloperWebhookSubscription]:
    await ensure_manage_developer_platform(authz, identity, organization_id)
    return list(
        (
            await db.scalars(
                select(DeveloperWebhookSubscription)
                .where(DeveloperWebhookSubscription.organization_id == organization_id)
                .order_by(DeveloperWebhookSubscription.created_at.desc())
            )
        ).all()
    )


async def update_developer_webhook_subscription(
    db: AsyncSession,
    identity: CurrentIdentity,
    subscription_id: UUID,
    payload: DeveloperWebhookSubscriptionUpdate,
    authz: AuthorizationService,
) -> DeveloperWebhookSubscription:
    subscription = await get_webhook_subscription(db, subscription_id)
    await ensure_manage_developer_platform(authz, identity, subscription.organization_id)
    if payload.status is not None:
        subscription.status = payload.status
    if payload.delivery_mode is not None:
        subscription.delivery_mode = payload.delivery_mode
    if payload.target_url is not None:
        subscription.target_url = payload.target_url
    if payload.event_types is not None:
        subscription.event_types = pack_list(payload.event_types)
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def create_developer_marketplace_listing(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: DeveloperMarketplaceListingCreate,
    authz: AuthorizationService,
) -> DeveloperMarketplaceListing:
    await get_organization(db, payload.organization_id)
    await ensure_manage_developer_platform(authz, identity, payload.organization_id)
    if payload.application_id is not None:
        await get_developer_application_for_organization(db, payload.application_id, payload.organization_id)
    listing = DeveloperMarketplaceListing(**payload.model_dump())
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return listing


async def list_developer_marketplace_listings(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[DeveloperMarketplaceListing]:
    await ensure_manage_developer_platform(authz, identity, organization_id)
    return list(
        (
            await db.scalars(
                select(DeveloperMarketplaceListing)
                .where(DeveloperMarketplaceListing.organization_id == organization_id)
                .order_by(DeveloperMarketplaceListing.created_at.desc())
            )
        ).all()
    )


async def review_developer_marketplace_listing(
    db: AsyncSession,
    identity: CurrentIdentity,
    listing_id: UUID,
    payload: DeveloperMarketplaceListingReview,
    authz: AuthorizationService,
) -> DeveloperMarketplaceListing:
    listing = await get_marketplace_listing(db, listing_id)
    await ensure_manage_developer_platform(authz, identity, listing.organization_id)
    listing.review_status = payload.review_status
    if payload.visibility is not None:
        listing.visibility = payload.visibility
    await db.commit()
    await db.refresh(listing)
    return listing


async def record_developer_marketplace_install(
    db: AsyncSession,
    identity: CurrentIdentity,
    listing_id: UUID,
    authz: AuthorizationService,
) -> DeveloperMarketplaceListing:
    listing = await get_marketplace_listing(db, listing_id)
    await ensure_manage_developer_platform(authz, identity, listing.organization_id)
    listing.install_count += 1
    await db.commit()
    await db.refresh(listing)
    return listing


async def developer_portal_summary(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> DeveloperPortalSummaryRead:
    await ensure_manage_developer_platform(authz, identity, organization_id)
    application_count = await count_where(db, DeveloperApplication, organization_id)
    active_application_count = await count_where(db, DeveloperApplication, organization_id, status_value="active")
    webhook_subscription_count = await count_where(db, DeveloperWebhookSubscription, organization_id)
    live_webhook_count = await count_where(
        db,
        DeveloperWebhookSubscription,
        organization_id,
        delivery_mode="webhook",
        status_value="active",
    )
    marketplace_listing_count = await count_where(db, DeveloperMarketplaceListing, organization_id)
    approved_marketplace_listing_count = await count_where(
        db,
        DeveloperMarketplaceListing,
        organization_id,
        status_column="review_status",
        status_value="approved",
    )
    install_count = int(
        await db.scalar(
            select(func.coalesce(func.sum(DeveloperMarketplaceListing.install_count), 0)).where(
                DeveloperMarketplaceListing.organization_id == organization_id
            )
        )
        or 0
    )
    next_steps: list[str] = []
    if application_count == 0:
        next_steps.append("Register a developer application before issuing third-party integrations.")
    if webhook_subscription_count == 0:
        next_steps.append("Create webhook subscriptions for tenant events that external systems need.")
    if approved_marketplace_listing_count == 0:
        next_steps.append("Prepare and approve a marketplace listing for trusted ecosystem distribution.")
    if not next_steps:
        next_steps.append("Review scopes, webhook delivery history, and listing visibility before public rollout.")
    return DeveloperPortalSummaryRead(
        organization_id=organization_id,
        application_count=application_count,
        active_application_count=active_application_count,
        webhook_subscription_count=webhook_subscription_count,
        live_webhook_count=live_webhook_count,
        marketplace_listing_count=marketplace_listing_count,
        approved_marketplace_listing_count=approved_marketplace_listing_count,
        install_count=install_count,
        recommended_next_steps=next_steps,
    )


async def count_where(
    db: AsyncSession,
    model,
    organization_id: UUID,
    *,
    delivery_mode: str | None = None,
    status_column: str = "status",
    status_value: str | None = None,
) -> int:
    query = select(func.count()).select_from(model).where(model.organization_id == organization_id)
    if delivery_mode is not None:
        query = query.where(model.delivery_mode == delivery_mode)
    if status_value is not None:
        query = query.where(getattr(model, status_column) == status_value)
    return int(await db.scalar(query) or 0)


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


async def get_developer_application(db: AsyncSession, application_id: UUID) -> DeveloperApplication:
    application = await db.get(DeveloperApplication, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer application not found")
    return application


async def get_developer_application_for_organization(
    db: AsyncSession,
    application_id: UUID,
    organization_id: UUID,
) -> DeveloperApplication:
    application = await get_developer_application(db, application_id)
    if application.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Application belongs to another organization")
    return application


async def get_webhook_subscription(db: AsyncSession, subscription_id: UUID) -> DeveloperWebhookSubscription:
    subscription = await db.get(DeveloperWebhookSubscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer webhook subscription not found")
    return subscription


async def get_marketplace_listing(db: AsyncSession, listing_id: UUID) -> DeveloperMarketplaceListing:
    listing = await db.get(DeveloperMarketplaceListing, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer marketplace listing not found")
    return listing


def hash_secret(secret: str) -> str:
    return sha256(secret.encode("utf-8")).hexdigest()


def pack_list(values: list[str]) -> str:
    return "\n".join(value.strip() for value in values if value.strip())


def unpack_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [entry for entry in value.splitlines() if entry]
