import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from response_parser import parse_multimodal_response


def valid_response() -> dict:
    return {
        "analysis_id": "ana_001",
        "status": "completed",
        "multimodal_result": {
            "multimodal_risk_score": 12,
            "risk_level": "low_risk",
            "is_financial_impersonation": False,
            "impersonated_brand": None,
            "brand_category": None,
            "attack_type": None,
            "detected_elements": [],
            "reasons": [{"code": "NO_IMPERSONATION", "description": "No impersonation evidence."}],
            "confidence": 0.9,
        },
        "model_name": "test-model",
        "prompt_version": "mm_prompt_v1",
    }


def test_parse_plain_json():
    assert parse_multimodal_response(json.dumps(valid_response()))["analysis_id"] == "ana_001"


def test_parse_fenced_json_with_whitespace():
    payload = "  ```json\n" + json.dumps(valid_response()) + "\n```  "
    assert parse_multimodal_response(payload)["multimodal_result"]["risk_level"] == "low_risk"


def test_invalid_json_has_clear_error():
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_multimodal_response("{not-json}")


def test_missing_required_field_has_clear_error():
    payload = valid_response()
    del payload["multimodal_result"]["confidence"]
    with pytest.raises(ValueError, match="missing required fields.*confidence"):
        parse_multimodal_response(json.dumps(payload))
