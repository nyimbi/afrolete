"""add opposition scouting

Revision ID: c5f7a9b1d3e6
Revises: b4e6f8a0c2d5
Create Date: 2026-05-29 15:10:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "c5f7a9b1d3e6"
down_revision: str | None = "b4e6f8a0c2d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "opposition_scouting_video_assets",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("competition_id", app.models.base.GUID(), nullable=True),
        sa.Column("event_id", app.models.base.GUID(), nullable=True),
        sa.Column("uploaded_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("opponent_name", sa.String(length=180), nullable=False),
        sa.Column("sport", sa.String(length=80), nullable=False),
        sa.Column("filename", sa.String(length=240), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("storage_url", sa.String(length=800), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("video_uri", sa.String(length=900), nullable=False),
        sa.Column("clip_label", sa.String(length=180), nullable=True),
        sa.Column("match_context", sa.Text(), nullable=True),
        sa.Column("analysis_focus", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"], name=op.f("fk_opposition_scouting_video_assets_competition_id_competitions")),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name=op.f("fk_opposition_scouting_video_assets_event_id_events")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_opposition_scouting_video_assets_organization_id_organizations")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_opposition_scouting_video_assets_team_id_teams")),
        sa.ForeignKeyConstraint(["uploaded_by_person_id"], ["persons.id"], name=op.f("fk_opposition_scouting_video_assets_uploaded_by_person_id_persons")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opposition_scouting_video_assets")),
        sa.UniqueConstraint("organization_id", "checksum", name="uq_opposition_scouting_video_assets_org_checksum"),
    )
    for column in [
        "analyzed_at",
        "checksum",
        "competition_id",
        "event_id",
        "opponent_name",
        "organization_id",
        "sport",
        "status",
        "team_id",
        "uploaded_by_person_id",
        "video_uri",
    ]:
        op.create_index(op.f(f"ix_opposition_scouting_video_assets_{column}"), "opposition_scouting_video_assets", [column])

    op.create_table(
        "opposition_scouting_reports",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("video_asset_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("competition_id", app.models.base.GUID(), nullable=True),
        sa.Column("event_id", app.models.base.GUID(), nullable=True),
        sa.Column("created_by_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("opponent_name", sa.String(length=180), nullable=False),
        sa.Column("sport", sa.String(length=80), nullable=False),
        sa.Column("match_context", sa.Text(), nullable=True),
        sa.Column("analysis_focus", sa.String(length=1000), nullable=True),
        sa.Column("model_policy", sa.String(length=180), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("formation_detected", sa.String(length=80), nullable=True),
        sa.Column("tactical_summary", sa.Text(), nullable=False),
        sa.Column("weaknesses_json", sa.Text(), nullable=False),
        sa.Column("threats_json", sa.Text(), nullable=False),
        sa.Column("recommendations_json", sa.Text(), nullable=False),
        sa.Column("set_pieces_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"], name=op.f("fk_opposition_scouting_reports_competition_id_competitions")),
        sa.ForeignKeyConstraint(["created_by_person_id"], ["persons.id"], name=op.f("fk_opposition_scouting_reports_created_by_person_id_persons")),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name=op.f("fk_opposition_scouting_reports_event_id_events")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_opposition_scouting_reports_organization_id_organizations")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_opposition_scouting_reports_team_id_teams")),
        sa.ForeignKeyConstraint(["video_asset_id"], ["opposition_scouting_video_assets.id"], name=op.f("fk_opposition_scouting_reports_video_asset_id_opposition_scouting_video_assets")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opposition_scouting_reports")),
    )
    for column in [
        "competition_id",
        "created_by_person_id",
        "event_id",
        "formation_detected",
        "generated_at",
        "model_policy",
        "opponent_name",
        "organization_id",
        "sport",
        "status",
        "team_id",
        "video_asset_id",
    ]:
        op.create_index(op.f(f"ix_opposition_scouting_reports_{column}"), "opposition_scouting_reports", [column])


def downgrade() -> None:
    for column in [
        "video_asset_id",
        "team_id",
        "status",
        "sport",
        "organization_id",
        "opponent_name",
        "model_policy",
        "generated_at",
        "formation_detected",
        "event_id",
        "created_by_person_id",
        "competition_id",
    ]:
        op.drop_index(op.f(f"ix_opposition_scouting_reports_{column}"), table_name="opposition_scouting_reports")
    op.drop_table("opposition_scouting_reports")
    for column in [
        "video_uri",
        "uploaded_by_person_id",
        "team_id",
        "status",
        "sport",
        "organization_id",
        "opponent_name",
        "event_id",
        "competition_id",
        "checksum",
        "analyzed_at",
    ]:
        op.drop_index(op.f(f"ix_opposition_scouting_video_assets_{column}"), table_name="opposition_scouting_video_assets")
    op.drop_table("opposition_scouting_video_assets")
