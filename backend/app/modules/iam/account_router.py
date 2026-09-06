from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.contracts import COMMON_ERROR_RESPONSES
from app.core.database import request_db_session
from app.core.errors import AppError

from .account_service import (
    account_counts,
    account_detail,
    admin_id,
    create_admin,
    create_enterprise,
    create_government,
    create_individual,
    list_accounts,
    set_account_enabled,
    update_account,
)
from .schemas import (
    AdminAccountCounts,
    AdminAccountDetail,
    AdminAccountPage,
    AdminAccountUpdate,
    AdminCreateAdminAccount,
    AdminCreateEnterpriseAccount,
    AdminCreateGovernmentAccount,
    AdminCreateIndividualAccount,
)
from .service import IdentityContext, get_current_identity

router = APIRouter(prefix="/admin/accounts", tags=["admin-account-management"])


def _session(session: Session | None) -> Session:
    if session is None: raise AppError("IDENTITY_STORE_UNAVAILABLE", "账号服务暂不可用", status_code=503)
    return session


@router.get("/counts", response_model=AdminAccountCounts, responses=COMMON_ERROR_RESPONSES)
def counts(response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminAccountCounts:
    admin_id(identity); response.headers["Cache-Control"] = "no-store"; return account_counts(_session(session))


@router.get("", response_model=AdminAccountPage, responses=COMMON_ERROR_RESPONSES)
def account_list(response: Response, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), role: str | None = Query(None), status: str | None = Query(None), keyword: str | None = Query(None, max_length=100), identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminAccountPage:
    admin_id(identity); response.headers["Cache-Control"] = "no-store"; return list_accounts(session=_session(session), page=page, page_size=page_size, role=role, status=status, keyword=keyword)


@router.get("/{user_id}", response_model=AdminAccountDetail, responses=COMMON_ERROR_RESPONSES)
def detail(user_id: UUID, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminAccountDetail:
    admin_id(identity); response.headers["Cache-Control"] = "no-store"; return account_detail(_session(session), user_id)


@router.post("/individual", response_model=AdminAccountDetail, responses=COMMON_ERROR_RESPONSES)
def add_individual(payload: AdminCreateIndividualAccount, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminAccountDetail:
    actor = admin_id(identity); response.headers["Cache-Control"] = "no-store"; return create_individual(session=_session(session), payload=payload, actor_id=actor)


@router.post("/enterprise", response_model=AdminAccountDetail, responses=COMMON_ERROR_RESPONSES)
def add_enterprise(payload: AdminCreateEnterpriseAccount, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminAccountDetail:
    actor = admin_id(identity); response.headers["Cache-Control"] = "no-store"; return create_enterprise(session=_session(session), payload=payload, actor_id=actor)


@router.post("/government", response_model=AdminAccountDetail, responses=COMMON_ERROR_RESPONSES)
def add_government(payload: AdminCreateGovernmentAccount, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminAccountDetail:
    actor = admin_id(identity); response.headers["Cache-Control"] = "no-store"; return create_government(session=_session(session), payload=payload, actor_id=actor)


@router.post("/admin", response_model=AdminAccountDetail, responses=COMMON_ERROR_RESPONSES)
def add_admin(payload: AdminCreateAdminAccount, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminAccountDetail:
    actor = admin_id(identity); response.headers["Cache-Control"] = "no-store"; return create_admin(session=_session(session), payload=payload, actor_id=actor)


@router.patch("/{user_id}", response_model=AdminAccountDetail, responses=COMMON_ERROR_RESPONSES)
def edit(user_id: UUID, payload: AdminAccountUpdate, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminAccountDetail:
    actor = admin_id(identity); response.headers["Cache-Control"] = "no-store"; return update_account(session=_session(session), user_id=user_id, payload=payload, actor_id=actor)


@router.post("/{user_id}/disable", response_model=AdminAccountDetail, responses=COMMON_ERROR_RESPONSES)
def disable(user_id: UUID, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminAccountDetail:
    actor = admin_id(identity); response.headers["Cache-Control"] = "no-store"; return set_account_enabled(session=_session(session), user_id=user_id, actor_id=actor, enabled=False)


@router.post("/{user_id}/enable", response_model=AdminAccountDetail, responses=COMMON_ERROR_RESPONSES)
def enable(user_id: UUID, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminAccountDetail:
    actor = admin_id(identity); response.headers["Cache-Control"] = "no-store"; return set_account_enabled(session=_session(session), user_id=user_id, actor_id=actor, enabled=True)
