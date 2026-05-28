# Status Matrix

This document separates the current state of `llmclozestat` into:

```text
implemented
specified but not implemented
partially specified
undefined or intentionally deferred
```

It is a working status document, not a roadmap promise.

## Summary

Current stage:

```text
v0.0 design / smoke-test phase
```

Implemented CLI surface:

```text
llmclozestat version
llmclozestat validate items --dataset <items.jsonl>
llmclozestat validate results --input <run.jsonl>
llmclozestat aggregate --input <run.jsonl> --out <summary.json>
llmclozestat validate summary --input <summary.json>
llmclozestat prepare-submission --submitter-id <id> --run-id <id> --environment-json <environment.json> --run-jsonl <run.jsonl> --summary-json <summary.json> --out-dir <submission-dir>
llmclozestat validate manifest --input <manifest.json> [--verify-files]
llmclozestat validate submission --path <submission-package-dir>
llmclozestat verify-integrity --path <submission-package-dir>
```

Implemented library core:

```text
item JSONL validation core
strict-v0 parser/scorer pure function core
result-record assembly helper
result JSONL validation core
summary aggregation helper
summary JSON validation core
manifest JSON validation helper
file SHA-256 helper
canonical package hash helper
local manifest integrity verification helper
prepare-submission package helper
submission path identity checker
```

The current executable pipeline is:

```text
run.jsonl
  -> validate results
  -> aggregate summary.json
  -> validate summary
  -> prepare-submission
  -> validate manifest / validate submission / verify-integrity
```

Most command-level behavior beyond item/result/summary/manifest validation, single-run aggregation, local package preparation, and local file-hash verification is still specified but not implemented.

## Status terms

| Status | Meaning |
|---|---|
| `implemented` | Code exists and is covered by tests or direct CLI surface |
| `partially implemented` | Some code exists, but it does not cover the full documented contract |
| `specified` | Documentation/schema/fixtures define the intended behavior, but no implementation exists |
| `partially specified` | Some design exists, but important choices remain open |
| `undefined` | No stable policy exists yet |
| `deferred` | Intentionally not part of the current phase |

## Command surface

| Area | Status | Evidence / current behavior | Gap |
|---|---|---|---|
| `version` | implemented | Prints package version | None for v0 |
| `validate items` | partially implemented | Validates JSONL parse, required/minItems-like item fields, selected cross-field checks, duplicate item/variant IDs | Not a complete JSON Schema validator |
| `validate results` | partially implemented | Validates JSONL parse, required result fields, condition fields, and selected scoring consistency rules | Not a complete JSON Schema validator |
| `validate summary` | partially implemented | Validates summary JSON parse, required fields, fill distribution shape, count/rate totals, and parse-fail sentinel consistency | Not a complete JSON Schema validator; no source run/environment cross-check |
| `prepare-submission` | partially implemented | Copies existing environment/run/summary artifacts into a package directory, writes a manifest, and verifies the package | Does not run aggregation, validate source files, perform semantic identity cross-checks, or create reports |
| `validate manifest` | partially implemented | Validates manifest JSON shape and can optionally verify listed file SHA-256 values plus package_hash | Not a complete JSON Schema validator; standalone manifest validation does not check package path identity unless validating a submission package |
| `validate submission` | partially implemented | Validates local package manifest, checks submitter/run path identity, and verifies listed file hashes plus package_hash | No regenerated-summary cross-check and no semantic environment/result/summary validation |
| `validate model` | specified | `model.toml` validation design exists | No implementation |
| `validate model-repo` | specified | one-model repository invariant is defined | No implementation |
| `run` | specified | CLI shape and runner constraints exist | No implementation |
| `aggregate` | partially implemented | Reads one result JSONL and writes one single-run `summary.json` | No sharded input, multi-run aggregation, summary.md generation, report generation, or manifest writing |
| `verify-integrity` | partially implemented | Verifies local `manifest.json`, submitter/run path identity, listed file hashes, and canonical package_hash inside one package directory | No regenerated-summary cross-check, no signature or ledger support |
| `report` | specified | report output role is defined | No implementation |
| `collect` | specified | convenience command policy exists | No implementation |

## Implemented item validation scope

`validate items` currently checks:

```text
file existence
JSONL parseability
line is JSON object
selected top-level required fields
selected blank required fields
empty expected_full_texts
empty accepted_fills
segments.length == blanks.length + 1
duplicate blank_id
duplicate blank position
positions consecutive from 1
depends_on references already-seen blank_id
duplicate normalized fill across accepted/near_miss/known_wrong
duplicate item_id inside dataset
duplicate variant_id inside dataset
```

Current output:

```text
JSON object with status/errors/warnings/info
exit code 1 when errors exist
```

Current item tests cover:

```text
smoke_v0 passes
valid item fixture passes
invalid item fixtures fail with expected metadata codes
fixture expected codes are registered in docs/error_codes.md
validation output contract shape for pass/fail
```

## Implemented result validation scope

`validate results` currently checks:

```text
file existence
JSONL parseability
line is JSON object
selected required result fields
required prompt/parser/generation condition fields
v0 extraction_mode support
support_mode zero with f_shot consistency
blank_results non-empty
duplicate blank_id inside one result record
content_pass and fill_class consistency
near_miss is not content-pass
parse_fail and blank_parse_pass consistency
parse_fail with extracted_fill warning
reserved blank-level format_fail warning
item_strict_pass formula consistency
duplicate result identity tuple
```

Current result tests cover:

```text
valid result fixture passes
invalid result fixtures fail with expected metadata codes
result fixture expected codes are registered in docs/error_codes.md
validation output contract shape for pass/fail
```

## Implemented summary aggregation scope

`aggregate` currently supports:

```text
one result JSONL input
one summary JSON output
overall content/instruction/format/strict/parse-fail rates
average latency over numeric latency_ms values
one or more blank-level groups
array-form fill_distribution
repeated fills counted without deduplication
parse failures represented with fill_key = __PARSE_FAIL__
Shannon entropy over fill counts
```

Current aggregation limitations:

```text
no sharded input
no multi-run aggregation
no exclusion filters
no summary.md generation
no report generation
no manifest writing
no source run.jsonl validation before aggregation
```

Current aggregation tests cover:

```text
repeated fills are counted without deduplication
overall pass/fail/parse-fail/latency rates are computed
blank group fill_distribution counts and rates are computed
parse failures use the sentinel fill key
entropy and top-fill fields are computed for fixture data
```

## Implemented summary validation scope

`validate summary` currently checks:

```text
file existence
summary JSON parseability
summary JSON is an object
selected top-level required fields
groups is a non-empty array
selected group required fields
fill_distribution is an array, not an object
selected fill_distribution required fields
fill_distribution count total equals group n_trials
fill_distribution rate total equals 1.0
parse_fail entries use extracted_fill null and fill_key __PARSE_FAIL__
```

Current summary validation limitations:

```text
not a complete JSON Schema validator
no source run.jsonl cross-check
no environment.json identity cross-check
no manifest/package cross-check
```

Current summary validation tests cover:

```text
valid summary fixtures pass
invalid summary fixtures fail with expected metadata codes
summary fixture expected codes are registered in docs/error_codes.md
```

## Implemented manifest validation and integrity scope

`validate manifest`, `validate submission`, and `verify-integrity` currently check:

```text
file existence
manifest JSON parseability
manifest JSON is an object
selected top-level required manifest fields
hash_algorithm is sha256
package_hash has sha256:<64 lowercase hex> form
files is a non-empty array
selected file entry required fields
file paths are safe relative POSIX-style paths
manifest.json is not listed inside its own v0 manifest file set
sha256 fields are 64 lowercase hex characters
size_bytes is non-negative integer or null when present
each listed file exists inside the package directory
each listed file is a regular file
each listed file SHA-256 matches raw file bytes
package_hash matches the canonical v0 package hash calculation
submitter_id matches the parent directory name for submission-package validation
run_id matches the package directory name for submission-package validation
```

Current manifest/integrity limitations:

```text
not a complete JSON Schema validator
no environment/result/summary identity cross-check
no regenerated-summary cross-check
no signature verification
no ledger anchoring
```

Current manifest validation tests cover:

```text
valid temporary package manifest passes file verification
submission path identity passes when parent/run directory match
submission path identity mismatch fails
wrong listed file hash fails
wrong package_hash fails when file hashes match
path traversal fails
missing manifest.json fails for a submission package
```

## Implemented prepare-submission scope

`prepare-submission` currently supports:

```text
copy existing environment.json into output package directory
copy existing run.jsonl into output package directory
copy existing summary.json into output package directory
optionally copy existing summary.md into output package directory
write manifest.json by default
compute listed file SHA-256 values over raw bytes
compute canonical v0 package_hash
verify the package manifest after writing it
reject non-empty output directories unless --overwrite is passed
allow --no-write-manifest for scratch packaging
```

Current prepare-submission limitations:

```text
does not run or validate aggregate before packaging
does not validate source environment/run/summary artifacts before copy
does not check environment/result/summary identity consistency
does not regenerate summary.json from run.jsonl
does not produce report files
```

Current prepare-submission tests cover:

```text
copies files and writes a manifest that verifies
rejects non-empty output directory without overwrite
can skip manifest writing for scratch use
```

## Defined but not fully implemented in item validation

| Requirement | Status | Notes |
|---|---|---|
| Full `schemas/item.schema.json` validation | partially implemented | Current validator is schema-like, not full JSON Schema |
| All enum/pattern/type constraints | partially implemented | Some required/type/minItems-like checks only |
| warning for `missing_expected_error_patterns` | specified | Not implemented |
| `not_equivalent_variant_aggregation` warning | specified | Not implemented |
| richer normalized fill policy | partially specified | Current implementation uses `strip()` only |
| fixture expected-code registry check against `docs/error_codes.md` | implemented | Tests verify fixture expected codes are registered in docs/error_codes.md |

## Defined but not fully implemented in result validation

| Requirement | Status | Notes |
|---|---|---|
| Full `schemas/result.schema.json` validation | partially implemented | Current validator is schema-like, not full JSON Schema |
| Generation config canonical hash validation | specified | Not implemented |
| Complete schema enum/type validation | partially implemented | Only selected checks are implemented |
| Sharded run JSONL validation | specified | Not implemented |
| Cross-file environment/result/summary consistency | specified | Not implemented |

## Defined but not fully implemented in summary validation

| Requirement | Status | Notes |
|---|---|---|
| Full `schemas/summary.schema.json` validation | partially implemented | Current validator is schema-like, not full JSON Schema |
| Source `run.jsonl` identity and rate cross-check | specified | Not implemented |
| `environment.json` identity cross-check | specified | Not implemented |
| Summary artifact/package validation | specified | Not implemented; belongs to submission or manifest validation |

## Defined but not fully implemented in manifest and submission validation

| Requirement | Status | Notes |
|---|---|---|
| Full `schemas/manifest.schema.json` validation | partially implemented | Current validator is schema-like, not full JSON Schema |
| Manifest generation | partially implemented | Implemented through `prepare-submission`, but no standalone `write-manifest` command |
| `submitter_id` / `run_id` path identity check | partially implemented | Implemented for `validate submission` and `verify-integrity`; not applied to standalone `validate manifest` |
| Cross-file environment/result/summary consistency | specified | Not implemented |
| Regenerate summary from run file and compare | specified | Not implemented |
| Signature / ledger optional artifacts | deferred | Not part of v0 core |

## Data and schema status

| Area | Status | Current state | Gap |
|---|---|---|---|
| Item schema | specified | `schemas/item.schema.json` exists | Full runtime validation not implemented |
| Result schema | partially implemented | `schemas/result.schema.json` exists and includes `known_wrong` fill class | Full runtime schema validation not implemented |
| Environment schema | specified | `schemas/environment.schema.json` exists | No environment validator |
| Summary schema | partially implemented | `schemas/summary.schema.json` exists; summary aggregation and validation cores exist | Full runtime schema validation and source cross-check not implemented |
| Manifest schema | partially implemented | `schemas/manifest.schema.json` exists; manifest validation and local integrity verification cores exist | Full runtime schema validation and cross-file checks not implemented |
| Model schema | specified | `schemas/model.schema.json` exists | No TOML parser/validator |
| Validation output schema | specified | `schemas/validation_output.schema.json` exists | No JSON Schema execution test yet |
| smoke dataset | implemented as data | `datasets/smoke_v0/items.jsonl` exists and is covered by tests | Only one item; not broad evaluation data |
| reference example package | specified fixture | `examples/smoke_v0` exists | Hash verification is implemented; regenerated-summary verification is not |
| model repository skeleton | specified template | `examples/model_repository` exists | No copier or scaffold command |

## Parser, scoring, and result-record status

| Area | Status | Defined behavior | Current state / gap |
|---|---|---|---|
| raw output preservation | partially implemented | Result records should preserve `raw_output` | Pure parser/scorer and result-record helper preserve it |
| normalization | partially implemented | v0 minimal normalization is intended | Implements newline normalization and trim only |
| exact full-text extraction | partially implemented | v0 extraction mode | Implemented in pure parser/scorer function and fixture-tested |
| segment extraction | partially implemented | v0 extraction mode | Implemented for simple ordered segment extraction and fixture-tested |
| fallback extraction | deferred | Not in MVP | No implementation, intentionally |
| fill classification | partially implemented | accepted / near_miss / known_wrong / wrong / parse_fail | Implemented and fixture-tested for initial cases |
| strict-pass formula | partially implemented | `instruction_following_pass and item_format_pass and all content_pass` | Implemented in pure function and result validator checks consistency |
| result-record assembly | partially implemented | parser/scorer output plus run/model/prompt/generation metadata | Implemented as a pure helper; not yet JSONL writer or runner-integrated |
| parser/scorer CLI surface | specified | future result generation should use parser/scorer | No run command or model backend integration |
| repeated fill counting | implemented | Do not deduplicate repeated fills | Implemented in single-run aggregation |

Current parser/scorer tests cover:

```text
accepted exact full-text
accepted segment extraction
near_miss classification
known_wrong classification
generic wrong classification
instruction-wrapper parse failure
segment parse failure
```

Current result-record tests cover:

```text
required result fields are present
parser/scorer output is preserved in the assembled record
missing required metadata raises an error
```

## Aggregation and reporting status

| Area | Status | Defined behavior | Gap |
|---|---|---|---|
| summary shape | partially implemented | array-form `fill_distribution` with `fill_key` | Implemented for single-run summary JSON; no full schema execution or source cross-check |
| parse-fail sentinel | implemented | `__PARSE_FAIL__` | Implemented in aggregation and summary validation |
| grouping keys | partially implemented | model/dataset/item/blank/prompt/parser/generation keys | Implemented for single-run aggregation; no sharded or multi-run grouping |
| repeated fill counting | implemented | Count every occurrence | Implemented and tested in aggregation |
| report files | specified | `reports/run_index.csv`, `blank_fills.csv`, etc. | No report generator |
| main CI report regeneration | specified | regenerate after merge | No implementation |

## Integrity status

| Area | Status | Defined behavior | Gap |
|---|---|---|---|
| file hash | implemented | SHA-256 over raw file bytes | Used for local manifest verification and prepare-submission |
| package hash | implemented | canonical compact UTF-8 JSON over selected fields | Used for verification and prepare-submission |
| manifest schema | partially implemented | `schemas/manifest.schema.json` | Schema-like validator exists; no full JSON Schema execution |
| manifest generation | partially implemented | Write manifest for prepared submission package | No standalone manifest generation command |
| manifest verification | partially implemented | verify per-file and package hash | Implemented for local package directory; no cross-file semantic checks |
| model authentication | deferred / out of scope | Explicitly not provided | No implementation by design |
| execution attestation | deferred / out of scope | Explicitly not provided | No implementation by design |

## Model repository and submission workflow status

| Area | Status | Defined behavior | Gap |
|---|---|---|---|
| local submission packaging | partially implemented | create local package from existing artifacts | No source validation or semantic identity cross-check |
| one model repository rule | specified | one repo = one model identity | No validator |
| `model.toml` | specified | schema exists | No TOML validation implementation |
| submitter identity | partially implemented | manifest must match local submission package path | No PR-author enforcement implementation |
| run ID | specified | dataset + UTC timestamp + random suffix | No generator implementation |
| result PR scope | specified | one new submission package only | No CI path classifier implementation |
| PR author check | specified | submitter_id should match PR author for normal public PR | No CI implementation |
| main CI report update | specified | regenerate reports after merge | No implementation |

## CI status

| Area | Status | Current state | Gap |
|---|---|---|---|
| unit test workflow | implemented | `.github/workflows/ci.yml` runs unittest | Recheck after latest prepare-submission and path-identity changes |
| item fixture regression | implemented | unittest checks valid/invalid item fixtures | No full schema validator test |
| parser fixture regression | implemented | unittest checks parser fixtures against pure parser/scorer output | No result schema validation yet |
| result-record assembly regression | implemented | unittest checks required fields, preserved parser output, and missing metadata error | No result schema execution test yet |
| result validation regression | implemented | unittest checks valid/invalid result fixtures and expected codes | No full JSON Schema validation yet |
| summary aggregation regression | implemented | unittest checks repeated fills, rates, sentinel parse failures, entropy, and top fill fields | Single-run fixture only |
| summary validation regression | implemented | unittest checks valid/invalid summary fixtures and expected codes | No full JSON Schema validation or source cross-check |
| manifest validation regression | implemented | unittest checks valid package verification, wrong file hash, wrong package hash, path traversal, missing manifest, and submission path identity | No full JSON Schema validation or cross-file semantic check |
| prepare-submission regression | implemented | unittest checks package copy, manifest verification, non-empty output rejection, and manifest skip mode | No source validation or semantic identity cross-check |
| expected error-code registry regression | implemented | unittest checks fixture expected codes are registered in docs/error_codes.md | Applies to item, result, and summary fixtures; manifest tests use direct assertions |
| validation output contract regression | partially implemented | Tests check `status/errors/warnings/info` shape without JSON Schema execution | No schema execution test yet |
| changed-path PR classification | specified | CI policy defines it | No implementation |
| result PR restrictions | specified | CI policy defines it | No implementation |
| report regeneration on main | specified | CI policy defines it | No implementation |
