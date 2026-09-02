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

    analysisId: str
    pageRiskScore: int = Field(ge=0, le=100, strict=True)
    verdict: Verdict

    impersonation: "ImpersonationResult"
    credentialIntent: "CredentialIntentResult"
    domainAnalysis: "DomainAnalysisResult"
    behaviorAnalysis: "BehaviorAnalysisResult"
    detectedSignals: list[str]
    reasons: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class ImpersonationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detected: bool = Field(strict=True)
    brand: str | None
    category: str | None


class CredentialIntentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detected: bool = Field(strict=True)
    types: list[str]


class DomainAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    currentDomain: str | None
    officialDomains: list[str]
    domainBrandMismatch: bool = Field(strict=True)


class BehaviorAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    financialActionRequest: bool = Field(strict=True)
    externalContactRequest: bool = Field(strict=True)
    downloadRequest: bool = Field(strict=True)


def unknown_response(reason: str, analysis_id: str | None = None) -> AnalyzeResponse:
    return AnalyzeResponse(
        analysisId=analysis_id or "unknown",
        pageRiskScore=0,
        verdict="UNKNOWN",
        impersonation=ImpersonationResult(detected=False, brand=None, category=None),
        credentialIntent=CredentialIntentResult(detected=False, types=[]),
        domainAnalysis=DomainAnalysisResult(
            currentDomain=None, officialDomains=[], domainBrandMismatch=False
        ),
        behaviorAnalysis=BehaviorAnalysisResult(
            financialActionRequest=False,
            externalContactRequest=False,
            downloadRequest=False,
        ),
        detectedSignals=[],
        reasons=[reason],
        confidence=0.0,
    )
