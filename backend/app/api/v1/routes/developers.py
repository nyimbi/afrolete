from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.developer import (
    DeveloperApiKeyCreate,
    DeveloperApiKeyInspectionRead,
    DeveloperApiKeyProvisionedRead,
    DeveloperApiKeyRead,
    DeveloperApplicationCreate,
    DeveloperApplicationProvisionedRead,
    DeveloperApplicationRead,
    DeveloperIntegrationCatalogRead,
    DeveloperMarketplaceListingCreate,
    DeveloperMarketplaceListingRead,
    DeveloperMarketplaceListingReview,
    DeveloperPortalSummaryRead,
    DeveloperPublicDocsRead,
    DeveloperWebhookDeliveryRead,
    DeveloperWebhookRetryRunRead,
    DeveloperWebhookSubscriptionCreate,
    DeveloperWebhookSubscriptionProvisionedRead,
    DeveloperWebhookSubscriptionRead,
    DeveloperWebhookSubscriptionUpdate,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.developer import (
    create_developer_api_key,
    create_developer_application,
    create_developer_marketplace_listing,
    create_developer_webhook_subscription,
    developer_integration_catalog,
    developer_portal_summary,
    developer_public_docs,
    inspect_developer_api_key,
    list_developer_api_keys,
    list_developer_applications,
    list_developer_marketplace_listings,
    list_developer_webhook_deliveries,
    list_developer_webhook_subscriptions,
    record_developer_marketplace_install,
    replay_developer_webhook_delivery,
    revoke_developer_api_key,
    review_developer_marketplace_listing,
    rotate_developer_application_secret,
    retry_developer_webhook_deliveries,
    unpack_list,
    update_developer_webhook_subscription,
)

router = APIRouter(prefix="/developers", tags=["developers"])


def application_read(application) -> DeveloperApplicationRead:
    return DeveloperApplicationRead(
        id=application.id,
        organization_id=application.organization_id,
        owner_person_id=application.owner_person_id,
        name=application.name,
        app_type=application.app_type,
        client_id=application.client_id,
        redirect_uris=unpack_list(application.redirect_uris),
        scopes=unpack_list(application.scopes),
        contact_email=application.contact_email,
        status=application.status,
        last_rotated_at=application.last_rotated_at,
        notes=application.notes,
    )


def api_key_read(api_key) -> DeveloperApiKeyRead:
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
        notes=api_key.notes,
    )


def webhook_subscription_read(subscription) -> DeveloperWebhookSubscriptionRead:
    return DeveloperWebhookSubscriptionRead(
        id=subscription.id,
        organization_id=subscription.organization_id,
        application_id=subscription.application_id,
        name=subscription.name,
        target_url=subscription.target_url,
        event_types=unpack_list(subscription.event_types),
        delivery_mode=subscription.delivery_mode,
        status=subscription.status,
        failure_count=subscription.failure_count,
        last_delivery_status=subscription.last_delivery_status,
        last_delivered_at=subscription.last_delivered_at,
    )


def webhook_delivery_read(delivery) -> DeveloperWebhookDeliveryRead:
    return DeveloperWebhookDeliveryRead(
        id=delivery.id,
        organization_id=delivery.organization_id,
        subscription_id=delivery.subscription_id,
        application_id=delivery.application_id,
        event_type=delivery.event_type,
        event_id=delivery.event_id,
        target_url=delivery.target_url,
        delivery_mode=delivery.delivery_mode,
        status=delivery.status,
        attempt_count=delivery.attempt_count,
        response_status_code=delivery.response_status_code,
        failure_reason=delivery.failure_reason,
        delivered_at=delivery.delivered_at,
    )


def marketplace_listing_read(listing) -> DeveloperMarketplaceListingRead:
    return DeveloperMarketplaceListingRead(
        id=listing.id,
        organization_id=listing.organization_id,
        application_id=listing.application_id,
        name=listing.name,
        category=listing.category,
        summary=listing.summary,
        install_url=listing.install_url,
        support_url=listing.support_url,
        pricing_model=listing.pricing_model,
        version=listing.version,
        visibility=listing.visibility,
        review_status=listing.review_status,
        install_count=listing.install_count,
    )


@router.get("/public/docs", response_model=DeveloperPublicDocsRead)
async def developer_public_docs_route() -> DeveloperPublicDocsRead:
    return developer_public_docs()


@router.post("/api-keys", response_model=DeveloperApiKeyProvisionedRead, status_code=status.HTTP_201_CREATED)
async def create_developer_api_key_route(
    payload: DeveloperApiKeyCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperApiKeyProvisionedRead:
    api_key, key = await create_developer_api_key(db, identity, payload, authz)
    return DeveloperApiKeyProvisionedRead(
        api_key=api_key_read(api_key),
        key=key,
        secret_hint="Copy now; the API key is only returned once.",
    )


@router.get("/api-keys", response_model=list[DeveloperApiKeyRead])
async def list_developer_api_keys_route(
    organization_id: UUID = Query(),
    application_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[DeveloperApiKeyRead]:
    return [
        api_key_read(api_key)
        for api_key in await list_developer_api_keys(db, identity, organization_id, authz, application_id)
    ]


@router.post("/api-keys/{api_key_id}/revoke", response_model=DeveloperApiKeyRead)
async def revoke_developer_api_key_route(
    api_key_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperApiKeyRead:
    return api_key_read(await revoke_developer_api_key(db, identity, api_key_id, authz))


@router.get("/auth/inspect", response_model=DeveloperApiKeyInspectionRead)
async def inspect_developer_api_key_route(
    request: Request,
    x_afrolete_api_key: str = Header(alias="X-Afrolete-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> DeveloperApiKeyInspectionRead:
    return await inspect_developer_api_key(db, x_afrolete_api_key, request.client.host if request.client else None)


@router.post("/applications", response_model=DeveloperApplicationProvisionedRead, status_code=status.HTTP_201_CREATED)
async def create_developer_application_route(
    payload: DeveloperApplicationCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperApplicationProvisionedRead:
    application, secret = await create_developer_application(db, identity, payload, authz)
    return DeveloperApplicationProvisionedRead(
        application=application_read(application),
        client_secret=secret,
        secret_hint="Copy now; the client secret is only returned once.",
    )


@router.get("/applications", response_model=list[DeveloperApplicationRead])
async def list_developer_applications_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[DeveloperApplicationRead]:
    return [
        application_read(application)
        for application in await list_developer_applications(db, identity, organization_id, authz)
    ]


@router.post("/applications/{application_id}/rotate-secret", response_model=DeveloperApplicationProvisionedRead)
async def rotate_developer_application_secret_route(
    application_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperApplicationProvisionedRead:
    application, secret = await rotate_developer_application_secret(db, identity, application_id, authz)
    return DeveloperApplicationProvisionedRead(
        application=application_read(application),
        client_secret=secret,
        secret_hint="Copy now; the rotated secret is only returned once.",
    )


@router.post(
    "/webhook-subscriptions",
    response_model=DeveloperWebhookSubscriptionProvisionedRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_developer_webhook_subscription_route(
    payload: DeveloperWebhookSubscriptionCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperWebhookSubscriptionProvisionedRead:
    subscription, secret = await create_developer_webhook_subscription(db, identity, payload, authz)
    return DeveloperWebhookSubscriptionProvisionedRead(
        subscription=webhook_subscription_read(subscription),
        signing_secret=secret,
        secret_hint="Copy now; the webhook signing secret is only returned once.",
    )


@router.get("/webhook-subscriptions", response_model=list[DeveloperWebhookSubscriptionRead])
async def list_developer_webhook_subscriptions_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[DeveloperWebhookSubscriptionRead]:
    return [
        webhook_subscription_read(subscription)
        for subscription in await list_developer_webhook_subscriptions(db, identity, organization_id, authz)
    ]


@router.get("/webhook-deliveries", response_model=list[DeveloperWebhookDeliveryRead])
async def list_developer_webhook_deliveries_route(
    organization_id: UUID = Query(),
    subscription_id: UUID | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[DeveloperWebhookDeliveryRead]:
    return [
        webhook_delivery_read(delivery)
        for delivery in await list_developer_webhook_deliveries(
            db,
            identity,
            organization_id,
            authz,
            subscription_id,
        )
    ]


@router.post("/webhook-deliveries/retry-due", response_model=DeveloperWebhookRetryRunRead)
async def retry_developer_webhook_deliveries_route(
    organization_id: UUID = Query(),
    max_attempts: int = Query(default=3, ge=1, le=25),
    limit: int = Query(default=25, ge=1, le=100),
    include_recorded: bool = Query(default=False),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperWebhookRetryRunRead:
    return await retry_developer_webhook_deliveries(
        db,
        identity,
        organization_id,
        authz,
        max_attempts=max_attempts,
        limit=limit,
        include_recorded=include_recorded,
    )


@router.post("/webhook-deliveries/{delivery_id}/replay", response_model=DeveloperWebhookDeliveryRead)
async def replay_developer_webhook_delivery_route(
    delivery_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperWebhookDeliveryRead:
    return webhook_delivery_read(await replay_developer_webhook_delivery(db, identity, delivery_id, authz))


@router.patch("/webhook-subscriptions/{subscription_id}", response_model=DeveloperWebhookSubscriptionRead)
async def update_developer_webhook_subscription_route(
    subscription_id: UUID,
    payload: DeveloperWebhookSubscriptionUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperWebhookSubscriptionRead:
    return webhook_subscription_read(
        await update_developer_webhook_subscription(db, identity, subscription_id, payload, authz)
    )


@router.post("/marketplace-listings", response_model=DeveloperMarketplaceListingRead, status_code=status.HTTP_201_CREATED)
async def create_developer_marketplace_listing_route(
    payload: DeveloperMarketplaceListingCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperMarketplaceListingRead:
    return marketplace_listing_read(await create_developer_marketplace_listing(db, identity, payload, authz))


@router.get("/marketplace-listings", response_model=list[DeveloperMarketplaceListingRead])
async def list_developer_marketplace_listings_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[DeveloperMarketplaceListingRead]:
    return [
        marketplace_listing_read(listing)
        for listing in await list_developer_marketplace_listings(db, identity, organization_id, authz)
    ]


@router.patch("/marketplace-listings/{listing_id}/review", response_model=DeveloperMarketplaceListingRead)
async def review_developer_marketplace_listing_route(
    listing_id: UUID,
    payload: DeveloperMarketplaceListingReview,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperMarketplaceListingRead:
    return marketplace_listing_read(await review_developer_marketplace_listing(db, identity, listing_id, payload, authz))


@router.post("/marketplace-listings/{listing_id}/install", response_model=DeveloperMarketplaceListingRead)
async def record_developer_marketplace_install_route(
    listing_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperMarketplaceListingRead:
    return marketplace_listing_read(await record_developer_marketplace_install(db, identity, listing_id, authz))


@router.get("/catalog", response_model=DeveloperIntegrationCatalogRead)
async def developer_integration_catalog_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperIntegrationCatalogRead:
    return await developer_integration_catalog(db, identity, organization_id, authz)


@router.get("/summary", response_model=DeveloperPortalSummaryRead)
async def developer_portal_summary_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> DeveloperPortalSummaryRead:
    return await developer_portal_summary(db, identity, organization_id, authz)
