"""Add standalone account registration applications and audit events."""

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_registration_applications"
down_revision = "0005_consultation_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    uuid = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    op.alter_column(
        "consultation_departments",
        "government_user_id",
        existing_type=uuid,
        nullable=True,
        schema="app",
    )
    op.create_table(
        "registration_applications",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("application_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("region_id", uuid, nullable=False),
        sa.Column("department_id", sa.String(96)),
        sa.Column("login_username", sa.String(128), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("form_data", postgresql.JSONB(), nullable=False),
        sa.Column("submitted_at", timestamp, nullable=False, server_default=sa.text("now()")),
        sa.Column("reviewed_at", timestamp),
        sa.Column("reviewer_user_id", uuid),
        sa.Column("review_reason", sa.String(2000)),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["region_id"], ["app.regions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["department_id"], ["app.consultation_departments.department_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["app.profiles.user_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("application_type IN ('enterprise', 'government')", name="ck_registration_application_type"),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'cancelled')", name="ck_registration_application_status"),
        sa.CheckConstraint("(application_type = 'government') = (department_id IS NOT NULL)", name="ck_registration_application_department"),
        schema="app",
    )
    op.create_index(
        "uq_registration_application_pending_username",
        "registration_applications",
        ["login_username"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
        schema="app",
    )
    op.create_index("ix_registration_applications_status_submitted", "registration_applications", ["status", "submitted_at"], schema="app")
    op.create_index(
        "uq_registration_government_department_active",
        "registration_applications",
        ["department_id"],
        unique=True,
        postgresql_where=sa.text("application_type = 'government' AND status IN ('pending', 'approved')"),
        schema="app",
    )
    op.create_table(
        "registration_application_events",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("application_id", uuid, nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("actor_user_id", uuid),
        sa.Column("reason", sa.String(2000)),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["application_id"], ["app.registration_applications.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["app.profiles.user_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("event_type IN ('submitted', 'approved', 'rejected', 'cancelled')", name="ck_registration_application_event_type"),
        schema="app",
    )
    op.create_index("ix_registration_application_events_application_created", "registration_application_events", ["application_id", "created_at"], schema="app")
    standalone = os.getenv("DATABASE_MODE", "supabase").strip().lower() == "standalone"
    for table in ("registration_applications", "registration_application_events"):
        op.execute(f"ALTER TABLE app.{table} ENABLE ROW LEVEL SECURITY")
        if not standalone:
            op.execute(f"REVOKE ALL PRIVILEGES ON TABLE app.{table} FROM anon")
            op.execute(f"REVOKE ALL PRIVILEGES ON TABLE app.{table} FROM authenticated")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.drop_table("registration_application_events", schema="app")
        op.drop_table("registration_applications", schema="app")
        op.alter_column(
            "consultation_departments",
            "government_user_id",
            existing_type=postgresql.UUID(as_uuid=True),
            nullable=False,
            schema="app",
        )
