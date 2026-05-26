# CLI Usage

`llmclozestat` is designed as a local-first CLI.

Users clone the repository, run evaluations locally, accumulate raw JSONL logs, aggregate summaries, and optionally prepare a Git submission package.

## Implementation status

This document describes the intended CLI shape. In v0.0, these commands are design targets until implementation is added.

Currently expected commands:

- `version`: minimal existing command.
- `run`: design target.
- `aggregate`: design target.
- `prepare-submission`: design target.
- `validate`: design target.
- `verify-integrity`: design target.
- `report`: design target.
- `collect`: design target for one-command run/package/validate/PR-oriented workflows.

## Target workflow

```text
git clone
  -> install CLI locally
  -> run evaluation locally
  -> append raw JSONL under results/
  -> aggregate summaries
  -> prepare submissions/<submitter_id>/<run_id>/
  -> write manifest.json for publishable submissions
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
  --prompt-template-id fill_full_sentence_v1.ja \
  --prompt-language ja \
  --support-mode zero \
  --f-shot 0 \
  --blank-rendering '（　　　）' \
  --temperature 0 \
  --top-p null \
  --seed null \
  --max-tokens 64 \
  --context-window null
```

## Collect command shape

`collect` is a future convenience command. It should run exactly one model under one condition and produce one submission package.

Recommended MVP constraint:

```text
one collect command = one model = one run = one submission
```

Possible shape:

```bash
llmclozestat collect \
  --dataset datasets/smoke_v0/items.jsonl \
  --provider openai-compatible \
  --base-url http://localhost:1234/v1 \
  --model local-model \
  --submitter-id github-username-or-local-name \
  --target-trials 20 \
  --prompt-template-id fill_full_sentence_v1.ja \
  --prompt-language ja \
  --support-mode zero \
  --f-shot 0 \
  --blank-rendering '（　　　）' \
  --prepare-submission \
  --write-manifest \
  --validate
```

`collect` may later support PR-oriented modes such as `--safe-pr`, but push and pull-request creation should be explicit. The MVP may stop at generating a validated local submission package.

`collect` should not mix multiple model identities in one submission package.

## Required run metadata

The run command should make these values explicit or derive them safely:

- `submitter_id`
- `run_id`
- `dataset_id`
- `model_id`
- `model_source`
- `quantization`
- `backend`
- `backend_version`
- `provider`
- `prompt_template_id`
- `prompt_language`
- `support_mode`
- `f_shot`
- `blank_rendering`
- `parser_config`
- `extraction_mode`
- `temperature`
- `top_p`
- `seed`
- `max_tokens`
- `context_window`
- `repeat_penalty`
- `stop`

`submitter_id` and `run_id` are not authentication. They are provenance fields for filtering and re-aggregation.

`prompt_template_id`, `prompt_language`, `support_mode`, `f_shot`, and `blank_rendering` are experimental conditions. They must be preserved so prompt changes are not mistaken for model behavior differences.

`extraction_mode` is required in result records. v0 should use only `exact_full_text` or `segment`; fallback extraction modes must not be mixed into v0 aggregates without grouping by extraction mode.

## Generation config identity

Aggregators should compare generation conditions using canonicalized generation config.

Recommended canonicalization:

- serialize as canonical JSON;
- sort object keys;
- preserve explicit null values;
- avoid insignificant whitespace;
- hash the canonical JSON when a compact grouping key is needed.

Recommended field:

```json
{
  "generation_config_hash": "sha256:..."
}
```

This avoids treating semantically identical JSON objects as different conditions only because their key order differs.

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

Aggregators should preserve grouping by:

- `model_id`
- `dataset_id`
- `probe_id`
- `variant_id`
- `language`
- `item_id`
- `blank_id`
- `prompt_template_id`
- `prompt_language`
- `support_mode`
- `f_shot`
- `blank_rendering`
- `extraction_mode`
- `generation_config` or `generation_config_hash`
- `submitter_id`
- `run_id`

## Prepare submission command shape

```bash
llmclozestat prepare-submission \
  --submitter-id github-username-or-local-name \
  --run-id smoke-local-model-20260525 \
  --run-jsonl results/smoke-local-model-20260525/run.jsonl \
  --summary-json results/smoke-local-model-20260525/summary.json \
  --out-dir submissions/github-username-or-local-name/smoke-local-model-20260525 \
  --write-manifest
```

The generated publishable directory should contain:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
  manifest.json
```

For larger runs, implementations should allow sharded JSONL output:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run-shards/
    run-000001.jsonl
    run-000002.jsonl
  summary.json
  summary.md
  manifest.json
```

`manifest.json` is required for publishable submissions. It is optional only for local scratch results under `results/`, which must be treated as unverified.

## Verify integrity command shape

```bash
llmclozestat verify-integrity \
  --path submissions/<submitter_id>/<run_id>
```

This command verifies package hashes only. It does not prove that the claimed model generated the outputs.

## Repository-retained data

The repository should retain:

- canonical datasets under `datasets/`;
- documentation under `docs/`;
- shareable submitted result packages under `submissions/`;
- examples and schemas when added.

The repository should not retain local scratch outputs under `results/`.

For large or repeated result collection, prefer separate model repositories. A model repository should contain results for one model identity and use the same submission package format.

## Local-first rule

The CLI should work without any hosted service controlled by this project.

A user should be able to:

1. clone the repository;
2. run a local or OpenAI-compatible model endpoint;
3. collect local raw JSONL;
4. aggregate locally;
5. decide whether to commit or submit results.

This keeps the tool simple and keeps model authentication, execution attestation, and hosted infrastructure out of scope.

Package-level manifest hashing is allowed because it only detects later package tampering. It must not be described as model authentication.
