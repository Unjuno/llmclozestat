# llmclozestat

`llmclozestat` is a CLI project for cloze-based statistical profiling of LLM outputs.

It asks language models to complete fill-in-the-blank items and output the completed full sentence. The tool records raw outputs, extracts filled spans, classifies each fill, and aggregates statistics such as content pass rate, format compliance, strict pass rate, parse failure rate, fill distribution, repeated wrong fills, and latency.

This is not an official leaderboard. The goal is to observe model behavior statistically.

## 日本語概要

`llmclozestat` は、LLMに穴埋め問題を解かせ、穴埋め後の全文を出力させることで、補完語・形式遵守・誤補完の分布を記録するCLIプロジェクトです。

4択問題ではありません。A/B/C/D の選択肢を集計するのではなく、モデルが実際に補った文字列を抽出し、その分布を見ます。

## Implementation status

This repository is still in the v0.0 design and smoke-test phase.

Currently implemented CLI commands:

- `version`
- `validate items` minimal item JSONL validation
- `validate environment` minimal environment JSON validation
- `validate results` minimal result JSONL consistency validation
- `aggregate` minimal result JSONL to summary JSON aggregation
- `validate summary` minimal summary JSON validation
- `prepare-submission` minimal source validation, artifact copy, and manifest writing
- `validate manifest` minimal manifest JSON validation with optional file/package hash verification
- `validate submission` minimal local submission package integrity and semantic identity validation
- `verify-integrity` minimal local submission package integrity and semantic identity verification

Currently implemented library core:

- strict-v0 parser/scorer pure function core
- result-record assembly helper
- environment JSON validation helper
- summary aggregation helper
- summary JSON validation core
- manifest JSON validation helper
- file SHA-256 and canonical package hash verification helper
- prepare-submission package helper with source artifact validation
- submission semantic identity checker for `environment.json`, `run.jsonl`, and `summary.json`

Still design targets:

- `run`
- `validate model`
- `validate model-repo`
- `report`
- `collect`

Use the current documentation as the implementation specification, not as a claim that the full CLI already works.

For a detailed implemented/specified/undefined breakdown, see `docs/status_matrix.md`.

## Operating model

`llmclozestat` is intended to be a normal local CLI tool.

The expected workflow is:

```text
git clone
  -> install CLI locally
  -> choose a dataset
  -> run against a local or OpenAI-compatible model endpoint
  -> append raw JSONL records under results/
  -> aggregate summaries
  -> prepare a publishable submission package
  -> write manifest.json for package-level tamper detection
  -> inspect reports
  -> repeat
  -> commit or open a PR when enough results are collected
```

Local scratch outputs should go under `results/`, which is ignored by Git. Shareable result packages should be prepared under `submissions/<submitter_id>/<run_id>/` and committed or submitted by pull request.

For scalable result collection, the preferred long-term data layout is:

```text
one model repository = one model identity
one collect command = one model = one run = one submission
one result PR = one submission package
```

See `docs/operating_model.md` for model-repository, fixed-condition, PR, CI, report, and storage policies.

Model-specific data repositories should use `model.toml`; see `docs/model_repository.md`, `docs/model_repository_usage.md`, and `schemas/model.schema.json`.

Submitter and run identifiers should follow `docs/submitter_identity.md` so repeated runs from the same user and different machines do not collide.

## Current repository focus

The repository currently contains:

- item/result/environment/summary/manifest/model schemas;
- one-item `smoke_v0` dataset;
- parser/scorer and result-format specifications;
- fill-class policy;
- fixture policy and parser/result/summary aggregation fixtures;
- minimal `validate items`, `validate environment`, and `validate results` commands;
- minimal `aggregate` command;
- minimal `validate summary` command;
- minimal `prepare-submission` command with source artifact validation;
- minimal `validate manifest` command;
- minimal `validate submission` command with manifest, hash, path, and semantic identity checks;
- minimal `verify-integrity` command;
- strict-v0 parser/scorer core;
- result-record assembly helper;
- summary aggregation helper;
- summary validation helper;
- package-level integrity design, manifest generation, and minimal verification core.

The first dataset, `smoke_v0`, is intentionally small. It is for validating the pipeline and collecting local probe statistics, not for broad model evaluation.

## Core idea

```text
cloze item
  -> completed sentence output
  -> fill extraction
  -> blank-level scoring
  -> fill distribution
  -> model behavior profile
```

Repeated fills are counted. If a model gives the same wrong or known-wrong fill at the same blank multiple times, those repetitions are treated as evidence of a systematic tendency, not as duplicates to remove.

## Required result metadata

Result records must preserve the experimental conditions needed for later re-aggregation.

Important fields include:

- `prompt_template_id`
- `prompt_language`
- `support_mode`
- `f_shot`
- `blank_rendering`
- `extraction_mode`
- `generation_config` or `generation_config_hash`

These fields prevent prompt changes, blank rendering changes, fallback extraction, or generation parameter differences from being mistaken for model behavior differences.

## Integrity boundary

`manifest.json` is for package-level tamper detection of publishable submissions. It can detect later changes to submitted files. It does not verify model execution.

`manifest.json` is required for publishable submissions under `submissions/<submitter_id>/<run_id>/`. Local scratch results under `results/` may omit it, but they should be treated as unverified.

Current minimal commands:

```bash
llmclozestat validate environment --input results/smoke/environment.json
llmclozestat validate results --input results/smoke/run.jsonl
llmclozestat aggregate --input results/smoke/run.jsonl --out results/smoke/summary.json
llmclozestat validate summary --input results/smoke/summary.json

llmclozestat prepare-submission \
  --submitter-id local-user \
  --run-id smoke-v0-local-run \
  --environment-json results/smoke/environment.json \
  --run-jsonl results/smoke/run.jsonl \
  --summary-json results/smoke/summary.json \
  --summary-md results/smoke/summary.md \
  --out-dir submissions/local-user/smoke-v0-local-run

llmclozestat validate manifest --input submissions/local-user/smoke-v0-local-run/manifest.json --verify-files
llmclozestat validate submission --path submissions/local-user/smoke-v0-local-run
llmclozestat verify-integrity --path submissions/local-user/smoke-v0-local-run
```

`prepare-submission` validates the source `environment.json`, `run.jsonl`, and `summary.json` before copying them by default. Use `--no-validate-sources` only for scratch/debug packaging, not for publishable submissions.

`validate submission` and `verify-integrity` require `environment.json`, `run.jsonl`, and `summary.json` to be listed in `manifest.json`, verify their file hashes, and check that `submitter_id`, `run_id`, `dataset_id`, and `model_id` agree across the three artifacts.

## What this is not

- Not a four-choice benchmark.
- Not an official leaderboard.
- Not a verifier for model execution.
- Not an LLM-judge scoring framework.
- Not a web dashboard.

## Initial dataset

See:

- `datasets/smoke_v0/items.jsonl`
- `datasets/smoke_v0/README.md`

The first item is a mirror-perspective probe. It tests whether a model can distinguish actual body-part correspondence from the common surface rule that mirrors “reverse left and right.”

## Reference example package

See:

- `examples/smoke_v0/README.md`
- `examples/smoke_v0/environment.json`
- `examples/smoke_v0/run.jsonl`
- `examples/smoke_v0/summary.json`
- `examples/smoke_v0/summary.md`
- `examples/smoke_v0/manifest.json`

This example is schema-compliant and intended as a fixture for implementing validation, parser/scorer output, aggregation, and manifest verification.

It is not a real benchmark result.

## Model repository example skeleton

See:

- `examples/model_repository/README.md`
- `examples/model_repository/model.toml`
- `examples/model_repository/DATA_LICENSE.md`
- `examples/model_repository/datasets/pinned/README.md`
- `examples/model_repository/datasets/pinned/.gitkeep`
- `examples/model_repository/submissions/README.md`
- `examples/model_repository/submissions/.gitkeep`
- `examples/model_repository/reports/README.md`
- `examples/model_repository/reports/.gitkeep`

This skeleton can be copied into a separate model-specific data repository.

It is not a real measured model repository.

## Result accumulation

The repository may collect community or personal run results through ordinary Git commits or pull requests.

Recommended publishable layout:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
  manifest.json
```

This is self-reported measurement data. For large or repeated result collection, prefer a separate model repository and keep this core repository focused on the CLI, schemas, documentation, smoke data, and small examples.

## Documentation

- `docs/research_plan.md` — research and evaluation plan
- `docs/research_rationale.md` — research value and diagnostic comparison rationale
- `docs/conceptual_model.md` — conceptual model and scoring design
- `docs/design.md` — project design and scope
- `docs/status_matrix.md` — implemented/specified/undefined status matrix
- `docs/current_status_notes.md` — temporary implementation-boundary notes pending status-matrix synchronization
- `docs/summary_scope.md` — single-run summary policy and future aggregate-report separation
- `docs/operating_model.md` — model-repository, fixed-condition, PR, CI, report, and storage policies
- `docs/model_repository.md` — model.toml metadata and one-model repository rules
- `docs/model_repository_usage.md` — practical model repository setup and changing-model guide
- `docs/ci_policy.md` — CI validation, PR classification, report generation, and size policy
