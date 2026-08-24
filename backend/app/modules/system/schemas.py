from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class LiveResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "degraded"]
    service: str
    version: str
    checks: dict[str, Any] = Field(default_factory=dict)


class ModelReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    adapter: str
    model_version: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_state(self) -> "ModelReadinessResponse":
        if self.status == "ready":
            if not self.model_version or self.reason is not None:
                raise ValueError("ready 模型状态必须包含版本且不能包含未就绪原因")
        elif not self.reason:
            raise ValueError("not_ready 模型状态必须包含原因")
        return self


class FeaturesResponse(BaseModel):
    environment: str
    auth_required: bool
    features: dict[str, bool] = Field(default_factory=dict)

