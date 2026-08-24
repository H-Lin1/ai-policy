from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Literal, Protocol


class PolicyAnswerError(Exception):
    """Stable failure raised by policy-answer engines."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def normalize_question(value: object) -> str:
    if not isinstance(value, str):
        raise PolicyAnswerError("QUESTION_REQUIRED", "请输入需要咨询的问题")
    normalized = " ".join(unicodedata.normalize("NFKC", value).split())
    if not normalized:
        raise PolicyAnswerError("QUESTION_REQUIRED", "请输入需要咨询的问题")
    return normalized


@dataclass(frozen=True, slots=True)
class PolicyQuestion:
    question: str
    region_id: str
    role_codes: tuple[str, ...]

    def normalized(self) -> PolicyQuestion:
        if self.region_id != "sz":
            raise PolicyAnswerError("REGION_NOT_SUPPORTED", "当前问答仅支持深圳范围")
        return PolicyQuestion(
            question=normalize_question(self.question),
            region_id="sz",
            role_codes=tuple(self.role_codes),
        )


@dataclass(frozen=True, slots=True)
class PolicyAnswerSource:
    source_type: Literal["policy_document", "historical_qa"]
    source_id: str
    title: str
    source_url: str
    published_date: str | None = None
    excerpt: str | None = None


@dataclass(frozen=True, slots=True)
class PolicyAnswerResult:
    region_id: Literal["sz"]
    answer_mode: Literal["placeholder", "rag"]
    answer: str
    sources: tuple[PolicyAnswerSource, ...]
    notices: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.answer.strip():
            raise PolicyAnswerError("POLICY_ANSWER_CONTRACT_INVALID", "问答结果格式无效")
        if len(self.sources) > 5:
            raise PolicyAnswerError("POLICY_ANSWER_CONTRACT_INVALID", "问答结果来源数量无效")
        if self.answer_mode == "placeholder" and self.sources:
            raise PolicyAnswerError("POLICY_ANSWER_CONTRACT_INVALID", "占位回答不能包含来源")


class PolicyAnswerEngine(Protocol):
    def answer(self, question: PolicyQuestion) -> PolicyAnswerResult: ...


class PlaceholderPolicyAnswerEngine:
    """Temporary, explicit UX flow only; it never claims to retrieve policies."""

    def answer(self, question: PolicyQuestion) -> PolicyAnswerResult:
        question.normalized()
        return PolicyAnswerResult(
            region_id="sz",
            answer_mode="placeholder",
            answer=(
                "已收到你的政策咨询。当前页面正在演示完整的问答流程，"
                "真实的深圳政策检索、依据核验与智能生成能力尚未接入。"
            ),
            sources=(),
            notices=(
                "当前为演示回答，不构成政策依据、办理意见或正式答复。",
                "真实检索能力接入后，系统将展示可回溯的官方来源。",
            ),
        )


def build_policy_answer_engine() -> PolicyAnswerEngine:
    """The placeholder is an intentional configured mode, never a failure fallback."""

    return PlaceholderPolicyAnswerEngine()
