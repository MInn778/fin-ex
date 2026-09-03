# Isolated feature export procedure

This exporter is for a disposable, isolated Linux research environment that contains an archived
dataset. Do not run it against raw phishing archives on the FinDer Windows workstation. Docker and
WSL alone must not be described or treated as complete malware isolation.

The exporter statically parses local HTML. It does not render a page, execute JavaScript, load an
iframe or resource, resolve DNS, fetch a URL, launch a browser, or start a subprocess. The raw input
JSONL and archived dataset remain inside the disposable environment.

## Local source contract

Each UTF-8 JSONL row has these fields:

- `sourceRecordId` or `sha256`: required stable source identifier.
- `url` or `requestedUrl`: required URL annotation. It is handled as text only.
- `label`: required; the CLI label arguments define the exact source-to-FinDer mapping.
- `html`: required local archived HTML string.
- `finalUrl`, `statusCode`, `title`, `targetBrand`: optional and retained only when annotated by the
  source. They are never inferred.

Use only harmless `.invalid` domains in repository tests. Never copy a raw source row or HTML
fixture from a phishing dataset into this repository.

## Procedure

1. Prepare a disposable isolated Linux VM suitable for handling research malware artifacts.
2. Acquire the public archived dataset inside that environment. Do not visit its live URLs.
3. Normalize the source into the local JSONL contract without rendering HTML or fetching resources.
4. Run the static exporter with an explicit dataset revision, split, label mapping, and timestamp:

```text
python -m evaluation.exporters.static_feature_exporter \
  --input /isolated/raw/source-records.jsonl \
  --output /isolated/out/feature-rich-inert.jsonl \
  --source phreshphish \
  --dataset-name KevinRoshan8/phreshphish \
  --dataset-revision <immutable-revision> \
  --source-split test \
  --extraction-timestamp 2026-09-03T00:00:00Z \
  --benign-label benign \
  --phishing-label phish
```

5. Run the output validator and tests inside the isolated environment. Any rejected row remains out
   of the output manifest; do not weaken the validator.
6. Verify that every `page.html` is empty and that no executable pattern or binary data is present.
7. Preserve dataset name/revision, source split/record ID, extraction version/timestamp, and feature
   availability in each output record.
8. Transfer only the validated feature-only JSONL to `evaluation/local-data/` on the FinDer PC.
9. The raw archive, normalized raw JSONL, and disposable environment may then be destroyed according
   to the research environment's handling policy.
10. On the FinDer PC, run safety tests before the offline rule-only evaluation. Never open a stored
    URL.

Example FinDer-side commands:

```text
python -m pytest -q tests/test_dataset_adapters.py tests/test_static_feature_exporter.py
python evaluation/run_evaluation.py --manifest evaluation/local-data/feature-rich-inert.jsonl --semantic-mode rule-only --run-id real-public-feature-rich-rule-only
```
