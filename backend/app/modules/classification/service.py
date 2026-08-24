from __future__ import annotations

import logging

from app.core.errors import AppError
from app.modules.iam.service import IdentityContext
from app.modules.intelligence.adapters import (
    ClassificationResult,
    ClassifierError,
    ClassifierInput,
    DepartmentClassifier,
    canonical_region_id,
)

from .schemas import ClassificationPrediction, ClassificationResponse

logger = logging.getLogger("ai_policy.classification")


def _ensure_scope(identity: IdentityContext) -> str:
    if identity.development_bypass:
        return "sz"
    if identity.region_code != "sz":
        raise AppError("IDENTITY_SCOPE_INACTIVE", "当前身份不在受支持的深圳范围内", status_code=403)
    return "sz"


def _safe_classifier_error(exc: ClassifierError) -> AppError:
    if exc.code in {"TEXT_REQUIRED", "REGION_REQUIRED", "REGION_INVALID", "CLASSIFIER_INPUT_INVALID"}:
        return AppError(exc.code, exc.message, status_code=422)
    if exc.code == "REGION_NOT_SUPPORTED":
        return AppError("IDENTITY_SCOPE_INACTIVE", "当前身份不在受支持的深圳范围内", status_code=403)
    if exc.code in {"MODEL_NOT_READY", "MODEL_ASSETS_INVALID"}:
        return AppError(exc.code, exc.message, status_code=503)
    if exc.code in {"CLASSIFIER_INFERENCE_FAILED", "CLASSIFIER_CONTRACT_INVALID"}:
        return AppError(exc.code, "部门分类暂不可用", status_code=503)
    return AppError("CLASSIFIER_INFERENCE_FAILED", "部门分类暂不可用", status_code=503)


def classify(
    *,
    identity: IdentityContext,
    classifier: DepartmentClassifier,
    text: str,
    requested_region_id: str | None,
) -> ClassificationResponse:
    region_id = _ensure_scope(identity)
    if requested_region_id is not None:
        try:
            requested_region_id = canonical_region_id(requested_region_id)
        except ClassifierError as exc:
            raise _safe_classifier_error(exc) from exc
        if requested_region_id != region_id:
            raise AppError("REGION_SCOPE_MISMATCH", "请求地区与当前身份范围不一致", status_code=403)
    try:
        result: ClassificationResult = classifier.classify(ClassifierInput(text=text, region_id=region_id))
    except ClassifierError as exc:
        raise _safe_classifier_error(exc) from exc
    except Exception as exc:  # Third-party adapters must not surface implementation details.
        logger.error("classification_execution_failed")
        raise AppError("CLASSIFIER_INFERENCE_FAILED", "部门分类暂不可用", status_code=503) from exc

    department_name = getattr(classifier, "department_name", None)
    if not callable(department_name):
        raise AppError("CLASSIFIER_CONTRACT_INVALID", "部门分类暂不可用", status_code=503)
    return ClassificationResponse(
        region_id=result.region_id,
        model_version=result.model_version,
        predictions=[
            ClassificationPrediction(
                department_id=item.department_id,
                department_name=department_name(item.department_id),
                confidence=item.confidence,
            )
            for item in result.predictions
        ],
    )
