"""Create the application schema without business tables.

Revision ID: 0001_foundation_schema
Revises:
"""

from alembic import op

revision = "0001_foundation_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite is useful for local smoke tests but has no schema namespace.
    # Supabase/PostgreSQL gets the application namespace created explicitly.
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE SCHEMA IF NOT EXISTS app")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP SCHEMA IF EXISTS app")
