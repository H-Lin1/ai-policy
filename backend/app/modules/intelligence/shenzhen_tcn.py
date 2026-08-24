"""Verified, application-neutral Shenzhen classifier computation.

This module deliberately contains only the model computation reimplemented for the
user-provided checkpoint.  It has no legacy HTTP, global state, search, or UI code.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from transformers import AutoModel, AutoTokenizer

from .adapters import (
    ADAPTER_NAME,
    MODEL_ASSETS_INVALID,
    AdapterReadiness,
    ClassificationResult,
    ClassifierAssetManifest,
    ClassifierError,
    ClassifierInput,
    DepartmentPrediction,
    ValidatedDepartmentClassifier,
)

logger = logging.getLogger("ai_policy.classifier")
MAX_TOKENS = 512
TOP_K = 5


@dataclass(frozen=True, slots=True)
class DepartmentLabel:
    department_id: str
    department_name: str


def _load_labels(path: str) -> tuple[DepartmentLabel, ...]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        labels = payload["labels"]
        if payload.get("schema_version") != "1" or payload.get("region_id") != "sz":
            raise ValueError("unsupported label schema")
        result = tuple(
            DepartmentLabel(
                department_id=item["department_id"],
                department_name=item["department_name"],
            )
            for item in labels
        )
        if not result or len({item.department_id for item in result}) != len(result):
            raise ValueError("invalid label IDs")
        if any(not item.department_name.strip() for item in result):
            raise ValueError("invalid label names")
        return result
    except Exception as exc:  # JSON asset errors are intentionally non-diagnostic.
        raise ClassifierError("MODEL_ASSETS_INVALID", "分类模型资产校验失败") from exc


class _Chomp1d:  # Defined in _build_model after Torch is imported lazily.
    pass


def _build_model(*, tokenizer_path: str, embeddings_path: str, class_count: int):
    """Build the exact checkpoint topology only after static assets pass validation."""

    import torch
    from torch import nn
    from torch.nn import functional

    class Chomp1d(nn.Module):
        def __init__(self, chomp_size: int) -> None:
            super().__init__()
            self.chomp_size = chomp_size

        def forward(self, value):
            return value[:, :, : -self.chomp_size] if self.chomp_size else value

    class TcnLayer(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            padding = 4
            self.conv1 = nn.Conv1d(256, 256, 3, padding=padding, dilation=2)
            self.chomp1 = Chomp1d(padding)
            self.bn1 = nn.BatchNorm1d(256)
            self.conv2 = nn.Conv1d(256, 256, 3, padding=padding, dilation=2)
            self.chomp2 = Chomp1d(padding)
            self.bn2 = nn.BatchNorm1d(256)
            self.res_conv = nn.Conv1d(256, 256, 1)

        def forward(self, value):
            residual = self.res_conv(value)
            value = functional.relu(self.bn1(self.chomp1(self.conv1(value))))
            value = functional.relu(self.bn2(self.chomp2(self.conv2(value))))
            return functional.relu(value + residual)

    class ShenzhenTcn(nn.Module):
        def __init__(self, bert, department_embeddings) -> None:
            super().__init__()
            self.roberta = bert
            self.department_embeddings = department_embeddings
            self.cross_attention2 = nn.MultiheadAttention(embed_dim=768, num_heads=8)
            self.self_attention = nn.MultiheadAttention(embed_dim=768, num_heads=8)
            self.cnn_layers = nn.ModuleList(
                [
                    nn.Conv1d(768, 256, kernel_size, padding=kernel_size // 2)
                    for kernel_size in (3, 4, 5)
                ]
            )
            self.cov_layers = nn.ModuleList(
                [
                    nn.Sequential(
                        nn.Conv1d(768 if index == 0 else 256, 256, 3, padding=1), nn.ReLU()
                    )
                    for index in range(3)
                ]
            )
            self.tcn_layer = TcnLayer()
            self.fc = nn.Linear(1024, class_count)

        def forward(self, input_ids, attention_mask):
            hidden = self.roberta(
                input_ids=input_ids, attention_mask=attention_mask
            ).last_hidden_state
            sentence = hidden[:, 0, :].unsqueeze(1)
            words = hidden[:, 1:, :]
            contexts = []
            for embedding in self.department_embeddings.values():
                value = embedding.to(input_ids.device)
                scores = torch.matmul(sentence, value.unsqueeze(0).transpose(-2, -1)) * (768**-0.5)
                contexts.append(torch.matmul(torch.softmax(scores, dim=-1), value.unsqueeze(0)))
            combined = torch.mean(torch.stack(contexts), dim=0)
            combined = torch.cat((combined, sentence), dim=1)
            word_attention, _ = self.self_attention(
                words.transpose(0, 1), words.transpose(0, 1), words.transpose(0, 1)
            )
            word_attention = word_attention.transpose(0, 1)
            expanded = combined.repeat_interleave(word_attention.size(1) // combined.size(1), dim=1)
            if expanded.size(1) < word_attention.size(1):
                expanded = torch.cat(
                    (
                        expanded,
                        expanded[:, -1:, :].repeat(1, word_attention.size(1) - expanded.size(1), 1),
                    ),
                    dim=1,
                )
            attended, _ = self.cross_attention2(
                expanded.transpose(0, 1),
                word_attention.transpose(0, 1),
                word_attention.transpose(0, 1),
            )
            value = attended.transpose(0, 1).transpose(1, 2)
            length = value.size(2)
            cnn = torch.cat(
                [
                    functional.interpolate(layer(value), size=length, mode="nearest")
                    for layer in self.cnn_layers
                ],
                dim=1,
            )
            value = cnn
            for layer in self.cov_layers:
                value = layer(value)
            fused = torch.cat((cnn, self.tcn_layer(value)), dim=1)
            return self.fc(torch.mean(fused, dim=2))

    embeddings = torch.load(embeddings_path, map_location="cpu", weights_only=True)
    if not isinstance(embeddings, dict) or any(
        not isinstance(name, str) or tuple(value.shape) != (1, 768)
        for name, value in embeddings.items()
    ):
        raise ValueError("invalid embeddings")
    bert = AutoModel.from_pretrained(tokenizer_path, local_files_only=True)
    return ShenzhenTcn(bert, embeddings)


class ShenzhenTcnDepartmentClassifier(ValidatedDepartmentClassifier):
    """CPU-only implementation for the audited Shenzhen TCN checkpoint."""

    def __init__(self, *, supported_regions, assets: ClassifierAssetManifest) -> None:
        super().__init__(supported_regions=supported_regions)
        self._assets = assets
        self._labels = _load_labels(assets.label_bindings_path or "")
        self._labels_by_id = {item.department_id: item.department_name for item in self._labels}
        self._model = None
        self._tokenizer = None

    def readiness(self) -> AdapterReadiness:
        reason = self._assets.readiness_reason()
        if not self.supported_regions or "sz" not in self.supported_regions:
            reason = MODEL_ASSETS_INVALID
        if len(self._labels) != 35:
            reason = MODEL_ASSETS_INVALID
        return AdapterReadiness(
            adapter=ADAPTER_NAME,
            ready=not reason,
            model_version=self._assets.model_version if not reason else None,
            reason=reason or None,
            supported_regions=self.supported_regions,
        )

    def department_name(self, department_id: str) -> str:
        try:
            return self._labels_by_id[department_id]
        except KeyError as exc:
            raise ClassifierError("CLASSIFIER_CONTRACT_INVALID", "分类标签绑定无效") from exc

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return
        try:
            import torch

            model = _build_model(
                tokenizer_path=self._assets.tokenizer_path or "",
                embeddings_path=self._assets.department_embeddings_path or "",
                class_count=len(self._labels),
            )
            state = torch.load(self._assets.model_path, map_location="cpu", weights_only=True)
            model.load_state_dict(state, strict=True)
            model.eval()
            tokenizer = AutoTokenizer.from_pretrained(
                self._assets.tokenizer_path, local_files_only=True, use_fast=True
            )
            self._model = model
            self._tokenizer = tokenizer
        except Exception as exc:  # Never emit load paths or package details.
            logger.error("classifier_model_load_failed")
            raise ClassifierError("CLASSIFIER_INFERENCE_FAILED", "部门分类模型暂不可用") from exc

    def _classify(self, request: ClassifierInput) -> ClassificationResult:
        self._ensure_loaded()
        try:
            import torch

            encoded = self._tokenizer(
                request.text,
                max_length=MAX_TOKENS,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            )
            with torch.inference_mode():
                probabilities = torch.softmax(
                    self._model(encoded["input_ids"], encoded["attention_mask"]), dim=1
                )[0]
            values, indices = torch.topk(probabilities, min(TOP_K, len(self._labels)))
            predictions = tuple(
                DepartmentPrediction(
                    department_id=self._labels[index.item()].department_id, confidence=value.item()
                )
                for value, index in zip(values, indices, strict=True)
            )
            return ClassificationResult(
                region_id="sz", predictions=predictions, model_version=self._assets.model_version
            )
        except ClassifierError:
            raise
        except Exception as exc:
            logger.error("classifier_inference_failed")
            raise ClassifierError("CLASSIFIER_INFERENCE_FAILED", "部门分类暂不可用") from exc
