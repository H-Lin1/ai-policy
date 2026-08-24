from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.api.contracts import ApiModel


class PolicyAnswerRequest(ApiModel):
    question: str = Field(min_length=1, max_length=4000, description="政策咨询问题")


class PolicyAnswerSourceResponse(ApiModel):
    source_type: Literal["policy_document", "historical_qa"]
    source_id: str
    title: str
    source_url: str
    published_date: str | None = None
    excerpt: str | None = Field(default=None, max_length=800)


class PolicyAnswerResponse(ApiModel):
    request_id: str
    region_id: Literal["sz"]
    answer_mode: Literal["placeholder", "rag"]
    answer: str
    sources: list[PolicyAnswerSourceResponse] = Field(max_length=5)
    notices: list[str] = Field(default_factory=list, max_length=5)
