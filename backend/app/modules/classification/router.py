from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.api.contracts import (
    AUTH_ERROR_RESPONSES,
    COMMON_ERROR_RESPONSES,
    IDENTITY_ERROR_RESPONSES,
    error_response,
)
from app.core.errors import AppError
from app.modules.iam.service import IdentityContext, get_current_identity
from app.modules.intelligence.adapters import DepartmentClassifier
from app.modules.system.router import classifier_dependency

from .schemas import ClassificationRequest, ClassificationResponse
from .service import classify

NO_STORE = "no-store"
router = APIRouter(prefix="/classifications", tags=["classification"])
ERRORS = {
    **COMMON_ERROR_RESPONSES,
    **AUTH_ERROR_RESPONSES,
    **IDENTITY_ERROR_RESPONSES,
    503: error_response("部门分类暂不可用", code="CLASSIFIER_INFERENCE_FAILED"),
}


@router.post(
    "",
    response_model=ClassificationResponse,
    summary="深圳部门分类",
    operation_id="classifyDepartment",
    responses=ERRORS,
)
def create_classification(
    payload: ClassificationRequest,
    response: Response,
    identity: IdentityContext = Depends(get_current_identity),
    classifier: DepartmentClassifier = Depends(classifier_dependency),
) -> ClassificationResponse:
    response.headers["Cache-Control"] = NO_STORE
    try:
        return classify(
            identity=identity,
            classifier=classifier,
            text=payload.text,
            requested_region_id=payload.region_id,
        )
    except AppError as exc:
        exc.headers = {**(exc.headers or {}), "Cache-Control": NO_STORE}
        raise
