# FinDer Page Behavior AI Evaluation

이 디렉터리는 commit `2b02dfd`의 판정 로직을 `baseline-v1`로 고정하고, 동일 입력을 반복 측정하기 위한 오프라인 평가 도구다. Production의 `analyze_dom_risk`와 `fuse_analysis`, `AnalyzeRequest`/`AnalyzeResponse`를 직접 재사용하며 scoring을 다시 구현하지 않는다.

## 실행

PowerShell과 Linux/macOS 모두 `multimodal-service`에서 실행한다.

```text
python evaluation/run_evaluation.py --manifest evaluation/datasets/baseline_manifest.jsonl --semantic-mode rule-only
python evaluation/run_evaluation.py --manifest evaluation/datasets/baseline_manifest.jsonl --semantic-mode mock-high --split test --run-id mock-high-test
```

`--semantic-mode`는 `rule-only`(기본값), `mock-low`, `mock-medium`, `mock-high`를 지원한다. mock은 고정 risk/confidence를 사용하며 Gemini provider를 호출하지 않는다. `--output-dir`, `--run-id`, `--split train|validation|test|holdout`, `--limit`도 지원한다.

## 평가 정책

- Strict: `PHISHING`만 positive, `NORMAL`은 negative다. `SUSPICIOUS`와 `UNKNOWN`은 abstain이며 confusion matrix와 binary precision/recall에서 제외하되 coverage에는 포함한다.
- Alert: `SUSPICIOUS`와 `PHISHING`은 positive, `NORMAL`은 negative다. `UNKNOWN`만 abstain이다.
- Classification metric에는 manifest label `BENIGN`/`PHISHING`만 포함한다. `UNKNOWN`/`SKIP` label은 향후 호환용이며 현재 실행에서는 제외한다.
- 모든 나눗셈은 분모가 0이면 `0.0`이고, 비율은 소수점 넷째 자리까지 기록한다.

runner는 manifest에 저장된 HTML, text, input, form, link, network metadata만 읽는다. URL은 domain 분석용 문자열일 뿐이며 `requests`, `urllib`, Playwright, 브라우저 등으로 접속하지 않는다. 실제 피싱 URL이나 외부 dataset도 내려받지 않는다.

각 실행은 `evaluation/results/<run-id>/`에 `predictions.jsonl`, `errors.jsonl`, `review_cases.jsonl`, `summary.json`, `report.md`를 만든다. screenshot binary나 원문 HTML은 결과에 복사하지 않는다.

Threshold tuning은 `train`/`validation`에서만 수행해야 하며 `test`와 `holdout`은 최종 검증 전까지 tuning에 사용하지 않는다. 이 단계는 tuning을 수행하지 않는다.

자세한 manifest 계약과 synthetic label 원칙은 [datasets/README.md](datasets/README.md)를 참고한다.
