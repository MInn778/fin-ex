"""Pydantic request and response contracts shared by the API and parser."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1, max_length=4096)
    final_url: str | None = Field(default=None, max_length=4096)
    screenshot_base64: str = Field(min_length=1)
    html: str = ""
    forms: list[dict] = Field(default_factory=list)


class Reason(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    description: str = Field(min_length=1)


class MultimodalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    multimodal_risk_score: int = Field(ge=0, le=100)
    risk_level: str = Field(min_length=1)
    is_financial_impersonation: bool
    impersonated_brand: str | None
    brand_category: str | None
    attack_type: str | None
    detected_elements: list[str]
    reasons: list[Reason]
    confidence: float = Field(ge=0, le=1)


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    multimodal_result: MultimodalResult
    model_name: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
