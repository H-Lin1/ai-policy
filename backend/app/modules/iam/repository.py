from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Organization, Profile, Region, Role, UserRole


@dataclass(frozen=True)
class RoleRecord:
    code: str
    name: str
    is_active: bool
    assignment_active: bool


@dataclass(frozen=True)
class IdentityRecord:
    user_id: UUID
    display_name: str
    profile_status: str
    region_code: str | None
    region_name: str | None
    region_active: bool
    organization_code: str | None
    organization_name: str | None
    organization_type: str | None
    organization_active: bool
    organization_region_id: UUID | None
    profile_region_id: UUID | None
    roles: tuple[RoleRecord, ...]


class IdentityRepository:
    """Read-only database boundary for the current application's identity."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def load(self, user_id: UUID) -> IdentityRecord | None:
        statement = (
            select(Profile, Region, Organization, UserRole, Role)
            .outerjoin(Region, Profile.region_id == Region.id)
            .outerjoin(Organization, Profile.organization_id == Organization.id)
            .outerjoin(UserRole, UserRole.user_id == Profile.user_id)
            .outerjoin(Role, UserRole.role_id == Role.id)
            .where(Profile.user_id == user_id)
            .order_by(Role.code.asc())
        )
        rows = self._session.execute(statement).all()
        if not rows:
            return None

        profile, region, organization, _, _ = rows[0]
        roles = tuple(
            RoleRecord(
                code=role.code,
                name=role.name,
                is_active=bool(role.is_active),
                assignment_active=bool(assignment.is_active),
            )
            for _, _, _, assignment, role in rows
            if assignment is not None and role is not None
        )
        return IdentityRecord(
            user_id=profile.user_id,
            display_name=profile.display_name,
            profile_status=profile.status,
            region_code=region.code if region is not None else None,
            region_name=region.name if region is not None else None,
            region_active=bool(region.is_active) if region is not None else False,
            organization_code=organization.code if organization is not None else None,
            organization_name=organization.name if organization is not None else None,
            organization_type=organization.organization_type if organization is not None else None,
            organization_active=bool(organization.is_active) if organization is not None else False,
            organization_region_id=organization.region_id if organization is not None else None,
            profile_region_id=profile.region_id,
            roles=roles,
        )
