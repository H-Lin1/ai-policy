from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import Response as StarletteResponse
from sqlalchemy.orm import Session

from app.api.contracts import COMMON_ERROR_RESPONSES
from app.core.database import request_db_session
from app.core.errors import AppError
from app.modules.iam.service import IdentityContext, get_current_identity

from .admin_service import (
    admin_actor,
    create_policy,
    list_admin_policies,
    parse_batch,
    publish_policy,
    withdraw_policy,
)
from .markdown import EXAMPLE_MARKDOWN
from .schemas import (
    AdminPolicyCreateRequest,
    AdminPolicyRecord,
    MarkdownBatchRequest,
    MarkdownBatchResponse,
    PolicyWithdrawRequest,
)

router = APIRouter(prefix="/admin/policies", tags=["admin-policy-publishing"])


def _session(session: Session | None) -> Session:
    if session is None:
        raise AppError("POLICY_STORE_UNAVAILABLE", "政策库暂不可用", status_code=503)
    return session


@router.get("/markdown-example", response_class=StarletteResponse, responses=COMMON_ERROR_RESPONSES)
def markdown_example(identity: IdentityContext = Depends(get_current_identity)) -> StarletteResponse:
    admin_actor(identity)
    return StarletteResponse(
        EXAMPLE_MARKDOWN,
        media_type="text/markdown; charset=utf-8",
        headers={"Cache-Control": "no-store", "Content-Disposition": 'attachment; filename="policy-example.md"'},
    )


@router.post("/markdown-parse", response_model=MarkdownBatchResponse, responses=COMMON_ERROR_RESPONSES)
def markdown_parse(payload: MarkdownBatchRequest, response: Response, identity: IdentityContext = Depends(get_current_identity)) -> MarkdownBatchResponse:
    admin_actor(identity); response.headers["Cache-Control"] = "no-store"; return parse_batch(payload)


@router.get("", response_model=list[AdminPolicyRecord], responses=COMMON_ERROR_RESPONSES)
def admin_policy_list(response: Response, status: str | None = Query(default=None), identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> list[AdminPolicyRecord]:
    admin_actor(identity); response.headers["Cache-Control"] = "no-store"; return list_admin_policies(_session(session), status)


@router.post("", response_model=AdminPolicyRecord, responses=COMMON_ERROR_RESPONSES)
def admin_policy_create(payload: AdminPolicyCreateRequest, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminPolicyRecord:
    actor = admin_actor(identity); response.headers["Cache-Control"] = "no-store"; return create_policy(session=_session(session), payload=payload, actor_id=actor)


@router.post("/{policy_id}/publish", response_model=AdminPolicyRecord, responses=COMMON_ERROR_RESPONSES)
def admin_policy_publish(policy_id: UUID, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminPolicyRecord:
    actor = admin_actor(identity); response.headers["Cache-Control"] = "no-store"; return publish_policy(session=_session(session), policy_id=policy_id, actor_id=actor)


@router.post("/{policy_id}/withdraw", response_model=AdminPolicyRecord, responses=COMMON_ERROR_RESPONSES)
def admin_policy_withdraw(policy_id: UUID, payload: PolicyWithdrawRequest, response: Response, identity: IdentityContext = Depends(get_current_identity), session: Session | None = Depends(request_db_session)) -> AdminPolicyRecord:
    actor = admin_actor(identity); response.headers["Cache-Control"] = "no-store"; return withdraw_policy(session=_session(session), policy_id=policy_id, actor_id=actor, reason=payload.reason)
