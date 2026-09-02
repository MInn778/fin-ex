import base64
import sys
from pathlib import Path

from fastapi.testclient import TestClient

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR / "app"))

import main
from schemas import AnalyzeRequest, AnalyzeResponse

client = TestClient(main.app)


def semantic(risk="HIGH"):
    return {"semanticRisk": risk, "impersonationContext": True, "credentialHarvestingContext": True,
            "socialEngineeringContext": True, "financialManipulationContext": False,
            "semanticEvidence": [], "confidence": 0.9}


def test_health_does_not_require_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.get("/health")
    assert response.status_code == 200 and response.json()["gemini_api_key_configured"] is False


def test_empty_collection_returns_unknown_without_calling_gemini(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    body = client.post("/v1/analyze", json={"analysisId": "empty-1", "requestedUrl": "https://blocked.example", "error": "CAPTCHA"}).json()
    assert body["analysisId"] == "empty-1"
    assert body["verdict"] == "UNKNOWN" and body["pageRiskScore"] == 0 and body["confidence"] == 0
    assert "CAPTCHA" in body["reasons"][0]


def test_direct_sandbox_payload_decodes_base64_and_extracts_dom(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    screenshot = (SERVICE_DIR / "fixtures" / "fake_bank" / "test.png").read_bytes()
    captured = {}
    def fake_analyze(input_data):
        captured.update(input_data)
        assert Path(input_data["screenshot_path"]).is_file()
        return semantic()
    monkeypatch.setattr(main, "analyze", fake_analyze)
    response = client.post("/v1/analyze", json={
        "analysisId": "AN-1", "requestedUrl": "https://fake-bank.example",
        "finalUrl": "https://fake-bank.example/login", "statusCode": 200,
        "title": "KB국민은행 로그인", "visibleText": "30분 이내 인증하지 않으면 계좌가 정지됩니다.",
        "html": "<form action='/collect' method='post'><input type='password'><input name='otp'></form>",
        "screenshotBase64": base64.b64encode(screenshot).decode("ascii"),
    })
    body = response.json()
    assert response.status_code == 200 and body["verdict"] == "PHISHING"
    assert body["analysisId"] == "AN-1" and not Path(captured["screenshot_path"]).exists()


def test_flat_and_nested_payloads_are_accepted(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    flat = client.post("/v1/analyze", json={"url": "https://example.com", "html": "<p>분석 가능 문서</p>"})
    assert flat.status_code == 200
    nested = client.post("/v1/analyze", json={"analysisId": "nested", "requestedUrl": "https://example.com",
        "page": {"title": "KB국민은행", "visibleText": "로그인", "html": "<form></form>"},
        "inputs": [{"type": "password"}], "forms": [{"method": "POST", "action": "https://example.com/verify"}],
        "links": [{"text": "상담", "href": "https://example.com/contact"}], "statusCode": 200})
    assert nested.status_code == 200 and nested.json()["analysisId"] == "nested"


def test_nested_collection_metadata_reaches_semantic_layer(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    captured = {}
    monkeypatch.setattr(main, "analyze", lambda data: captured.update(data) or semantic("MEDIUM"))
    payload = {
        "analysisId": "AN-20260902-001", "requestedUrl": "https://example.com",
        "finalUrl": "https://example.com/login", "statusCode": 200,
        "page": {"title": "KB국민은행", "visibleText": "본인인증", "html": "<form></form>"},
        "inputs": [{"type": "password", "name": "sandbox-input"}],
        "forms": [{"method": "POST", "action": "https://example.com/verify"}],
        "links": [{"text": "상담", "href": "https://example.com/contact"}],
        "network": {"requestDomains": ["example.com"], "downloadDetected": False},
        "redirectChain": ["https://example.com", "https://example.com/login"],
        "screenshot": {"available": True, "url": "/api/analyses/AN-20260902-001/screenshot"},
        "collectedAt": "2026-09-02T12:00:00+09:00",
    }
    assert client.post("/v1/analyze", json=payload).status_code == 200
    assert captured["analysis_id"] == payload["analysisId"]
    assert captured["inputs"][0]["name"] == "sandbox-input"
    assert captured["network"] == {"request_domains": ["example.com"], "download_detected": False}
    assert captured["redirect_chain"] == payload["redirectChain"]
    assert captured["screenshot_url"] == payload["screenshot"]["url"]
    assert captured["collected_at"] == payload["collectedAt"]
    assert captured["rule_analysis"]["domainAnalysis"]["domainBrandMismatch"] is True


def test_empty_sandbox_collections_fall_back_to_dom(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    html = '<label for="otp">OTP 인증번호</label><form action="/verify" method="post"><input id="otp" name="otp"></form>'
    body = client.post("/v1/analyze", json={"requestedUrl": "https://example.com", "page": {"html": html}}).json()
    assert "OTP_FIELD" in body["detectedSignals"] and "POST_FORM" in body["detectedSignals"]


def test_invalid_base64_returns_422(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    assert client.post("/v1/analyze", json={"url": "https://example.com", "screenshot_base64": "not-base64!"}).status_code == 422


def test_gemini_error_falls_back_to_rules(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    monkeypatch.setattr(main, "analyze", lambda _: (_ for _ in ()).throw(RuntimeError("down")))
    response = client.post("/v1/analyze", json={"requestedUrl": "https://example.com", "html": "<input type='password'>"})
    assert response.status_code == 200 and response.json()["verdict"] == "NORMAL"


def test_response_model_has_only_canonical_contract_fields():
    assert set(AnalyzeResponse.model_fields) == {"analysisId", "pageRiskScore", "verdict", "impersonation",
        "credentialIntent", "domainAnalysis", "behaviorAnalysis", "detectedSignals", "reasons", "confidence"}


def test_flat_payload_still_parses_with_snake_case_aliases():
    request = AnalyzeRequest.model_validate({"analysis_id": "legacy", "requested_url": "https://example.com", "visible_text": "text", "unknown": True})
    assert request.analysis_id == "legacy" and request.visible_text == "text"
