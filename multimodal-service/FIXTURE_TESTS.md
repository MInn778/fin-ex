# Multimodal fixture 테스트

`run_fixture_tests.py`는 fixture 폴더의 `input.json`을 읽어 기존
`app/analyzer.py`의 `analyze()` 함수를 호출하고, 반환된 JSON 전체를
`results/<fixture 이름>.json`으로 저장한다. Gemini API 키는 기존과 동일하게
`GEMINI_API_KEY` 환경변수에서만 읽는다.

## 테스트 이미지 준비

실제 피싱 사이트에 접속하거나 그 화면을 수집하지 않는다. 아래 설명에 따라
로컬에서 합성한 1280x720 PNG 이미지를 각 경로의 `test.png`로 준비한다.
이미지의 화면 문구는 해당 폴더의 `input.json`과 일치해야 한다.

- `fixtures/card_capital/test.png`: KB캐피탈을 표시한 대환대출 신청 화면.
  "긴급 저금리 대환대출", "오늘 마감", "본인인증 후 즉시 승인" 문구와
  이름, 휴대전화번호, 주민등록번호, 계좌번호 입력란 및 "대출 신청" 버튼이
  보이도록 한다.
- `fixtures/internet_bank/test.png`: 카카오뱅크를 표시한 이상거래 본인인증
  화면. "이상거래 감지", "계좌 보호" 문구와 휴대전화번호, 계좌 비밀번호,
  인증번호 입력란 및 "인증 완료" 버튼이 보이도록 한다.
- `fixtures/government_support/test.png`: 정부24를 표시한 소상공인 정책자금
  신청 화면. "추가 지급 대상", "환급금 300만원", "오늘 신청 마감" 문구와
  성명, 주민등록번호, 휴대전화번호, 은행명, 계좌번호, 계좌 비밀번호 입력란 및
  "지원금 신청" 버튼이 보이도록 한다.
- `fixtures/non_financial/test.png`: 가상의 게임 "별빛용사" 여름 출석 이벤트
  화면. 금융기관, 정부기관, 대출, 지원금 문구 없이 게임 캐릭터, 한정판 의상
  안내, 게임 ID와 게임 비밀번호 입력란 및 "게임 로그인" 버튼만 보이도록 한다.

상표 표시는 오직 폐쇄된 테스트 환경의 합성 이미지에만 사용하며, 모든 URL은
외부 피싱 사이트가 아닌 `.example` 예약 도메인을 사용한다.

## 실행

PowerShell에서 프로젝트 루트를 현재 경로로 두고 실행한다.

```powershell
$env:GEMINI_API_KEY = "발급받은_API_키"
python .\run_fixture_tests.py
```

특정 fixture만 실행할 수도 있다.

```powershell
python .\run_fixture_tests.py card_capital
python .\run_fixture_tests.py internet_bank government_support non_financial
```

이미지가 없거나 분석 결과에 필수 필드가 없으면 해당 fixture는 실패로 표시되고
다음 fixture를 계속 실행한다. 성공한 결과만 `results/` 아래에 저장한다.
