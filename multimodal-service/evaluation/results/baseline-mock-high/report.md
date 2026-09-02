# FinDer Page Behavior AI Evaluation

- Run ID: `baseline-mock-high`
- Baseline commit: `2b02dfd171991491e37703edb907cc65cd88cd1d`
- Dataset: `C:\kb_phishing_fixture\fin-ex-pages\multimodal-service\evaluation\datasets\baseline_manifest.jsonl`
- Semantic mode: `mock-high`
- Sample count: 18

## Strict Metrics

| Metric | Value |
|---|---:|
| evaluatedSamples | 17 |
| tp | 9 |
| tn | 8 |
| fp | 0 |
| fn | 0 |
| accuracy | 1.0 |
| precision | 1.0 |
| recall | 1.0 |
| f1 | 1.0 |
| falsePositiveRate | 0.0 |
| falseNegativeRate | 0.0 |
| specificity | 1.0 |
| coverage | 0.9444 |

## Alert Metrics

| Metric | Value |
|---|---:|
| evaluatedSamples | 18 |
| tp | 10 |
| tn | 8 |
| fp | 0 |
| fn | 0 |
| accuracy | 1.0 |
| precision | 1.0 |
| recall | 1.0 |
| f1 | 1.0 |
| falsePositiveRate | 0.0 |
| falseNegativeRate | 0.0 |
| specificity | 1.0 |
| coverage | 1.0 |

## Coverage

| Verdict | Count | Rate |
|---|---:|---:|
| NORMAL | 8 | 0.4444 |
| SUSPICIOUS | 1 | 0.0556 |
| PHISHING | 9 | 0.5 |
| UNKNOWN | 0 | 0.0 |

## Score Distribution

| Label | Count | Min | Max | Mean | Median | P25 | P75 | P90 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BENIGN | 8 | 8 | 21 | 13.125 | 12.5 | 9.0 | 16.25 | 18.2 |
| PHISHING | 10 | 41 | 100 | 80.6 | 84.0 | 73.25 | 95.5 | 100.0 |

## Verdict Distribution

```json
{
  "BENIGN": {
    "NORMAL": {
      "count": 8,
      "rate": 1.0
    },
    "SUSPICIOUS": {
      "count": 0,
      "rate": 0.0
    },
    "PHISHING": {
      "count": 0,
      "rate": 0.0
    },
    "UNKNOWN": {
      "count": 0,
      "rate": 0.0
    }
  },
  "PHISHING": {
    "NORMAL": {
      "count": 0,
      "rate": 0.0
    },
    "SUSPICIOUS": {
      "count": 1,
      "rate": 0.1
    },
    "PHISHING": {
      "count": 9,
      "rate": 0.9
    },
    "UNKNOWN": {
      "count": 0,
      "rate": 0.0
    }
  }
}
```

## Field Metrics

```json
{
  "brandCandidate": {
    "annotated": 18,
    "correct": 18,
    "accuracy": 1.0
  },
  "credentialTypes": {
    "annotated": 18,
    "exactMatchAccuracy": 1.0,
    "microPrecision": 1.0,
    "microRecall": 1.0,
    "microF1": 1.0
  },
  "domainBrandMismatch": {
    "annotated": 18,
    "accuracy": 1.0
  },
  "detectedSignals": {
    "annotated": 1,
    "exactMatchAccuracy": 1.0,
    "subsetAccuracy": 1.0
  }
}
```

## False Positives

- None

## False Negatives

- None

## Review Cases

- `phish-external-form`: PHISHING → SUSPICIOUS (score 41)
