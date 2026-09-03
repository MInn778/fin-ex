# Evaluation manifest contract

## Public archived datasets

Public dataset records must be feature-only and inert. Keep `page.html` empty and retain only
URL metadata plus safely extracted title, visible text, input, form, and link fields. Never copy
raw archives into this directory. `evaluation/raw/`, `evaluation/cache/`, and
`evaluation/downloads/` are ignored as an additional guardrail, but endpoint-protection warnings
must still stop processing immediately.

The offline adapters under `evaluation/adapters/` implement the documented PhishIntention and
Phishpedia per-site directory layout (`info.txt`, `shot.png`, and optional `html.txt`). The label
must be supplied by the caller because the documented site directory does not encode ground truth.
HTML parsing is opt-in for PhishIntention and is disabled by default; screenshots are never copied.
Adapters do not fetch, resolve, or open the URL stored in `info.txt`.

No `real_public_manifest.jsonl` is checked in until a genuinely public, labeled, safely acquired
source provides enough inert metadata. The official large PhishIntention/Phishpedia releases contain
raw HTML/screenshots, so they are unsupported for automatic download or extraction on this Windows
workstation. PhreshPhish was reviewed only at the schema level and must not be bulk-downloaded here.

UTF-8 JSONL 한 줄이 한 sample이다. 필수 top-level field는 `sampleId`(전체 manifest에서 unique), `source`, `split`, `label`, `input`이다. `split`은 `train`, `validation`, `test`, `holdout`; `label`은 `BENIGN`, `PHISHING`이며 향후 `UNKNOWN`, `SKIP`도 허용한다. `input`은 Sandbox `AnalyzeRequest`와 같은 camelCase 계약을 쓴다.

```json
{"sampleId":"benign-001","source":"internal_fixture","split":"test","label":"BENIGN","input":{"analysisId":"eval-benign-001","requestedUrl":"https://www.kbstar.com/","finalUrl":"https://www.kbstar.com/","statusCode":200,"page":{"title":"KB국민은행","visibleText":"KB국민은행 로그인","html":"<main>...</main>"},"inputs":[],"forms":[],"links":[],"network":{"requestDomains":["kbstar.com"],"downloadDetected":false},"redirectChain":[],"screenshot":{"available":false,"url":null},"error":null},"expected":{"brand":"KB국민은행","credentialTypes":[],"domainBrandMismatch":false}}
```

`expected`는 선택 annotation이다. `brand`는 rule analysis의 canonical primary brand candidate와 비교한다. `credentialTypes`는 exact/micro precision/recall/F1을, `domainBrandMismatch`는 accuracy를 계산한다. `detectedSignals`가 있으면 exact 및 expected-subset accuracy도 계산한다.

Baseline sample은 실제 사이트를 복제하거나 접속하지 않은 안전한 합성 metadata다. 공식 기관·일반 login은 의도상 `BENIGN`, 비공식 domain에서 기관 사칭과 credential/social-engineering 또는 금융 행동이 결합된 sample은 `PHISHING`으로 먼저 annotation했다. 단일 신호 sample도 보수적으로 `BENIGN` 또는 명백한 공격 흐름의 일부로 `PHISHING`을 지정했으며, 현재 baseline 출력에 맞춰 label을 역으로 바꾸지 않는다.
