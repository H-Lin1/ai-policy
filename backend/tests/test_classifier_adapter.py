from __future__ import annotations

import math
from pathlib import Path

import pytest

from app.core.config import Settings
from app.modules.intelligence.adapters import (
    ADAPTER_NOT_VERIFIED,
    MODEL_ASSETS_INVALID,
    MODEL_NOT_CONFIGURED,
    AdapterReadiness,
    ClassificationResult,
    ClassifierAssetManifest,
    ClassifierError,
    ClassifierInput,
    DepartmentPrediction,
    UnavailableDepartmentClassifier,
    ValidatedDepartmentClassifier,
    build_department_classifier,
    validate_classification_result,
    validate_readiness_status,
    validate_result_for_request,
)


class RecordingClassifier(ValidatedDepartmentClassifier):
    def __init__(
        self,
        *,
        result_region: str = "sz",
        result_version: str = "test-v1",
    ) -> None:
        super().__init__(supported_regions=("sz",))
        self.result_region = result_region
        self.result_version = result_version
        self.received: ClassifierInput | None = None

    def readiness(self) -> AdapterReadiness:
        return AdapterReadiness(
            adapter="recording-classifier",
            ready=True,
            model_version="test-v1",
            supported_regions=self.supported_regions,
        )

    def _classify(self, request: ClassifierInput) -> ClassificationResult:
        self.received = request
        return ClassificationResult(
            region_id=self.result_region,
            predictions=(
                DepartmentPrediction(department_id="dept-b", confidence=0.4),
                DepartmentPrediction(department_id="dept-a", confidence=0.9),
            ),
            model_version=self.result_version,
        )


class MalformedStatusClassifier(ValidatedDepartmentClassifier):
    def __init__(self) -> None:
        super().__init__(supported_regions=("sz",))

    def readiness(self) -> AdapterReadiness:
        return None  # type: ignore[return-value]

    def _classify(self, request: ClassifierInput) -> ClassificationResult:
        raise AssertionError("invalid readiness must stop inference")


class ForgedStatusClassifier(ValidatedDepartmentClassifier):
    def __init__(self) -> None:
        super().__init__(supported_regions=("sz",))

    def readiness(self) -> AdapterReadiness:
        status = object.__new__(AdapterReadiness)
        object.__setattr__(status, "adapter", "recording-classifier")
        object.__setattr__(status, "ready", "false")
        object.__setattr__(status, "model_version", "test-v1")
        object.__setattr__(status, "reason", None)
        object.__setattr__(status, "supported_regions", ("sz",))
        return status

    def _classify(self, request: ClassifierInput) -> ClassificationResult:
        raise AssertionError("forged readiness must stop inference")


class ForgedResultClassifier(ValidatedDepartmentClassifier):
    def __init__(self) -> None:
        super().__init__(supported_regions=("sz",))

    def readiness(self) -> AdapterReadiness:
        return AdapterReadiness(
            adapter="recording-classifier",
            ready=True,
            model_version="test-v1",
            supported_regions=("sz",),
        )

    def _classify(self, request: ClassifierInput) -> ClassificationResult:
        result = object.__new__(ClassificationResult)
        object.__setattr__(result, "region_id", "sz")
        object.__setattr__(result, "predictions", ())
        object.__setattr__(result, "model_version", "test-v1")
        return result


class ForgedPredictionClassifier(ValidatedDepartmentClassifier):
    def __init__(self) -> None:
        super().__init__(supported_regions=("sz",))

    def readiness(self) -> AdapterReadiness:
        return AdapterReadiness(
            adapter="recording-classifier",
            ready=True,
            model_version="test-v1",
            supported_regions=("sz",),
        )

    def _classify(self, request: ClassifierInput) -> ClassificationResult:
        prediction = object.__new__(DepartmentPrediction)
        object.__setattr__(prediction, "department_id", "  ")
        object.__setattr__(prediction, "confidence", math.nan)
        result = object.__new__(ClassificationResult)
        object.__setattr__(result, "region_id", "sz")
        object.__setattr__(result, "predictions", (prediction,))
        object.__setattr__(result, "model_version", "test-v1")
        return result


def test_unavailable_classifier_reports_not_ready() -> None:
    adapter = UnavailableDepartmentClassifier()

    readiness = adapter.readiness()

    assert readiness.ready is False
    assert readiness.reason == MODEL_NOT_CONFIGURED
    assert readiness.supported_regions == ("sz",)


def test_unavailable_classifier_does_not_return_mock_result() -> None:
    adapter = UnavailableDepartmentClassifier()

    with pytest.raises(ClassifierError) as error:
        adapter.classify(ClassifierInput(text="政策咨询", region_id="sz"))

    assert error.value.code == "MODEL_NOT_READY"


def test_classifier_input_normalizes_unicode_whitespace_and_region() -> None:
    normalized = ClassifierInput(
        text=" \u3000Ａ  政策\n咨询 ",
        region_id=" SZ ",
    ).normalized()

    assert normalized == ClassifierInput(text="A 政策 咨询", region_id="sz")


@pytest.mark.parametrize(
    ("classifier_request", "expected_code"),
    [
        (ClassifierInput(text=" \n ", region_id="sz"), "TEXT_REQUIRED"),
        (ClassifierInput(text="政策咨询", region_id=" \t"), "REGION_REQUIRED"),
        (ClassifierInput(text="政策咨询", region_id="shenzhen city"), "REGION_INVALID"),
        (ClassifierInput(text="政策咨询", region_id="深圳"), "REGION_INVALID"),
    ],
)
def test_classifier_rejects_invalid_input(
    classifier_request: ClassifierInput,
    expected_code: str,
) -> None:
    adapter = UnavailableDepartmentClassifier()

    with pytest.raises(ClassifierError) as error:
        adapter.classify(classifier_request)

    assert error.value.code == expected_code


def test_unsupported_region_is_rejected_before_model_readiness() -> None:
    adapter = UnavailableDepartmentClassifier(supported_regions=("sz",))

    with pytest.raises(ClassifierError) as error:
        adapter.classify(ClassifierInput(text="政策咨询", region_id="beijing"))

    assert error.value.code == "REGION_NOT_SUPPORTED"
    assert error.value.details == {"region_id": "beijing"}


def test_empty_region_registry_is_not_ready_and_rejects_every_region() -> None:
    adapter = UnavailableDepartmentClassifier(supported_regions=())

    assert adapter.readiness().reason == "no_supported_regions_configured"
    with pytest.raises(ClassifierError) as error:
        adapter.classify(ClassifierInput(text="政策咨询", region_id="sz"))
    assert error.value.code == "REGION_NOT_SUPPORTED"


def test_verified_template_normalizes_input_and_orders_predictions() -> None:
    adapter = RecordingClassifier()

    result = adapter.classify(ClassifierInput(text="  政策\n 咨询 ", region_id="SZ"))

    assert adapter.received == ClassifierInput(text="政策 咨询", region_id="sz")
    assert result.region_id == "sz"
    assert [item.department_id for item in result.predictions] == ["dept-a", "dept-b"]
    assert result.model_version == "test-v1"


def test_validated_template_rejects_malformed_readiness() -> None:
    with pytest.raises(ClassifierError) as error:
        MalformedStatusClassifier().classify(ClassifierInput(text="政策", region_id="sz"))

    assert error.value.code == "CLASSIFIER_CONTRACT_INVALID"


def test_readiness_rebuild_rejects_forged_non_boolean_state() -> None:
    status = object.__new__(AdapterReadiness)
    object.__setattr__(status, "adapter", "recording-classifier")
    object.__setattr__(status, "ready", "false")
    object.__setattr__(status, "model_version", "test-v1")
    object.__setattr__(status, "reason", None)
    object.__setattr__(status, "supported_regions", ("sz",))

    with pytest.raises(ClassifierError) as error:
        validate_readiness_status(status)
    assert error.value.code == "CLASSIFIER_CONTRACT_INVALID"

    with pytest.raises(ClassifierError) as template_error:
        ForgedStatusClassifier().classify(ClassifierInput(text="政策", region_id="sz"))
    assert template_error.value.code == "CLASSIFIER_CONTRACT_INVALID"


@pytest.mark.parametrize(
    "confidence",
    [-0.01, 1.01, math.nan, math.inf, -math.inf, True, "0.5", "not-a-number"],
)
def test_prediction_rejects_invalid_confidence(confidence: object) -> None:
    with pytest.raises(ClassifierError) as error:
        DepartmentPrediction(department_id="dept-a", confidence=confidence)  # type: ignore[arg-type]

    assert error.value.code == "CLASSIFIER_CONTRACT_INVALID"


@pytest.mark.parametrize("department_id", ["", "  ", "dept one", None])
def test_prediction_rejects_invalid_department_id(department_id: object) -> None:
    with pytest.raises(ClassifierError) as error:
        DepartmentPrediction(department_id=department_id, confidence=0.5)  # type: ignore[arg-type]

    assert error.value.code == "CLASSIFIER_CONTRACT_INVALID"


def test_result_rejects_empty_or_duplicate_predictions_and_blank_version() -> None:
    prediction = DepartmentPrediction(department_id="dept-a", confidence=0.5)

    invalid_values = [
        {"predictions": (), "model_version": "v1"},
        {"predictions": (prediction, prediction), "model_version": "v1"},
        {"predictions": (prediction,), "model_version": "  "},
    ]
    for values in invalid_values:
        with pytest.raises(ClassifierError) as error:
            ClassificationResult(region_id="sz", **values)  # type: ignore[arg-type]
        assert error.value.code == "CLASSIFIER_CONTRACT_INVALID"


@pytest.mark.parametrize(
    ("region_id", "model_version"),
    [
        ("", "v1"),
        ("bad region", "v1"),
        ("sz", "/private/model/version"),
    ],
)
def test_result_wraps_invalid_region_and_metadata_as_contract_failure(
    region_id: str,
    model_version: str,
) -> None:
    prediction = DepartmentPrediction(department_id="dept-a", confidence=0.5)

    with pytest.raises(ClassifierError) as error:
        ClassificationResult(
            region_id=region_id,
            predictions=(prediction,),
            model_version=model_version,
        )

    assert error.value.code == "CLASSIFIER_CONTRACT_INVALID"


def test_result_must_match_request_region_and_readiness_version() -> None:
    result = ClassificationResult(
        region_id="beijing",
        predictions=(DepartmentPrediction(department_id="dept-a", confidence=0.5),),
        model_version="test-v1",
    )

    with pytest.raises(ClassifierError) as mismatch:
        validate_result_for_request(ClassifierInput(text="政策", region_id="sz"), result)
    assert mismatch.value.code == "CLASSIFIER_CONTRACT_INVALID"

    with pytest.raises(ClassifierError) as version_mismatch:
        RecordingClassifier(result_version="other-v1").classify(
            ClassifierInput(text="政策", region_id="sz")
        )
    assert version_mismatch.value.code == "CLASSIFIER_CONTRACT_INVALID"


def test_result_rebuild_rejects_forged_empty_predictions() -> None:
    result = object.__new__(ClassificationResult)
    object.__setattr__(result, "region_id", "sz")
    object.__setattr__(result, "predictions", ())
    object.__setattr__(result, "model_version", "test-v1")

    with pytest.raises(ClassifierError) as error:
        validate_classification_result(result)
    assert error.value.code == "CLASSIFIER_CONTRACT_INVALID"

    with pytest.raises(ClassifierError) as template_error:
        ForgedResultClassifier().classify(ClassifierInput(text="政策", region_id="sz"))
    assert template_error.value.code == "CLASSIFIER_CONTRACT_INVALID"


def test_result_rebuild_rejects_forged_nested_prediction() -> None:
    prediction = object.__new__(DepartmentPrediction)
    object.__setattr__(prediction, "department_id", "  ")
    object.__setattr__(prediction, "confidence", math.nan)
    result = object.__new__(ClassificationResult)
    object.__setattr__(result, "region_id", "sz")
    object.__setattr__(result, "predictions", (prediction,))
    object.__setattr__(result, "model_version", "test-v1")

    with pytest.raises(ClassifierError) as error:
        validate_classification_result(result)
    assert error.value.code == "CLASSIFIER_CONTRACT_INVALID"

    with pytest.raises(ClassifierError) as template_error:
        ForgedPredictionClassifier().classify(ClassifierInput(text="政策", region_id="sz"))
    assert template_error.value.code == "CLASSIFIER_CONTRACT_INVALID"


def test_asset_manifest_distinguishes_absent_partial_invalid_and_valid(
    tmp_path: Path,
) -> None:
    assert ClassifierAssetManifest().readiness_reason() == MODEL_NOT_CONFIGURED
    assert (
        ClassifierAssetManifest(model_path="model.bin").readiness_reason()
        == MODEL_ASSETS_INVALID
    )
    assert (
        ClassifierAssetManifest(
            model_path=str(tmp_path / "missing-model"),
            tokenizer_path=str(tmp_path / "missing-tokenizer"),
            label_bindings_path=str(tmp_path / "missing-labels"),
            department_embeddings_path=str(tmp_path / "missing-embeddings"),
        ).readiness_reason()
        == MODEL_ASSETS_INVALID
    )

    model_path = tmp_path / "model.bin"
    tokenizer_path = tmp_path / "tokenizer"
    labels_path = tmp_path / "labels.json"
    embeddings_path = tmp_path / "embeddings.bin"
    for path in (model_path, labels_path, embeddings_path):
        path.write_text("test-only", encoding="utf-8")
    tokenizer_path.mkdir()
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "vocab.txt"):
        (tokenizer_path / name).write_text("test-only", encoding="utf-8")
    manifest = ClassifierAssetManifest(
        model_path=str(model_path),
        tokenizer_path=str(tokenizer_path),
        label_bindings_path=str(labels_path),
        department_embeddings_path=str(embeddings_path),
    )

    assert manifest.readiness_reason() == ""
    adapter = UnavailableDepartmentClassifier(assets=manifest)
    assert adapter.readiness().reason == ADAPTER_NOT_VERIFIED
    with pytest.raises(ClassifierError) as error:
        adapter.classify(ClassifierInput(text="政策咨询", region_id="sz"))
    assert error.value.code == "MODEL_NOT_READY"


def test_asset_manifest_rejects_directory_and_unreadable_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    regular_files = [tmp_path / name for name in ("model.bin", "embeddings.bin")]
    for path in regular_files:
        path.write_text("test-only", encoding="utf-8")
    labels_directory = tmp_path / "labels"
    labels_directory.mkdir()
    directory_manifest = ClassifierAssetManifest(
        model_path=str(regular_files[0]),
        tokenizer_path=str(regular_files[1]),
        label_bindings_path=str(labels_directory),
        department_embeddings_path=str(regular_files[1]),
    )
    assert directory_manifest.readiness_reason() == MODEL_ASSETS_INVALID

    labels_file = tmp_path / "labels.json"
    labels_file.write_text("test-only", encoding="utf-8")
    unreadable_manifest = ClassifierAssetManifest(
        model_path=str(regular_files[0]),
        tokenizer_path=str(regular_files[1]),
        label_bindings_path=str(labels_file),
        department_embeddings_path=str(regular_files[1]),
    )
    monkeypatch.setattr(
        "app.modules.intelligence.adapters.os.access",
        lambda path, mode: path != str(labels_file),
    )
    assert unreadable_manifest.readiness_reason() == MODEL_ASSETS_INVALID


def test_settings_parse_regions_and_factory_uses_assets(tmp_path: Path) -> None:
    paths = [tmp_path / name for name in ("model.bin", "labels.json", "embeddings.bin")]
    for path in paths:
        path.write_text("test-only", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        classifier_supported_regions=" SZ,sz,shenzhen,bad region ",
        classifier_model_path=str(paths[0]),
        classifier_tokenizer_path=str(tmp_path / "missing-tokenizer"),
        classifier_label_bindings_path=str(paths[1]),
        classifier_department_embeddings_path=str(paths[2]),
    )

    classifier = build_department_classifier(settings)
    readiness = classifier.readiness()

    assert settings.classifier_supported_region_ids == ("sz", "shenzhen")
    assert readiness.supported_regions == ("sz", "shenzhen")
    assert readiness.reason == MODEL_ASSETS_INVALID


def test_settings_region_registry_uses_nfkc_and_asset_status_ignores_whitespace() -> None:
    settings = Settings(
        _env_file=None,
        classifier_supported_regions=" ＳＺ,Shenzhen ",
        classifier_model_path=" ",
        classifier_tokenizer_path="\t",
        classifier_label_bindings_path="\n",
    )

    assert settings.classifier_supported_region_ids == ("sz", "shenzhen")
    assert settings.classifier_configured is False


@pytest.mark.parametrize(
    "readiness",
    [
        {"ready": True, "model_version": None, "reason": None},
        {"ready": True, "model_version": "v1", "reason": "unexpected"},
        {"ready": False, "model_version": None, "reason": None},
        {"ready": "false", "model_version": "v1", "reason": None},
        {
            "ready": False,
            "model_version": None,
            "reason": "/private/unsafe/reason",
        },
        {"ready": True, "model_version": "/private/model", "reason": None},
        {
            "ready": True,
            "model_version": "v1",
            "reason": None,
            "supported_regions": (),
        },
        {"ready": False, "model_version": "/private/model", "reason": MODEL_ASSETS_INVALID},
        {"ready": False, "model_version": 123, "reason": MODEL_ASSETS_INVALID},
    ],
)
def test_readiness_rejects_inconsistent_state(readiness: dict[str, object]) -> None:
    with pytest.raises(ClassifierError) as error:
        AdapterReadiness(adapter="classifier", **readiness)  # type: ignore[arg-type]

    assert error.value.code == "CLASSIFIER_CONTRACT_INVALID"


def test_intelligence_adapter_has_no_legacy_framework_or_route_imports() -> None:
    source = (Path(__file__).parents[1] / "app/modules/intelligence/adapters.py").read_text(
        encoding="utf-8"
    )

    assert "from flask" not in source.lower()
    assert "app0723" not in source.lower()
    assert '"/classify"' not in source
