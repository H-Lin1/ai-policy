from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

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


class RegistrationBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=12, max_length=256)
    password_confirmation: str = Field(min_length=12, max_length=256)
    terms_accepted: bool


class IndividualRegistrationRequest(RegistrationBase):
    display_name: str = Field(min_length=1, max_length=160)


class EnterpriseRegistrationRequest(RegistrationBase):
    enterprise_name: str = Field(min_length=1, max_length=160)
    unified_social_credit_code: str = Field(min_length=8, max_length=64)
    enterprise_type: str = Field(min_length=1, max_length=64)
    registered_address: str = Field(min_length=1, max_length=300)
    user_name: str = Field(min_length=1, max_length=160)
    job_title: str = Field(min_length=1, max_length=120)
    contact_phone: str = Field(min_length=5, max_length=40)
    contact_email: str = Field(min_length=3, max_length=320)


class GovernmentRegistrationRequest(RegistrationBase):
    department_id: str = Field(min_length=1, max_length=96)
    user_name: str = Field(min_length=1, max_length=160)
    job_title: str = Field(min_length=1, max_length=120)
    work_email: str = Field(min_length=3, max_length=320)
    contact_phone: str = Field(min_length=5, max_length=40)
    employee_identifier: str | None = Field(default=None, max_length=120)
    usage_scenario: str = Field(min_length=1, max_length=1000)
    application_reason: str = Field(min_length=1, max_length=2000)


class RegistrationCreatedResponse(BaseModel):
    id: UUID | None = None
    status: Literal["created", "pending"]
    message: str


class RegistrationStatusResponse(BaseModel):
    id: UUID
    application_type: Literal["enterprise", "government"]
    status: Literal["pending", "approved", "rejected", "cancelled"]
    submitted_at: datetime
    reviewed_at: datetime | None = None
    review_reason: str | None = None


class AdminApplicationSummary(BaseModel):
    id: UUID
    application_type: Literal["enterprise", "government"]
    status: Literal["pending", "approved", "rejected", "cancelled"]
    title: str
    user_name: str
    department_name: str | None = None
    submitted_at: datetime
    reviewed_at: datetime | None = None


class AdminApplicationDetail(AdminApplicationSummary):
    form_data: dict[str, object]
    login_username: str
    review_reason: str | None = None


class AdminDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str | None = Field(default=None, max_length=2000)


class AdminRejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=1, max_length=2000)


class AdminAccountSummary(BaseModel):
    user_id: UUID
    username: str
    display_name: str
    email: str | None = None
    contact_phone: str | None = None
    job_title: str | None = None
    roles: list[str]
    organization_id: UUID | None = None
    organization_name: str | None = None
    organization_type: str | None = None
    department_id: str | None = None
    department_name: str | None = None
    status: Literal["active", "disabled"]
    created_at: datetime


class AdminAccountDetail(AdminAccountSummary):
    region_code: str


class AdminAccountPage(BaseModel):
    items: list[AdminAccountSummary]
    page: int
    page_size: int
    total: int
    total_pages: int


class AdminAccountCounts(BaseModel):
    individual: int
    enterprise: int
    government: int
    admin: int
    active: int
    disabled: int


class AdminAccountCreateBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=12, max_length=256)
    password_confirmation: str = Field(min_length=12, max_length=256)
    display_name: str = Field(min_length=1, max_length=160)
    email: str | None = Field(default=None, max_length=320)
    contact_phone: str | None = Field(default=None, max_length=40)
    job_title: str | None = Field(default=None, max_length=120)


class AdminCreateIndividualAccount(AdminAccountCreateBase):
    pass


class AdminCreateEnterpriseAccount(AdminAccountCreateBase):
    organization_id: UUID | None = None
    enterprise_name: str | None = Field(default=None, max_length=160)
    organization_code: str | None = Field(default=None, max_length=64)


class AdminCreateGovernmentAccount(AdminAccountCreateBase):
    department_id: str = Field(min_length=1, max_length=96)


class AdminCreateAdminAccount(AdminAccountCreateBase):
    pass


class AdminAccountUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=160)
    email: str | None = Field(default=None, max_length=320)
    contact_phone: str | None = Field(default=None, max_length=40)
    job_title: str | None = Field(default=None, max_length=120)
    role_code: RoleCode
    organization_id: UUID | None = None
    department_id: str | None = Field(default=None, max_length=96)
