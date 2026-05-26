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
- manifest hash mismatch.

### WARNING

A warning means the file can be used, but interpretation may be weak or risky.

Examples:

- `claim_scope` is missing in legacy data;
- `expected_error_patterns` is missing;
- multilingual variant has `equivalence_level = adapted`;
- `seed` is null;
- `backend_version` is missing;
- `hardware` is missing;
- dataset has only one item;
- low number of trials;
- local scratch results do not have `manifest.json`.

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

### Schema checks

Each line should validate against:

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
- `extraction_mode` is one of the supported modes;
- v0 result records should use only `exact_full_text` or `segment` extraction;
- `support_mode = zero` implies `f_shot = 0`;
- `support_mode != zero` should usually imply `f_shot >= 1`;
- `prompt_language`, `prompt_template_id`, and `blank_rendering` are present and stable within a comparable run;
- `generation_config_hash`, when present, matches canonical JSON for `generation_config`;
- `trial_id` is positive;
- repeated result identity tuples are either rejected or reported.

Recommended result identity tuple:

```text
submitter_id + run_id + dataset_id + model_id + item_id + trial_id + prompt_template_id + support_mode
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
- `dataset_id` matches `run.jsonl`;
- `model_id` matches `run.jsonl`;
- `backend` and `provider` match `run.jsonl`;
- `prompt_template_id`, `prompt_language`, `support_mode`, and `blank_rendering` match `run.jsonl`;
- `generation_config` is consistent with result records;
- `parser_config.extraction_modes_enabled` is compatible with result `extraction_mode` values.

Missing fields such as `seed`, `backend_version`, `quantization`, or `hardware` should usually be warnings, not errors.

## Submission package validation

Input:

```text
submissions/<submitter_id>/<run_id>/
```

Publishable submissions must contain:

```text
environment.json
run.jsonl
summary.json
summary.md
manifest.json
```

Local scratch results under `results/` may omit `manifest.json`, but such results must be treated as unverified and should not be described as integrity-checked.

### Package checks

The validator should check:

- required files exist;
- path `<submitter_id>` matches `environment.json.submitter_id`;
- path `<run_id>` matches `environment.json.run_id`;
- all `run.jsonl` records use the same `submitter_id` and `run_id`;
- all `run.jsonl` records use comparable prompt and generation metadata unless intentionally grouped;
- `summary.json` can be regenerated from `run.jsonl`, or at least declares how it was generated;
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

## Environment validation commands

Planned CLI shape:

```bash
llmclozestat validate environment \
  --input submissions/example/run/environment.json
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
