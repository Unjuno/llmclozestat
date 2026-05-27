# Fixtures

This document defines the fixture policy for `llmclozestat` tests.

Fixtures are small, explicit files used to verify validators, parser/scorer behavior, aggregation, manifest verification, and model-repository checks.

## Principle

Fixtures should be minimal and diagnostic.

A fixture should usually test one thing.

Bad fixture design:

```text
one invalid file breaks ten unrelated rules
```

Good fixture design:

```text
one invalid file breaks one named rule
```

Fixture expected error codes should come from:

```text
docs/error_codes.md
```

## Directory layout

Recommended layout:

```text
tests/fixtures/
  README.md

  items/
    valid/
      smoke_v0_minimal.jsonl
    invalid/
      segments_blanks_mismatch.jsonl
      duplicate_blank_id.jsonl
      position_not_consecutive.jsonl
      empty_accepted_fills.jsonl
      missing_claim_scope.jsonl

  results/
    valid/
      smoke_v0_one_trial.jsonl
    invalid/
      content_pass_near_miss.jsonl
      parse_fail_with_blank_parse_pass.jsonl
      strict_pass_inconsistent.jsonl
      format_fail_v0.jsonl

  summaries/
    valid/
      smoke_v0_summary.json
    invalid/
      object_fill_distribution.json
      summary_wrong_counts.json

  manifests/
    valid/
      smoke_v0_manifest.json
    invalid/
      wrong_file_hash.json
      wrong_package_hash.json

  model_repository/
    valid/
      model.toml
    invalid/
      missing_one_model_repo.toml
      mixed_model_submission/
```

This layout is a target. Early implementation may add fixtures gradually.

## Naming rule

Invalid fixture names should describe the expected failure code or validation rule.

Examples:

```text
segments_blanks_mismatch.jsonl
duplicate_blank_id.jsonl
format_fail_v0.jsonl
wrong_package_hash.json
```

Do not use vague names such as:

```text
bad1.json
broken.jsonl
sample_invalid.json
```

## Valid item fixtures

Valid item fixtures should pass both schema validation and cross-field validation.

At minimum:

```text
segments.length == blanks.length + 1
blank_id unique inside item
position consecutive from 1
accepted_fills non-empty
claim_scope present
item_id unique inside dataset fixture
```

The current smoke item may be reused as the first valid item fixture.

## Invalid item fixtures

Each invalid item fixture should target one expected validation error.

Recommended initial invalid fixtures:

| Fixture | Expected failure | Code |
|---|---|---|
| `segments_blanks_mismatch.jsonl` | `segments.length != blanks.length + 1` | `segments_blanks_mismatch` |
| `duplicate_blank_id.jsonl` | duplicate `blank_id` inside one item | `duplicate_blank_id` |
| `position_not_consecutive.jsonl` | positions do not start at 1 or skip a value | `position_not_consecutive` |
| `empty_accepted_fills.jsonl` | a blank has no accepted fills | `empty_accepted_fills` |
| `missing_claim_scope.jsonl` | current-schema item has no claim scope | `missing_claim_scope` |

## Result fixtures

Valid result fixtures should preserve:

- `raw_output`;
- `normalized_output`;
- prompt condition fields;
- parser condition fields;
- generation condition fields;
- blank-level scoring;
- item-level scoring.

Invalid result fixtures should target scoring consistency rules.

Recommended initial invalid result fixtures:

| Fixture | Expected failure | Code |
|---|---|---|
| `content_pass_near_miss.jsonl` | `fill_class = near_miss` with `content_pass = true` | `content_pass_near_miss` |
| `parse_fail_with_blank_parse_pass.jsonl` | `parse_fail = true` with `blank_parse_pass = true` | `parse_fail_with_blank_parse_pass` |
| `strict_pass_inconsistent.jsonl` | `item_strict_pass = true` despite failed blank or format | `strict_pass_inconsistent` |
| `format_fail_v0.jsonl` | blank-level `fill_class = format_fail` in v0 | `format_fail_v0` |

## Summary fixtures

Valid summary fixtures should use array-form `fill_distribution` entries.

Recommended entry shape:

```json
{
  "extracted_fill": "右",
  "fill_key": "右",
  "count": 1,
  "rate": 1.0,
  "fill_class": "accepted"
}
```

For parse failures:

```json
{
  "extracted_fill": null,
  "fill_key": "__PARSE_FAIL__",
  "count": 1,
  "rate": 1.0,
  "fill_class": "parse_fail"
}
```

Invalid summary fixtures should include:

| Fixture | Expected failure | Code |
|---|---|---|
| `object_fill_distribution.json` | old object-keyed fill distribution format | `object_fill_distribution` |
| `summary_wrong_counts.json` | counts or rates do not match raw result records | `summary_wrong_counts` |

## Manifest fixtures

Valid manifest fixtures should match the canonicalization algorithm in `docs/integrity.md`.

Invalid manifest fixtures should include:

| Fixture | Expected failure | Code |
|---|---|---|
| `wrong_file_hash.json` | one listed file SHA-256 does not match raw bytes | `wrong_file_hash` |
| `wrong_package_hash.json` | per-file hashes match but `package_hash` is wrong | `wrong_package_hash` |

## Model repository fixtures

Valid model repository fixtures should include:

```text
model.toml
submissions/<submitter_id>/<run_id>/...
```

and satisfy:

```text
environment.json.model_id == model.toml.model.model_id
all result records model_id == model.toml.model.model_id
summary.json.model_id == model.toml.model.model_id
```

Invalid model repository fixtures should include:

| Fixture | Expected failure | Code |
|---|---|---|
| `missing_one_model_repo.toml` | `policy.one_model_repo` missing or false | `missing_one_model_repo` |
| `mixed_model_submission/` | submission model differs from `model.toml` | `mixed_model_submission` |

## Expected-failure metadata

Each invalid fixture should eventually have expected-failure metadata.

Possible formats:

```text
<fixture>.expected.json
```

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

This prevents tests from merely checking that validation failed. They must check that validation failed for the intended reason.

Expected codes must be registered in:

```text
docs/error_codes.md
```

## Implementation order

Add fixtures in this order:

```text
1. item valid/invalid fixtures
2. parser/scorer result fixtures
3. summary fixtures
4. manifest fixtures
5. model repository fixtures
```

This order matches `docs/implementation_plan.md`.

## Rule for invalid fixtures

Invalid fixtures are allowed to live in the repository.

CI must not treat every file under `tests/fixtures/**/invalid/` as data that should pass validation.

Instead, CI should run negative tests that assert these files fail with expected validation errors.
