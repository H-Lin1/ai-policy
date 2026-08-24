"""Create the B1.2 read-only policy library table.

Revision ID: 0003_policy_library
Revises: 0002_identity_access
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_policy_library"
down_revision = "0002_identity_access"
branch_labels = None
depends_on = None


def _postgresql_only() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _postgresql_only():
        return
    uuid_type = postgresql.UUID(as_uuid=True)
    timestamp_type = sa.DateTime(timezone=True)
    op.create_table(
        "policy_documents",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("region_id", uuid_type, nullable=False),
        sa.Column("region_code", sa.String(length=32), nullable=False, server_default=sa.text("'sz'")),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("document_no", sa.Text(), nullable=True),
        sa.Column("issuing_organization", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("document_url", sa.Text(), nullable=True),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("collected_at", timestamp_type, nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("effective_status", sa.String(length=32), nullable=True),
        sa.Column("requested_title", sa.Text(), nullable=True),
        sa.Column("reference_count", sa.Integer(), nullable=True),
        sa.Column("source_years", sa.Text(), nullable=True),
        sa.Column("created_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["region_id"], ["app.regions.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("source_url", "content_sha256", name="uq_policy_documents_source_hash"),
        sa.CheckConstraint("length(btrim(title)) > 0", name="ck_policy_documents_title"),
        sa.CheckConstraint("length(btrim(source_url)) > 0", name="ck_policy_documents_source_url"),
        sa.CheckConstraint("length(btrim(content_text)) > 0", name="ck_policy_documents_content"),
        sa.CheckConstraint("content_sha256 ~ '^[0-9a-f]{64}$'", name="ck_policy_documents_hash"),
        sa.CheckConstraint("region_code = 'sz'", name="ck_policy_documents_region"),
        schema="app",
    )
    op.create_index("ix_policy_documents_region_published", "policy_documents", ["region_code", "published_date"], schema="app")
    op.create_index("ix_policy_documents_title", "policy_documents", ["title"], schema="app")
    op.execute("ALTER TABLE app.policy_documents ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE app.policy_documents FROM anon")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE app.policy_documents FROM authenticated")


def downgrade() -> None:
    if _postgresql_only():
        op.drop_table("policy_documents", schema="app")
