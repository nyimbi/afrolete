from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, IdMixin, TimestampMixin


class DeveloperApplication(IdMixin, TimestampMixin, Base):
    __tablename__ = "developer_applications"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    owner_person_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("persons.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    app_type: Mapped[str] = mapped_column(String(80), default="server_to_server", nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    client_secret_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    redirect_uris: Mapped[str | None] = mapped_column(Text)
    scopes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(320), index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    last_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text)


class DeveloperApiKey(IdMixin, TimestampMixin, Base):
    __tablename__ = "developer_api_keys"
    __table_args__ = (UniqueConstraint("application_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    application_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("developer_applications.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    key_prefix: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    environment: Mapped[str] = mapped_column(String(40), default="sandbox", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_used_ip: Mapped[str | None] = mapped_column(String(80))
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class DeveloperWebhookSubscription(IdMixin, TimestampMixin, Base):
    __tablename__ = "developer_webhook_subscriptions"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    application_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("developer_applications.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(String(500), nullable=False)
    event_types: Mapped[str] = mapped_column(Text, nullable=False)
    signing_secret_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    delivery_mode: Mapped[str] = mapped_column(String(40), default="record_only", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False, index=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_delivery_status: Mapped[str | None] = mapped_column(String(80))
    last_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class DeveloperMarketplaceListing(IdMixin, TimestampMixin, Base):
    __tablename__ = "developer_marketplace_listings"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("organizations.id"), index=True)
    application_id: Mapped[UUID | None] = mapped_column(GUID(), ForeignKey("developer_applications.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    install_url: Mapped[str | None] = mapped_column(String(500))
    support_url: Mapped[str | None] = mapped_column(String(500))
    pricing_model: Mapped[str] = mapped_column(String(80), default="free", nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(40), default="1.0.0", nullable=False)
    visibility: Mapped[str] = mapped_column(String(40), default="private", nullable=False, index=True)
    review_status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False, index=True)
    install_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
