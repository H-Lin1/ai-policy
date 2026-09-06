from __future__ import annotations

from datetime import UTC, datetime
from math import ceil
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.local_auth import hash_password
from app.modules.consultation.models import ConsultationDepartment

from .models import AccountManagementEvent, Organization, Profile, Region, Role, User, UserRole
from .schemas import (
    AdminAccountCounts,
    AdminAccountDetail,
    AdminAccountPage,
    AdminAccountSummary,
    AdminAccountUpdate,
    AdminCreateAdminAccount,
    AdminCreateEnterpriseAccount,
    AdminCreateGovernmentAccount,
    AdminCreateIndividualAccount,
)


def admin_id(identity) -> UUID:
    if "admin" not in identity.role_codes:
        raise AppError("ROLE_FORBIDDEN", "只有管理员可以管理账号", status_code=403)
    try:
        return UUID(identity.subject)
    except ValueError as exc:
        raise AppError("IDENTITY_STORE_UNAVAILABLE", "应用身份服务暂不可用", status_code=503) from exc


def _role(session: Session, code: str) -> Role:
    item = session.execute(select(Role).where(Role.code == code, Role.is_active.is_(True))).scalar_one_or_none()
    if item is None:
        raise AppError("ACCOUNT_SCOPE_INVALID", "账号角色不可用", status_code=409)
    return item


def _region(session: Session) -> Region:
    item = session.execute(select(Region).where(Region.code == "sz", Region.is_active.is_(True))).scalar_one_or_none()
    if item is None:
        raise AppError("ACCOUNT_SCOPE_INVALID", "深圳地区不可用", status_code=409)
    return item


def _platform(session: Session) -> Organization:
    item = session.execute(select(Organization).where(Organization.organization_type == "platform", Organization.is_active.is_(True))).scalar_one_or_none()
    if item is None:
        raise AppError("ACCOUNT_SCOPE_INVALID", "平台组织不可用", status_code=409)
    return item


def _summary(session: Session, user: User, profile: Profile, organization: Organization | None) -> AdminAccountSummary:
    assignments = list(session.execute(select(UserRole, Role).join(Role, UserRole.role_id == Role.id).where(UserRole.user_id == user.id).order_by(UserRole.assigned_at.desc())).all())
    roles = [role.code for assignment, role in assignments if assignment.is_active]
    if not roles and assignments:
        roles = [assignments[0][1].code]
    department = session.execute(select(ConsultationDepartment).where(ConsultationDepartment.government_user_id == user.id)).scalar_one_or_none()
    status = "active" if user.is_active and profile.status == "active" and any(session.execute(select(UserRole.is_active).where(UserRole.user_id == user.id)).scalars()) else "disabled"
    return AdminAccountSummary(
        user_id=user.id, username=user.username, display_name=profile.display_name,
        email=user.email, contact_phone=user.contact_phone, job_title=user.job_title, roles=roles,
        organization_id=organization.id if organization else None,
        organization_name=organization.name if organization else None,
        organization_type=organization.organization_type if organization else None,
        department_id=department.department_id if department else None,
        department_name=department.department_name if department else None,
        status=status, created_at=user.created_at,
    )


def _rows(session: Session):
    return session.execute(
        select(User, Profile, Organization)
        .join(Profile, Profile.user_id == User.id)
        .outerjoin(Organization, Profile.organization_id == Organization.id)
        .order_by(User.created_at.desc(), User.username.asc())
    ).all()


def list_accounts(*, session: Session, page: int, page_size: int, role: str | None, status: str | None, keyword: str | None) -> AdminAccountPage:
    items = [_summary(session, user, profile, organization) for user, profile, organization in _rows(session)]
    if role in {"individual", "enterprise", "government", "admin"}:
        items = [item for item in items if role in item.roles]
    if status in {"active", "disabled"}:
        items = [item for item in items if item.status == status]
    if keyword and keyword.strip():
        needle = keyword.strip().casefold()
        items = [item for item in items if any(needle in (value or "").casefold() for value in (item.username, item.display_name, item.email, item.organization_name, item.department_name))]
    total = len(items); total_pages = ceil(total / page_size) if total else 0
    return AdminAccountPage(items=items[(page - 1) * page_size: page * page_size], page=page, page_size=page_size, total=total, total_pages=total_pages)


def account_counts(session: Session) -> AdminAccountCounts:
    page = list_accounts(session=session, page=1, page_size=10000, role=None, status=None, keyword=None)
    return AdminAccountCounts(
        individual=sum("individual" in x.roles for x in page.items),
        enterprise=sum("enterprise" in x.roles for x in page.items),
        government=sum("government" in x.roles for x in page.items),
        admin=sum("admin" in x.roles for x in page.items),
        active=sum(x.status == "active" for x in page.items),
        disabled=sum(x.status == "disabled" for x in page.items),
    )


def account_detail(session: Session, user_id: UUID) -> AdminAccountDetail:
    row = session.execute(select(User, Profile, Organization).join(Profile, Profile.user_id == User.id).outerjoin(Organization, Profile.organization_id == Organization.id).where(User.id == user_id)).one_or_none()
    if row is None:
        raise AppError("ACCOUNT_NOT_FOUND", "账号不存在", status_code=404)
    summary = _summary(session, *row)
    region_code = session.execute(select(Region.code).where(Region.id == row[1].region_id)).scalar_one()
    return AdminAccountDetail(**summary.model_dump(), region_code=region_code)


def _validate_password(payload) -> None:
    if payload.password != payload.password_confirmation:
        raise AppError("ACCOUNT_INVALID", "两次输入的密码不一致", status_code=422)


def _create(*, session: Session, payload, role_code: str, actor_id: UUID, organization: Organization | None, department: ConsultationDepartment | None = None) -> AdminAccountDetail:
    _validate_password(payload)
    if session.execute(select(User.id).where(User.username == payload.username.strip())).scalar_one_or_none():
        raise AppError("ACCOUNT_DUPLICATE", "登录账号已存在", status_code=409)
    region = _region(session); role = _role(session, role_code)
    try:
        user = User(username=payload.username.strip(), password_hash=hash_password(payload.password), email=payload.email.strip() if payload.email else None, contact_phone=payload.contact_phone.strip() if payload.contact_phone else None, job_title=payload.job_title.strip() if payload.job_title else None, display_name=payload.display_name.strip(), is_active=True)
        session.add(user); session.flush()
        session.add(Profile(user_id=user.id, display_name=user.display_name, region_id=region.id, organization_id=organization.id if organization else None, status="active", is_demo=False))
        session.add(UserRole(user_id=user.id, role_id=role.id, is_active=True)); session.flush()
        if department is not None:
            department.government_user_id = user.id
        session.add(AccountManagementEvent(target_user_id=user.id, actor_user_id=actor_id, event_type="account_created", change_summary={"role": role_code}))
        session.commit()
        return account_detail(session, user.id)
    except AppError:
        session.rollback(); raise
    except IntegrityError as exc:
        session.rollback(); raise AppError("ACCOUNT_DUPLICATE", "账号或组织已存在", status_code=409) from exc
    except SQLAlchemyError as exc:
        session.rollback(); raise AppError("IDENTITY_STORE_UNAVAILABLE", "账号服务暂不可用", status_code=503) from exc


def create_individual(*, session: Session, payload: AdminCreateIndividualAccount, actor_id: UUID) -> AdminAccountDetail:
    return _create(session=session, payload=payload, role_code="individual", actor_id=actor_id, organization=None)


def create_enterprise(*, session: Session, payload: AdminCreateEnterpriseAccount, actor_id: UUID) -> AdminAccountDetail:
    organization = session.get(Organization, payload.organization_id) if payload.organization_id else None
    if organization is not None and (organization.organization_type != "enterprise" or not organization.is_active):
        raise AppError("ACCOUNT_SCOPE_INVALID", "所选企业组织不可用", status_code=409)
    if organization is None:
        if not payload.enterprise_name or not payload.organization_code:
            raise AppError("ACCOUNT_SCOPE_INVALID", "创建企业账号需要企业名称和组织代码", status_code=422)
        organization = Organization(code=payload.organization_code.strip().lower(), name=payload.enterprise_name.strip(), organization_type="enterprise", region_id=_region(session).id, is_active=True, is_demo=False)
        session.add(organization); session.flush()
    return _create(session=session, payload=payload, role_code="enterprise", actor_id=actor_id, organization=organization)


def create_government(*, session: Session, payload: AdminCreateGovernmentAccount, actor_id: UUID) -> AdminAccountDetail:
    department = session.execute(select(ConsultationDepartment).where(ConsultationDepartment.department_id == payload.department_id, ConsultationDepartment.is_active.is_(True)).with_for_update()).scalar_one_or_none()
    if department is None or department.government_user_id is not None:
        raise AppError("ACCOUNT_DEPARTMENT_UNAVAILABLE", "所选政府部门不可用", status_code=409)
    organization = session.get(Organization, department.organization_id)
    if organization is None or organization.organization_type != "government" or not organization.is_active:
        raise AppError("ACCOUNT_SCOPE_INVALID", "政府组织不可用", status_code=409)
    return _create(session=session, payload=payload, role_code="government", actor_id=actor_id, organization=organization, department=department)


def create_admin(*, session: Session, payload: AdminCreateAdminAccount, actor_id: UUID) -> AdminAccountDetail:
    return _create(session=session, payload=payload, role_code="admin", actor_id=actor_id, organization=_platform(session))


def update_account(*, session: Session, user_id: UUID, payload: AdminAccountUpdate, actor_id: UUID) -> AdminAccountDetail:
    user = session.get(User, user_id); profile = session.get(Profile, user_id)
    if user is None or profile is None:
        raise AppError("ACCOUNT_NOT_FOUND", "账号不存在", status_code=404)
    if user_id == actor_id and payload.role_code != "admin":
        raise AppError("ACCOUNT_SELF_ROLE_FORBIDDEN", "不能移除当前管理员账号的管理员角色", status_code=409)
    role = _role(session, payload.role_code)
    organization: Organization | None = None; department: ConsultationDepartment | None = None
    if payload.role_code == "admin": organization = _platform(session)
    elif payload.role_code == "enterprise":
        organization = session.get(Organization, payload.organization_id) if payload.organization_id else None
        if organization is None or organization.organization_type != "enterprise" or not organization.is_active: raise AppError("ACCOUNT_SCOPE_INVALID", "企业组织不可用", status_code=409)
    elif payload.role_code == "government":
        department = session.get(ConsultationDepartment, payload.department_id) if payload.department_id else None
        if department is None or not department.is_active or (department.government_user_id not in {None, user_id}): raise AppError("ACCOUNT_DEPARTMENT_UNAVAILABLE", "政府部门不可用", status_code=409)
        organization = session.get(Organization, department.organization_id)
    old_departments = list(session.execute(select(ConsultationDepartment).where(ConsultationDepartment.government_user_id == user_id)).scalars())
    for item in old_departments:
        if item is not department: item.government_user_id = None
    for assignment in session.execute(select(UserRole).where(UserRole.user_id == user_id)).scalars(): assignment.is_active = assignment.role_id == role.id
    target_assignment = session.get(UserRole, {"user_id": user_id, "role_id": role.id})
    if target_assignment is None:
        session.add(UserRole(user_id=user_id, role_id=role.id, is_active=True, assigned_at=datetime.now(UTC)))
    else:
        target_assignment.is_active = True
        target_assignment.assigned_at = datetime.now(UTC)
    if department is not None: department.government_user_id = user_id
    user.display_name = payload.display_name.strip(); user.email = payload.email.strip() if payload.email else None; user.contact_phone = payload.contact_phone.strip() if payload.contact_phone else None; user.job_title = payload.job_title.strip() if payload.job_title else None
    profile.display_name = user.display_name; profile.organization_id = organization.id if organization else None
    session.add(AccountManagementEvent(target_user_id=user_id, actor_user_id=actor_id, event_type="account_updated", change_summary={"role": payload.role_code, "fields": ["display_name", "email", "contact_phone", "job_title", "scope"]}))
    session.commit(); return account_detail(session, user_id)


def set_account_enabled(*, session: Session, user_id: UUID, actor_id: UUID, enabled: bool) -> AdminAccountDetail:
    if user_id == actor_id and not enabled:
        raise AppError("ACCOUNT_SELF_DISABLE_FORBIDDEN", "不能停用当前管理员账号", status_code=409)
    user = session.get(User, user_id); profile = session.get(Profile, user_id)
    if user is None or profile is None: raise AppError("ACCOUNT_NOT_FOUND", "账号不存在", status_code=404)
    assignments = list(session.execute(select(UserRole).where(UserRole.user_id == user_id).order_by(UserRole.assigned_at.desc())).scalars())
    if enabled and not assignments: raise AppError("ACCOUNT_SCOPE_INVALID", "账号没有可恢复的角色", status_code=409)
    if enabled:
        latest_role = session.get(Role, assignments[0].role_id)
        organization = session.get(Organization, profile.organization_id) if profile.organization_id else None
        if latest_role is None:
            raise AppError("ACCOUNT_SCOPE_INVALID", "账号角色不可用", status_code=409)
        if latest_role.code == "enterprise" and (organization is None or organization.organization_type != "enterprise" or not organization.is_active):
            raise AppError("ACCOUNT_SCOPE_INVALID", "企业组织不可用", status_code=409)
        if latest_role.code == "admin" and (organization is None or organization.organization_type != "platform" or not organization.is_active):
            raise AppError("ACCOUNT_SCOPE_INVALID", "平台组织不可用", status_code=409)
        if latest_role.code == "government":
            department = session.execute(select(ConsultationDepartment).where(ConsultationDepartment.government_user_id == user_id, ConsultationDepartment.is_active.is_(True))).scalar_one_or_none()
            if department is None or organization is None or organization.organization_type != "government" or not organization.is_active:
                raise AppError("ACCOUNT_SCOPE_INVALID", "政府部门或组织不可用", status_code=409)
    user.is_active = enabled; profile.status = "active" if enabled else "disabled"
    for index, assignment in enumerate(assignments): assignment.is_active = enabled and index == 0
    session.add(AccountManagementEvent(target_user_id=user_id, actor_user_id=actor_id, event_type="account_enabled" if enabled else "account_disabled", change_summary={"enabled": enabled}))
    session.commit(); return account_detail(session, user_id)
