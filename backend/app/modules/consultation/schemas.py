from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field

from app.api.contracts import ApiModel, UtcDateTime


class ConsultationDepartmentResponse(ApiModel):
    department_id: str
    department_name: str


class ConsultationPrediction(ApiModel):
    department_id: str
    department_name: str
    confidence: float = Field(ge=0, le=1)


class CreateConsultationRequest(ApiModel):
    question: str = Field(min_length=1, max_length=4000)
    selected_department_id: str = Field(min_length=1, max_length=96)


class ConsultationResponse(ApiModel):
    id: UUID
    selected_department: ConsultationDepartmentResponse
    status: Literal["assigned", "closed"]
    question_text: str
    recommendations: list[ConsultationPrediction] = Field(min_length=1, max_length=3)
    created_at: UtcDateTime
    assigned_at: UtcDateTime
    answer_text: str | None = None
    publish_to_history: bool = False
    historical_qa_id: UUID | None = None
    replied_at: UtcDateTime | None = None
    closed_at: UtcDateTime | None = None


class ReplyConsultationRequest(ApiModel):
    answer: str = Field(min_length=1, max_length=8000)
    publish_to_history: bool = False
    public_question: str | None = Field(default=None, min_length=1, max_length=4000)
    public_answer: str | None = Field(default=None, min_length=1, max_length=8000)
