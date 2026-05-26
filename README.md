# llmclozestat

`llmclozestat` is a CLI project for cloze-based statistical profiling of LLM outputs.

It asks language models to complete fill-in-the-blank items and output the completed full sentence. The tool records raw outputs, extracts filled spans, classifies each fill, and aggregates statistics such as content pass rate, format compliance, strict pass rate, parse failure rate, fill distribution, repeated wrong fills, and latency.

This is not an official leaderboard. The goal is to observe model behavior statistically.

## 日本語概要

`llmclozestat` は、LLMに穴埋め問題を解かせ、穴埋め後の全文を出力させることで、補完語・形式遵守・誤補完の分布を記録するCLIプロジェクトです。

4択問題ではありません。A/B/C/D の選択肢を集計するのではなく、モデルが実際に補った文字列を抽出し、その分布を見ます。

## Implementation status

This repository is still in the v0.0 design and smoke-test phase.

Only the minimal Python package skeleton exists. The `version` command exists, but the following commands are design targets and are not implemented yet:

- `run`
- `aggregate`
- `prepare-submission`
- `validate`
- `verify-integrity`
- `report`

Use the current documentation as the implementation specification, not as a claim that the full CLI already works.

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

There is no built-in proof that a claimed model truly generated a result. Local outputs are measurement logs for analysis, not certified benchmark records.

Local scratch outputs should go under `results/`, which is ignored by Git. Shareable result packages should be prepared under `submissions/<submitter_id>/<run_id>/` and committed or submitted by pull request.

## Current status

The project is in the v0.0 design/smoke-test phase.

Current repository contents focus on:

- item format
- prompt design
- parser and scoring design
- result format
- problem data policy
- validation design
- package-level integrity and tamper detection
- scoring/conceptual model
- research rationale and plan
- schemas for item/result/environment records
- one-item smoke dataset
- schema-compliant reference examples
- minimal Python package skeleton

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

Repeated fills are counted. If a model gives the same wrong fill at the same blank multiple times, those repetitions are treated as evidence of a systematic tendency, not as duplicates to remove.

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

`llmclozestat` supports package-level integrity checks through `manifest.json` for publishable submissions.

This can detect later changes to submitted files. It does not prove that the claimed model generated the outputs.

`manifest.json` is required for publishable submissions under `submissions/<submitter_id>/<run_id>/`. Local scratch results under `results/` may omit it, but they should be treated as unverified.

## What this is not

- Not a four-choice benchmark.
- Not an official leaderboard.
- Not an authentication system for model execution.
- Not proof that a claimed model truly generated a result.
- Not an execution attestation system.
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

This is still self-reported data. The project does not certify that a submitted result was honestly produced by a claimed model.

## Documentation

- `docs/research_plan.md` — research and evaluation plan
- `docs/research_rationale.md` — research value and diagnostic comparison rationale
- `docs/conceptual_model.md` — conceptual model and scoring design
- `docs/design.md` — project design and scope
- `docs/problem_data_policy.md` — rules for authoring probe items
- `docs/prompting.md` — prompt templates, support modes, and output contract
- `docs/parser_scoring.md` — deterministic extraction and scoring rules
- `docs/result_format.md` — raw result JSONL and aggregate format
- `docs/validation.md` — validation layers, severity, and command design
- `docs/integrity.md` — package-level integrity and tamper detection
- `docs/cli_usage.md` — intended CLI workflow and command shapes
- `schemas/README.md` — schema purpose and validation stance

## Early development plan

1. Finalize item/result formats.
2. Implement parser and scorer.
3. Implement basic aggregation.
4. Add validation for item/result files.
5. Add package manifest and local integrity verification.
6. Add OpenAI-compatible runner for LM Studio and similar local servers.
7. Add lightweight terminal progress display.
8. Add Markdown report generation.

## License

- Code: Apache-2.0
- Dataset/docs: see `DATA_LICENSE.md`
