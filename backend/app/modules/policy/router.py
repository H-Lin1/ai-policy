from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.contracts import (
    AUTH_ERROR_RESPONSES,
    COMMON_ERROR_RESPONSES,
    IDENTITY_ERROR_RESPONSES,
    PageResponse,
    PaginationMeta,
    PaginationParams,
    error_response,
)
from app.modules.iam.service import IdentityContext, get_current_identity

from .repository import FixturePolicyRepository, PolicyRepository
from .schemas import PolicyDetail, PolicyListItem, PolicyPage
from .service import get_policy, list_policies, policy_repository_dependency

NO_STORE = "no-store"
router = APIRouter(prefix="/policies", tags=["policy-library"])
ERRORS = {
    **COMMON_ERROR_RESPONSES,
    **AUTH_ERROR_RESPONSES,
    **IDENTITY_ERROR_RESPONSES,
    404: error_response("政策记录不存在", code="POLICY_NOT_FOUND"),
    503: error_response("政策库暂不可用", code="POLICY_STORE_UNAVAILABLE"),
}


@router.get(
    "",
    response_model=PolicyPage,
    summary="政策列表",
    operation_id="policyList",
    responses=ERRORS,
)
def policy_list(
    response: Response,
    pagination: PaginationParams = Depends(),
    q: str | None = Query(default=None, max_length=80),
    identity: IdentityContext = Depends(get_current_identity),
    repository: PolicyRepository | FixturePolicyRepository | None = Depends(policy_repository_dependency),
) -> PageResponse[PolicyListItem]:
    response.headers["Cache-Control"] = NO_STORE
    result = list_policies(
        identity=identity,
        repository=repository,
        offset=pagination.offset,
        limit=pagination.page_size,
        query=q,
    )
    return PageResponse[PolicyListItem](
        items=[PolicyListItem.model_validate(item, from_attributes=True) for item in result.items],
        meta=PaginationMeta.from_total(pagination, result.total),
    )


@router.get(
    "/{policy_id}",
    response_model=PolicyDetail,
    summary="政策详情",
    operation_id="policyDetail",
    responses=ERRORS,
)
def policy_detail(
    policy_id: UUID,
    response: Response,
    identity: IdentityContext = Depends(get_current_identity),
    repository: PolicyRepository | FixturePolicyRepository | None = Depends(policy_repository_dependency),
) -> PolicyDetail:
    response.headers["Cache-Control"] = NO_STORE
    record = get_policy(identity=identity, repository=repository, policy_id=policy_id)
    return PolicyDetail.model_validate(record, from_attributes=True)
