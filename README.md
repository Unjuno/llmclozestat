# llmclozestat

`llmclozestat` is a CLI project for cloze-based statistical profiling of LLM outputs.

It asks language models to complete fill-in-the-blank items and output the completed full sentence. The tool records raw outputs, extracts filled spans, classifies each fill, and aggregates statistics such as content pass rate, format compliance, strict pass rate, parse failure rate, fill distribution, repeated wrong fills, and latency.

This is not an official leaderboard. The goal is to observe model behavior statistically.

## 日本語概要

`llmclozestat` は、LLMに穴埋め問題を解かせ、穴埋め後の全文を出力させることで、補完語・形式遵守・誤補完の分布を記録するCLIプロジェクトです。

4択問題ではありません。A/B/C/D の選択肢を集計するのではなく、モデルが実際に補った文字列を抽出し、その分布を見ます。

## Operating model

`llmclozestat` is intended to be a normal local CLI tool.

The expected workflow is:

```text
git clone
  -> install CLI locally
  -> choose a dataset
  -> run against a local or OpenAI-compatible model endpoint
  -> append raw JSONL records
  -> aggregate summaries
  -> inspect reports
  -> repeat
  -> commit or open a PR when enough results are collected
```

There is no built-in model authentication, result attestation, anti-tamper system, or official result verification. Local outputs are measurement logs for analysis, not certified benchmark records.

Local scratch outputs should go under `results/`, which is ignored by Git. Shareable result packages should be prepared under `submissions/<user>/<run_id>/` and committed or submitted by pull request.

## Current status

The project is in the v0.0 design/smoke-test phase.

Current repository contents focus on:

- item format
- result format
- problem data policy
- scoring/conceptual model
- research rationale
- one-item smoke dataset
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

## What this is not

- Not a four-choice benchmark.
- Not an official leaderboard.
- Not an authentication system for LLM outputs.
- Not an anti-tamper evaluation system.
- Not a signed-result or attestation framework.
- Not an LLM-judge scoring framework.
- Not a web dashboard.

## Initial dataset

See:

- `datasets/smoke_v0/items.jsonl`
- `datasets/smoke_v0/README.md`

The first item is a mirror-perspective probe. It tests whether a model can distinguish actual body-part correspondence from the common surface rule that mirrors “reverse left and right.”

## Result accumulation

The repository may collect community or personal run results through ordinary Git commits or pull requests.

Recommended publishable layout:

```text
submissions/<user>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
```

This is still self-reported data. The project does not certify that a submitted result was honestly produced by a claimed model.

## Documentation

- `docs/research_rationale.md` — research value and diagnostic comparison rationale
- `docs/conceptual_model.md` — conceptual model and scoring design
- `docs/design.md` — project design and scope
- `docs/problem_data_policy.md` — rules for authoring probe items
- `docs/result_format.md` — raw result JSONL and aggregate format
- `docs/cli_usage.md` — intended CLI workflow and command shapes

## Early development plan

1. Finalize item/result formats.
2. Implement parser and scorer.
3. Implement basic aggregation.
4. Add validation for item/result files.
5. Add OpenAI-compatible runner for LM Studio and similar local servers.
6. Add lightweight terminal progress display.
7. Add Markdown report generation.

## License

- Code: Apache-2.0
- Dataset/docs: see `DATA_LICENSE.md`
