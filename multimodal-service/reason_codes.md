# Reason Codes

`detectedSignals`는 Sandbox DOM/Text에서 deterministic하게 확인된 사실만 포함한다.
`BRAND_IMPERSONATION`은 기존 이름을 유지하지만 실제 의미는 브랜드 후보 탐지이다.
public `impersonation.detected`는 도메인 불일치 또는 Gemini 사칭 문맥이 함께 있어야 true가 된다.

| Signal | 사용자용 reason 의미 |
|---|---|
| BRAND_DOMAIN_MISMATCH | 공식 도메인과 현재 도메인 불일치 |
| PASSWORD_FIELD / OTP_FIELD | 비밀번호 또는 OTP 입력 요구 |
| EXTERNAL_FORM_ACTION | 다른 도메인으로 form 전송 가능성 |
| EXTERNAL_CONTACT | 외부 상담·메신저 이동 유도 |
| DOWNLOAD_REQUEST | 파일·프로그램 다운로드 유도 |
| URGENCY_MESSAGE | 즉시 행동을 요구하는 긴급성 문구 |
| ACCOUNT_SUSPENSION_MESSAGE | 계정·계좌 제한 경고 |
| BENEFIT_LURE | 지원금·환급금·대출 혜택 강조 |
| FINANCIAL_ACTION_REQUEST | 송금·이체·계좌정보 등 금융 행동 요구 |
