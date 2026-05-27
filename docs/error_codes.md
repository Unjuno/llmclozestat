# Error Codes

This document defines stable validation error and warning codes for `llmclozestat`.

The purpose is to connect:

```text
validators
  -> test fixtures
  -> CI diagnostics
  -> user-facing error messages
```

A validator should not invent ad-hoc error code names during implementation.

## Principles

### Stable names

Error codes should be stable once used by fixtures or CI.

Changing a code should be treated as a compatibility change because tests and expected-failure metadata may depend on it.

### One code, one meaning

A code should describe one failure mode.

Bad:

```text
invalid_item
bad_data
validation_failed
```

Good:

```text
segments_blanks_mismatch
empty_accepted_fills
duplicate_blank_id
```

### Schema vs cross-field validation

Use different codes for different validation layers.

Examples:

```text
json_parse_error
schema_validation_error
segments_blanks_mismatch
```

Do not hide cross-field validation failures under a generic schema error.

### Specific schema-derived codes

Some field-level constraints are already expressible in JSON Schema, but they are important enough to have stable user-facing codes.

Examples:

```text
empty_accepted_fills
missing_claim_scope
empty_expected_full_texts
```

A validator may map an unambiguous schema failure to a specific code instead of only returning `schema_validation_error`.

Recommended behavior:

```text
schema violation with known mapping -> specific code + schema detail
schema violation without known mapping -> schema_validation_error
```

This allows fixtures to expect `empty_accepted_fills` even when the immediate failure is caused by `minItems: 1` in `item.schema.json`.

## Severity

Recommended severity values:

```text
ERROR
WARNING
INFO
```

An `ERROR` means the file or package should not be used.

A `WARNING` means the file may be usable but interpretation is weaker or policy-dependent.

`INFO` is diagnostic metadata.

## Common codes

| Code | Severity | Meaning |
|---|---:|---|
| `json_parse_error` | ERROR | JSON or JSONL line cannot be parsed |
| `toml_parse_error` | ERROR | TOML file cannot be parsed |
| `schema_validation_error` | ERROR | File does not conform to its JSON Schema and no more specific mapping is available |
| `path_traversal` | ERROR | A manifest or submission path escapes its package directory |
| `unsafe_slug` | ERROR | `submitter_id` or similar path component is not a safe slug |

## Item validation codes

These are the first implementation target.

| Code | Severity | Meaning |
|---|---:|---|
| `segments_blanks_mismatch` | ERROR | `segments.length != blanks.length + 1` |
| `duplicate_blank_id` | ERROR | Same `blank_id` appears more than once inside one item |
| `duplicate_blank_position` | ERROR | Same blank `position` appears more than once inside one item |
| `position_not_consecutive` | ERROR | Blank positions do not start at 1 and increase consecutively |
| `empty_accepted_fills` | ERROR | A blank has an empty `accepted_fills` list |
| `missing_claim_scope` | ERROR | Current-schema item has no `claim_scope` |
| `duplicate_normalized_fill` | ERROR | A normalized fill appears more than once across accepted/near-miss/wrong lists for a blank |
| `depends_on_unknown_blank` | ERROR | A blank depends on a blank ID not present earlier in the item |
| `empty_expected_full_texts` | ERROR | `expected_full_texts` is empty |
| `duplicate_item_id` | ERROR | Same `item_id` appears more than once in one dataset |
| `duplicate_variant_id` | ERROR | Same `variant_id` appears more than once in one dataset |
| `not_equivalent_variant_aggregation` | WARNING | `equivalence_level = not_equivalent` should not be aggregated as the same probe without explicit override |
| `missing_expected_error_patterns` | WARNING | `known_wrong_fills` exists but `expected_error_patterns` is empty |

## Result validation codes

| Code | Severity | Meaning |
|---|---:|---|
| `empty_blank_results` | ERROR | Result record has no `blank_results` |
| `duplicate_result_blank_id` | ERROR | Same `blank_id` appears more than once in one result record |
| `invalid_item_partial_score` | ERROR | `item_partial_score` is outside `[0, 1]` |
| `strict_pass_inconsistent` | ERROR | `item_strict_pass` does not match the strict-pass formula |
| `content_pass_fill_class_inconsistent` | ERROR | `content_pass = true` but `fill_class` is not `accepted` in v0 |
| `content_pass_near_miss` | ERROR | `fill_class = near_miss` with `content_pass = true` |
| `parse_fail_with_blank_parse_pass` | ERROR | `parse_fail = true` but `blank_parse_pass = true` |
| `parse_fail_with_extracted_fill` | WARNING | `parse_fail = true` but `extracted_fill` is not null |
| `format_fail_v0` | WARNING | Blank-level `fill_class = format_fail` appears in v0 data |
| `unsupported_extraction_mode` | ERROR | `extraction_mode` is not supported by the active policy |
| `zero_support_mode_with_f_shot` | ERROR | `support_mode = zero` but `f_shot != 0` |
| `missing_condition_field` | ERROR | Required prompt/parser/generation condition field is missing |
| `duplicate_result_identity` | ERROR | Two result records have the same result identity tuple |

## Summary validation codes

| Code | Severity | Meaning |
|---|---:|---|
| `summary_schema_validation_error` | ERROR | `summary.json` does not match `schemas/summary.schema.json` |
| `object_fill_distribution` | ERROR | Summary uses old object-keyed `fill_distribution` format |
| `parse_fail_missing_sentinel` | ERROR | Parse-fail entry does not use `fill_key = "__PARSE_FAIL__"` |
| `summary_wrong_counts` | ERROR | Summary counts do not match raw result records |
| `summary_wrong_rates` | ERROR | Summary rates do not match raw result records |
| `summary_identity_mismatch` | ERROR | Summary submitter/run/dataset/model fields do not match source records |

## Manifest and integrity codes

| Code | Severity | Meaning |
|---|---:|---|
| `manifest_schema_validation_error` | ERROR | `manifest.json` does not match `schemas/manifest.schema.json` |
| `missing_manifest` | ERROR | Publishable submission has no `manifest.json` |
| `missing_listed_file` | ERROR | Manifest lists a file that does not exist |
| `unexpected_manifest_self_reference` | ERROR | `manifest.json` is included in v0 package hash input |
| `wrong_file_hash` | ERROR | Listed file SHA-256 does not match raw file bytes |
| `wrong_package_hash` | ERROR | Per-file hashes may match but `package_hash` is wrong |
| `manifest_identity_mismatch` | ERROR | Manifest submitter/run fields do not match path or environment |

## Model repository codes

| Code | Severity | Meaning |
|---|---:|---|
| `model_toml_missing` | ERROR | Model repository has no `model.toml` |
| `model_schema_validation_error` | ERROR | Parsed `model.toml` does not match `schemas/model.schema.json` |
| `missing_one_model_repo` | ERROR | `policy.one_model_repo` is missing or not true |
| `mixed_model_submission` | ERROR | Submission model ID differs from `model.toml.model.model_id` |
| `model_id_changed_with_existing_submissions` | ERROR | PR changes model identity after real submissions exist |

## Submitter and run identity codes

| Code | Severity | Meaning |
|---|---:|---|
| `submitter_id_path_mismatch` | ERROR | Path submitter ID does not match package metadata |
| `run_id_path_mismatch` | ERROR | Path run ID does not match package metadata |
| `submitter_id_author_mismatch` | ERROR | Ordinary public PR submitter ID does not match PR author login |
| `run_id_invalid_format` | ERROR | `run_id` does not match the dataset/timestamp/random structure |
| `submission_path_already_exists` | ERROR | PR attempts to reuse an existing submission path |

## Expected-failure metadata

Invalid fixtures should declare expected codes.

Example:

```json
{
  "expected_status": "failed",
  "expected_errors": [
    {
      "code": "segments_blanks_mismatch"
    }
  ]
}
```

Tests should verify both:

```text
1. the invalid fixture fails
2. it fails for the expected code
```

## Adding new codes

When adding a validator rule:

```text
1. Add the code here.
2. Add or update an invalid fixture.
3. Add expected-failure metadata.
4. Update validation documentation if the rule changes policy.
```

Do not add new codes only inside implementation code.
