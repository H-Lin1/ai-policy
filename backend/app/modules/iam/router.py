from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.contracts import (
    AUTH_ERROR_RESPONSES,
    COMMON_ERROR_RESPONSES,
    IDENTITY_ERROR_RESPONSES,
    PageResponse,
    PaginationParams,
)
from app.core.config import Settings, get_settings
from app.core.database import request_db_session
from app.core.errors import AppError
from app.core.local_auth import issue_token, verify_password
from app.modules.consultation.models import ConsultationDepartment

from .models import User
from .registration_service import (
    _require_local_database,
    admin_detail,
    applicant_status,
    decide_application,
    list_admin_applications,
    register_enterprise,
    register_government,
    register_individual,
)
from .schemas import (
    AdminApplicationDetail,
    AdminApplicationSummary,
    AdminDecisionRequest,
    AdminRejectRequest,
    EnterpriseRegistrationRequest,
    GovernmentRegistrationRequest,
    IndividualRegistrationRequest,
    LocalLoginRequest,
    LocalLoginResponse,
    RegistrationCreatedResponse,
    RegistrationStatusResponse,
    RoleCode,
    WorkspaceResponse,
)
from .service import IdentityContext, get_current_identity, role_title

NO_STORE = "no-store"

router = APIRouter(prefix="/iam", tags=["identity-access"])


@router.post(
    "/login",
    response_model=LocalLoginResponse,
    summary="本地账号登录",
    operation_id="localLogin",
    responses=COMMON_ERROR_RESPONSES,
)
def local_login(
    payload: LocalLoginRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    session: Session | None = Depends(request_db_session),
) -> LocalLoginResponse:
    response.headers["Cache-Control"] = NO_STORE
    if settings.auth_mode != "local":
        raise AppError("ROUTE_NOT_FOUND", "请求的接口不存在", status_code=404)
    if session is None:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503)
    username = payload.username.strip()
    account = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if account is None or not account.is_active or not verify_password(payload.password, account.password_hash):
        raise AppError("AUTH_INVALID", "账号或密码错误", status_code=401)
    token, expires_in = issue_token(user_id=account.id, username=account.username, settings=settings)
    return LocalLoginResponse(access_token=token, expires_in=expires_in)


@router.post("/registrations/individual", response_model=RegistrationCreatedResponse, responses=COMMON_ERROR_RESPONSES, operation_id="registerIndividual")
def register_individual_route(payload: IndividualRegistrationRequest, response: Response, settings: Settings = Depends(get_settings), session: Session | None = Depends(request_db_session)) -> RegistrationCreatedResponse:
    response.headers["Cache-Control"] = NO_STORE
    return register_individual(payload=payload, session=session, settings=settings)  # type: ignore[arg-type]


@router.post("/registrations/enterprise", response_model=RegistrationCreatedResponse, responses=COMMON_ERROR_RESPONSES, operation_id="registerEnterprise")
def register_enterprise_route(payload: EnterpriseRegistrationRequest, response: Response, settings: Settings = Depends(get_settings), session: Session | None = Depends(request_db_session)) -> RegistrationCreatedResponse:
    response.headers["Cache-Control"] = NO_STORE
    return register_enterprise(payload=payload, session=session, settings=settings)  # type: ignore[arg-type]


@router.post("/registrations/government", response_model=RegistrationCreatedResponse, responses=COMMON_ERROR_RESPONSES, operation_id="registerGovernment")
def register_government_route(payload: GovernmentRegistrationRequest, response: Response, settings: Settings = Depends(get_settings), session: Session | None = Depends(request_db_session)) -> RegistrationCreatedResponse:
    response.headers["Cache-Control"] = NO_STORE
    return register_government(payload=payload, session=session, settings=settings)  # type: ignore[arg-type]


@router.get("/registration-applications/{application_id}/status", response_model=RegistrationStatusResponse, responses=COMMON_ERROR_RESPONSES, operation_id="registrationApplicationStatus")
def registration_status_route(application_id: UUID, response: Response, verification: str = Query(min_length=1, max_length=320), settings: Settings = Depends(get_settings), session: Session | None = Depends(request_db_session)) -> RegistrationStatusResponse:
    response.headers["Cache-Control"] = NO_STORE
    return applicant_status(application_id=application_id, verification=verification, session=session, settings=settings)  # type: ignore[arg-type]


admin_router = APIRouter(prefix="/admin/registration-applications", tags=["registration-approval"])


@router.get("/registration-departments", response_model=list[dict[str, str]], responses=COMMON_ERROR_RESPONSES, operation_id="registrationDepartments")
def registration_departments_route(response: Response, settings: Settings = Depends(get_settings), session: Session | None = Depends(request_db_session)) -> list[dict[str, str]]:
    response.headers["Cache-Control"] = NO_STORE
    database = _require_local_database(settings, session)
    rows = database.execute(select(ConsultationDepartment).where(ConsultationDepartment.is_active.is_(True), ConsultationDepartment.government_user_id.is_(None)).order_by(ConsultationDepartment.department_name.asc())).scalars()
    return [{"department_id": item.department_id, "department_name": item.department_name} for item in rows]


def _admin_identity(identity: IdentityContext) -> UUID:
    if "admin" not in identity.role_codes:
        raise AppError("ROLE_FORBIDDEN", "当前身份无权访问注册申请", status_code=403)
    try:
        return UUID(identity.subject)
    except ValueError as exc:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503) from exc


@admin_router.get("", response_model=PageResponse[AdminApplicationSummary], responses=COMMON_ERROR_RESPONSES, operation_id="adminRegistrationApplicationList")
def admin_application_list_route(response: Response, page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), application_type: str | None = Query(default=None), status: str | None = Query(default=None), keyword: str | None = Query(default=None, max_length=100), identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> PageResponse[AdminApplicationSummary]:
    response.headers["Cache-Control"] = NO_STORE
    _admin_identity(identity)
    if session is None:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503)
    return list_admin_applications(session=session, params=PaginationParams(page=page, page_size=page_size), application_type=application_type, status=status, keyword=keyword)


@admin_router.get("/{application_id}", response_model=AdminApplicationDetail, responses=COMMON_ERROR_RESPONSES, operation_id="adminRegistrationApplicationDetail")
def admin_application_detail_route(application_id: UUID, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminApplicationDetail:
    response.headers["Cache-Control"] = NO_STORE
    _admin_identity(identity)
    if session is None:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503)
    return admin_detail(application_id=application_id, session=session)


@admin_router.post("/{application_id}/approve", response_model=AdminApplicationDetail, responses=COMMON_ERROR_RESPONSES, operation_id="approveRegistrationApplication")
def admin_application_approve_route(application_id: UUID, payload: AdminDecisionRequest, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminApplicationDetail:
    response.headers["Cache-Control"] = NO_STORE
    actor_id = _admin_identity(identity)
    if session is None:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503)
    return decide_application(application_id=application_id, approve=True, note=payload.note, reason=None, actor_id=actor_id, session=session)


@admin_router.post("/{application_id}/reject", response_model=AdminApplicationDetail, responses=COMMON_ERROR_RESPONSES, operation_id="rejectRegistrationApplication")
def admin_application_reject_route(application_id: UUID, payload: AdminRejectRequest, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminApplicationDetail:
    response.headers["Cache-Control"] = NO_STORE
    actor_id = _admin_identity(identity)
    if session is None:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503)
    return decide_application(application_id=application_id, approve=False, note=None, reason=payload.reason, actor_id=actor_id, session=session)




@router.get(
    "/workspaces/{role}",
    response_model=WorkspaceResponse,
    summary="角色工作区访问检查",
    operation_id="iamWorkspaceAccess",
    responses={**COMMON_ERROR_RESPONSES, **AUTH_ERROR_RESPONSES, **IDENTITY_ERROR_RESPONSES},
)
def workspace_access(
    response: Response,
    role: RoleCode = Path(description="请求进入的稳定角色代码"),
    identity: IdentityContext = Depends(get_current_identity),
) -> WorkspaceResponse:
    response.headers["Cache-Control"] = NO_STORE
    if role not in identity.role_codes:
        raise AppError("ROLE_FORBIDDEN", "当前身份无权进入该工作区", status_code=403)
    return WorkspaceResponse(
        role=role,
        title=role_title(role),
        subject=identity.subject,
        region=(
            {"code": identity.region_code, "name": identity.region_name}
            if identity.region_code and identity.region_name
            else None
        ),
        organization=(
            {
                "code": identity.organization_code,
                "name": identity.organization_name,
                "organization_type": identity.organization_type,
            }
            if identity.organization_code and identity.organization_name and identity.organization_type
            else None
        ),
    )
