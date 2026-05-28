from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeveloperApplicationCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=180)
    app_type: str = Field(default="server_to_server", min_length=2, max_length=80)
    redirect_uris: list[str] = Field(default_factory=list, max_length=20)
    scopes: list[str] = Field(default_factory=lambda: ["read:organization"], max_length=40)
    contact_email: str | None = Field(default=None, max_length=320)
    notes: str | None = Field(default=None, max_length=4000)


class DeveloperApplicationRead(BaseModel):
    id: UUID
    organization_id: UUID
    owner_person_id: UUID | None
    name: str
    app_type: str
    client_id: str
    redirect_uris: list[str]
    scopes: list[str]
    contact_email: str | None
    status: str
    last_rotated_at: datetime | None
    notes: str | None


class DeveloperApplicationProvisionedRead(BaseModel):
    application: DeveloperApplicationRead
    client_secret: str
    secret_hint: str


class DeveloperApiKeyCreate(BaseModel):
    organization_id: UUID
    application_id: UUID
    name: str = Field(min_length=2, max_length=180)
    scopes: list[str] = Field(default_factory=lambda: ["read:organization"], max_length=40)
    environment: str = Field(default="sandbox", max_length=40)
    expires_at: datetime | None = None
    rate_limit_per_minute: int = Field(default=60, ge=1, le=100_000)
    notes: str | None = Field(default=None, max_length=4000)


class DeveloperApiKeyRead(BaseModel):
    id: UUID
    organization_id: UUID
    application_id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    environment: str
    status: str
    expires_at: datetime | None
    last_used_at: datetime | None
    last_used_ip: str | None
    usage_count: int
    rate_limit_per_minute: int
    window_started_at: datetime | None
    window_request_count: int
    last_rate_limited_at: datetime | None
    notes: str | None


class DeveloperApiKeyProvisionedRead(BaseModel):
    api_key: DeveloperApiKeyRead
    key: str
    secret_hint: str


class DeveloperOAuthAuthorizationCreate(BaseModel):
    organization_id: UUID
    client_id: str = Field(min_length=8, max_length=160)
    redirect_uri: str = Field(min_length=8, max_length=500)
    scopes: list[str] = Field(min_length=1, max_length=40)
    state: str | None = Field(default=None, max_length=500)
    code_challenge: str | None = Field(default=None, min_length=8, max_length=256)
    code_challenge_method: str | None = Field(default=None, max_length=16)


class DeveloperOAuthAuthorizationRead(BaseModel):
    id: UUID
    organization_id: UUID
    application_id: UUID
    client_id: str
    application_name: str
    redirect_uri: str
    requested_scopes: list[str]
    granted_scopes: list[str]
    state: str | None
    code_challenge_method: str | None
    public_client: bool
    status: str
    expires_at: datetime
    consented_at: datetime | None
    redeemed_at: datetime | None
    authorization_code: str | None = None
    redirect_url: str | None = None


class DeveloperOAuthTokenExchange(BaseModel):
    client_id: str = Field(min_length=8, max_length=160)
    client_secret: str | None = Field(default=None, min_length=8, max_length=500)
    code: str = Field(min_length=16, max_length=500)
    redirect_uri: str = Field(min_length=8, max_length=500)
    code_verifier: str | None = Field(default=None, min_length=8, max_length=256)


class DeveloperOAuthTokenRead(BaseModel):
    access_token: str
    token_type: str
    auth_header: str
    api_key: DeveloperApiKeyRead
    scopes: list[str]
    expires_in: int | None = None


class DeveloperApiKeyInspectionRead(BaseModel):
    valid: bool
    organization_id: UUID
    application_id: UUID
    api_key_id: UUID
    client_id: str
    application_name: str
    environment: str
    scopes: list[str]
    rate_limit_per_minute: int
    usage_count: int
    window_started_at: datetime | None
    window_request_count: int


class DeveloperWebhookSubscriptionCreate(BaseModel):
    organization_id: UUID
    application_id: UUID | None = None
    name: str = Field(min_length=2, max_length=180)
    target_url: str = Field(min_length=8, max_length=500)
    event_types: list[str] = Field(min_length=1, max_length=80)
    delivery_mode: str = Field(default="record_only", max_length=40)


class DeveloperWebhookSubscriptionUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    delivery_mode: str | None = Field(default=None, max_length=40)
    target_url: str | None = Field(default=None, min_length=8, max_length=500)
    event_types: list[str] | None = Field(default=None, min_length=1, max_length=80)


class DeveloperWebhookSubscriptionRead(BaseModel):
    id: UUID
    organization_id: UUID
    application_id: UUID | None
    name: str
    target_url: str
    event_types: list[str]
    delivery_mode: str
    status: str
    failure_count: int
    last_delivery_status: str | None
    last_delivered_at: datetime | None


class DeveloperWebhookSubscriptionProvisionedRead(BaseModel):
    subscription: DeveloperWebhookSubscriptionRead
    signing_secret: str
    secret_hint: str


class DeveloperWebhookDeliveryRead(BaseModel):
    id: UUID
    organization_id: UUID
    subscription_id: UUID
    application_id: UUID | None
    event_type: str
    event_id: str
    target_url: str
    delivery_mode: str
    status: str
    attempt_count: int
    response_status_code: int | None
    failure_reason: str | None
    delivered_at: datetime | None


class DeveloperWebhookRetryRunRead(BaseModel):
    organization_id: UUID
    eligible_count: int
    replayed_count: int
    skipped_count: int
    failed_count: int
    delivery_ids: list[UUID]
    statuses: dict[str, int]
    max_attempts: int
    include_recorded: bool


class DeveloperApiScopeCatalogRead(BaseModel):
    scope: str
    category: str
    description: str
    recommended_for: list[str]


class DeveloperWebhookEventCatalogRead(BaseModel):
    event_type: str
    category: str
    description: str
    emission_status: str
    payload_fields: list[str]
    recommended_scopes: list[str]
    example_payload: dict[str, object]


class DeveloperSdkCatalogRead(BaseModel):
    language: str
    package_name: str
    install_command: str
    status: str
    entry_points: list[str]


class DeveloperQuickstartRead(BaseModel):
    title: str
    language: str
    description: str
    steps: list[str]
    code_sample: str


class DeveloperIntegrationCatalogRead(BaseModel):
    organization_id: UUID
    api_base_path: str
    auth_header: str
    webhook_signature_header: str
    scopes: list[DeveloperApiScopeCatalogRead]
    webhook_events: list[DeveloperWebhookEventCatalogRead]
    sdks: list[DeveloperSdkCatalogRead]
    configured_event_types: list[str]


class DeveloperPublicDocsRead(BaseModel):
    title: str
    version: str
    api_base_path: str
    authentication: str
    auth_header: str
    webhook_signature_header: str
    webhook_timestamp_header: str
    quickstarts: list[DeveloperQuickstartRead]
    scopes: list[DeveloperApiScopeCatalogRead]
    webhook_events: list[DeveloperWebhookEventCatalogRead]
    sdks: list[DeveloperSdkCatalogRead]
    marketplace_categories: list[str]
    security_requirements: list[str]


class DeveloperMarketplaceListingCreate(BaseModel):
    organization_id: UUID
    application_id: UUID | None = None
    name: str = Field(min_length=2, max_length=180)
    category: str = Field(min_length=2, max_length=120)
    summary: str = Field(min_length=2, max_length=500)
    install_url: str | None = Field(default=None, max_length=500)
    support_url: str | None = Field(default=None, max_length=500)
    pricing_model: str = Field(default="free", max_length=80)
    version: str = Field(default="1.0.0", max_length=40)
    visibility: str = Field(default="private", max_length=40)


class DeveloperMarketplaceListingReview(BaseModel):
    review_status: str = Field(min_length=2, max_length=40)
    visibility: str | None = Field(default=None, max_length=40)


class DeveloperMarketplaceListingRead(BaseModel):
    id: UUID
    organization_id: UUID
    application_id: UUID | None
    name: str
    category: str
    summary: str
    install_url: str | None
    support_url: str | None
    pricing_model: str
    version: str
    visibility: str
    review_status: str
    install_count: int


class DeveloperPortalSummaryRead(BaseModel):
    organization_id: UUID
    application_count: int
    active_application_count: int
    api_key_count: int
    active_api_key_count: int
    webhook_subscription_count: int
    live_webhook_count: int
    marketplace_listing_count: int
    approved_marketplace_listing_count: int
    install_count: int
    recommended_next_steps: list[str]
