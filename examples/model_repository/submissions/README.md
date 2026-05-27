# Submissions

Place publishable run packages here.

Recommended layout:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run-shards/
    run-000001.jsonl
  summary.json
  summary.md
  manifest.json
```

Small examples may use `run.jsonl`, but long or repeated measurements should use `run-shards/`.

## One model rule

All submissions in this repository should use the same `model_id` as `model.toml`.

Do not submit results for another model into this repository.

## Result PR rule

A result PR should add only one submission package:

```text
submissions/<submitter_id>/<run_id>/**
```

Do not update global reports or datasets in the same PR.

## Source of truth

Raw result JSONL files are the source of truth.

`summary.json`, `summary.md`, and `reports/` are derived outputs.
