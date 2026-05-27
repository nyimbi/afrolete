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
