"""HTTP input and public output contracts for the multimodal service."""

from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


Verdict = Literal["NORMAL", "SUSPICIOUS", "PHISHING", "UNKNOWN"]
ImpersonationType = Literal[
    "FINANCIAL_INSTITUTION",
    "POLICY_FUND",
    "GOVERNMENT_SUPPORT",
    "GENERIC_CREDENTIAL_THEFT",
    "OTHER",
    "UNKNOWN",
]


class SandboxModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class PageData(SandboxModel):
    title: str = Field(default="", max_length=1000)
    visible_text: str = Field(
        default="", validation_alias=AliasChoices("visibleText", "visible_text")
    )
    html: str = ""


class InputData(SandboxModel):
    type: str | None = None
    name: str | None = None
    id: str | None = None
    placeholder: str | None = None
    label: str | None = None
    autocomplete: str | None = None


class FormData(SandboxModel):
    method: str | None = None
    action: str | None = None
    inputs: list[InputData] = Field(default_factory=list)


class LinkData(SandboxModel):
    text: str = ""
    href: str | None = None
    destination: str | None = None


class NetworkData(SandboxModel):
    request_domains: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("requestDomains", "request_domains"),
    )
    download_detected: bool = Field(
        default=False,
        validation_alias=AliasChoices("downloadDetected", "download_detected"),
    )


class ScreenshotData(SandboxModel):
    available: bool = False
    url: str | None = None


class AnalyzeRequest(SandboxModel):
    """Accept both the Sandbox response and the existing backend adapter payload."""

    analysis_id: str | None = Field(
        default=None, validation_alias=AliasChoices("analysisId", "analysis_id")
    )

    requested_url: str | None = Field(
        default=None,
        max_length=4096,
        validation_alias=AliasChoices(
            "requestedUrl", "requested_url", "url", "original_url"
        ),
    )
    final_url: str | None = Field(
        default=None,
        max_length=4096,
        validation_alias=AliasChoices("finalUrl", "final_url"),
    )
    page: PageData | None = None
    title: str = Field(default="", max_length=1000)
    html: str = ""
    visible_text: str = Field(
        default="",
        validation_alias=AliasChoices("visibleText", "visible_text", "page_text"),
    )
    screenshot_base64: str | None = Field(
        default=None,
        validation_alias=AliasChoices("screenshotBase64", "screenshot_base64"),
    )
    status_code: int | None = Field(
        default=None,
        validation_alias=AliasChoices("statusCode", "status_code"),
    )
    error: str | None = None
    inputs: list[InputData] = Field(default_factory=list)
    forms: list[FormData] = Field(default_factory=list)
    links: list[LinkData] = Field(default_factory=list)
    network: NetworkData | None = None
    redirect_chain: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("redirectChain", "redirect_chain"),
    )
    screenshot: ScreenshotData | None = None
    collected_at: str | None = Field(
        default=None, validation_alias=AliasChoices("collectedAt", "collected_at")
    )


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: Verdict
    risk_score: int = Field(ge=0, le=100, strict=True)
    impersonation_type: ImpersonationType
    impersonated_brand: str | None
    credential_request: bool = Field(strict=True)
    financial_action_request: bool = Field(strict=True)
    app_install_request: bool = Field(strict=True)
    external_contact_request: bool = Field(strict=True)
    evidence: list[str]


def unknown_response(reason: str) -> AnalyzeResponse:
    return AnalyzeResponse(
        verdict="UNKNOWN",
        risk_score=0,
        impersonation_type="UNKNOWN",
        impersonated_brand=None,
        credential_request=False,
        financial_action_request=False,
        app_install_request=False,
        external_contact_request=False,
        evidence=[reason],
    )
