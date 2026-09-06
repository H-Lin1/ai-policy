from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.contracts import PageResponse, PaginationMeta, PaginationParams
from app.core.errors import AppError
from app.core.local_auth import hash_password
from app.modules.consultation.models import ConsultationDepartment

from .models import (
    Organization,
    Profile,
    Region,
    RegistrationApplication,
    RegistrationApplicationEvent,
    Role,
    User,
    UserRole,
)
from .schemas import (
    AdminApplicationDetail,
    AdminApplicationSummary,
    EnterpriseRegistrationRequest,
    GovernmentRegistrationRequest,
    IndividualRegistrationRequest,
    RegistrationCreatedResponse,
    RegistrationStatusResponse,
)

SZ_REGION_ID = UUID("10000000-0000-4000-8000-000000000001")


def _require_local_database(settings, session: Session | None) -> Session:
    if settings.auth_mode != "local":
        raise AppError("REGISTRATION_UNAVAILABLE", "当前认证模式不支持注册", status_code=404)
    if session is None:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503)
    return session


def _validate_common(payload) -> None:
    if payload.password != payload.password_confirmation:
        raise AppError("REGISTRATION_INVALID", "两次输入的密码不一致", status_code=422)
    if not payload.terms_accepted:
        raise AppError("REGISTRATION_INVALID", "请先同意服务条款", status_code=422)


def _username_available(session: Session, username: str) -> bool:
    existing = session.execute(select(User.id).where(User.username == username)).scalar_one_or_none()
    if existing is not None:
        return False
    pending = session.execute(select(RegistrationApplication.id).where(RegistrationApplication.login_username == username, RegistrationApplication.status == "pending")).scalar_one_or_none()
    return pending is None


def _role(session: Session, code: str) -> Role:
    role = session.execute(select(Role).where(Role.code == code, Role.is_active.is_(True))).scalar_one_or_none()
    if role is None:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503)
    return role


def _region(session: Session) -> Region:
    region = session.execute(select(Region).where(Region.code == "sz", Region.is_active.is_(True))).scalar_one_or_none()
    if region is None:
        raise AppError("IDENTITY_SCOPE_INACTIVE", "当前身份不在受支持的深圳范围内", status_code=503)
    return region


def register_individual(*, payload: IndividualRegistrationRequest, session: Session, settings) -> RegistrationCreatedResponse:
    _require_local_database(settings, session)
    _validate_common(payload)
    username = payload.username.strip()
    display_name = payload.display_name.strip()
    if not username or not display_name or not _username_available(session, username):
        raise AppError("REGISTRATION_DUPLICATE_ACCOUNT", "账号已存在或正在申请中", status_code=409)
    try:
        region = _region(session)
        user = User(username=username, password_hash=hash_password(payload.password), display_name=display_name, is_active=True)
        session.add(user)
        session.flush()
        profile = Profile(user_id=user.id, display_name=display_name, region_id=region.id, status="active", is_demo=False)
        session.add(profile)
        session.add(UserRole(user_id=user.id, role_id=_role(session, "individual").id, is_active=True))
        session.commit()
        return RegistrationCreatedResponse(status="created", message="个人账号注册成功，请登录")
    except AppError:
        session.rollback()
        raise
    except IntegrityError as exc:
        session.rollback()
        raise AppError("REGISTRATION_DUPLICATE_ACCOUNT", "账号已存在或正在申请中", status_code=409) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503) from exc


def _create_application(*, session: Session, application_type: str, username: str, password: str, region_id: UUID, department_id: str | None, form_data: dict[str, object]) -> RegistrationCreatedResponse:
    if not _username_available(session, username):
        raise AppError("REGISTRATION_DUPLICATE_ACCOUNT", "账号已存在或正在申请中", status_code=409)
    item = RegistrationApplication(application_type=application_type, region_id=region_id, department_id=department_id, login_username=username, password_hash=hash_password(password), form_data=form_data, status="pending")
    session.add(item)
    session.flush()
    session.add(RegistrationApplicationEvent(application_id=item.id, event_type="submitted"))
    session.commit()
    return RegistrationCreatedResponse(id=item.id, status="pending", message="申请已提交，请等待管理员审核")


def register_enterprise(*, payload: EnterpriseRegistrationRequest, session: Session, settings) -> RegistrationCreatedResponse:
    _require_local_database(settings, session)
    _validate_common(payload)
    try:
        region = _region(session)
        credit = payload.unified_social_credit_code.strip().upper()
        duplicate = session.execute(select(RegistrationApplication.id).where(RegistrationApplication.application_type == "enterprise", RegistrationApplication.status == "pending", RegistrationApplication.form_data["unified_social_credit_code"].astext == credit)).scalar_one_or_none()
        if duplicate:
            raise AppError("REGISTRATION_DUPLICATE_CREDIT_CODE", "该企业已提交申请", status_code=409)
        return _create_application(session=session, application_type="enterprise", username=payload.username.strip(), password=payload.password, region_id=region.id, department_id=None, form_data={"enterprise_name": payload.enterprise_name.strip(), "unified_social_credit_code": credit, "enterprise_type": payload.enterprise_type.strip(), "registered_address": payload.registered_address.strip(), "user_name": payload.user_name.strip(), "job_title": payload.job_title.strip(), "contact_phone": payload.contact_phone.strip(), "contact_email": payload.contact_email.strip()})
    except AppError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503) from exc


def register_government(*, payload: GovernmentRegistrationRequest, session: Session, settings) -> RegistrationCreatedResponse:
    _require_local_database(settings, session)
    _validate_common(payload)
    try:
        region = _region(session)
        department = session.execute(select(ConsultationDepartment).where(ConsultationDepartment.department_id == payload.department_id.strip(), ConsultationDepartment.is_active.is_(True)).with_for_update()).scalar_one_or_none()
        if department is None:
            raise AppError("REGISTRATION_DEPARTMENT_UNAVAILABLE", "所选政府部门当前不可申请", status_code=409)
        occupied = department.government_user_id is not None or session.execute(select(RegistrationApplication.id).where(RegistrationApplication.application_type == "government", RegistrationApplication.department_id == department.department_id, RegistrationApplication.status == "pending")).scalar_one_or_none() is not None
        if occupied:
            raise AppError("REGISTRATION_DEPARTMENT_UNAVAILABLE", "所选政府部门当前不可申请", status_code=409)
        return _create_application(session=session, application_type="government", username=payload.username.strip(), password=payload.password, region_id=region.id, department_id=department.department_id, form_data={"department_name": department.department_name, "user_name": payload.user_name.strip(), "job_title": payload.job_title.strip(), "work_email": payload.work_email.strip(), "contact_phone": payload.contact_phone.strip(), "employee_identifier": payload.employee_identifier.strip() if payload.employee_identifier else None, "usage_scenario": payload.usage_scenario.strip(), "application_reason": payload.application_reason.strip()})
    except AppError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503) from exc


def applicant_status(*, application_id: UUID, verification: str, session: Session, settings) -> RegistrationStatusResponse:
    _require_local_database(settings, session)
    item = session.get(RegistrationApplication, application_id)
    if item is None:
        raise AppError("REGISTRATION_NOT_FOUND", "申请信息不存在或无法查询", status_code=404)
    contacts = [str(item.form_data.get("contact_phone") or ""), str(item.form_data.get("contact_email") or ""), str(item.form_data.get("work_email") or "")]
    if not verification.strip() or verification.strip() not in contacts:
        raise AppError("REGISTRATION_NOT_FOUND", "申请信息不存在或无法查询", status_code=404)
    return RegistrationStatusResponse(id=item.id, application_type=item.application_type, status=item.status, submitted_at=item.submitted_at, reviewed_at=item.reviewed_at, review_reason=item.review_reason)


def _summary(item: RegistrationApplication) -> AdminApplicationSummary:
    data = item.form_data
    title = str(data.get("enterprise_name") or data.get("department_name") or "注册申请")
    return AdminApplicationSummary(id=item.id, application_type=item.application_type, status=item.status, title=title, user_name=str(data.get("user_name") or ""), department_name=str(data.get("department_name")) if data.get("department_name") else None, submitted_at=item.submitted_at, reviewed_at=item.reviewed_at)


def list_admin_applications(*, session: Session, params: PaginationParams, application_type: str | None = None, status: str | None = None, keyword: str | None = None) -> PageResponse[AdminApplicationSummary]:
    query = select(RegistrationApplication).order_by(RegistrationApplication.submitted_at.desc())
    if application_type in {"enterprise", "government"}:
        query = query.where(RegistrationApplication.application_type == application_type)
    if status in {"pending", "approved", "rejected", "cancelled"}:
        query = query.where(RegistrationApplication.status == status)
    items = list(session.execute(query).scalars())
    if keyword:
        needle = keyword.strip().lower()
        items = [item for item in items if needle in str(item.form_data).lower() or needle in str(item.id).lower()]
    total = len(items)
    page_items = items[params.offset: params.offset + params.page_size]
    return PageResponse(items=[_summary(item) for item in page_items], meta=PaginationMeta.from_total(params, total))


def admin_detail(*, application_id: UUID, session: Session) -> AdminApplicationDetail:
    item = session.get(RegistrationApplication, application_id)
    if item is None:
        raise AppError("REGISTRATION_NOT_FOUND", "注册申请不存在", status_code=404)
    summary = _summary(item)
    return AdminApplicationDetail(**summary.model_dump(), form_data=item.form_data, login_username=item.login_username, review_reason=item.review_reason)


def decide_application(*, application_id: UUID, approve: bool, note: str | None, reason: str | None, actor_id: UUID, session: Session) -> AdminApplicationDetail:
    item = session.get(RegistrationApplication, application_id, with_for_update=True)
    if item is None:
        raise AppError("REGISTRATION_NOT_FOUND", "注册申请不存在", status_code=404)
    if item.status != "pending":
        raise AppError("REGISTRATION_ALREADY_PROCESSED", "该申请已经处理", status_code=409)
    if not approve and not (reason and reason.strip()):
        raise AppError("REGISTRATION_INVALID", "拒绝申请必须填写原因", status_code=422)
    try:
        now = datetime.now(UTC)
        if approve:
            region = session.get(Region, item.region_id)
            if region is None or region.code != "sz" or not region.is_active:
                raise AppError("REGISTRATION_INVALID", "申请地区不可用", status_code=409)
            role_code = "enterprise" if item.application_type == "enterprise" else "government"
            role = _role(session, role_code)
            data = item.form_data
            if item.application_type == "enterprise":
                credit = str(data["unified_social_credit_code"])
                if session.execute(select(Organization.id).where(Organization.code == f"enterprise-{credit.lower()}")).scalar_one_or_none():
                    raise AppError("REGISTRATION_DUPLICATE_CREDIT_CODE", "该企业已存在", status_code=409)
                organization = Organization(code=f"enterprise-{credit.lower()}", name=str(data["enterprise_name"]), organization_type="enterprise", region_id=region.id, is_active=True)
                session.add(organization)
                session.flush()
                display_name = str(data["user_name"])
            else:
                department = session.execute(select(ConsultationDepartment).where(ConsultationDepartment.department_id == item.department_id).with_for_update()).scalar_one_or_none()
                if department is None or department.government_user_id is not None:
                    raise AppError("REGISTRATION_DEPARTMENT_UNAVAILABLE", "所选政府部门当前不可用", status_code=409)
                organization = session.get(Organization, department.organization_id)
                if organization is None or not organization.is_active:
                    raise AppError("REGISTRATION_DEPARTMENT_UNAVAILABLE", "所选政府部门当前不可用", status_code=409)
                display_name = str(data["user_name"])
            if session.execute(select(User.id).where(User.username == item.login_username)).scalar_one_or_none():
                raise AppError("REGISTRATION_DUPLICATE_ACCOUNT", "账号已存在或正在申请中", status_code=409)
            user = User(username=item.login_username, password_hash=item.password_hash, email=str(data.get("contact_email") or data.get("work_email") or "") or None, display_name=display_name, is_active=True)
            session.add(user)
            session.flush()
            session.add(Profile(user_id=user.id, display_name=display_name, region_id=region.id, organization_id=organization.id, status="active", is_demo=False))
            session.add(UserRole(user_id=user.id, role_id=role.id, is_active=True))
            # The department FK points at profiles, but no ORM relationship declares
            # that dependency. Flush identity rows before assigning the department.
            session.flush()
            if item.application_type == "government":
                department.government_user_id = user.id
        item.status = "approved" if approve else "rejected"
        item.reviewed_at = now
        item.reviewer_user_id = actor_id
        item.review_reason = (note or "").strip() if approve else (reason or "").strip()
        session.add(RegistrationApplicationEvent(application_id=item.id, event_type=item.status, actor_user_id=actor_id, reason=item.review_reason or None))
        session.commit()
        return admin_detail(application_id=item.id, session=session)
    except AppError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503) from exc
