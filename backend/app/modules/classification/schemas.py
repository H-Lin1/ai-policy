from __future__ import annotations

from pydantic import Field

from app.api.contracts import ApiModel


class ClassificationRequest(ApiModel):
    text: str = Field(min_length=1, max_length=10000, description="待分类文本")
    region_id: str | None = Field(default=None, max_length=63, description="仅测试用途的显式地区")


class ClassificationPrediction(ApiModel):
    department_id: str
    department_name: str
    confidence: float = Field(ge=0, le=1)


class ClassificationResponse(ApiModel):
    region_id: str
    model_version: str
    predictions: list[ClassificationPrediction] = Field(min_length=1)
