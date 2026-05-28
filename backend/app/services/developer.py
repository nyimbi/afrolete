import hmac
import json
import time
from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from urllib.parse import urlencode
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.developer import (
    DeveloperApiKey,
    DeveloperApplication,
    DeveloperMarketplaceListing,
    DeveloperOAuthAuthorization,
    DeveloperWebhookDelivery,
    DeveloperWebhookSubscription,
)
from app.models.enums import (
    SafeguardingIncidentSeverity,
    SafeguardingIncidentStatus,
    SafeguardingIncidentType,
)
from app.models.event import SafeguardingIncident
from app.models.organization import Organization
from app.schemas.developer import (
    DeveloperApiKeyCreate,
    DeveloperApiKeyInspectionRead,
    DeveloperApiKeyRead,
    DeveloperOAuthAuthorizationCreate,
    DeveloperOAuthAuthorizationRead,
    DeveloperOAuthRefreshTokenExchange,
    DeveloperOAuthTokenExchange,
    DeveloperOAuthTokenRead,
    DeveloperApplicationCreate,
    DeveloperApiScopeCatalogRead,
    DeveloperIntegrationCatalogRead,
    DeveloperMarketplaceListingCreate,
    DeveloperMarketplaceListingReview,
    DeveloperPortalSummaryRead,
    DeveloperPublicDocsRead,
    DeveloperQuickstartRead,
    DeveloperSdkCatalogRead,
    DeveloperWebhookEventCatalogRead,
    DeveloperWebhookRetryRunRead,
    DeveloperWebhookRetryWorkerRunRead,
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


async def create_developer_oauth_authorization(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: DeveloperOAuthAuthorizationCreate,
    authz: AuthorizationService,
) -> DeveloperOAuthAuthorizationRead:
    application = await get_developer_application_by_client_id(db, payload.client_id)
    if application.status != "active":
        raise HTTPException(status_code=422, detail="Developer application is not active")
    if application.organization_id != payload.organization_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Application belongs to another organization")
    await ensure_manage_developer_platform(authz, identity, payload.organization_id)
    allowed_redirects = set(unpack_list(application.redirect_uris))
    if payload.redirect_uri not in allowed_redirects:
        raise HTTPException(status_code=422, detail="Redirect URI is not registered for this application")
    application_scopes = set(unpack_list(application.scopes))
    requested_scopes = [scope for scope in payload.scopes if scope in application_scopes]
    if len(requested_scopes) != len(payload.scopes):
        raise HTTPException(status_code=422, detail="Requested scope is not allowed for this application")
    code_challenge_method = normalized_pkce_method(payload.code_challenge, payload.code_challenge_method)
    authorization_code = token_urlsafe(32)
    now = datetime.now(UTC)
    authorization = DeveloperOAuthAuthorization(
        organization_id=payload.organization_id,
        application_id=application.id,
        user_person_id=identity.person_id,
        redirect_uri=payload.redirect_uri,
        requested_scopes=pack_list(payload.scopes),
        granted_scopes=pack_list(requested_scopes),
        state=payload.state,
        code_hash=hash_secret(authorization_code),
        code_challenge=payload.code_challenge,
        code_challenge_method=code_challenge_method,
        status="granted",
        expires_at=now + timedelta(minutes=10),
        consented_at=now,
    )
    db.add(authorization)
    await db.commit()
    await db.refresh(authorization)
    return oauth_authorization_read(application, authorization, authorization_code=authorization_code)


async def list_developer_oauth_authorizations(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[DeveloperOAuthAuthorizationRead]:
    await ensure_manage_developer_platform(authz, identity, organization_id)
    authorizations = list(
        (
            await db.scalars(
                select(DeveloperOAuthAuthorization)
                .where(DeveloperOAuthAuthorization.organization_id == organization_id)
                .order_by(DeveloperOAuthAuthorization.created_at.desc())
                .limit(100)
            )
        ).all()
    )
    if not authorizations:
        return []
    applications = {
        application.id: application
        for application in (
            await db.scalars(
                select(DeveloperApplication).where(
                    DeveloperApplication.id.in_({authorization.application_id for authorization in authorizations})
                )
            )
        ).all()
    }
    return [
        oauth_authorization_read(applications[authorization.application_id], authorization)
        for authorization in authorizations
        if authorization.application_id in applications
    ]


async def exchange_developer_oauth_token(
    db: AsyncSession,
    payload: DeveloperOAuthTokenExchange,
) -> DeveloperOAuthTokenRead:
    application = await get_developer_application_by_client_id(db, payload.client_id)
    if application.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OAuth client credentials")
    authorization = await db.scalar(
        select(DeveloperOAuthAuthorization).where(
            DeveloperOAuthAuthorization.application_id == application.id,
            DeveloperOAuthAuthorization.code_hash == hash_secret(payload.code),
        )
    )
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OAuth authorization code")
    now = datetime.now(UTC)
    if authorization.status != "granted":
        raise HTTPException(status_code=422, detail="OAuth authorization code has already been used")
    if authorization.redirect_uri != payload.redirect_uri:
        raise HTTPException(status_code=422, detail="Redirect URI does not match authorization")
    if as_utc(authorization.expires_at) <= now:
        authorization.status = "expired"
        await db.commit()
        raise HTTPException(status_code=422, detail="OAuth authorization code has expired")
    if authorization.code_challenge:
        verify_pkce_challenge(authorization, payload.code_verifier)
    elif payload.client_secret is None or application.client_secret_hash != hash_secret(payload.client_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OAuth client credentials")
    refresh_family_id = uuid4()
    raw_key, refresh_token, api_key = build_oauth_api_key(
        authorization.organization_id,
        application.id,
        authorization.granted_scopes,
        now=now,
        token_label=str(authorization.id)[:8],
        notes=f"OAuth token minted from authorization {authorization.id}",
        refresh_family_id=refresh_family_id,
    )
    authorization.status = "redeemed"
    authorization.redeemed_at = now
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return DeveloperOAuthTokenRead(
        access_token=raw_key,
        refresh_token=refresh_token,
        token_type="AfroleteApiKey",
        auth_header="X-Afrolete-API-Key",
        api_key=developer_api_key_read(api_key),
        scopes=unpack_list(api_key.scopes),
        expires_in=30 * 24 * 60 * 60,
        refresh_expires_in=90 * 24 * 60 * 60,
    )


async def refresh_developer_oauth_token(
    db: AsyncSession,
    payload: DeveloperOAuthRefreshTokenExchange,
) -> DeveloperOAuthTokenRead:
    application = await get_developer_application_by_client_id(db, payload.client_id)
    if application.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OAuth refresh client")
    current_key = await db.scalar(
        select(DeveloperApiKey).where(
            DeveloperApiKey.application_id == application.id,
            DeveloperApiKey.refresh_token_hash == hash_secret(payload.refresh_token),
        )
    )
    now = datetime.now(UTC)
    if current_key is None or current_key.environment != "oauth" or current_key.status != "active":
        await mark_reused_refresh_family(db, application.id, payload.refresh_token, now)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OAuth refresh token")
    if current_key.refresh_expires_at is None or as_utc(current_key.refresh_expires_at) <= now:
        current_key.status = "expired"
        current_key.refresh_token_hash = None
        await db.commit()
        raise HTTPException(status_code=422, detail="OAuth refresh token has expired")
    raw_key, refresh_token, new_key = build_oauth_api_key(
        current_key.organization_id,
        current_key.application_id,
        current_key.scopes,
        now=now,
        token_label=f"refresh {str(current_key.id)[:8]}",
        notes=f"OAuth token rotated from {current_key.id}",
        refresh_family_id=current_key.refresh_token_family_id or uuid4(),
        refresh_parent_key_id=current_key.id,
    )
    current_key.status = "revoked"
    current_key.notes = (
        f"{current_key.notes or ''}\nRotated refresh token hash: {current_key.refresh_token_hash}".strip()
    )
    current_key.refresh_token_hash = None
    current_key.refresh_rotated_at = now
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    return DeveloperOAuthTokenRead(
        access_token=raw_key,
        refresh_token=refresh_token,
        token_type="AfroleteApiKey",
        auth_header="X-Afrolete-API-Key",
        api_key=developer_api_key_read(new_key),
        scopes=unpack_list(new_key.scopes),
        expires_in=30 * 24 * 60 * 60,
        refresh_expires_in=90 * 24 * 60 * 60,
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
    expires_at = as_utc(api_key.expires_at)
    if expires_at is not None and expires_at <= datetime.now(UTC):
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


async def retry_developer_webhook_deliveries(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
    *,
    max_attempts: int = 3,
    limit: int = 25,
    include_recorded: bool = False,
) -> DeveloperWebhookRetryRunRead:
    await ensure_manage_developer_platform(authz, identity, organization_id)
    worker_run = await run_developer_webhook_retry_due(
        db,
        organization_id=organization_id,
        max_attempts=max_attempts,
        limit=limit,
        include_recorded=include_recorded,
    )
    return DeveloperWebhookRetryRunRead(
        organization_id=organization_id,
        eligible_count=worker_run.eligible_count,
        replayed_count=worker_run.replayed_count,
        skipped_count=worker_run.skipped_count,
        failed_count=worker_run.failed_count,
        delivery_ids=worker_run.delivery_ids,
        statuses=worker_run.statuses,
        max_attempts=worker_run.max_attempts,
        include_recorded=worker_run.include_recorded,
    )


async def run_developer_webhook_retry_due(
    db: AsyncSession,
    *,
    organization_id: UUID | None = None,
    max_attempts: int = 3,
    limit: int = 25,
    include_recorded: bool = False,
) -> DeveloperWebhookRetryWorkerRunRead:
    retry_statuses = ["failed", "queued"]
    if include_recorded:
        retry_statuses.append("recorded")
    now = datetime.now(UTC)
    statement = select(DeveloperWebhookDelivery).where(
        DeveloperWebhookDelivery.status.in_(retry_statuses),
        DeveloperWebhookDelivery.attempt_count < max_attempts,
        or_(
            DeveloperWebhookDelivery.next_attempt_at.is_(None),
            DeveloperWebhookDelivery.next_attempt_at <= now,
        ),
    )
    if organization_id is not None:
        statement = statement.where(DeveloperWebhookDelivery.organization_id == organization_id)
    deliveries = list(
        (
            await db.scalars(
                statement.order_by(
                    DeveloperWebhookDelivery.next_attempt_at.asc().nulls_first(),
                    DeveloperWebhookDelivery.created_at.asc(),
                )
                .limit(limit)
            )
        ).all()
    )
    replayed_count = 0
    skipped_count = 0
    for delivery in deliveries:
        subscription = await db.get(DeveloperWebhookSubscription, delivery.subscription_id)
        if subscription is None or subscription.status != "active":
            skipped_count += 1
            continue
        delivery.status = "queued"
        delivery.failure_reason = None
        delivery.response_status_code = None
        delivery.delivered_at = None
        await deliver_single_webhook(db, subscription, delivery)
        replayed_count += 1
    await db.commit()
    statuses: dict[str, int] = {}
    for delivery in deliveries:
        await db.refresh(delivery)
        statuses[delivery.status] = statuses.get(delivery.status, 0) + 1
    return DeveloperWebhookRetryWorkerRunRead(
        organization_id=organization_id,
        eligible_count=len(deliveries),
        replayed_count=replayed_count,
        skipped_count=skipped_count,
        failed_count=statuses.get("failed", 0),
        delivery_ids=[delivery.id for delivery in deliveries],
        statuses=statuses,
        organization_count=len({delivery.organization_id for delivery in deliveries}),
        max_attempts=max_attempts,
        include_recorded=include_recorded,
    )


async def deliver_single_webhook(
    db: AsyncSession,
    subscription: DeveloperWebhookSubscription,
    delivery: DeveloperWebhookDelivery,
) -> None:
    now = datetime.now(UTC)
    delivery.attempt_count += 1
    delivery.last_attempted_at = now
    if subscription.delivery_mode == "record_only":
        delivery.status = "recorded"
        delivery.delivered_at = now
        delivery.next_attempt_at = None
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
            delivery.next_attempt_at = None
        else:
            delivery.status = "failed"
            delivery.failure_reason = f"Webhook returned {response.status_code}: {response.text[:500]}"
            delivery.next_attempt_at = next_webhook_attempt_at(now, delivery.attempt_count)
            subscription.failure_count += 1
    except httpx.HTTPError as error:
        delivery.status = "failed"
        delivery.failure_reason = f"Webhook delivery failed: {error}"
        delivery.next_attempt_at = next_webhook_attempt_at(now, delivery.attempt_count)
        subscription.failure_count += 1
    subscription.last_delivery_status = delivery.status
    subscription.last_delivered_at = delivery.delivered_at
    await db.flush()


def next_webhook_attempt_at(now: datetime, attempt_count: int) -> datetime:
    delay_seconds = min(60 * (2 ** max(attempt_count - 1, 0)), 60 * 60)
    return now + timedelta(seconds=delay_seconds)


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


async def developer_integration_catalog(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> DeveloperIntegrationCatalogRead:
    await ensure_manage_developer_platform(authz, identity, organization_id)
    subscriptions = list(
        (
            await db.scalars(
                select(DeveloperWebhookSubscription).where(
                    DeveloperWebhookSubscription.organization_id == organization_id
                )
            )
        ).all()
    )
    configured_event_types = sorted(
        {
            event_type
            for subscription in subscriptions
            for event_type in unpack_list(subscription.event_types)
        }
    )
    return DeveloperIntegrationCatalogRead(
        organization_id=organization_id,
        api_base_path="/api/v1/sdk",
        auth_header="X-Afrolete-API-Key",
        webhook_signature_header="X-Afrolete-Webhook-Signature",
        scopes=developer_scope_catalog(),
        webhook_events=developer_webhook_event_catalog(),
        sdks=developer_sdk_catalog(),
        configured_event_types=configured_event_types,
    )


def developer_public_docs() -> DeveloperPublicDocsRead:
    return DeveloperPublicDocsRead(
        title="AfroLete Developer Platform",
        version="v1",
        api_base_path="/api/v1/sdk",
        authentication="Send tenant developer API keys in the X-Afrolete-API-Key header.",
        auth_header="X-Afrolete-API-Key",
        webhook_signature_header="X-Afrolete-Webhook-Signature",
        webhook_timestamp_header="X-Afrolete-Webhook-Timestamp",
        quickstarts=developer_quickstarts(),
        scopes=developer_scope_catalog(),
        webhook_events=developer_webhook_event_catalog(),
        sdks=developer_sdk_catalog(),
        marketplace_categories=[
            "operations",
            "performance",
            "communications",
            "billing",
            "compliance",
            "ai_agents",
            "media",
            "hardware",
        ],
        security_requirements=[
            "Store raw API keys and webhook signing secrets outside source control.",
            "Use sandbox keys until the tenant has approved production access.",
            "Verify webhook signatures with the timestamped payload before trusting event bodies.",
            "Request only the scopes needed for the integration workflow.",
            "Treat cataloged webhook events as contracts in progress unless emission_status is active.",
        ],
    )


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


def developer_api_key_read(api_key: DeveloperApiKey) -> DeveloperApiKeyRead:
    return DeveloperApiKeyRead(
        id=api_key.id,
        organization_id=api_key.organization_id,
        application_id=api_key.application_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=unpack_list(api_key.scopes),
        environment=api_key.environment,
        status=api_key.status,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        last_used_ip=api_key.last_used_ip,
        usage_count=api_key.usage_count,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        window_started_at=api_key.window_started_at,
        window_request_count=api_key.window_request_count,
        last_rate_limited_at=api_key.last_rate_limited_at,
        refresh_token_family_id=api_key.refresh_token_family_id,
        refresh_parent_key_id=api_key.refresh_parent_key_id,
        refresh_expires_at=api_key.refresh_expires_at,
        refresh_rotated_at=api_key.refresh_rotated_at,
        refresh_reused_at=api_key.refresh_reused_at,
        notes=api_key.notes,
    )


async def mark_reused_refresh_family(
    db: AsyncSession,
    application_id: UUID,
    refresh_token: str,
    detected_at: datetime,
) -> None:
    reused_key = await db.scalar(
        select(DeveloperApiKey).where(
            DeveloperApiKey.application_id == application_id,
            DeveloperApiKey.environment == "oauth",
            DeveloperApiKey.notes.contains(hash_secret(refresh_token)),
        )
    )
    if reused_key is None or reused_key.refresh_token_family_id is None:
        return
    reused_key.refresh_reused_at = detected_at
    family_keys = list(
        (
            await db.scalars(
                select(DeveloperApiKey).where(
                    DeveloperApiKey.application_id == application_id,
                    DeveloperApiKey.refresh_token_family_id == reused_key.refresh_token_family_id,
                    DeveloperApiKey.environment == "oauth",
                )
            )
        ).all()
    )
    incident = await create_oauth_refresh_compromise_incident(db, reused_key, family_keys, detected_at)
    for family_key in family_keys:
        family_key.status = "revoked"
        family_key.refresh_token_hash = None
        family_key.refresh_rotated_at = family_key.refresh_rotated_at or detected_at
        if "refresh token family compromised" not in (family_key.notes or ""):
            family_key.notes = (
                f"{family_key.notes or ''}\nOAuth refresh token family compromised at "
                f"{detected_at.isoformat()} after security incident {incident.id}."
            ).strip()
    await db.commit()


async def create_oauth_refresh_compromise_incident(
    db: AsyncSession,
    reused_key: DeveloperApiKey,
    family_keys: list[DeveloperApiKey],
    detected_at: datetime,
) -> SafeguardingIncident:
    open_statuses = (
        SafeguardingIncidentStatus.OPEN,
        SafeguardingIncidentStatus.TRIAGED,
        SafeguardingIncidentStatus.INVESTIGATING,
    )
    family_id = str(reused_key.refresh_token_family_id)
    existing_incident = await db.scalar(
        select(SafeguardingIncident)
        .where(
            SafeguardingIncident.organization_id == reused_key.organization_id,
            SafeguardingIncident.incident_type == SafeguardingIncidentType.SECURITY,
            SafeguardingIncident.status.in_(open_statuses),
            SafeguardingIncident.description.contains(family_id),
        )
        .order_by(SafeguardingIncident.created_at.desc())
    )
    if existing_incident is not None:
        return existing_incident

    incident = SafeguardingIncident(
        organization_id=reused_key.organization_id,
        incident_type=SafeguardingIncidentType.SECURITY,
        severity=SafeguardingIncidentSeverity.HIGH,
        status=SafeguardingIncidentStatus.OPEN,
        occurred_at=detected_at,
        location="Developer OAuth",
        title="OAuth refresh-token replay detected",
        description=(
            "A previously rotated OAuth refresh token was presented again. "
            f"Application ID: {reused_key.application_id}. "
            f"Refresh-token family ID: {family_id}. "
            f"Reused key ID: {reused_key.id}. "
            f"Affected OAuth key count: {len(family_keys)}. "
            f"Detected at: {detected_at.isoformat()}."
        ),
        immediate_action="Revoked active OAuth tokens in the compromised refresh-token family.",
        medical_follow_up_required="not_applicable",
        regulatory_report_required=False,
    )
    db.add(incident)
    await db.flush()
    return incident


def build_oauth_api_key(
    organization_id: UUID,
    application_id: UUID,
    scopes: str,
    *,
    now: datetime,
    token_label: str,
    notes: str,
    refresh_family_id: UUID,
    refresh_parent_key_id: UUID | None = None,
) -> tuple[str, str, DeveloperApiKey]:
    raw_key = build_api_key("oauth", "oauth")
    refresh_token = token_urlsafe(40)
    api_key = DeveloperApiKey(
        organization_id=organization_id,
        application_id=application_id,
        name=f"OAuth token {token_label}",
        key_prefix=raw_key.split(".", 1)[0],
        key_hash=hash_secret(raw_key),
        scopes=scopes,
        environment="oauth",
        rate_limit_per_minute=600,
        expires_at=now + timedelta(days=30),
        refresh_token_hash=hash_secret(refresh_token),
        refresh_token_family_id=refresh_family_id,
        refresh_parent_key_id=refresh_parent_key_id,
        refresh_expires_at=now + timedelta(days=90),
        notes=notes,
    )
    return raw_key, refresh_token, api_key


def oauth_authorization_read(
    application: DeveloperApplication,
    authorization: DeveloperOAuthAuthorization,
    *,
    authorization_code: str | None = None,
) -> DeveloperOAuthAuthorizationRead:
    redirect_url = None
    if authorization_code is not None:
        separator = "&" if "?" in authorization.redirect_uri else "?"
        parameters = {"code": authorization_code}
        if authorization.state:
            parameters["state"] = authorization.state
        redirect_url = f"{authorization.redirect_uri}{separator}{urlencode(parameters)}"
    return DeveloperOAuthAuthorizationRead(
        id=authorization.id,
        organization_id=authorization.organization_id,
        application_id=authorization.application_id,
        client_id=application.client_id,
        application_name=application.name,
        redirect_uri=authorization.redirect_uri,
        requested_scopes=unpack_list(authorization.requested_scopes),
        granted_scopes=unpack_list(authorization.granted_scopes),
        state=authorization.state,
        code_challenge_method=authorization.code_challenge_method,
        public_client=authorization.code_challenge is not None,
        status=authorization.status,
        expires_at=authorization.expires_at,
        consented_at=authorization.consented_at,
        redeemed_at=authorization.redeemed_at,
        authorization_code=authorization_code,
        redirect_url=redirect_url,
    )


def normalized_pkce_method(code_challenge: str | None, code_challenge_method: str | None) -> str | None:
    if code_challenge is None:
        if code_challenge_method:
            raise HTTPException(status_code=422, detail="PKCE code challenge method requires a code challenge")
        return None
    method = code_challenge_method or "S256"
    if method not in {"S256", "plain"}:
        raise HTTPException(status_code=422, detail="Unsupported PKCE code challenge method")
    return method


def verify_pkce_challenge(authorization: DeveloperOAuthAuthorization, code_verifier: str | None) -> None:
    if not code_verifier:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OAuth PKCE verifier is required")
    method = authorization.code_challenge_method or "S256"
    if method == "plain":
        actual_challenge = code_verifier
    else:
        actual_challenge = urlsafe_b64encode(sha256(code_verifier.encode("utf-8")).digest()).decode("ascii").rstrip("=")
    if not hmac.compare_digest(actual_challenge, authorization.code_challenge or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OAuth PKCE verifier is invalid")


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


async def get_developer_application_by_client_id(db: AsyncSession, client_id: str) -> DeveloperApplication:
    application = await db.scalar(select(DeveloperApplication).where(DeveloperApplication.client_id == client_id))
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


def developer_scope_catalog() -> list[DeveloperApiScopeCatalogRead]:
    return [
        DeveloperApiScopeCatalogRead(
            scope="read:organization",
            category="organization",
            description="Read tenant identity, branding, and public profile metadata.",
            recommended_for=["directory sync", "public site integrations", "analytics imports"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="write:events",
            category="events",
            description="Create or update tenant event, fixture, and scheduling records.",
            recommended_for=["calendar sync", "competition systems", "facility schedulers"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="read:events",
            category="events",
            description="Read tenant event, fixture, schedule, and travel-adjacent event metadata.",
            recommended_for=["calendar sync", "competition portals", "fan engagement"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="read:teams",
            category="teams",
            description="Read tenant team directory metadata for roster, schedule, and directory integrations.",
            recommended_for=["team websites", "fixture imports", "roster-aware analytics"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="write:teams",
            category="teams",
            description="Create tenant team records through SDK routes.",
            recommended_for=["league onboarding", "school SIS sync", "club management imports"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="write:roster",
            category="teams",
            description="Assign existing people to team rosters through SDK routes.",
            recommended_for=["club management imports", "school SIS sync", "roster automation"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="write:people",
            category="people",
            description="Create or reuse tenant person records and attach organization membership.",
            recommended_for=["registration imports", "school SIS sync", "club member onboarding"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="write:guardians",
            category="safeguarding",
            description="Link parents or guardians to athlete person records through SDK routes.",
            recommended_for=["minor onboarding", "school SIS sync", "guardian consent preparation"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="write:consent",
            category="safeguarding",
            description="Create one-use guardian consent requests through SDK routes.",
            recommended_for=["minor onboarding", "event consent automation", "school trip imports"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="read:training",
            category="training",
            description="Read training drill library records through SDK routes.",
            recommended_for=["training libraries", "AI coaching tools", "session planners"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="write:training",
            category="training",
            description="Create training drills and coaching-plan inputs through SDK routes.",
            recommended_for=["training libraries", "AI coaching tools", "session planners"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="read:performance",
            category="performance",
            description="Read athlete observations, assessments, and performance summaries.",
            recommended_for=["analytics dashboards", "scouting tools", "wearable imports"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="write:performance",
            category="performance",
            description="Submit reviewed or provider-sourced performance observations.",
            recommended_for=["video analysis", "wearables", "AI evidence ingestion"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="read:communications",
            category="communications",
            description="Read communication templates and delivery status metadata.",
            recommended_for=["CRM sync", "guardian engagement", "message analytics"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="write:communications",
            category="communications",
            description="Request tenant-scoped communication delivery through approved channels.",
            recommended_for=["notification providers", "fan engagement", "emergency messaging"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="read:billing",
            category="billing",
            description="Read subscription, invoice, entitlement, and marketplace commerce metadata.",
            recommended_for=["accounting sync", "marketplace analytics", "finance dashboards"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="write:billing",
            category="billing",
            description="Submit approved billing, payment, and settlement updates.",
            recommended_for=["payment processors", "tax filing adapters", "accounting systems"],
        ),
        DeveloperApiScopeCatalogRead(
            scope="admin:*",
            category="administration",
            description="Administrative tenant access for deeply trusted internal integrations.",
            recommended_for=["first-party automation", "migration tooling", "tenant operations"],
        ),
    ]


def developer_webhook_event_catalog() -> list[DeveloperWebhookEventCatalogRead]:
    return [
        DeveloperWebhookEventCatalogRead(
            event_type="training.drill.created",
            category="training",
            description="A developer API key created a tenant training drill.",
            emission_status="active",
            payload_fields=["organization_id", "drill_id", "sport", "name", "focus_area", "source"],
            recommended_scopes=["write:training"],
            example_payload={
                "organization_id": "tenant-uuid",
                "drill_id": "drill-uuid",
                "sport": "football",
                "name": "Advanced Passing Circuit",
                "focus_area": "Passing",
                "source": "developer_api",
            },
        ),
        DeveloperWebhookEventCatalogRead(
            event_type="events.created",
            category="events",
            description="A developer API key created a tenant event or fixture.",
            emission_status="active",
            payload_fields=["organization_id", "id", "team_id", "event_type", "title", "starts_at", "source"],
            recommended_scopes=["write:events"],
            example_payload={
                "organization_id": "tenant-uuid",
                "id": "event-uuid",
                "team_id": "team-uuid",
                "event_type": "match",
                "title": "U17 League Match",
                "starts_at": "2026-06-01T15:00:00Z",
                "source": "developer_api",
            },
        ),
        DeveloperWebhookEventCatalogRead(
            event_type="events.updated",
            category="events",
            description="A tenant event, fixture, travel movement, or attendance-critical schedule changed.",
            emission_status="cataloged",
            payload_fields=["organization_id", "event_id", "change_type", "updated_at"],
            recommended_scopes=["write:events"],
            example_payload={
                "organization_id": "tenant-uuid",
                "event_id": "event-uuid",
                "change_type": "time_changed",
                "updated_at": "2026-06-01T10:00:00Z",
            },
        ),
        DeveloperWebhookEventCatalogRead(
            event_type="performance.observation.created",
            category="performance",
            description="A performance observation has been created or accepted from an evidence pipeline.",
            emission_status="active",
            payload_fields=[
                "organization_id",
                "athlete_profile_id",
                "metric_definition_id",
                "metric_code",
                "value",
                "confidence",
                "verification_status",
            ],
            recommended_scopes=["write:performance"],
            example_payload={
                "organization_id": "tenant-uuid",
                "athlete_profile_id": "athlete-profile-uuid",
                "metric_definition_id": "metric-uuid",
                "metric_code": "sprint_speed",
                "value": 8.7,
                "confidence": 0.91,
                "verification_status": "pending_review",
            },
        ),
        DeveloperWebhookEventCatalogRead(
            event_type="consent.granted",
            category="safeguarding",
            description="A guardian or authorized contact granted consent for a minor activity.",
            emission_status="cataloged",
            payload_fields=["organization_id", "minor_person_id", "guardian_person_id", "scope_type", "scope_id"],
            recommended_scopes=["read:communications"],
            example_payload={
                "organization_id": "tenant-uuid",
                "minor_person_id": "person-uuid",
                "guardian_person_id": "guardian-uuid",
                "scope_type": "event",
                "scope_id": "event-uuid",
            },
        ),
        DeveloperWebhookEventCatalogRead(
            event_type="agent.task.completed",
            category="ai_agents",
            description="A first-class AfroLete AI agent completed a tenant-scoped task.",
            emission_status="cataloged",
            payload_fields=["organization_id", "agent_id", "task_id", "task_type", "review_status"],
            recommended_scopes=["read:organization"],
            example_payload={
                "organization_id": "tenant-uuid",
                "agent_id": "agent-uuid",
                "task_id": "task-uuid",
                "task_type": "scorecard_anomaly_review",
                "review_status": "pending_human_review",
            },
        ),
        DeveloperWebhookEventCatalogRead(
            event_type="billing.invoice.paid",
            category="billing",
            description="A SaaS or tenant invoice was reconciled as paid.",
            emission_status="cataloged",
            payload_fields=["organization_id", "invoice_id", "provider", "amount_paid", "currency"],
            recommended_scopes=["read:billing", "write:billing"],
            example_payload={
                "organization_id": "tenant-uuid",
                "invoice_id": "invoice-uuid",
                "provider": "stripe",
                "amount_paid": "159.00",
                "currency": "USD",
            },
        ),
    ]


def developer_sdk_catalog() -> list[DeveloperSdkCatalogRead]:
    return [
        DeveloperSdkCatalogRead(
            language="TypeScript",
            package_name="@afrolete/sdk",
            install_command="pnpm add @afrolete/sdk",
            status="repository_package",
            entry_points=[
                "client.me",
                "client.organization.get",
                "client.people.create",
                "client.people.linkGuardian",
                "client.people.createConsentRequest",
                "client.teams.list",
                "client.teams.create",
                "client.teams.addMember",
                "client.events.list",
                "client.events.create",
                "client.performance.metrics.list",
                "client.performance.observations.list",
                "client.performance.observations.create",
                "client.training.drills.list",
                "client.training.drills.create",
            ],
        ),
        DeveloperSdkCatalogRead(
            language="Python",
            package_name="afrolete-sdk",
            install_command="uv add afrolete-sdk",
            status="repository_package",
            entry_points=[
                "client.me",
                "client.organization.get",
                "client.people.create",
                "client.people.link_guardian",
                "client.people.create_consent_request",
                "client.teams.list",
                "client.teams.create",
                "client.teams.add_member",
                "client.events.list",
                "client.events.create",
                "client.performance.metrics.list",
                "client.performance.observations.list",
                "client.performance.observations.create",
                "client.training.drills.list",
                "client.training.drills.create",
            ],
        ),
        DeveloperSdkCatalogRead(
            language="Raw HTTP",
            package_name="OpenAPI",
            install_command="curl -H 'X-Afrolete-API-Key: ...' /api/v1/sdk/me",
            status="active",
            entry_points=[
                "GET /sdk/me",
                "GET /sdk/organization",
                "POST /sdk/people",
                "POST /sdk/people/{athlete_person_id}/guardians",
                "POST /sdk/people/{athlete_person_id}/consent-requests",
                "GET /sdk/teams",
                "POST /sdk/teams",
                "POST /sdk/teams/{team_id}/members",
                "GET /sdk/events",
                "POST /sdk/events",
                "GET /sdk/performance/metrics",
                "GET /sdk/performance/athletes/{athlete_profile_id}/observations",
                "POST /sdk/performance/athletes/{athlete_profile_id}/observations",
                "GET /sdk/training/drills",
                "POST /sdk/training/drills",
            ],
        ),
    ]


def developer_quickstarts() -> list[DeveloperQuickstartRead]:
    return [
        DeveloperQuickstartRead(
            title="Inspect an API key",
            language="HTTP",
            description="Confirm a tenant-issued API key and learn its application, scopes, and quota state.",
            steps=[
                "Create or select an active developer application in the tenant console.",
                "Issue a sandbox API key and copy the raw key immediately.",
                "Call /api/v1/developers/auth/inspect with X-Afrolete-API-Key.",
            ],
            code_sample=(
                "curl -s \"$AFROLETE_API/api/v1/developers/auth/inspect\" \\\n"
                "  -H \"X-Afrolete-API-Key: $AFROLETE_API_KEY\""
            ),
        ),
        DeveloperQuickstartRead(
            title="Create a training drill",
            language="HTTP",
            description="Write training-library content into a tenant using the SDK route protected by write:training.",
            steps=[
                "Grant the API key write:training for the tenant.",
                "POST a drill payload to /api/v1/sdk/training/drills.",
                "Subscribe to training.drill.created to fan out the event to external systems.",
            ],
            code_sample=(
                "curl -s \"$AFROLETE_API/api/v1/sdk/training/drills\" \\\n"
                "  -H \"Content-Type: application/json\" \\\n"
                "  -H \"X-Afrolete-API-Key: $AFROLETE_API_KEY\" \\\n"
                "  -d '{\"organization_id\":\"'$ORG_ID'\",\"sport\":\"football\","
                "\"name\":\"Advanced Passing Circuit\",\"focus_area\":\"Passing\","
                "\"category\":\"technical\",\"description\":\"One-touch passing square.\"}'"
            ),
        ),
        DeveloperQuickstartRead(
            title="Create a tenant event",
            language="HTTP",
            description="Create a tenant schedule item through the SDK route protected by write:events.",
            steps=[
                "Grant the API key write:events for the tenant.",
                "POST an event payload to /api/v1/sdk/events.",
                "Subscribe to events.created to fan out schedule creation to external systems.",
            ],
            code_sample=(
                "curl -s \"$AFROLETE_API/api/v1/sdk/events\" \\\n"
                "  -H \"Content-Type: application/json\" \\\n"
                "  -H \"X-Afrolete-API-Key: $AFROLETE_API_KEY\" \\\n"
                "  -d '{\"organization_id\":\"'$ORG_ID'\",\"event_type\":\"match\","
                "\"title\":\"U17 League Match\",\"starts_at\":\"2026-06-01T15:00:00Z\"}'"
            ),
        ),
        DeveloperQuickstartRead(
            title="Use the TypeScript SDK",
            language="TypeScript",
            description="Call tenant SDK routes from a typed client using the same X-Afrolete-API-Key boundary.",
            steps=[
                "Install @afrolete/sdk from the repository package or future registry package.",
                "Create an AfroLeteClient with baseUrl and a tenant-issued API key.",
                "Call organization, event, or training drill helpers instead of hand-building SDK URLs.",
            ],
            code_sample=(
                "import { AfroLeteClient } from \"@afrolete/sdk\";\n\n"
                "const client = new AfroLeteClient({\n"
                "  baseUrl: process.env.AFROLETE_API!,\n"
                "  apiKey: process.env.AFROLETE_API_KEY!,\n"
                "});\n\n"
                "const events = await client.events.list({ organizationId: process.env.AFROLETE_ORG_ID! });"
            ),
        ),
        DeveloperQuickstartRead(
            title="Use the Python SDK",
            language="Python",
            description="Use the repository Python package for server-side integrations and scheduled sync jobs.",
            steps=[
                "Install afrolete-sdk from the repository package or future registry package.",
                "Create an AfroLeteClient with base_url and a tenant-issued API key.",
                "Call organization, teams, events, or training drill helpers from integration jobs.",
            ],
            code_sample=(
                "from afrolete_sdk import AfroLeteClient\n\n"
                "client = AfroLeteClient(\n"
                "    base_url=\"https://api.afrolete.example\",\n"
                "    api_key=\"afl_live_example\",\n"
                ")\n\n"
                "teams = client.teams.list(organization_id=\"tenant-uuid\")"
            ),
        ),
        DeveloperQuickstartRead(
            title="Exchange an OAuth code",
            language="HTTP",
            description="Redeem a tenant-approved authorization code for an expiring AfroLete API token with client-secret or PKCE proof.",
            steps=[
                "Register a developer application with a redirect URI and allowed scopes.",
                "Ask a tenant manager to grant OAuth consent for the requested scopes and optional PKCE code challenge.",
                "POST the authorization code, redirect URI, and either client_secret or code_verifier to /api/v1/developers/oauth/token.",
            ],
            code_sample=(
                "curl -s \"$AFROLETE_API/api/v1/developers/oauth/token\" \\\n"
                "  -H \"Content-Type: application/json\" \\\n"
                "  -d '{\"client_id\":\"'$CLIENT_ID'\",\"client_secret\":\"'$CLIENT_SECRET'\","
                "\"code\":\"'$AUTH_CODE'\",\"redirect_uri\":\"https://sync.example/callback\"}'"
            ),
        ),
        DeveloperQuickstartRead(
            title="Rotate a refresh token",
            language="HTTP",
            description="Exchange a valid refresh token for a new access token and replacement refresh token.",
            steps=[
                "Store refresh tokens outside source control and browser-visible logs.",
                "POST client_id and refresh_token to /api/v1/developers/oauth/refresh.",
                "Replace both stored tokens; the previous access token and refresh token are revoked.",
            ],
            code_sample=(
                "curl -s \"$AFROLETE_API/api/v1/developers/oauth/refresh\" \\\n"
                "  -H \"Content-Type: application/json\" \\\n"
                "  -d '{\"client_id\":\"'$CLIENT_ID'\",\"refresh_token\":\"'$REFRESH_TOKEN'\"}'"
            ),
        ),
        DeveloperQuickstartRead(
            title="Verify a webhook",
            language="TypeScript",
            description="Validate provider-neutral AfroLete webhooks before processing event payloads.",
            steps=[
                "Read the raw request body before JSON parsing.",
                "Build timestamp.payload and compare the HMAC SHA-256 signature.",
                "Reject old timestamps or mismatched signatures.",
            ],
            code_sample=(
                "const signed = `${timestamp}.${rawBody}`;\n"
                "const expected = hmacSha256(signingSecretHash, signed);\n"
                "if (`sha256=${expected}` !== signatureHeader) throw new Error(\"bad signature\");"
            ),
        ),
    ]


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
