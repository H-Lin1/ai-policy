"""Create B1.6 consultation workflow and dedicated department bindings.

Revision ID: 0005_consultation_workflow
Revises: 0004_historical_qa
"""

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_consultation_workflow"
down_revision = "0004_historical_qa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    uuid = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "consultation_departments",
        sa.Column("department_id", sa.String(96), primary_key=True),
        sa.Column("department_name", sa.String(160), nullable=False),
        sa.Column("organization_id", uuid, nullable=False, unique=True),
        sa.Column("government_user_id", uuid, nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["app.organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["government_user_id"], ["app.profiles.user_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("length(btrim(department_id)) > 0", name="ck_consultation_department_id"),
        sa.CheckConstraint("length(btrim(department_name)) > 0", name="ck_consultation_department_name"), schema="app",
    )
    op.create_table(
        "consultations",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("requester_user_id", uuid, nullable=False), sa.Column("selected_department_id", sa.String(96), nullable=False),
        sa.Column("assigned_organization_id", uuid, nullable=False), sa.Column("assigned_user_id", uuid, nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'assigned'")),
        sa.Column("classification_model_version", sa.String(160), nullable=False), sa.Column("classification_predictions", postgresql.JSONB(), nullable=False),
        sa.Column("answer_text", sa.Text()), sa.Column("publish_to_history", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("public_question_text", sa.Text()), sa.Column("public_answer_text", sa.Text()), sa.Column("historical_qa_id", uuid, unique=True),
        sa.Column("replied_at", timestamp), sa.Column("closed_at", timestamp),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", timestamp, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["requester_user_id"], ["app.profiles.user_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["selected_department_id"], ["app.consultation_departments.department_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_organization_id"], ["app.organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["app.profiles.user_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["historical_qa_id"], ["app.historical_qa.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("status IN ('submitted', 'assigned', 'replied', 'published', 'closed')", name="ck_consultations_status"),
        sa.CheckConstraint("length(btrim(question_text)) > 0", name="ck_consultations_question"),
        sa.CheckConstraint("answer_text IS NULL OR length(btrim(answer_text)) > 0", name="ck_consultations_answer"), schema="app",
    )
    op.create_index("ix_consultations_requester_created", "consultations", ["requester_user_id", "created_at"], schema="app")
    op.create_index("ix_consultations_assignee_created", "consultations", ["assigned_user_id", "created_at"], schema="app")
    op.create_table(
        "consultation_events", sa.Column("id", uuid, primary_key=True), sa.Column("consultation_id", uuid, nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False), sa.Column("actor_user_id", uuid),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["consultation_id"], ["app.consultations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["app.profiles.user_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("event_type IN ('submitted', 'assigned', 'replied', 'published', 'closed')", name="ck_consultation_events_type"), schema="app",
    )
    op.create_index("ix_consultation_events_consultation_created", "consultation_events", ["consultation_id", "created_at"], schema="app")
    standalone_mode = os.getenv("DATABASE_MODE", "supabase").strip().lower() == "standalone"
    for table in ("consultation_departments", "consultations", "consultation_events"):
        op.execute(f"ALTER TABLE app.{table} ENABLE ROW LEVEL SECURITY")
        if not standalone_mode:
            op.execute(f"REVOKE ALL PRIVILEGES ON TABLE app.{table} FROM anon")
            op.execute(f"REVOKE ALL PRIVILEGES ON TABLE app.{table} FROM authenticated")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table in ("consultation_events", "consultations", "consultation_departments"):
            op.drop_table(table, schema="app")
