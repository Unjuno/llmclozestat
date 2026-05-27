# Validation Design

This document defines validation responsibilities for `llmclozestat`.

Validation is separate from scoring. Validation checks whether data can be trusted structurally enough to run or aggregate. Scoring checks model behavior after a valid run record exists.

## Validation layers

Validation should be layered:

```text
schema validation
  -> cross-field validation
  -> dataset-level validation
  -> result-level validation
  -> environment validation
  -> summary validation
  -> manifest validation
  -> model repository validation
  -> submission package validation
  -> package integrity validation
```

Each layer should report either `ERROR`, `WARNING`, or `INFO`.

## Severity levels

### ERROR

An error means the file should not be used.

Examples:

- invalid JSON or JSONL;
- missing required fields;
- `segments.length != blanks.length + 1`;
- empty `accepted_fills`;
- duplicate `blank_id` inside an item;
- invalid `fill_class`;
- result record missing `submitter_id` or `run_id`;
- publishable submission missing `manifest.json`;
- manifest hash mismatch;
- summary cannot be regenerated from raw results;
- current-schema item missing `claim_scope`;
- one-model submission contains more than one `model_id`;
- submission path `submitter_id` or `run_id` does not match package metadata.

### WARNING

A warning means the file can be used, but interpretation may be weak or risky.

Examples:

- `claim_scope` is missing in explicitly declared legacy data;
- `expected_error_patterns` is missing;
- multilingual variant has `equivalence_level = adapted`;
- `seed` is null;
- `backend_version` is missing;
- `hardware` is missing;
- dataset has only one item;
- low number of trials;
- local scratch results do not have `manifest.json`;
- blank-level `fill_class = format_fail` appears in v0 data without an explicit later policy.

### INFO

Info is non-problematic metadata.

Examples:

- number of items loaded;
- number of variants per probe;
- number of languages;
- number of trials;
- number of submitters;
- number of excluded runs;
- integrity status such as `manifest_verified` or `unverified_local_result`.

## Item validation

Input:

```text
datasets/<dataset_id>/items.jsonl
```

### Schema checks

Each line should validate against:

```text
schemas/item.schema.json
```

This catches missing required fields and basic type errors.

For current schema validation, missing `claim_scope` is an error. For explicitly declared legacy datasets, a compatibility validator may report missing `claim_scope` as a warning instead.

### Cross-field checks

Schema alone is not enough. Validation code should also check:

- `segments.length == blanks.length + 1`;
- `blank_id` values are unique inside an item;
- `position` values are unique inside an item;
- `position` values are consecutive starting at 1;
- every `accepted_fills` list is non-empty;
- every `expected_full_texts` entry is non-empty;
- every blank with `depends_on` references an existing earlier blank;
- `context_distance` is present for each blank when context analysis is intended;
- `claim_scope` exists for every new item;
- `accepted_fills`, `near_miss_fills`, and `known_wrong_fills` do not contain duplicate normalized values;
- if `known_wrong_fills` is non-empty, missing `expected_error_patterns` should be reported;
- `item_id` is unique inside the dataset and should not collide across language variants.

### Reconstruction checks

For each item, the validator should try to reconstruct at least one expected full text from:

```text
segments + accepted_fills
```

For one-blank items, this is direct.

For multi-blank items, full reconstruction may require the first accepted fill of each blank. This is a structural check, not a correctness proof.

### Probe and variant checks

Dataset-level validation should check:

- `item_id` is unique inside the dataset;
- `variant_id` is unique inside the dataset;
- each `probe_id` has at least one variant;
- each language variant has `language`, `translation_relation`, and `equivalence_level`;
- variants with the same `probe_id` should have compatible `validation_target.main_question`, or the validator should warn;
- `equivalence_level = not_equivalent` variants should not be aggregated as the same probe without explicit override.

## Result validation

Input:

```text
run.jsonl
```

or sharded input:

```text
run-shards/*.jsonl
```

### Schema checks

Each JSONL line should validate against:

```text
schemas/result.schema.json
```

### Cross-field checks

Validation code should also check:

- `blank_results` is non-empty;
- each `blank_id` appears only once per result record;
- `item_partial_score` is in `[0, 1]`;
- `item_strict_pass` is true only if all blank `content_pass` values are true, `instruction_following_pass` is true, and `item_format_pass` is true;
- for v0, `instruction_following_pass` should equal `item_format_pass`;
- `parse_fail = true` implies `blank_parse_pass = false`;
- `blank_parse_pass = false` should usually imply `extracted_fill = null`;
- `content_pass = true` should imply `fill_class = accepted` unless later policy allows exceptions;
- `fill_class = near_miss` must not imply `content_pass = true` in v0;
- `fill_class = format_fail` should be rejected or warned in v0 unless an explicit later policy enables blank-level format failure;
- `extraction_mode` is one of the supported modes;
- v0 result records should use only `exact_full_text` or `segment` extraction;
- `support_mode = zero` implies `f_shot = 0`;
- `support_mode != zero` should usually imply `f_shot >= 1`;
- `prompt_language`, `prompt_template_id`, `f_shot`, and `blank_rendering` are present and stable within a comparable run;
- `generation_config_hash`, when present, matches canonical JSON for `generation_config`;
- `trial_id` is positive;
- repeated result identity tuples are either rejected or reported.

Recommended result identity tuple:

```text
submitter_id
+ run_id
+ dataset_id
+ model_id
+ item_id
+ trial_id
+ prompt_template_id
+ prompt_language
+ support_mode
+ f_shot
+ blank_rendering
+ extraction_mode
+ generation_config_hash
```

### Dataset join checks

When the dataset is available, result validation should check:

- every `item_id` exists in the dataset;
- result `probe_id` matches dataset `probe_id` for that item;
- result `variant_id` matches dataset `variant_id`;
- result `language` matches dataset `language`;
- every result `blank_id` exists in the dataset item;
- each extracted fill is classified consistently with `accepted_fills` and `near_miss_fills`.

If the dataset is unavailable, result validation can still validate the record structure, but should warn that classification cannot be fully checked.

## Environment validation

Input:

```text
environment.json
```

### Schema checks

The file should validate against:

```text
schemas/environment.schema.json
```

### Consistency checks

Validation code should check:

- `submitter_id` matches the submission path;
- `run_id` matches the submission path;
- `dataset_id` matches result records;
- `model_id` matches result records;
- `backend` and `provider` match result records;
- `prompt_template_id`, `prompt_language`, `support_mode`, `f_shot`, and `blank_rendering` match result records;
- `generation_config` is consistent with result records;
- `parser_config.extraction_modes_enabled` is compatible with result `extraction_mode` values.

Missing fields such as `seed`, `backend_version`, `quantization`, or `hardware` should usually be warnings, not errors.

## Summary validation

Input:

```text
summary.json
```

### Schema checks

The file should validate against:

```text
schemas/summary.schema.json
```

### Consistency checks

Schema validity is not enough because `summary.json` is derived data.

Validation code should also check:

- `submitter_id`, `run_id`, `dataset_id`, and `model_id` match the source result records;
- `n_trials` matches the source result records;
- pass rates are recomputable from raw results;
- group keys are stable and include prompt/parser/generation grouping fields;
- group-level `fill_distribution` is an array of entries with `extracted_fill`, `fill_key`, `count`, `rate`, and `fill_class`;
- parse-fail entries with `extracted_fill = null` use `fill_key = "__PARSE_FAIL__"` unless a later policy defines another sentinel;
- group-level `fill_distribution` counts and rates match raw extracted fills;
- `unique_fill_count`, `top_fill`, `top_wrong_fill`, and `mean_entropy` match regenerated aggregation when implemented.

If `summary.json` does not match regenerated aggregation, treat it as an error for publishable submissions.

## Manifest validation

Input:

```text
manifest.json
```

### Schema checks

The file should validate against:

```text
schemas/manifest.schema.json
```

### Consistency checks

Validation code should also check:

- `submitter_id` and `run_id` match the submission path and `environment.json`;
- every listed file exists;
- listed paths are relative and do not escape the submission directory;
- each listed `sha256` matches the actual file content;
- `package_hash` matches the deterministic package hash calculation defined in `docs/integrity.md`;
- `manifest.json`, `signature.json`, and `ledger_receipt.json` are excluded from the v0 package hash input;
- `size_bytes`, if present, is not included in the v0 package hash input.

`manifest.json` verifies package files. It does not authenticate model execution.

## Model repository validation

Input:

```text
model.toml
```

### Schema checks

The TOML file should be parsed into an object and validate against:

```text
schemas/model.schema.json
```

### Consistency checks

Validation code should also check:

- `policy.one_model_repo = true`;
- `model.model_id` is filesystem- and URL-friendly;
- every submission in the model repository uses `model.model_id`;
- every `environment.json.model_id` matches `model.model_id`;
- all result records in every submission use `model.model_id`;
- `allow_mixed_model_ids = true` is unsupported in MVP unless explicitly allowed by a future policy.

`model.toml` is provenance metadata. It does not prove model execution authenticity.

## Submission package validation

Input:

```text
submissions/<submitter_id>/<run_id>/
```

Publishable submissions must contain:

```text
environment.json
summary.json
summary.md
manifest.json
```

and one of:

```text
run.jsonl
```

or:

```text
run-shards/*.jsonl
```

Local scratch results under `results/` may omit `manifest.json`, but such results must be treated as unverified and should not be described as integrity-checked.

### One-model submission policy

MVP submissions should contain exactly one model identity.

The validator should check:

- all result records have the same `model_id`;
- `environment.json.model_id` matches all result records;
- if `model.toml` exists in a model repository, `model.toml.model.model_id` matches the submission model ID;
- a submission package does not mix unrelated quantization or backend identities unless a future policy explicitly allows it.

### Submitter and run identity policy

The validator should check the policy defined in `docs/submitter_identity.md`.

Required checks:

- path `<submitter_id>` matches `environment.json.submitter_id`;
- path `<run_id>` matches `environment.json.run_id`;
- all result records use the same `submitter_id` and `run_id`;
- `summary.json.submitter_id` and `summary.json.run_id` match `environment.json`;
- `manifest.json.submitter_id` and `manifest.json.run_id` match `environment.json`;
- `submitter_id` is a safe lowercase slug;
- `run_id` has the recommended dataset/timestamp/random structure, or is explicitly accepted by a future compatibility policy;
- for ordinary public PRs, `submitter_id` should match the lowercase PR author login;
- the submission path should be new relative to the base branch.

### Package checks

The validator should check:

- required files exist;
- either `run.jsonl` or at least one `run-shards/*.jsonl` file exists;
- all result records use comparable prompt, parser, and generation metadata unless intentionally grouped by a future policy;
- `summary.json` can be regenerated from result JSONL, or at least declares how it was generated;
- `summary.md` is present and human-readable;
- `manifest.json` exists for publishable submissions;
- every file listed in `manifest.json` exists;
- every listed file hash matches;
- `package_hash` matches the deterministic package hash calculation.

If `summary.json` does not match regenerated aggregation, treat it as an error for submission review.

If `manifest.json` is missing from a publishable submission, treat it as an error. If it is missing from local scratch results, report a warning or info status such as `unverified_local_result`.

## Dataset validation commands

Planned CLI shape:

```bash
llmclozestat validate items \
  --dataset datasets/smoke_v0/items.jsonl
```

Optional strict mode:

```bash
llmclozestat validate items \
  --dataset datasets/smoke_v0/items.jsonl \
  --strict
```

In strict mode, some warnings can be promoted to errors.

## Result validation commands

Planned CLI shape:

```bash
llmclozestat validate results \
  --input results/example/run.jsonl \
  --dataset datasets/smoke_v0/items.jsonl
```

If `--dataset` is omitted, only schema and internal consistency checks are possible.

For sharded results:

```bash
llmclozestat validate results \
  --input submissions/example/run/run-shards \
  --dataset datasets/smoke_v0/items.jsonl
```

## Environment validation commands

Planned CLI shape:

```bash
llmclozestat validate environment \
  --input submissions/example/run/environment.json
```

## Summary validation commands

Planned CLI shape:

```bash
llmclozestat validate summary \
  --input submissions/example/run/summary.json \
  --results submissions/example/run/run.jsonl
```

For sharded results:

```bash
llmclozestat validate summary \
  --input submissions/example/run/summary.json \
  --results submissions/example/run/run-shards
```

## Manifest validation commands

Planned CLI shape:

```bash
llmclozestat validate manifest \
  --input submissions/example/run/manifest.json \
  --package-dir submissions/example/run
```

## Model repository validation commands

Planned CLI shape:

```bash
llmclozestat validate model \
  --input model.toml
```

For a model repository:

```bash
llmclozestat validate model-repo \
  --path .
```

## Submission validation commands

Planned CLI shape:

```bash
llmclozestat validate submission \
  --path submissions/<submitter_id>/<run_id> \
  --dataset datasets/smoke_v0/items.jsonl
```

## Integrity verification commands

Planned CLI shape:

```bash
llmclozestat verify-integrity \
  --path submissions/<submitter_id>/<run_id>
```

This command checks package hashes only. It does not authenticate model execution.

## Validation output format

Validation should be machine-readable and human-readable.

Recommended JSON output:

```json
{
  "status": "failed",
  "errors": [
    {
      "code": "segments_blanks_mismatch",
      "message": "segments.length must equal blanks.length + 1",
      "path": "datasets/smoke_v0/items.jsonl:1"
    }
  ],
  "warnings": [],
  "info": [
    {"code": "item_count", "message": "Loaded 1 item"}
  ]
}
```

Recommended terminal summary:

```text
ERROR   segments_blanks_mismatch   items.jsonl:1
WARNING missing_claim_scope         items.jsonl:3
INFO    item_count=100
```

## Design rule

Validation must not silently fix data.

It may suggest repairs, but raw dataset and result files should only be changed by explicit user action.
