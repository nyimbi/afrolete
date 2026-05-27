import hmac
import json
import time
from datetime import UTC, datetime
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.developer import (
    DeveloperApiKey,
    DeveloperApplication,
    DeveloperMarketplaceListing,
    DeveloperWebhookDelivery,
    DeveloperWebhookSubscription,
)
from app.models.organization import Organization
from app.schemas.developer import (
    DeveloperApiKeyCreate,
    DeveloperApiKeyInspectionRead,
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


async def create_developer_api_key(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: DeveloperApiKeyCreate,
    authz: AuthorizationService,
) -> tuple[DeveloperApiKey, str]:
    organization = await get_organization(db, payload.organization_id)
    await ensure_manage_developer_platform(authz, identity, payload.organization_id)
    await get_developer_application_for_organization(db, payload.application_id, payload.organization_id)
    key = build_api_key(organization.slug, payload.environment)
    key_record = DeveloperApiKey(
        organization_id=payload.organization_id,
        application_id=payload.application_id,
        name=payload.name,
        key_prefix=key.split(".", 1)[0],
        key_hash=hash_secret(key),
        scopes=pack_list(payload.scopes),
        environment=payload.environment,
        expires_at=payload.expires_at,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        notes=payload.notes,
    )
    db.add(key_record)
    await db.commit()
    await db.refresh(key_record)
    return key_record, key


async def list_developer_api_keys(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    application_id: UUID | None = None,
) -> list[DeveloperApiKey]:
    await ensure_manage_developer_platform(authz, identity, organization_id)
    query = select(DeveloperApiKey).where(DeveloperApiKey.organization_id == organization_id)
    if application_id is not None:
        query = query.where(DeveloperApiKey.application_id == application_id)
    return list((await db.scalars(query.order_by(DeveloperApiKey.created_at.desc()))).all())


async def revoke_developer_api_key(
    db: AsyncSession,
    identity: CurrentIdentity,
    api_key_id: UUID,
    authz: AuthorizationService,
) -> DeveloperApiKey:
    api_key = await get_developer_api_key(db, api_key_id)
    await ensure_manage_developer_platform(authz, identity, api_key.organization_id)
    api_key.status = "revoked"
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def inspect_developer_api_key(
    db: AsyncSession,
    raw_key: str,
    request_ip: str | None = None,
) -> DeveloperApiKeyInspectionRead:
    api_key = await authenticate_developer_api_key(db, raw_key, request_ip=request_ip)
    application = await get_developer_application(db, api_key.application_id)
    return DeveloperApiKeyInspectionRead(
        valid=True,
        organization_id=api_key.organization_id,
        application_id=api_key.application_id,
        api_key_id=api_key.id,
        client_id=application.client_id,
        application_name=application.name,
        environment=api_key.environment,
        scopes=unpack_list(api_key.scopes),
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        usage_count=api_key.usage_count,
        window_started_at=api_key.window_started_at,
        window_request_count=api_key.window_request_count,
    )


def ensure_developer_api_scope(
    credential: DeveloperApiKeyInspectionRead,
    organization_id: UUID,
    required_scopes: set[str],
) -> None:
    if credential.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key cannot access this organization")
    granted_scopes = set(credential.scopes)
    if "admin:*" not in granted_scopes and granted_scopes.isdisjoint(required_scopes):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key scope is insufficient")


async def authenticate_developer_api_key(
    db: AsyncSession,
    raw_key: str,
    request_ip: str | None = None,
) -> DeveloperApiKey:
    prefix = raw_key.split(".", 1)[0]
    api_key = await db.scalar(select(DeveloperApiKey).where(DeveloperApiKey.key_prefix == prefix))
    if api_key is None or api_key.key_hash != hash_secret(raw_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid developer API key")
    if api_key.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Developer API key is not active")
    if api_key.expires_at is not None and api_key.expires_at <= datetime.now(UTC):
        api_key.status = "expired"
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Developer API key has expired")
    application = await get_developer_application(db, api_key.application_id)
    if application.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Developer application is not active")
    now = datetime.now(UTC)
    window_started_at = as_utc(api_key.window_started_at)
    if window_started_at is None or (now - window_started_at).total_seconds() >= 60:
        api_key.window_started_at = now
        api_key.window_request_count = 0
    if api_key.window_request_count >= api_key.rate_limit_per_minute:
        api_key.last_rate_limited_at = now
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Developer API key rate limit exceeded",
        )
    api_key.window_request_count += 1
    api_key.last_used_at = now
    api_key.last_used_ip = request_ip
    api_key.usage_count += 1
    await db.commit()
    await db.refresh(api_key)
    return api_key


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


async def deliver_developer_webhook_event(
    db: AsyncSession,
    organization_id: UUID,
    event_type: str,
    event_id: str,
    payload: dict[str, object],
) -> list[DeveloperWebhookDelivery]:
    subscriptions = list(
        (
            await db.scalars(
                select(DeveloperWebhookSubscription).where(
                    DeveloperWebhookSubscription.organization_id == organization_id,
                    DeveloperWebhookSubscription.status == "active",
                )
            )
        ).all()
    )
    matching_subscriptions = [
        subscription
        for subscription in subscriptions
        if event_type in set(unpack_list(subscription.event_types))
    ]
    deliveries = [
        DeveloperWebhookDelivery(
            organization_id=organization_id,
            subscription_id=subscription.id,
            application_id=subscription.application_id,
            event_type=event_type,
            event_id=event_id,
            target_url=subscription.target_url,
            delivery_mode=subscription.delivery_mode,
            payload=stable_json(payload),
        )
        for subscription in matching_subscriptions
    ]
    for delivery in deliveries:
        db.add(delivery)
    await db.flush()
    for subscription, delivery in zip(matching_subscriptions, deliveries, strict=True):
        await deliver_single_webhook(db, subscription, delivery)
    await db.commit()
    for delivery in deliveries:
        await db.refresh(delivery)
    return deliveries


async def list_developer_webhook_deliveries(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    subscription_id: UUID | None = None,
) -> list[DeveloperWebhookDelivery]:
    await ensure_manage_developer_platform(authz, identity, organization_id)
    query = select(DeveloperWebhookDelivery).where(DeveloperWebhookDelivery.organization_id == organization_id)
    if subscription_id is not None:
        query = query.where(DeveloperWebhookDelivery.subscription_id == subscription_id)
    return list((await db.scalars(query.order_by(DeveloperWebhookDelivery.created_at.desc()).limit(100))).all())


async def replay_developer_webhook_delivery(
    db: AsyncSession,
    identity: CurrentIdentity,
    delivery_id: UUID,
    authz: AuthorizationService,
) -> DeveloperWebhookDelivery:
    delivery = await get_webhook_delivery(db, delivery_id)
    await ensure_manage_developer_platform(authz, identity, delivery.organization_id)
    subscription = await get_webhook_subscription(db, delivery.subscription_id)
    if subscription.status != "active":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot replay delivery for inactive webhook subscription",
        )
    delivery.status = "queued"
    delivery.failure_reason = None
    delivery.response_status_code = None
    delivery.delivered_at = None
    await deliver_single_webhook(db, subscription, delivery)
    await db.commit()
    await db.refresh(delivery)
    return delivery


async def deliver_single_webhook(
    db: AsyncSession,
    subscription: DeveloperWebhookSubscription,
    delivery: DeveloperWebhookDelivery,
) -> None:
    now = datetime.now(UTC)
    delivery.attempt_count += 1
    if subscription.delivery_mode == "record_only":
        delivery.status = "recorded"
        delivery.delivered_at = now
        subscription.last_delivery_status = delivery.status
        subscription.last_delivered_at = now
        return
    try:
        timestamp = str(int(time.time()))
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                subscription.target_url,
                content=delivery.payload,
                headers=developer_webhook_headers(subscription, delivery, timestamp),
            )
        delivery.response_status_code = response.status_code
        if 200 <= response.status_code < 300:
            delivery.status = "delivered"
            delivery.delivered_at = now
        else:
            delivery.status = "failed"
            delivery.failure_reason = f"Webhook returned {response.status_code}: {response.text[:500]}"
            subscription.failure_count += 1
    except httpx.HTTPError as error:
        delivery.status = "failed"
        delivery.failure_reason = f"Webhook delivery failed: {error}"
        subscription.failure_count += 1
    subscription.last_delivery_status = delivery.status
    subscription.last_delivered_at = delivery.delivered_at
    await db.flush()


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
    api_key_count = await count_where(db, DeveloperApiKey, organization_id)
    active_api_key_count = await count_where(db, DeveloperApiKey, organization_id, status_value="active")
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
    if api_key_count == 0:
        next_steps.append("Issue a sandbox API key so SDK clients can authenticate against tenant APIs.")
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
        api_key_count=api_key_count,
        active_api_key_count=active_api_key_count,
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


async def get_developer_api_key(db: AsyncSession, api_key_id: UUID) -> DeveloperApiKey:
    api_key = await db.get(DeveloperApiKey, api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer API key not found")
    return api_key


async def get_webhook_subscription(db: AsyncSession, subscription_id: UUID) -> DeveloperWebhookSubscription:
    subscription = await db.get(DeveloperWebhookSubscription, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer webhook subscription not found")
    return subscription


async def get_webhook_delivery(db: AsyncSession, delivery_id: UUID) -> DeveloperWebhookDelivery:
    delivery = await db.get(DeveloperWebhookDelivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Developer webhook delivery not found")
    return delivery


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


def stable_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def developer_webhook_headers(
    subscription: DeveloperWebhookSubscription,
    delivery: DeveloperWebhookDelivery,
    timestamp: str,
) -> dict[str, str]:
    signed = f"{timestamp}.{delivery.payload}".encode("utf-8")
    signature = hmac.new(subscription.signing_secret_hash.encode("utf-8"), signed, sha256).hexdigest()
    return {
        "Content-Type": "application/json",
        "X-Afrolete-Webhook-Event": delivery.event_type,
        "X-Afrolete-Webhook-Delivery": str(delivery.id),
        "X-Afrolete-Webhook-Timestamp": timestamp,
        "X-Afrolete-Webhook-Signature": f"sha256={signature}",
    }


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def build_api_key(organization_slug: str, environment: str) -> str:
    slug_part = "".join(character for character in organization_slug.lower() if character.isalnum())[:12] or "tenant"
    environment_part = "".join(character for character in environment.lower() if character.isalnum())[:12] or "sandbox"
    prefix = f"al_{slug_part}_{environment_part}_{token_urlsafe(6)}"
    return f"{prefix}.{token_urlsafe(32)}"
