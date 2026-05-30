# CLI Usage

`llmclozestat` is designed as a local-first CLI.

Users clone the repository, run evaluations locally, accumulate raw JSONL logs, aggregate summaries, and optionally prepare a Git submission package.

## Implementation status

This document describes the current v0.0 smoke-test CLI surface. Implemented commands are intentionally narrow MVP implementations unless marked otherwise.

Currently implemented commands:

- `version`: print package version.
- `run`: minimal TOML-configured runner for OpenAI-compatible chat-completion backends; backend call failures are retained as trial-level parse-fail records.
- `validate items`: minimal item JSONL validation.
- `validate environment`: minimal environment JSON validation.
- `validate results`: minimal result JSONL consistency validation.
- `aggregate`: minimal single-result-JSONL to `summary.json` aggregation; validates input by default.
- `validate summary`: minimal summary JSON validation.
- `prepare-submission`: validate source artifacts, copy them into a submission package, and write a manifest.
- `validate manifest`: validate manifest shape and optionally verify file/package hashes.
- `validate submission`: validate local package integrity, path identity, artifact identity, and regenerated summary consistency.
- `verify-integrity`: same local package integrity path as `validate submission`.
- `validate model`: minimal `model.toml` validation.
- `validate model-repo`: minimal one-model repository validation.
- `report`: minimal CSV report generation from submission summaries.

Still design targets:

- `collect`
- full JSON Schema execution for every schema
- sharded and multi-run aggregation
- automated PR/report workflows
- signatures or ledger anchoring

## Target workflow

```text
git clone
  -> install CLI locally
  -> choose or pin a dataset
  -> run evaluation locally
  -> write raw JSONL under a run directory
  -> aggregate summary.json
  -> validate summary.json
  -> prepare submissions/<submitter_id>/<run_id>/
  -> write manifest.json for publishable submissions
  -> validate submission integrity
  -> commit or open a pull request
```

## Run command

Implemented command:

```bash
llmclozestat run --config run.toml
```

The run config is TOML. The implemented runner reads:

- `[run]`
- `[backend]`
- `[prompt]`
- `[generation]`
- optional `[parser]`
- `model.toml`, selected by `run.model_toml` or defaulting to `model.toml`

Current scope:

```text
one config file
one dataset JSONL
one model identity
one prompt condition
single-process execution
OpenAI-compatible chat completions backend
writes environment.json, run.jsonl, summary.json, manifest.json
keeps backend call failures as trial-level result records
```

Backend failure behavior:

```text
trial_status = backend_error
backend_error.type = exception class name
backend_error.message = sanitized single-line message
raw_output = ""
normalized_output = ""
extraction_mode = segment
blank_results[*].fill_class = parse_fail
blank_results[*].parse_fail = true
instruction_following_pass = false
item_format_pass = false
item_strict_pass = false
item_partial_score = 0.0
```

This keeps failed trials in the denominator instead of silently reducing `n_trials`.

Minimal config shape:

```toml
[run]
submitter_id = "local-user"
run_id = "smoke_v0-20260527T143012Z-a7f3c9"
dataset_path = "datasets/smoke_v0/items.jsonl"
trials_per_item = 1
output_dir = "submissions"
overwrite = false
model_toml = "model.toml"

[backend]
type = "openai_compatible"
provider = "local"
api_key_env = "OPENAI_API_KEY"
base_url = "http://localhost:1234/v1"
model_name = "local-model"

[prompt]
prompt_template_id = "fill_full_sentence_v1.ja"
prompt_language = "ja"
support_mode = "zero"
f_shot = 0
blank_rendering = "（　　　）"

[generation]
temperature = 0
top_p = 1.0
seed = 1
max_tokens = 64
stop = []

[parser]
normalization = "v0_minimal"
extraction_modes_enabled = ["exact_full_text", "segment"]
fallback_extraction_enabled = false
```

Current limitations:

```text
no same-run parallel execution
no sharded output
no retry policy beyond backend/client behavior
no execution attestation
no proof that the claimed model actually produced the output
```

## Validate items command

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

## Validate environment command

Implemented command:

```bash
llmclozestat validate environment \
  --input submissions/local-user/run-id/environment.json
```

Current scope:

```text
JSON parse
selected required fields
support_mode and f_shot consistency
parser_config shape
generation_config shape
```

This is not yet a complete JSON Schema validator.

## Validate results command

Implemented command:

```bash
llmclozestat validate results \
  --input submissions/local-user/run-id/run.jsonl
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

## Aggregate command

Implemented command:

```bash
llmclozestat aggregate \
  --input submissions/local-user/run-id/run.jsonl \
  --out submissions/local-user/run-id/summary.json
```

By default, `aggregate` validates `run.jsonl` before writing `summary.json`. If validation fails, it prints the validation result and exits nonzero without writing the summary.

For scratch/debug inspection only, input validation can be explicitly skipped:

```bash
llmclozestat aggregate \
  --input scratch/incomplete-run.jsonl \
  --out scratch/summary.json \
  --no-validate-input
```

Current scope:

```text
one input result JSONL file
one output summary JSON file
overall pass/fail/parse-fail/latency rates
blank-level fill_distribution
parse failures represented with __PARSE_FAIL__
repeated fills counted without deduplication
```

Current limitations:

```text
no multi-file or sharded input
no exclusion filters
no summary.md generation
no report regeneration inside aggregate
no manifest writing inside aggregate
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
- `generation_config_hash`
- `submitter_id`
- `run_id`

## Validate summary command

Implemented command:

```bash
llmclozestat validate summary \
  --input submissions/local-user/run-id/summary.json
```

Current scope:

```text
JSON parse
selected required fields
groups array shape
fill_distribution array shape
count and rate totals
parse-fail sentinel consistency
```

Standalone summary validation does not currently reload the source `run.jsonl`. Submission validation performs the regenerated-summary check.

## Prepare submission command

Implemented command:

```bash
llmclozestat prepare-submission \
  --submitter-id local-user \
  --run-id smoke_v0-20260527T143012Z-a7f3c9 \
  --environment-json results/smoke/environment.json \
  --run-jsonl results/smoke/run.jsonl \
  --summary-json results/smoke/summary.json \
  --summary-md results/smoke/summary.md \
  --out-dir submissions/local-user/smoke_v0-20260527T143012Z-a7f3c9
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

Current behavior:

```text
validates source environment.json, run.jsonl, and summary.json by default
copies source artifacts
optionally copies summary.md
writes manifest.json by default
verifies generated manifest by default
rejects non-empty output directories unless --overwrite is passed
```

`prepare-submission` does not itself regenerate `summary.json` from `run.jsonl`. That regenerated-summary consistency check is performed by `validate submission` and `verify-integrity`.

## Validate manifest command

Implemented command:

```bash
llmclozestat validate manifest \
  --input submissions/local-user/run-id/manifest.json \
  --verify-files
```

Use `--package-dir` when the manifest should be verified against a directory other than the manifest parent directory.

## Validate submission / verify integrity commands

Implemented commands:

```bash
llmclozestat validate submission \
  --path submissions/<submitter_id>/<run_id>

llmclozestat verify-integrity \
  --path submissions/<submitter_id>/<run_id>
```

These commands verify:

```text
manifest.json exists
manifest shape is valid enough for v0
listed files exist and are regular files
listed file SHA-256 values match raw bytes
canonical package_hash matches manifest contents
manifest submitter_id and run_id match the package path
environment.json, run.jsonl, and summary.json identity fields agree
summary.json matches a regenerated summary from run.jsonl
```

These commands do not verify model execution.

## Validate model command

Implemented command:

```bash
llmclozestat validate model --input model.toml
```

Current scope:

```text
TOML parse
[model] required fields
[policy] one_model_repo policy
optional default_condition prompt/generation/parser checks
```

## Validate model-repo command

Implemented command:

```bash
llmclozestat validate model-repo --path .
```

Current scope:

```text
validate model.toml
check local submission artifacts against one model_id when present
```

## Report command

Implemented command:

```bash
llmclozestat report \
  --submissions-dir submissions \
  --out-dir reports
```

Current output:

```text
reports/run_index.csv
reports/blank_fills.csv
```

Reports are derived artifacts. Raw submissions remain the source of truth.

## Collect command

`collect` is a future convenience command. It should run exactly one model under one condition and produce one submission package.

Recommended MVP constraint:

```text
one collect command = one model = one run = one submission
```

`collect` may later support PR-oriented modes, but push and pull-request creation should be explicit. The MVP may stop at generating a validated local submission package.

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
