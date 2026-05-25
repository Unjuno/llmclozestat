# CLI Usage

`llmclozestat` is designed as a local-first CLI.

Users clone the repository, run evaluations locally, accumulate raw JSONL logs, aggregate summaries, and optionally prepare a Git submission package.

## Target workflow

```text
git clone
  -> install CLI locally
  -> run evaluation locally
  -> append raw JSONL under results/
  -> aggregate summaries
  -> prepare submissions/<submitter_id>/<run_id>/
  -> commit or open a pull request
```

## Run command shape

The exact implementation may change, but the CLI should support this shape:

```bash
llmclozestat run \
  --dataset datasets/smoke_v0/items.jsonl \
  --provider openai-compatible \
  --base-url http://localhost:1234/v1 \
  --model local-model \
  --submitter-id github-username-or-local-name \
  --run-id smoke-local-model-20260525 \
  --out results/smoke-local-model-20260525/run.jsonl \
  --temperature 0 \
  --max-tokens 64
```

## Required run metadata

The run command should make these values explicit or derive them safely:

- `submitter_id`
- `run_id`
- `dataset_id`
- `model_id`
- `backend`
- `provider`
- `temperature`
- `max_tokens`

`submitter_id` and `run_id` are not authentication. They are provenance fields for filtering and re-aggregation.

## Aggregate command shape

```bash
llmclozestat aggregate \
  --input results/smoke-local-model-20260525/run.jsonl \
  --out results/smoke-local-model-20260525/summary.json
```

Aggregators should later support exclusion filters:

```bash
llmclozestat aggregate \
  --input submissions \
  --exclude-submitter-id example-user \
  --exclude-run-id broken-run-001 \
  --out reports/summary.json
```

## Prepare submission command shape

```bash
llmclozestat prepare-submission \
  --submitter-id github-username-or-local-name \
  --run-id smoke-local-model-20260525 \
  --run-jsonl results/smoke-local-model-20260525/run.jsonl \
  --summary-json results/smoke-local-model-20260525/summary.json \
  --out-dir submissions/github-username-or-local-name/smoke-local-model-20260525
```

The generated directory should contain:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
```

## Repository-retained data

The repository should retain:

- canonical datasets under `datasets/`;
- documentation under `docs/`;
- shareable submitted result packages under `submissions/`;
- examples and schemas when added.

The repository should not retain local scratch outputs under `results/`.

## Local-first rule

The CLI should work without any hosted service controlled by this project.

A user should be able to:

1. clone the repository;
2. run a local or OpenAI-compatible model endpoint;
3. collect local raw JSONL;
4. aggregate locally;
5. decide whether to commit or submit results.

This keeps the tool simple and keeps authentication, attestation, and hosted infrastructure out of scope.
