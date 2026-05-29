"""add community engagement

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-05-30 02:30:00.000000
"""

from collections.abc import Sequence

import app.models.base
import sqlalchemy as sa
from alembic import op


revision: str = "e3f4a5b6c7d8"
down_revision: str | None = "d2e3f4a5b6c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "community_posts",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("author_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("post_type", sa.String(length=60), nullable=False),
        sa.Column("visibility", sa.String(length=60), nullable=False),
        sa.Column("media_url", sa.String(length=500), nullable=True),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["author_person_id"], ["persons.id"], name=op.f("fk_community_posts_author_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_community_posts_organization_id_organizations")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_community_posts_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_community_posts")),
    )
    op.create_index(op.f("ix_community_posts_author_person_id"), "community_posts", ["author_person_id"])
    op.create_index(op.f("ix_community_posts_organization_id"), "community_posts", ["organization_id"])
    op.create_index(op.f("ix_community_posts_pinned"), "community_posts", ["pinned"])
    op.create_index(op.f("ix_community_posts_post_type"), "community_posts", ["post_type"])
    op.create_index(op.f("ix_community_posts_published_at"), "community_posts", ["published_at"])
    op.create_index(op.f("ix_community_posts_status"), "community_posts", ["status"])
    op.create_index(op.f("ix_community_posts_team_id"), "community_posts", ["team_id"])
    op.create_index(op.f("ix_community_posts_title"), "community_posts", ["title"])
    op.create_index(op.f("ix_community_posts_visibility"), "community_posts", ["visibility"])

    op.create_table(
        "community_comments",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("post_id", app.models.base.GUID(), nullable=False),
        sa.Column("author_person_id", app.models.base.GUID(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["author_person_id"], ["persons.id"], name=op.f("fk_community_comments_author_person_id_persons")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_community_comments_organization_id_organizations")),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"], name=op.f("fk_community_comments_post_id_community_posts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_community_comments")),
    )
    op.create_index(op.f("ix_community_comments_author_person_id"), "community_comments", ["author_person_id"])
    op.create_index(op.f("ix_community_comments_organization_id"), "community_comments", ["organization_id"])
    op.create_index(op.f("ix_community_comments_post_id"), "community_comments", ["post_id"])
    op.create_index(op.f("ix_community_comments_status"), "community_comments", ["status"])

    op.create_table(
        "community_reactions",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("post_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=False),
        sa.Column("reaction_type", sa.String(length=40), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_community_reactions_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_community_reactions_person_id_persons")),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"], name=op.f("fk_community_reactions_post_id_community_posts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_community_reactions")),
        sa.UniqueConstraint("post_id", "person_id", "reaction_type", name=op.f("uq_community_reactions_post_id")),
    )
    op.create_index(op.f("ix_community_reactions_organization_id"), "community_reactions", ["organization_id"])
    op.create_index(op.f("ix_community_reactions_person_id"), "community_reactions", ["person_id"])
    op.create_index(op.f("ix_community_reactions_post_id"), "community_reactions", ["post_id"])
    op.create_index(op.f("ix_community_reactions_reaction_type"), "community_reactions", ["reaction_type"])

    op.create_table(
        "fan_polls",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("team_id", app.models.base.GUID(), nullable=True),
        sa.Column("post_id", app.models.base.GUID(), nullable=True),
        sa.Column("question", sa.String(length=240), nullable=False),
        sa.Column("audience", sa.String(length=60), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("closes_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_fan_polls_organization_id_organizations")),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"], name=op.f("fk_fan_polls_post_id_community_posts")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("fk_fan_polls_team_id_teams")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fan_polls")),
    )
    op.create_index(op.f("ix_fan_polls_audience"), "fan_polls", ["audience"])
    op.create_index(op.f("ix_fan_polls_closes_at"), "fan_polls", ["closes_at"])
    op.create_index(op.f("ix_fan_polls_organization_id"), "fan_polls", ["organization_id"])
    op.create_index(op.f("ix_fan_polls_post_id"), "fan_polls", ["post_id"])
    op.create_index(op.f("ix_fan_polls_question"), "fan_polls", ["question"])
    op.create_index(op.f("ix_fan_polls_status"), "fan_polls", ["status"])
    op.create_index(op.f("ix_fan_polls_team_id"), "fan_polls", ["team_id"])

    op.create_table(
        "fan_poll_options",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("poll_id", app.models.base.GUID(), nullable=False),
        sa.Column("label", sa.String(length=180), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_fan_poll_options_organization_id_organizations")),
        sa.ForeignKeyConstraint(["poll_id"], ["fan_polls.id"], name=op.f("fk_fan_poll_options_poll_id_fan_polls")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fan_poll_options")),
    )
    op.create_index(op.f("ix_fan_poll_options_organization_id"), "fan_poll_options", ["organization_id"])
    op.create_index(op.f("ix_fan_poll_options_poll_id"), "fan_poll_options", ["poll_id"])

    op.create_table(
        "fan_poll_votes",
        sa.Column("organization_id", app.models.base.GUID(), nullable=False),
        sa.Column("poll_id", app.models.base.GUID(), nullable=False),
        sa.Column("option_id", app.models.base.GUID(), nullable=False),
        sa.Column("person_id", app.models.base.GUID(), nullable=False),
        sa.Column("id", app.models.base.GUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["option_id"], ["fan_poll_options.id"], name=op.f("fk_fan_poll_votes_option_id_fan_poll_options")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_fan_poll_votes_organization_id_organizations")),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], name=op.f("fk_fan_poll_votes_person_id_persons")),
        sa.ForeignKeyConstraint(["poll_id"], ["fan_polls.id"], name=op.f("fk_fan_poll_votes_poll_id_fan_polls")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fan_poll_votes")),
        sa.UniqueConstraint("poll_id", "person_id", name=op.f("uq_fan_poll_votes_poll_id")),
    )
    op.create_index(op.f("ix_fan_poll_votes_option_id"), "fan_poll_votes", ["option_id"])
    op.create_index(op.f("ix_fan_poll_votes_organization_id"), "fan_poll_votes", ["organization_id"])
    op.create_index(op.f("ix_fan_poll_votes_person_id"), "fan_poll_votes", ["person_id"])
    op.create_index(op.f("ix_fan_poll_votes_poll_id"), "fan_poll_votes", ["poll_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_fan_poll_votes_poll_id"), table_name="fan_poll_votes")
    op.drop_index(op.f("ix_fan_poll_votes_person_id"), table_name="fan_poll_votes")
    op.drop_index(op.f("ix_fan_poll_votes_organization_id"), table_name="fan_poll_votes")
    op.drop_index(op.f("ix_fan_poll_votes_option_id"), table_name="fan_poll_votes")
    op.drop_table("fan_poll_votes")

    op.drop_index(op.f("ix_fan_poll_options_poll_id"), table_name="fan_poll_options")
    op.drop_index(op.f("ix_fan_poll_options_organization_id"), table_name="fan_poll_options")
    op.drop_table("fan_poll_options")

    op.drop_index(op.f("ix_fan_polls_team_id"), table_name="fan_polls")
    op.drop_index(op.f("ix_fan_polls_status"), table_name="fan_polls")
    op.drop_index(op.f("ix_fan_polls_question"), table_name="fan_polls")
    op.drop_index(op.f("ix_fan_polls_post_id"), table_name="fan_polls")
    op.drop_index(op.f("ix_fan_polls_organization_id"), table_name="fan_polls")
    op.drop_index(op.f("ix_fan_polls_closes_at"), table_name="fan_polls")
    op.drop_index(op.f("ix_fan_polls_audience"), table_name="fan_polls")
    op.drop_table("fan_polls")

    op.drop_index(op.f("ix_community_reactions_reaction_type"), table_name="community_reactions")
    op.drop_index(op.f("ix_community_reactions_post_id"), table_name="community_reactions")
    op.drop_index(op.f("ix_community_reactions_person_id"), table_name="community_reactions")
    op.drop_index(op.f("ix_community_reactions_organization_id"), table_name="community_reactions")
    op.drop_table("community_reactions")

    op.drop_index(op.f("ix_community_comments_status"), table_name="community_comments")
    op.drop_index(op.f("ix_community_comments_post_id"), table_name="community_comments")
    op.drop_index(op.f("ix_community_comments_organization_id"), table_name="community_comments")
    op.drop_index(op.f("ix_community_comments_author_person_id"), table_name="community_comments")
    op.drop_table("community_comments")

    op.drop_index(op.f("ix_community_posts_visibility"), table_name="community_posts")
    op.drop_index(op.f("ix_community_posts_title"), table_name="community_posts")
    op.drop_index(op.f("ix_community_posts_team_id"), table_name="community_posts")
    op.drop_index(op.f("ix_community_posts_status"), table_name="community_posts")
    op.drop_index(op.f("ix_community_posts_published_at"), table_name="community_posts")
    op.drop_index(op.f("ix_community_posts_post_type"), table_name="community_posts")
    op.drop_index(op.f("ix_community_posts_pinned"), table_name="community_posts")
    op.drop_index(op.f("ix_community_posts_organization_id"), table_name="community_posts")
    op.drop_index(op.f("ix_community_posts_author_person_id"), table_name="community_posts")
    op.drop_table("community_posts")
