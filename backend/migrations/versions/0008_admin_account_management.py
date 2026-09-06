"""Add administrator account-management metadata and audit events."""

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_admin_account_management"
down_revision = "0007_admin_policy_publishing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    uuid = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    op.add_column("users", sa.Column("contact_phone", sa.String(40)), schema="app")
    op.add_column("users", sa.Column("job_title", sa.String(120)), schema="app")
    op.create_table(
        "account_management_events",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("target_user_id", uuid, nullable=False),
        sa.Column("actor_user_id", uuid, nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("change_summary", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["target_user_id"], ["app.users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["app.profiles.user_id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "event_type IN ('account_created', 'account_updated', 'account_disabled', 'account_enabled', 'role_assigned', 'role_removed', 'organization_bound', 'department_bound')",
            name="ck_account_management_event_type",
        ),
        schema="app",
    )
    op.create_index("ix_account_management_events_target_created", "account_management_events", ["target_user_id", "created_at"], schema="app")
    op.execute("ALTER TABLE app.account_management_events ENABLE ROW LEVEL SECURITY")
    if os.getenv("DATABASE_MODE", "supabase").strip().lower() != "standalone":
        op.execute("REVOKE ALL PRIVILEGES ON TABLE app.account_management_events FROM anon")
        op.execute("REVOKE ALL PRIVILEGES ON TABLE app.account_management_events FROM authenticated")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.drop_table("account_management_events", schema="app")
    op.drop_column("users", "job_title", schema="app")
    op.drop_column("users", "contact_phone", schema="app")
