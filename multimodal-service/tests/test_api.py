import base64
import sys
from pathlib import Path

from fastapi.testclient import TestClient

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR / "app"))

import main
from schemas import AnalyzeRequest, AnalyzeResponse


client = TestClient(main.app)


def sample_result() -> dict:
    return {
        "verdict": "PHISHING",
        "risk_score": 92,
        "impersonation_type": "FINANCIAL_INSTITUTION",
        "impersonated_brand": "KB국민은행",
        "credential_request": True,
        "financial_action_request": False,
        "app_install_request": False,
        "external_contact_request": False,
        "evidence": ["비공식 도메인에서 계좌 비밀번호 입력을 요구합니다."],
    }


def test_health_does_not_require_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"
    assert response.json()["gemini_api_key_configured"] is False


def test_empty_collection_returns_unknown_without_calling_gemini(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post(
        "/v1/analyze",
        json={"requestedUrl": "https://blocked.example", "error": "CAPTCHA"},
    )
    assert response.status_code == 200
    assert response.json()["verdict"] == "UNKNOWN"
    assert "CAPTCHA" in response.json()["evidence"][0]


def test_direct_sandbox_payload_decodes_base64_and_extracts_dom(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    screenshot = (SERVICE_DIR / "fixtures" / "fake_bank" / "test.png").read_bytes()
    captured = {}

    def fake_analyze(input_data):
        captured.update(input_data)
        assert Path(input_data["screenshot_path"]).is_file()
        return sample_result()

    monkeypatch.setattr(main, "analyze", fake_analyze)
    response = client.post(
        "/v1/analyze",
        json={
            "requestedUrl": "https://fake-bank.example",
            "finalUrl": "https://fake-bank.example/login",
            "statusCode": 200,
            "title": "은행 로그인",
            "html": "<form action='/collect'><input type='password' name='account_password'><button>인증</button></form><a href='/app.apk' download>앱 설치</a>",
            "screenshotBase64": base64.b64encode(screenshot).decode("ascii"),
            "htmlSizeBytes": 200,
            "screenshotSizeBytes": len(screenshot),
            "loadTimeMs": 12,
            "error": None,
        },
    )
    assert response.status_code == 200
    assert response.json() == sample_result()
    assert captured["forms"][0]["inputs"][0]["name"] == "account_password"
    assert captured["dom_signals"]["downloads"][0]["destination"].endswith("/app.apk")
    assert not Path(captured["screenshot_path"]).exists()


def test_existing_snake_case_backend_payload_is_accepted(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    monkeypatch.setattr(main, "analyze", lambda input_data: sample_result())
    response = client.post(
        "/v1/analyze",
        json={
            "url": "https://example.com",
            "final_url": "https://example.com/login",
            "html": "<p>분석 가능 문서</p>",
        },
    )
    assert response.status_code == 200


def test_invalid_base64_returns_422(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    response = client.post(
        "/v1/analyze",
        json={"url": "https://example.com", "screenshot_base64": "not-base64!"},
    )
    assert response.status_code == 422


def test_gemini_error_is_isolated_and_server_stays_healthy(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")

    def fail(_):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(main, "analyze", fail)
    response = client.post(
        "/v1/analyze",
        json={"requestedUrl": "https://example.com", "html": "<p>분석 가능 문서</p>"},
    )
    assert response.status_code == 502
    assert client.get("/health").status_code == 200


def test_response_model_has_only_latest_contract_fields():
    assert set(AnalyzeResponse.model_fields) == set(sample_result())


def test_flat_payload_still_parses_with_snake_case_aliases():
    request = AnalyzeRequest.model_validate({
        "analysis_id": "legacy-analysis",
        "requested_url": "https://example.com",
        "visible_text": "legacy text",
        "screenshot_base64": "YWJj",
        "unknownLegacyField": True,
    })
    assert request.analysis_id == "legacy-analysis"
    assert request.requested_url == "https://example.com"
    assert request.visible_text == "legacy text"


def test_nested_sandbox_payload_is_forwarded_without_losing_collection_data(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    captured = {}
    monkeypatch.setattr(main, "analyze", lambda input_data: captured.update(input_data) or sample_result())
    payload = {
        "analysisId": "AN-20260902-001",
        "requestedUrl": "https://example.com",
        "finalUrl": "https://example.com/login",
        "statusCode": 200,
        "page": {"title": "KB국민은행 보안인증센터", "visibleText": "본인인증을 진행해 주세요.", "html": "<form action='/dom'><input name='dom-input'></form>"},
        "inputs": [{"type": "password", "name": "sandbox-input", "id": "password", "label": "비밀번호"}],
        "forms": [{"method": "POST", "action": "https://example.com/verify"}],
        "links": [{"text": "상담", "href": "https://example.com/contact"}],
        "network": {"requestDomains": ["example.com"], "downloadDetected": False},
        "redirectChain": ["https://example.com", "https://example.com/login"],
        "screenshot": {"available": True, "url": "/api/analyses/AN-20260902-001/screenshot"},
        "collectedAt": "2026-09-02T12:00:00+09:00",
        "error": None,
    }
    response = client.post("/v1/analyze", json=payload)
    assert response.status_code == 200
    assert captured["analysis_id"] == payload["analysisId"]
    assert captured["title"] == payload["page"]["title"]
    assert captured["page_text"] == payload["page"]["visibleText"]
    assert captured["html"] == payload["page"]["html"]
    assert captured["inputs"][0]["name"] == "sandbox-input"
    assert captured["forms"][0]["action"] == "https://example.com/verify"
    assert captured["links"][0]["href"] == "https://example.com/contact"
    assert captured["network"] == {"request_domains": ["example.com"], "download_detected": False}
    assert captured["redirect_chain"] == payload["redirectChain"]
    assert captured["screenshot_url"] == payload["screenshot"]["url"]
    assert captured["screenshot"] == payload["screenshot"]
    assert captured["collected_at"] == payload["collectedAt"]
    assert captured["status_code"] == 200
    assert captured["rule_analysis"]["impersonation"]["brand"] == "KB국민은행"
    assert captured["rule_analysis"]["domainAnalysis"]["domainBrandMismatch"] is True


def test_empty_sandbox_collections_fall_back_to_dom(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    captured = {}
    monkeypatch.setattr(main, "analyze", lambda input_data: captured.update(input_data) or sample_result())
    html = """<label for="otp">OTP 인증번호</label>
        <form action="/verify" method="post"><input id="otp" name="otp"></form>
        <a href="/contact">상담</a>"""
    response = client.post("/v1/analyze", json={
        "requestedUrl": "https://example.com", "page": {"html": html},
        "inputs": [], "forms": [], "links": [],
    })
    assert response.status_code == 200
    assert captured["inputs"][0]["id"] == "otp"
    assert captured["inputs"][0]["label"] == "OTP 인증번호"
    assert captured["forms"][0]["method"] == "POST"
    assert captured["links"][0]["destination"] == "https://example.com/contact"
    assert captured["links"][0]["href"] == "https://example.com/contact"
