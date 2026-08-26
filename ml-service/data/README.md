# ML Data Card

이 폴더는 1차 URL 위험도 모델 학습과 시연에 필요한 작은 기준 데이터를 보관합니다.

## 커밋하는 데이터

- `financial_brands.csv`: 국내 주요 금융기관 브랜드명, 공식 도메인, 탐지 키워드 레지스트리
- `financial_official_urls.csv`: 정상 금융기관 URL 예시
- `korean_public_cases.csv`: 공개 보도/주의 문구를 바탕으로 만든 피싱 패턴 메모
- `sample_urls.csv`: 서비스 동작 확인용 소형 샘플 데이터

## 커밋하지 않는 데이터

대량 학습 데이터와 원본 공개 데이터는 `data/raw/`, 가공 결과는 `data/processed/`에 둡니다. 이 경로는 저장소에 올리지 않습니다.

이유는 세 가지입니다.

- 피싱 URL 원본은 악성 URL을 포함할 수 있어 public 저장소에 그대로 노출하기 부적절합니다.
- PhishTank, Tranco 등 외부 데이터는 최신성과 재배포 조건을 분리해서 관리해야 합니다.
- 공모전 제출에서는 원본 덤프보다 출처, 수집일, 라벨 기준, train/validation/test 분리 방식이 더 중요합니다.

## 권장 출처

- PhishTank verified online phishing feed: 피싱 URL 후보
- Tranco top list: 정상 도메인 후보
- 금융감독원/금융보안원/KISA/경찰청 공개 보도자료: 국내 금융 피싱 유형 설명과 키워드 보강

## 재현 절차

1. 외부 원본 파일을 `data/raw/`에 저장합니다.
2. `python -m src.prepare_dataset --phishtank data/raw/phishtank.csv.bz2 --tranco data/raw/tranco.csv.zip --output data/processed`를 실행합니다.
3. 생성된 `manifest.json`의 행 수와 SHA-256 값을 보고서에 기록합니다.
4. `python -m src.train --data data/processed/train.csv --eval-data data/processed/validation.csv --output artifacts/url_xgb.joblib`로 학습합니다.
