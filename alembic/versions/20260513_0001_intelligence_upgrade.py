"""intelligence upgrade

Revision ID: 20260513_0001
Revises:
Create Date: 2026-05-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260513_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("access_event", sa.Column("normalized_path", sa.Text(), nullable=False, server_default="/"))
    op.add_column("access_event", sa.Column("crawler_name", sa.String(length=128), nullable=True))
    op.add_column("access_event", sa.Column("organization_name", sa.String(length=255), nullable=True))
    op.add_column("access_event", sa.Column("organization_domain", sa.String(length=255), nullable=True))
    op.add_column("access_event", sa.Column("organization_type", sa.String(length=64), nullable=True))
    op.add_column("access_event", sa.Column("organization_source", sa.String(length=64), nullable=True))
    op.add_column("access_event", sa.Column("organization_confidence", sa.Integer(), nullable=True))
    op.create_index("ix_access_event_normalized_path", "access_event", ["normalized_path"])
    op.create_index("ix_access_event_crawler_name", "access_event", ["crawler_name"])
    op.create_index("ix_access_event_organization_name", "access_event", ["organization_name"])
    op.create_index("ix_access_event_organization_type", "access_event", ["organization_type"])

    op.create_table(
        "core_page",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["site.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("site_id", "path", name="uq_core_page_site_path"),
    )
    op.create_index("ix_core_page_id", "core_page", ["id"])
    op.create_index("ix_core_page_site_id", "core_page", ["site_id"])
    op.create_index("ix_core_page_path", "core_page", ["path"])
    op.create_index("ix_core_page_category", "core_page", ["category"])
    op.create_index("ix_core_page_priority", "core_page", ["priority"])
    op.create_index("ix_core_page_is_active", "core_page", ["is_active"])

    op.create_table(
        "visitor_identity_rule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_type", sa.String(length=32), nullable=False),
        sa.Column("pattern", sa.String(length=255), nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=False),
        sa.Column("organization_domain", sa.String(length=255), nullable=True),
        sa.Column("organization_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_type", "pattern", name="uq_visitor_identity_rule_type_pattern"),
    )
    op.create_index("ix_visitor_identity_rule_id", "visitor_identity_rule", ["id"])
    op.create_index("ix_visitor_identity_rule_rule_type", "visitor_identity_rule", ["rule_type"])
    op.create_index("ix_visitor_identity_rule_pattern", "visitor_identity_rule", ["pattern"])
    op.create_index("ix_visitor_identity_rule_organization_name", "visitor_identity_rule", ["organization_name"])
    op.create_index("ix_visitor_identity_rule_organization_type", "visitor_identity_rule", ["organization_type"])
    op.create_index("ix_visitor_identity_rule_priority", "visitor_identity_rule", ["priority"])
    op.create_index("ix_visitor_identity_rule_is_active", "visitor_identity_rule", ["is_active"])

    op.create_table(
        "visitor_enrichment_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_ip", sa.String(length=64), nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=True),
        sa.Column("organization_domain", sa.String(length=255), nullable=True),
        sa.Column("organization_type", sa.String(length=64), nullable=True),
        sa.Column("organization_source", sa.String(length=64), nullable=False),
        sa.Column("organization_confidence", sa.Integer(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_ip"),
    )
    op.create_index("ix_visitor_enrichment_cache_id", "visitor_enrichment_cache", ["id"])
    op.create_index("ix_visitor_enrichment_cache_client_ip", "visitor_enrichment_cache", ["client_ip"])
    op.create_index("ix_visitor_enrichment_cache_organization_name", "visitor_enrichment_cache", ["organization_name"])
    op.create_index("ix_visitor_enrichment_cache_organization_type", "visitor_enrichment_cache", ["organization_type"])


def downgrade() -> None:
    op.drop_index("ix_visitor_enrichment_cache_organization_type", table_name="visitor_enrichment_cache")
    op.drop_index("ix_visitor_enrichment_cache_organization_name", table_name="visitor_enrichment_cache")
    op.drop_index("ix_visitor_enrichment_cache_client_ip", table_name="visitor_enrichment_cache")
    op.drop_index("ix_visitor_enrichment_cache_id", table_name="visitor_enrichment_cache")
    op.drop_table("visitor_enrichment_cache")

    op.drop_index("ix_visitor_identity_rule_is_active", table_name="visitor_identity_rule")
    op.drop_index("ix_visitor_identity_rule_priority", table_name="visitor_identity_rule")
    op.drop_index("ix_visitor_identity_rule_organization_type", table_name="visitor_identity_rule")
    op.drop_index("ix_visitor_identity_rule_organization_name", table_name="visitor_identity_rule")
    op.drop_index("ix_visitor_identity_rule_pattern", table_name="visitor_identity_rule")
    op.drop_index("ix_visitor_identity_rule_rule_type", table_name="visitor_identity_rule")
    op.drop_index("ix_visitor_identity_rule_id", table_name="visitor_identity_rule")
    op.drop_table("visitor_identity_rule")

    op.drop_index("ix_core_page_is_active", table_name="core_page")
    op.drop_index("ix_core_page_priority", table_name="core_page")
    op.drop_index("ix_core_page_category", table_name="core_page")
    op.drop_index("ix_core_page_path", table_name="core_page")
    op.drop_index("ix_core_page_site_id", table_name="core_page")
    op.drop_index("ix_core_page_id", table_name="core_page")
    op.drop_table("core_page")

    op.drop_index("ix_access_event_organization_type", table_name="access_event")
    op.drop_index("ix_access_event_organization_name", table_name="access_event")
    op.drop_index("ix_access_event_crawler_name", table_name="access_event")
    op.drop_index("ix_access_event_normalized_path", table_name="access_event")
    op.drop_column("access_event", "organization_confidence")
    op.drop_column("access_event", "organization_source")
    op.drop_column("access_event", "organization_type")
    op.drop_column("access_event", "organization_domain")
    op.drop_column("access_event", "organization_name")
    op.drop_column("access_event", "crawler_name")
    op.drop_column("access_event", "normalized_path")
