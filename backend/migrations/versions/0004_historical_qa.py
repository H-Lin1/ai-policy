"""Create the B1.3 privacy-screened historical Q&A read model.

Revision ID: 0004_historical_qa
Revises: 0003_policy_library
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_historical_qa"
down_revision = "0003_policy_library"
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
        "historical_qa",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("region_id", uuid_type, nullable=False),
        sa.Column("region_code", sa.String(length=32), nullable=False, server_default=sa.text("'sz'")),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("question_at", timestamp_type, nullable=True),
        sa.Column("replied_at", timestamp_type, nullable=True),
        sa.Column("publishing_organization", sa.Text(), nullable=False),
        sa.Column("collected_at", timestamp_type, nullable=False),
        sa.Column("contains_legal_basis", sa.Boolean(), nullable=False),
        sa.Column("legal_basis_name", sa.Text(), nullable=True),
        sa.Column("legal_basis_citation", sa.Text(), nullable=True),
        sa.Column("adjudication_result", sa.String(length=32), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["region_id"], ["app.regions.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("source_url", "content_sha256", name="uq_historical_qa_source_hash"),
        sa.CheckConstraint("length(btrim(topic)) > 0", name="ck_historical_qa_topic"),
        sa.CheckConstraint("length(btrim(question_text)) > 0", name="ck_historical_qa_question"),
        sa.CheckConstraint("length(btrim(answer_text)) > 0", name="ck_historical_qa_answer"),
        sa.CheckConstraint("length(btrim(source_url)) > 0", name="ck_historical_qa_source_url"),
        sa.CheckConstraint("content_sha256 ~ '^[0-9a-f]{64}$'", name="ck_historical_qa_hash"),
        sa.CheckConstraint("region_code = 'sz'", name="ck_historical_qa_region"),
        schema="app",
    )
    op.create_index("ix_historical_qa_region_replied", "historical_qa", ["region_code", "replied_at"], schema="app")
    op.create_index("ix_historical_qa_topic", "historical_qa", ["topic"], schema="app")
    op.execute("ALTER TABLE app.historical_qa ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE app.historical_qa FROM anon")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE app.historical_qa FROM authenticated")


def downgrade() -> None:
    # No downgrade is invoked operationally; this exists only for Alembic's
    # source contract and must never be used as an automatic rollback path.
    if _postgresql_only():
        op.drop_table("historical_qa", schema="app")
