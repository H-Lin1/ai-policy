from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RoleCode = Literal["individual", "enterprise", "government", "admin"]
ROLE_CODES: tuple[str, ...] = ("individual", "enterprise", "government", "admin")


class RoleSummary(BaseModel):
    code: str
    name: str


class RegionSummary(BaseModel):
    code: str
    name: str


class OrganizationSummary(BaseModel):
    code: str
    name: str
    organization_type: str


class MeResponse(BaseModel):
    subject: str
    email: str | None = None
    display_name: str
    roles: list[str] = Field(default_factory=list)
    role_summaries: list[RoleSummary] = Field(default_factory=list)
    region: RegionSummary | None = None
    organization: OrganizationSummary | None = None
    development_bypass: bool = False


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: RoleCode
    title: str
    subject: str
    region: RegionSummary | None = None
    organization: OrganizationSummary | None = None


class LocalLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class LocalLoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
