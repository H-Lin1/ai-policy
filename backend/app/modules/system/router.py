import logging

from fastapi import APIRouter, Depends, Response

from app.api.contracts import (
    AUTH_ERROR_RESPONSES,
    IDENTITY_ERROR_RESPONSES,
    NOT_READY_ERROR_RESPONSES,
)
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.modules.iam.schemas import MeResponse
from app.modules.iam.service import IdentityContext, get_current_identity, role_summaries
from app.modules.intelligence.adapters import (
    ADAPTER_NAME,
    CONFIGURATION_INVALID,
    READINESS_CHECK_FAILED,
    SAFE_READINESS_REASONS,
    DepartmentClassifier,
    UnavailableDepartmentClassifier,
    build_department_classifier,
    is_safe_metadata,
    validate_readiness_status,
)

from .schemas import (
    FeaturesResponse,
    LiveResponse,
    ModelReadinessResponse,
    ReadinessResponse,
)
from .service import features_payload, live_payload, readiness_payload

# A cached readiness result can report a dependency healthy after it has failed.
NO_STORE = "no-store"


def _is_fully_ready(checks: dict[str, object]) -> bool:
    return checks.get("database") == "ok" and checks.get("authentication") in {
        "configured",
        "development_bypass",
    }

router = APIRouter(tags=["system"])
logger = logging.getLogger("ai_policy.system")


def classifier_dependency(settings: Settings = Depends(get_settings)) -> DepartmentClassifier:
    """Create a classifier from app settings without mutable module state."""

    try:
        return build_department_classifier(settings)
    except Exception:  # noqa: BLE001 - dependency probes must fail closed.
        # A malformed runtime setting must fail closed without exposing its value.
        logger.error("classifier_factory_not_ready")
        return UnavailableDepartmentClassifier(
            supported_regions=(),
            forced_reason=CONFIGURATION_INVALID,
        )


@router.get(
    "/health/live",
    response_model=LiveResponse,
    summary="进程存活检查",
    operation_id="healthLive",
)
def health_live(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> LiveResponse:
    response.headers["Cache-Control"] = NO_STORE
    # Deliberately no database, JWKS, or model access: this only answers
    # whether the process and routing layer are running.
    return LiveResponse.model_validate(live_payload(settings))


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="依赖就绪检查",
    operation_id="healthReady",
    responses=NOT_READY_ERROR_RESPONSES,
)
def health_ready(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    response.headers["Cache-Control"] = NO_STORE
    ready, checks = readiness_payload(settings)
    if not ready:
        raise AppError(
            "SERVICE_NOT_READY",
            "服务依赖尚未就绪",
            status_code=503,
            details=checks,
            headers={"Cache-Control": NO_STORE},
        )
    return ReadinessResponse(
        status="ready" if _is_fully_ready(checks) else "degraded",
        service=settings.app_name,
        version=settings.app_version,
        checks=checks,
    )


@router.get(
    "/health",
    response_model=ReadinessResponse,
    summary="浏览器健康检查",
    operation_id="healthOverview",
)
def health(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    response.headers["Cache-Control"] = NO_STORE
    ready, checks = readiness_payload(settings)
    if not ready:
        return ReadinessResponse(
            status="degraded",
            service=settings.app_name,
            version=settings.app_version,
            checks=checks,
        )
    return ReadinessResponse(
        status="ready" if _is_fully_ready(checks) else "degraded",
        service=settings.app_name,
        version=settings.app_version,
        checks=checks,
    )


@router.get(
    "/system/features",
    response_model=FeaturesResponse,
    summary="功能开关快照",
    operation_id="systemFeatures",
)
def system_features(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> FeaturesResponse:
    response.headers["Cache-Control"] = NO_STORE
    return FeaturesResponse.model_validate(features_payload(settings))


@router.get(
    "/ai/readiness",
    response_model=ModelReadinessResponse,
    summary="模型适配器就绪检查",
    operation_id="aiReadiness",
)
def model_readiness(
    response: Response,
    classifier: DepartmentClassifier = Depends(classifier_dependency),
) -> ModelReadinessResponse:
    response.headers["Cache-Control"] = NO_STORE
    try:
        status = validate_readiness_status(classifier.readiness())
        if not is_safe_metadata(status.adapter):
            raise ValueError("unsafe adapter identifier")
        if status.ready:
            if not is_safe_metadata(status.model_version):
                raise ValueError("unsafe model version")
            return ModelReadinessResponse(
                status="ready",
                adapter=status.adapter,
                model_version=status.model_version,
            )
        if status.reason not in SAFE_READINESS_REASONS:
            raise ValueError("unsafe readiness reason")
        return ModelReadinessResponse(
            status="not_ready",
            adapter=status.adapter,
            model_version=status.model_version,
            reason=status.reason,
        )
    except Exception:  # noqa: BLE001 - third-party adapters must not break the probe.
        # Readiness is fail closed; never expose an implementation traceback.
        logger.error("classifier_readiness_failed")
        return ModelReadinessResponse(
            status="not_ready",
            adapter=ADAPTER_NAME,
            reason=READINESS_CHECK_FAILED,
        )


@router.get(
    "/me",
    response_model=MeResponse,
    summary="当前登录主体",
    operation_id="currentPrincipal",
    responses={**AUTH_ERROR_RESPONSES, **IDENTITY_ERROR_RESPONSES},
)
def me(
    response: Response,
    identity: IdentityContext = Depends(get_current_identity),
) -> MeResponse:
    response.headers["Cache-Control"] = NO_STORE
    return MeResponse(
        subject=identity.subject,
        email=identity.email,
        display_name=identity.display_name,
        roles=list(identity.role_codes),
        role_summaries=role_summaries(identity),
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
        development_bypass=identity.development_bypass,
    )
