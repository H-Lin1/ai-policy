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

from .repository import FixtureHistoricalQaRepository, HistoricalQaRepository
from .schemas import HistoricalQaDetail, HistoricalQaListItem, HistoricalQaPage
from .service import get_historical_qa, historical_qa_repository_dependency, list_historical_qa

NO_STORE = "no-store"
router = APIRouter(prefix="/qa", tags=["historical-qa"])
ERRORS = {
    **COMMON_ERROR_RESPONSES,
    **AUTH_ERROR_RESPONSES,
    **IDENTITY_ERROR_RESPONSES,
    404: error_response("历史问答记录不存在", code="HISTORICAL_QA_NOT_FOUND"),
    503: error_response("历史问答暂不可用", code="HISTORICAL_QA_STORE_UNAVAILABLE"),
}


@router.get("", response_model=HistoricalQaPage, summary="历史问答列表", operation_id="historicalQaList", responses=ERRORS)
def historical_qa_list(
    response: Response, pagination: PaginationParams = Depends(), q: str | None = Query(default=None, max_length=80),
    identity: IdentityContext = Depends(get_current_identity),
    repository: HistoricalQaRepository | FixtureHistoricalQaRepository | None = Depends(historical_qa_repository_dependency),
) -> PageResponse[HistoricalQaListItem]:
    response.headers["Cache-Control"] = NO_STORE
    result = list_historical_qa(identity=identity, repository=repository, offset=pagination.offset, limit=pagination.page_size, query=q)
    return PageResponse[HistoricalQaListItem](items=[HistoricalQaListItem.model_validate(item, from_attributes=True) for item in result.items], meta=PaginationMeta.from_total(pagination, result.total))


@router.get("/{qa_id}", response_model=HistoricalQaDetail, summary="历史问答详情", operation_id="historicalQaDetail", responses=ERRORS)
def historical_qa_detail(
    qa_id: UUID, response: Response, identity: IdentityContext = Depends(get_current_identity),
    repository: HistoricalQaRepository | FixtureHistoricalQaRepository | None = Depends(historical_qa_repository_dependency),
) -> HistoricalQaDetail:
    response.headers["Cache-Control"] = NO_STORE
    return HistoricalQaDetail.model_validate(get_historical_qa(identity=identity, repository=repository, qa_id=qa_id), from_attributes=True)
