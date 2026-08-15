# ML Service — XGBoost + SHAP

의심 URL을 빠르게 선별하는 1차 분석 서비스입니다. URL 문자열에서 재현 가능한 보안 피처 20개를 추출해 XGBoost로 위험 확률을 계산하고, SHAP으로 판단 근거를 제공합니다. 외부 URL에 직접 접속하지 않으므로 실제 페이지 수집은 sandbox 담당 영역과 분리됩니다.

## 주요 파일

- `src/features.py`: URL 구조·난독화·도메인·금융 키워드 기반 피처 추출
- `src/train.py`: `url,label` CSV 학습, 평가 지표 출력, 모델 저장
- `src/model.py`: 추론 및 상위 SHAP 기여도 생성
- `src/api.py`: Spring Boot가 호출할 `POST /v1/analyze` API
- `tests/`: 피처 스키마와 핵심 보안 신호 회귀 테스트

## 데이터 형식

```csv
url,label
https://www.example.com,0
http://secure-bank-login.xyz/verify,1
```

공개 데이터는 출처, 수집일, 라벨 기준을 별도 데이터 카드에 기록해야 합니다. 동일 도메인이 학습·평가 세트 양쪽에 섞이면 성능이 과대평가될 수 있으므로 최종 실험에서는 도메인 단위 분리를 권장합니다.

## 실행

```bash
python -m venv .venv
pip install -r requirements.txt
python -m src.train --data data/urls.csv --output artifacts/url_xgb.joblib
uvicorn src.api:app --host 0.0.0.0 --port 8001
pytest
```

모델 파일이 없을 때 `/health`는 `model_loaded: false`, 분석 API는 HTTP 503을 반환합니다. 임의의 규칙 점수를 AI 결과로 가장하지 않기 위한 동작입니다.

## 응답 계약

`POST /v1/analyze`는 위험 확률·점수·라벨, 2차 분석 필요 여부, SHAP 판단 근거, 피처와 모델 버전을 반환합니다. 기본 정책은 40% 이상을 2차 Sandbox/Multimodal 분석 대상으로 전달하고, 70% 이상을 1차 고위험으로 표시합니다. 임계값은 검증 데이터의 재현율과 오탐률을 근거로 최종 조정해야 합니다.
