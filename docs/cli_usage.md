# CLI Usage

`llmclozestat` is designed as a local-first CLI.

Users clone the repository, run evaluations locally, accumulate raw JSONL logs, aggregate summaries, and optionally prepare a Git submission package.

## Implementation status

This document describes the intended CLI shape. In v0.0, most commands are design targets until implementation is added.

Currently implemented commands:

- `version`: minimal existing command.
- `validate items`: minimal item JSONL validation.
- `validate results`: minimal result JSONL consistency validation.

Currently implemented library core:

- strict-v0 parser/scorer pure function core.
- result-record assembly helper.

Still design targets:

- `run`
- `aggregate`
- `prepare-submission`
- `validate summary`
- `validate manifest`
- `validate submission`
- `validate model`
- `validate model-repo`
- `verify-integrity`
- `report`
- `collect`

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
  --run-id smoke_v0-20260527T143012Z-a7f3c9 \
  --out results/smoke_v0-20260527T143012Z-a7f3c9/run.jsonl \
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

## Validate items command shape

Implemented command:

```bash
llmclozestat validate items \
  --dataset datasets/smoke_v0/items.jsonl
```

It returns a JSON validation result and exits with code `1` when errors are present.

Current scope:

```text
JSONL parse
schema-like required/minItems checks for item data
item cross-field checks
basic dataset-level duplicate ID checks
```

This is not yet a complete JSON Schema validator for every constraint in `schemas/item.schema.json`.

## Validate results command shape

Implemented command:

```bash
llmclozestat validate results \
  --input submissions/example/run/run.jsonl
```

It returns a JSON validation result and exits with code `1` when errors are present.

Current scope:

```text
JSONL parse
schema-like required result fields
prompt/parser/generation condition field presence
supported v0 extraction_mode checks
zero support_mode and f_shot consistency
blank-level scoring consistency
item_strict_pass formula consistency
duplicate result identity detection
```

This is not yet a complete JSON Schema validator for every constraint in `schemas/result.schema.json`.

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

## Submitter and run identity defaults

`submitter_id` and `run_id` are provenance fields for filtering, conflict avoidance, and re-aggregation.

Recommended defaults:

```text
submitter_id = explicit CLI argument, or lowercase GitHub username when safely detected
run_id = <dataset_id>-<UTC timestamp>-<random suffix>
```

Example:

```text
submitter_id = unjuno
run_id = smoke_v0-20260527T143012Z-a7f3c9
```

The CLI should not silently reuse an existing `run_id`.

If the target output directory already exists, the command should fail unless an explicit later resume or overwrite option is provided.

Multiple machines owned by the same user should use the same `submitter_id` and different automatically generated `run_id` values.

See `docs/submitter_identity.md` for the full policy.

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
  --input results/smoke_v0-20260527T143012Z-a7f3c9/run.jsonl \
  --out results/smoke_v0-20260527T143012Z-a7f3c9/summary.json
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
  --run-id smoke_v0-20260527T143012Z-a7f3c9 \
  --run-jsonl results/smoke_v0-20260527T143012Z-a7f3c9/run.jsonl \
  --summary-json results/smoke_v0-20260527T143012Z-a7f3c9/summary.json \
  --out-dir submissions/github-username-or-local-name/smoke_v0-20260527T143012Z-a7f3c9 \
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

This command verifies package hashes only. It does not verify model execution.

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

This keeps the tool simple and keeps hosted infrastructure out of scope.

Package-level manifest hashing is allowed because it only detects later package tampering.
