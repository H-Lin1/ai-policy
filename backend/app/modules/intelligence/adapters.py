from __future__ import annotations

import math
import os
import re
import unicodedata
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from numbers import Real
from pathlib import Path
from typing import Protocol

from app.core.config import Settings, get_settings

ADAPTER_NAME = "department-classifier"
MODEL_NOT_CONFIGURED = "verified_model_not_configured"
MODEL_ASSETS_INVALID = "model_assets_invalid"
ADAPTER_NOT_VERIFIED = "verified_adapter_not_implemented"
NO_REGIONS_CONFIGURED = "no_supported_regions_configured"
CONFIGURATION_INVALID = "classifier_configuration_invalid"
READINESS_CHECK_FAILED = "readiness_check_failed"
MODEL_LOAD_FAILED = "model_load_failed"

SAFE_READINESS_REASONS = frozenset(
    {
        MODEL_NOT_CONFIGURED,
        MODEL_ASSETS_INVALID,
        ADAPTER_NOT_VERIFIED,
        NO_REGIONS_CONFIGURED,
        CONFIGURATION_INVALID,
        READINESS_CHECK_FAILED,
        MODEL_LOAD_FAILED,
    }
)

_REGION_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$")
_SAFE_METADATA_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}$")


class ClassifierError(Exception):
    """Stable domain failure raised below the HTTP/application boundary."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: object | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


# Keep a descriptive alias for callers that want to make the adapter boundary explicit.
ClassifierAdapterError = ClassifierError


def is_safe_metadata(value: object) -> bool:
    return isinstance(value, str) and bool(_SAFE_METADATA_PATTERN.fullmatch(value))


def normalize_classifier_text(value: object) -> str:
    if not isinstance(value, str):
        raise ClassifierError("TEXT_REQUIRED", "分类文本不能为空")
    normalized = " ".join(unicodedata.normalize("NFKC", value).split())
    if not normalized:
        raise ClassifierError("TEXT_REQUIRED", "分类文本不能为空")
    return normalized


def canonical_region_id(value: object) -> str:
    if not isinstance(value, str):
        raise ClassifierError("REGION_REQUIRED", "必须提供地区标识")
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    if not normalized:
        raise ClassifierError("REGION_REQUIRED", "必须提供地区标识")
    if not _REGION_PATTERN.fullmatch(normalized):
        raise ClassifierError("REGION_INVALID", "地区标识格式无效")
    return normalized


def _stable_department_id(value: object) -> str:
    if not isinstance(value, str):
        raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "部门标识格式无效")
    normalized = unicodedata.normalize("NFKC", value).strip()
    if not normalized or any(char.isspace() for char in normalized):
        raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "部门标识格式无效")
    return normalized


@dataclass(frozen=True, slots=True)
class ClassifierInput:
    text: str
    region_id: str

    def normalized(self) -> ClassifierInput:
        return ClassifierInput(
            text=normalize_classifier_text(self.text),
            region_id=canonical_region_id(self.region_id),
        )


@dataclass(frozen=True, slots=True)
class DepartmentPrediction:
    department_id: str
    confidence: float

    def __post_init__(self) -> None:
        department_id = _stable_department_id(self.department_id)
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (Real, Decimal)):
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "置信度格式无效")
        try:
            confidence = float(self.confidence)
        except (TypeError, ValueError) as exc:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "置信度格式无效") from exc
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "置信度必须在 0 到 1 之间")
        object.__setattr__(self, "department_id", department_id)
        object.__setattr__(self, "confidence", confidence)


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    region_id: str
    predictions: tuple[DepartmentPrediction, ...]
    model_version: str

    def __post_init__(self) -> None:
        try:
            region_id = canonical_region_id(self.region_id)
        except ClassifierError as exc:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类结果地区格式无效") from exc
        try:
            predictions = (
                self.predictions if isinstance(self.predictions, tuple) else tuple(self.predictions)
            )
        except TypeError as exc:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类结果格式无效") from exc
        if not predictions:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类结果至少包含一个部门")
        source_predictions = predictions
        try:
            predictions = tuple(
                DepartmentPrediction(
                    department_id=item.department_id,
                    confidence=item.confidence,
                )
                for item in source_predictions
                if isinstance(item, DepartmentPrediction)
            )
        except Exception as exc:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类结果格式无效") from exc
        if len(predictions) != len(source_predictions):
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类结果格式无效")
        department_ids = [item.department_id for item in predictions]
        if len(set(department_ids)) != len(department_ids):
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类结果包含重复部门")
        if not isinstance(self.model_version, str) or not self.model_version.strip():
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "模型版本不能为空")
        if not is_safe_metadata(self.model_version.strip()):
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "模型版本格式无效")
        ordered = tuple(
            sorted(predictions, key=lambda item: (-item.confidence, item.department_id))
        )
        object.__setattr__(self, "region_id", region_id)
        object.__setattr__(self, "predictions", ordered)
        object.__setattr__(self, "model_version", self.model_version.strip())


def validate_classification_result(result: object) -> ClassificationResult:
    """Rebuild an inference result so injected implementations cannot bypass invariants."""

    if not isinstance(result, ClassificationResult):
        raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类结果格式无效")
    try:
        return ClassificationResult(
            region_id=result.region_id,
            predictions=result.predictions,
            model_version=result.model_version,
        )
    except Exception as exc:
        raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类结果格式无效") from exc


def validate_result_for_request(
    request: ClassifierInput,
    result: object,
) -> ClassificationResult:
    """Ensure a future implementation cannot return a cross-region result."""

    normalized_request = request.normalized()
    validated_result = validate_classification_result(result)
    if validated_result.region_id != normalized_request.region_id:
        raise ClassifierError(
            "CLASSIFIER_CONTRACT_INVALID",
            "分类结果地区与请求不一致",
        )
    return validated_result


@dataclass(frozen=True, slots=True)
class AdapterReadiness:
    adapter: str
    ready: bool
    model_version: str | None = None
    reason: str | None = None
    supported_regions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.ready) is not bool:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "就绪状态格式无效")
        if not is_safe_metadata(
            self.adapter.strip() if isinstance(self.adapter, str) else self.adapter
        ):
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "适配器标识不能为空")
        if self.model_version is not None and (
            not isinstance(self.model_version, str)
            or not is_safe_metadata(self.model_version.strip())
        ):
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "模型版本格式无效")
        if self.ready:
            if (
                self.reason is not None
                or not isinstance(self.model_version, str)
                or not self.model_version.strip()
                or not is_safe_metadata(self.model_version.strip())
            ):
                raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "就绪状态元数据无效")
        elif not isinstance(self.reason, str) or self.reason not in SAFE_READINESS_REASONS:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "未就绪状态必须包含原因")
        try:
            regions: list[str] = []
            supported_regions = (
                (self.supported_regions,)
                if isinstance(self.supported_regions, str)
                else self.supported_regions
            )
            for region in supported_regions:
                canonical = canonical_region_id(region)
                if canonical not in regions:
                    regions.append(canonical)
        except (ClassifierError, TypeError) as exc:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "支持地区配置格式无效") from exc
        if self.ready and not regions:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "就绪适配器必须配置支持地区")
        object.__setattr__(self, "adapter", self.adapter.strip())
        object.__setattr__(
            self, "model_version", self.model_version.strip() if self.model_version else None
        )
        object.__setattr__(self, "reason", self.reason if self.reason else None)
        object.__setattr__(self, "supported_regions", tuple(regions))


def validate_readiness_status(status: object) -> AdapterReadiness:
    """Rebuild a readiness value so injected implementations cannot bypass invariants."""

    if not isinstance(status, AdapterReadiness):
        raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "就绪状态格式无效")
    try:
        return AdapterReadiness(
            adapter=status.adapter,
            ready=status.ready,
            model_version=status.model_version,
            reason=status.reason,
            supported_regions=status.supported_regions,
        )
    except Exception as exc:
        raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "就绪状态格式无效") from exc


@dataclass(frozen=True, slots=True)
class ClassifierAssetManifest:
    model_path: str | None = None
    tokenizer_path: str | None = None
    label_bindings_path: str | None = None
    department_embeddings_path: str | None = None
    model_version: str = "sz-tcn-bert-v1"

    def __post_init__(self) -> None:
        for field_name in (
            "model_path",
            "tokenizer_path",
            "label_bindings_path",
            "department_embeddings_path",
        ):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "模型资产配置格式无效")
            normalized = value.strip() if isinstance(value, str) else None
            object.__setattr__(self, field_name, normalized or None)
        if not isinstance(self.model_version, str) or not is_safe_metadata(
            self.model_version.strip()
        ):
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "模型版本配置格式无效")
        object.__setattr__(self, "model_version", self.model_version.strip())

    @classmethod
    def from_settings(cls, settings: Settings) -> ClassifierAssetManifest:
        return cls(
            model_path=settings.classifier_model_path,
            tokenizer_path=settings.classifier_tokenizer_path,
            label_bindings_path=settings.classifier_label_bindings_path,
            department_embeddings_path=settings.classifier_department_embeddings_path,
            model_version=settings.classifier_model_version,
        )

    def readiness_reason(self) -> str:
        values = (
            self.model_path,
            self.tokenizer_path,
            self.label_bindings_path,
            self.department_embeddings_path,
        )
        if not any(values):
            return MODEL_NOT_CONFIGURED
        if not all(values):
            return MODEL_ASSETS_INVALID
        try:
            model_valid = Path(self.model_path).is_file() and os.access(self.model_path, os.R_OK)
            labels_valid = Path(self.label_bindings_path).is_file() and os.access(
                self.label_bindings_path, os.R_OK
            )
            embeddings_valid = Path(self.department_embeddings_path).is_file() and os.access(
                self.department_embeddings_path, os.R_OK
            )
            tokenizer = Path(self.tokenizer_path)
            tokenizer_valid = (
                tokenizer.is_dir()
                and os.access(tokenizer, os.R_OK)
                and all(
                    (tokenizer / name).is_file() and os.access(tokenizer / name, os.R_OK)
                    for name in (
                        "config.json",
                        "tokenizer.json",
                        "tokenizer_config.json",
                        "vocab.txt",
                    )
                )
            )
            valid_files = model_valid and labels_valid and embeddings_valid and tokenizer_valid
        except (OSError, ValueError):
            valid_files = False
        return "" if valid_files else MODEL_ASSETS_INVALID


def _canonical_supported_regions(regions: Iterable[str]) -> tuple[str, ...]:
    if isinstance(regions, str):
        regions = (regions,)
    result: list[str] = []
    for region in regions:
        canonical = canonical_region_id(region)
        if canonical not in result:
            result.append(canonical)
    return tuple(result)


class DepartmentClassifier(Protocol):
    @property
    def supported_regions(self) -> tuple[str, ...]: ...

    def readiness(self) -> AdapterReadiness: ...

    def classify(self, request: ClassifierInput) -> ClassificationResult: ...


class ValidatedDepartmentClassifier(ABC):
    """Template that enforces the contract around a concrete computation."""

    def __init__(self, *, supported_regions: Iterable[str]) -> None:
        self._supported_regions = _canonical_supported_regions(supported_regions)

    @property
    def supported_regions(self) -> tuple[str, ...]:
        return self._supported_regions

    @abstractmethod
    def readiness(self) -> AdapterReadiness:
        """Return a safe snapshot without raising for expected not-ready states."""

    @abstractmethod
    def _classify(self, request: ClassifierInput) -> ClassificationResult:
        """Run only the concrete inference computation on normalized input."""

    def classify(self, request: ClassifierInput) -> ClassificationResult:
        if not isinstance(request, ClassifierInput):
            raise ClassifierError("CLASSIFIER_INPUT_INVALID", "分类请求格式无效")
        normalized = request.normalized()
        if normalized.region_id not in self._supported_regions:
            raise ClassifierError(
                "REGION_NOT_SUPPORTED",
                "当前适配器不支持该地区",
                details={"region_id": normalized.region_id},
            )
        status = validate_readiness_status(self.readiness())
        if not status.ready:
            raise ClassifierError(
                "MODEL_NOT_READY",
                "部门分类模型尚未完成验证和配置",
            )
        result = validate_result_for_request(normalized, self._classify(normalized))
        if result.model_version != status.model_version:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "模型版本与就绪状态不一致")
        return result


class UnavailableDepartmentClassifier(ValidatedDepartmentClassifier):
    """Default adapter until a verified computation is explicitly wired."""

    def __init__(
        self,
        *,
        supported_regions: Iterable[str] = ("sz",),
        assets: ClassifierAssetManifest | None = None,
        forced_reason: str | None = None,
    ) -> None:
        super().__init__(supported_regions=supported_regions)
        self._assets = assets or ClassifierAssetManifest()
        self._forced_reason = forced_reason.strip() if forced_reason else None

    def readiness(self) -> AdapterReadiness:
        if self._forced_reason:
            reason = self._forced_reason
        elif not self._supported_regions:
            reason = NO_REGIONS_CONFIGURED
        else:
            assets_reason = self._assets.readiness_reason()
            reason = assets_reason or ADAPTER_NOT_VERIFIED
        return AdapterReadiness(
            adapter=ADAPTER_NAME,
            ready=False,
            reason=reason,
            supported_regions=self._supported_regions,
        )

    def _classify(self, request: ClassifierInput) -> ClassificationResult:
        raise ClassifierError(
            "MODEL_NOT_READY",
            "部门分类模型尚未完成验证和配置",
        )


def build_department_classifier(settings: Settings) -> DepartmentClassifier:
    assets = ClassifierAssetManifest.from_settings(settings)
    if assets.readiness_reason():
        return UnavailableDepartmentClassifier(
            supported_regions=settings.classifier_supported_region_ids,
            assets=assets,
        )
    from .shenzhen_tcn import ShenzhenTcnDepartmentClassifier

    return ShenzhenTcnDepartmentClassifier(
        supported_regions=settings.classifier_supported_region_ids,
        assets=assets,
    )


def get_department_classifier(settings: Settings | None = None) -> DepartmentClassifier:
    """Build an adapter from explicit settings without mutable module state."""

    return build_department_classifier(settings or get_settings())
