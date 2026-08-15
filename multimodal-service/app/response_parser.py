import json


def parse_multimodal_response(response_text: str) -> dict:
    """
    멀티모달 AI가 반환한 JSON 문자열을
    Python dict로 변환한다.
    """

    try:
        result = json.loads(response_text)
        return result

    except json.JSONDecodeError as e:
        raise ValueError(
            f"멀티모달 AI 응답을 JSON으로 변환할 수 없습니다: {e}"
        )


if __name__ == "__main__":

    test_response = """
    {
      "analysis_id": "ana_001",
      "status": "completed",
      "multimodal_result": {
        "multimodal_risk_score": 87,
        "risk_level": "high_risk_suspected",
        "is_financial_impersonation": true,
        "impersonated_brand": "KB국민은행",
        "brand_category": "bank",
        "attack_type": "credential_theft",
        "detected_elements": [
          "bank_logo",
          "login_form",
          "otp_input"
        ],
        "reasons": [
          {
            "code": "BANK_LOGO_DETECTED",
            "description": "금융기관 로고와 유사한 요소가 발견되었습니다."
          },
          {
            "code": "CREDENTIAL_FORM_DETECTED",
            "description": "로그인 또는 금융 인증정보 입력 폼이 발견되었습니다."
          }
        ],
        "confidence": 0.91
      },
      "model_name": "multimodal-provider-name",
      "prompt_version": "mm_prompt_v1"
    }
    """

    parsed = parse_multimodal_response(test_response)

    print(parsed)