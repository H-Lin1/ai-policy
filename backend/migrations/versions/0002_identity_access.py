"""Create the B1.1 identity and access foundation.

Revision ID: 0002_identity_access
Revises: 0001_foundation_schema
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_identity_access"
down_revision = "0001_foundation_schema"
branch_labels = None
depends_on = None

ROLE_CODES = ("individual", "enterprise", "government", "admin")
ORGANIZATION_TYPES = ("platform", "government", "enterprise")


def _postgresql_only() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    # The application schema is a PostgreSQL/Supabase boundary. SQLite remains
    # available for Stage 0 hermetic checks but must not create a false IAM DB.
    if not _postgresql_only():
        return

    uuid_type = postgresql.UUID(as_uuid=True)
    timestamp_type = sa.DateTime(timezone=True)

    op.create_table(
        "regions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("parent_id", uuid_type, nullable=True),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["parent_id"], ["app.regions.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("code", name="uq_regions_code"),
        sa.CheckConstraint(
            "code = lower(btrim(code)) AND length(btrim(code)) > 0",
            name="ck_regions_code",
        ),
        sa.CheckConstraint("length(btrim(name)) > 0", name="ck_regions_name"),
        sa.CheckConstraint(
            "level IN ('country', 'province', 'city', 'district', 'other')",
            name="ck_regions_level",
        ),
        schema="app",
    )

    op.create_table(
        "roles",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=256), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("code", name="uq_roles_code"),
        sa.CheckConstraint(
            "code IN ('individual', 'enterprise', 'government', 'admin')",
            name="ck_roles_code",
        ),
        sa.CheckConstraint(
            "code = lower(btrim(code)) AND length(btrim(code)) > 0",
            name="ck_roles_code_normalized",
        ),
        sa.CheckConstraint("length(btrim(name)) > 0", name="ck_roles_name"),
        sa.CheckConstraint(
            "length(btrim(description)) > 0",
            name="ck_roles_description",
        ),
        schema="app",
    )

    op.create_table(
        "organizations",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("organization_type", sa.String(length=32), nullable=False),
        sa.Column("region_id", uuid_type, nullable=False),
        sa.Column("parent_id", uuid_type, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["region_id"], ["app.regions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_id"], ["app.organizations.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("code", name="uq_organizations_code"),
        sa.CheckConstraint(
            "organization_type IN ('platform', 'government', 'enterprise')",
            name="ck_organizations_type",
        ),
        sa.CheckConstraint(
            "code = lower(btrim(code)) AND length(btrim(code)) > 0",
            name="ck_organizations_code",
        ),
        sa.CheckConstraint("length(btrim(name)) > 0", name="ck_organizations_name"),
        schema="app",
    )

    op.create_table(
        "profiles",
        sa.Column("user_id", uuid_type, primary_key=True),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("region_id", uuid_type, nullable=False),
        sa.Column("organization_id", uuid_type, nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["region_id"], ["app.regions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["app.organizations.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_profiles_status"),
        sa.CheckConstraint(
            "length(btrim(display_name)) > 0",
            name="ck_profiles_display_name",
        ),
        schema="app",
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("role_id", uuid_type, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("assigned_at", timestamp_type, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["app.profiles.user_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["role_id"], ["app.roles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_user_roles"),
        schema="app",
    )

    for table in ("regions", "roles", "organizations", "profiles", "user_roles"):
        op.execute(f"ALTER TABLE app.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL PRIVILEGES ON TABLE app.{table} FROM anon")
        op.execute(f"REVOKE ALL PRIVILEGES ON TABLE app.{table} FROM authenticated")


def downgrade() -> None:
    if not _postgresql_only():
        return
    for table in ("user_roles", "profiles", "organizations", "roles", "regions"):
        op.drop_table(table, schema="app")
