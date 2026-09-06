"""Add administrator policy authoring, publication lifecycle and audit."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_admin_policy_publishing"
down_revision = "0006_registration_applications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    uuid = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    op.drop_constraint("ck_policy_documents_source_url", "policy_documents", schema="app", type_="check")
    op.alter_column("policy_documents", "source_url", existing_type=sa.Text(), nullable=True, schema="app")
    op.add_column("policy_documents", sa.Column("source_type", sa.String(32), nullable=False, server_default=sa.text("'external_url'")), schema="app")
    op.add_column("policy_documents", sa.Column("publication_status", sa.String(32), nullable=False, server_default=sa.text("'published'")), schema="app")
    op.add_column("policy_documents", sa.Column("raw_markdown", sa.Text()), schema="app")
    op.add_column("policy_documents", sa.Column("raw_markdown_sha256", sa.String(64)), schema="app")
    for name in ("created_by", "published_by", "withdrawn_by"):
        op.add_column("policy_documents", sa.Column(name, uuid), schema="app")
        op.create_foreign_key(f"fk_policy_documents_{name}", "policy_documents", "profiles", [name], ["user_id"], source_schema="app", referent_schema="app", ondelete="RESTRICT")
    op.add_column("policy_documents", sa.Column("published_at", timestamp), schema="app")
    op.add_column("policy_documents", sa.Column("withdrawn_at", timestamp), schema="app")
    op.create_check_constraint("ck_policy_documents_source_type", "policy_documents", "source_type IN ('external_url', 'manual', 'markdown')", schema="app")
    op.create_check_constraint("ck_policy_documents_publication_status", "policy_documents", "publication_status IN ('draft', 'published', 'withdrawn')", schema="app")
    op.create_check_constraint("ck_policy_documents_source_contract", "policy_documents", "source_type <> 'external_url' OR (source_url IS NOT NULL AND length(btrim(source_url)) > 0)", schema="app")
    op.create_unique_constraint("uq_policy_documents_markdown_hash", "policy_documents", ["raw_markdown_sha256"], schema="app")
    op.create_index("ix_policy_documents_publication_created", "policy_documents", ["publication_status", "created_at"], schema="app")
    op.create_table(
        "policy_document_events",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("policy_id", uuid, nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("actor_user_id", uuid, nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["policy_id"], ["app.policy_documents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["app.profiles.user_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("event_type IN ('drafted', 'published', 'withdrawn')", name="ck_policy_document_events_type"),
        schema="app",
    )
    op.create_index("ix_policy_document_events_policy_created", "policy_document_events", ["policy_id", "created_at"], schema="app")
    op.execute("ALTER TABLE app.policy_document_events ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.drop_table("policy_document_events", schema="app")
    for name in ("withdrawn_at", "published_at", "withdrawn_by", "published_by", "created_by", "raw_markdown_sha256", "raw_markdown", "publication_status", "source_type"):
        op.drop_column("policy_documents", name, schema="app")
    op.alter_column("policy_documents", "source_url", existing_type=sa.Text(), nullable=False, schema="app")
    op.create_check_constraint("ck_policy_documents_source_url", "policy_documents", "length(btrim(source_url)) > 0", schema="app")
