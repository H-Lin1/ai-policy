from __future__ import annotations

from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    false,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Region(Base):
    __tablename__ = "regions"
    __table_args__ = (
        UniqueConstraint("code", name="uq_regions_code"),
        CheckConstraint(
            "code = lower(btrim(code)) AND length(btrim(code)) > 0",
            name="ck_regions_code",
        ),
        CheckConstraint("length(btrim(name)) > 0", name="ck_regions_name"),
        CheckConstraint(
            "level IN ('country', 'province', 'city', 'district', 'other')",
            name="ck_regions_level",
        ),
        {"schema": "app"},
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(128))
    parent_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.regions.id", ondelete="RESTRICT")
    )
    level: Mapped[str] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("code", name="uq_roles_code"),
        CheckConstraint(
            "code IN ('individual', 'enterprise', 'government', 'admin')",
            name="ck_roles_code",
        ),
        CheckConstraint(
            "code = lower(btrim(code)) AND length(btrim(code)) > 0",
            name="ck_roles_code_normalized",
        ),
        CheckConstraint("length(btrim(name)) > 0", name="ck_roles_name"),
        CheckConstraint(
            "length(btrim(description)) > 0",
            name="ck_roles_description",
        ),
        {"schema": "app"},
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    assignments: Mapped[list[UserRole]] = relationship(
        back_populates="role", passive_deletes=True
    )


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        UniqueConstraint("code", name="uq_organizations_code"),
        CheckConstraint(
            "organization_type IN ('platform', 'government', 'enterprise')",
            name="ck_organizations_type",
        ),
        CheckConstraint(
            "code = lower(btrim(code)) AND length(btrim(code)) > 0",
            name="ck_organizations_code",
        ),
        CheckConstraint("length(btrim(name)) > 0", name="ck_organizations_name"),
        {"schema": "app"},
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(160))
    organization_type: Mapped[str] = mapped_column(String(32))
    region_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.regions.id", ondelete="RESTRICT")
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.organizations.id", ondelete="RESTRICT")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    region: Mapped[Region] = relationship()


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled')", name="ck_profiles_status"),
        CheckConstraint(
            "length(btrim(display_name)) > 0",
            name="ck_profiles_display_name",
        ),
        {"schema": "app"},
    )

    # Supabase owns auth.users; migration 0002 carries that cross-schema FK so
    # SQLAlchemy never has to resolve the managed table in application metadata.
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(String(160))
    region_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.regions.id", ondelete="RESTRICT")
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.organizations.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(
        String(32), default="active", server_default=text("'active'")
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    region: Mapped[Region] = relationship()
    organization: Mapped[Organization | None] = relationship()
    user_roles: Mapped[list[UserRole]] = relationship(
        back_populates="profile", passive_deletes=True
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__: ClassVar[dict[str, str]] = {"schema": "app"}

    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("app.profiles.user_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    role_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("app.roles.id", ondelete="RESTRICT"), primary_key=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    profile: Mapped[Profile] = relationship(back_populates="user_roles")
    role: Mapped[Role] = relationship(back_populates="assignments")
