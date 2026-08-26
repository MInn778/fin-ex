"""FastAPI boundary for the backend orchestrator.

Sandbox 결과(base64 스크린샷 + HTML)를 받아 analyzer.analyze()가 기대하는
입력 형태(screenshot_path가 있는 dict)로 변환한 뒤 Gemini 분석을 호출한다.
GEMINI_API_KEY가 없으면 503을 반환한다 - 가짜 결과를 만들어 AI 판정인 척하지 않는다.
"""

import base64
import binascii
import tempfile
import uuid
from pathlib import Path

from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException

from analyzer import analyze
from config import Settings
from schemas import AnalyzeRequest

app = FastAPI(title="fin-der Multimodal Service", version="1.0.0")


def extract_page_text(html: str) -> str:
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


@app.get("/health")
def health() -> dict[str, object]:
    current_settings = Settings.from_env()
    return {"status": "ok", "gemini_api_key_configured": current_settings.gemini_api_key is not None}


@app.post("/v1/analyze")
def analyze_endpoint(request: AnalyzeRequest) -> dict[str, object]:
    current_settings = Settings.from_env()
    if current_settings.gemini_api_key is None:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY가 설정되어 있지 않습니다. 실제 Gemini 분석 없이는 결과를 만들지 않습니다.",
        )

    try:
        screenshot_bytes = base64.b64decode(request.screenshot_base64, validate=True)
    except (binascii.Error, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"screenshot_base64 디코딩 실패: {error}") from error

    if len(screenshot_bytes) > current_settings.max_screenshot_bytes:
        raise HTTPException(status_code=413, detail="Decoded screenshot exceeds the configured size limit")

    tmp_path = Path(tempfile.gettempdir()) / f"multimodal-{uuid.uuid4().hex}.png"
    try:
        tmp_path.write_bytes(screenshot_bytes)

        input_data = {
            "analysis_id": uuid.uuid4().hex,
            "original_url": request.url,
            "final_url": request.final_url or request.url,
            "screenshot_path": str(tmp_path),
            "page_text": extract_page_text(request.html),
            "html": request.html,
            "forms": request.forms,
        }

        try:
            return analyze(input_data)
        except ValueError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=502, detail=f"멀티모달 분석 실패: {error}") from error
    finally:
        tmp_path.unlink(missing_ok=True)
