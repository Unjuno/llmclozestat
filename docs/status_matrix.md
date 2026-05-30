# Status Matrix

This document separates the current state of `llmclozestat` into implemented, partially implemented, specified, deferred, and undefined areas. It is a working status document, not a roadmap promise.

## Summary

Current stage:

```text
v0.0 smoke-test phase
```

Implemented CLI surface:

```text
llmclozestat version
llmclozestat run --config <run.toml>
llmclozestat validate items --dataset <items.jsonl>
llmclozestat validate environment --input <environment.json>
llmclozestat validate results --input <run.jsonl>
llmclozestat aggregate --input <run.jsonl> --out <summary.json> [--no-validate-input]
llmclozestat validate summary --input <summary.json>
llmclozestat prepare-submission --submitter-id <id> --run-id <id> --environment-json <environment.json> --run-jsonl <run.jsonl> --summary-json <summary.json> --out-dir <submission-dir>
llmclozestat validate manifest --input <manifest.json> [--verify-files]
llmclozestat validate submission --path <submission-package-dir>
llmclozestat verify-integrity --path <submission-package-dir>
llmclozestat validate model --input <model.toml>
llmclozestat validate model-repo --path <model-repository-dir>
llmclozestat report --submissions-dir <submissions-dir> --out-dir <reports-dir>
```

Implemented library core:

```text
item JSONL validation core
environment JSON validation core
strict-v0 parser/scorer pure function core
result-record assembly helper
backend failure result-record helper
result JSONL validation core
summary aggregation helper
summary JSON validation core
manifest JSON validation helper
file SHA-256 helper
canonical package hash helper
local manifest integrity verification helper
prepare-submission package helper
source artifact validation before packaging
submission path identity checker
submission artifact manifest-inclusion checker
submission semantic identity checker
submission regenerated-summary checker
model.toml validation helper
model repository validation helper
minimal report generation helper
minimal OpenAI-compatible runner helper
```

Current executable pipelines:

```text
manual artifact pipeline:
  environment.json
  run.jsonl
    -> validate environment
    -> validate results
    -> aggregate summary.json
    -> validate summary
    -> prepare-submission
    -> validate manifest / validate submission / verify-integrity

run-config pipeline:
  run.toml + model.toml + dataset items.jsonl
    -> run
    -> environment.json + run.jsonl + summary.json + manifest.json
    -> validate submission / verify-integrity

report pipeline:
  submissions/*/*/summary.json
    -> report
    -> reports/run_index.csv + reports/blank_fills.csv
```

The implemented commands are still narrow MVP implementations. They are not a complete benchmark platform.

## Status terms

| Status | Meaning |
|---|---|
| `implemented` | Code exists and is covered by tests or direct CLI surface |
| `partially implemented` | Some code exists, but it does not cover the full documented contract |
| `specified` | Documentation/schema/fixtures define intended behavior, but no implementation exists |
| `partially specified` | Some design exists, but important choices remain open |
| `undefined` | No stable policy exists yet |
| `deferred` | Intentionally not part of the current phase |

## Command surface

| Area | Status | Evidence / current behavior | Gap |
|---|---|---|---|
| `version` | implemented | Prints package version | None for v0 |
| `run` | partially implemented | Reads TOML config, validates model/dataset metadata, calls an OpenAI-compatible chat-completions backend, writes `environment.json`, `run.jsonl`, `summary.json`, and `manifest.json`, and records backend call failures as trial-level parse-fail observations | No sharded output, retry policy, resume policy, or execution attestation |
| `validate items` | partially implemented | Validates JSONL parse, required/minItems-like item fields, selected cross-field checks, duplicate item/variant IDs | Not a complete JSON Schema validator |
| `validate environment` | partially implemented | Validates environment JSON parse, required fields, support mode, parser config, and generation config | Not a complete JSON Schema validator; no generation_config_hash recomputation |
| `validate results` | partially implemented | Validates JSONL parse, required result fields, condition fields, and selected scoring consistency rules | Not a complete JSON Schema validator; no sharded input |
| `aggregate` | partially implemented | Validates input by default, reads one result JSONL, and writes one single-run `summary.json` | No sharded input, multi-run aggregation, exclusion filters, summary.md generation, report generation, or manifest writing |
| `validate summary` | partially implemented | Validates summary JSON parse, required fields, fill distribution shape, count/rate totals, and parse-fail sentinel consistency | No source run/environment cross-check inside standalone summary validator |
| `prepare-submission` | partially implemented | Validates source environment/run/summary artifacts, copies them into a package directory, writes a manifest, and verifies the package | Does not run aggregation, regenerate summary, or create reports |
| `validate manifest` | partially implemented | Validates manifest JSON shape and can optionally verify listed file SHA-256 values plus package_hash | Standalone manifest validation does not check submission package path identity |
| `validate submission` | partially implemented | Validates local package manifest, checks submitter/run path identity, requires required artifacts in manifest, verifies hashes, checks environment/run/summary identity, and checks regenerated summary consistency | No signature or ledger support |
| `verify-integrity` | partially implemented | Same package-level integrity, semantic identity, and regenerated-summary verification as `validate submission` | No signature or ledger support |
| `validate model` | partially implemented | Parses TOML and validates selected `model.toml` fields and policy fields | Not a complete JSON Schema validator |
| `validate model-repo` | partially implemented | Validates model metadata and one-model repository consistency for local submissions | No PR-author enforcement or full CI policy integration |
| `report` | partially implemented | Generates `run_index.csv` and `blank_fills.csv` from submission summaries | No derived metadata.json, position-level report, commit metadata, or automatic main-branch report refresh |
| `collect` | specified | Convenience command policy exists | No implementation |

## Implemented validation scopes

### Item validation

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

### Environment validation

`validate environment` currently checks:

```text
file existence
JSON parseability
JSON object shape
selected required environment fields
non-empty submitter/run/tool/dataset/model/backend/provider/prompt fields
prompt_language length
support_mode enum
zero support_mode requires f_shot = 0
f_shot non-negative integer
parser_config object
parser_config.normalization
parser_config.extraction_modes_enabled non-empty unique supported modes
generation_config object
generation_config.temperature
generation_config.max_tokens
generation_config.top_p
```

Current environment validation limitations:

```text
not a complete JSON Schema validator
no generation_config_hash recomputation
```

### Result validation

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

Backend call failure records are valid result records. They use:

```text
trial_status = backend_error
backend_error.type
backend_error.message
raw_output = ""
normalized_output = ""
extraction_mode = segment
blank-level fill_class = parse_fail
blank-level parse_fail = true
```

### Summary aggregation

`aggregate` currently supports:

```text
input run.jsonl validation by default
explicit --no-validate-input for scratch/debug work
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
no report generation inside aggregate
no manifest writing inside aggregate
```

### Summary validation

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
no source run.jsonl cross-check inside standalone summary validation
```

Submission validation performs regenerated-summary comparison against `run.jsonl`.

### Manifest, submission, and integrity validation

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
required artifacts environment.json/run.jsonl/summary.json are listed in manifest.json
required artifacts exist in the package directory
environment.json, run.jsonl, and summary.json agree on submitter_id/run_id/dataset_id/dataset_sha256/condition_hash/experiment_hash/model_id
summary.json matches a regenerated summary from run.jsonl
```

Current manifest/submission limitations:

```text
not a complete JSON Schema validator
no signature verification
no ledger anchoring
```

### Prepare-submission

`prepare-submission` currently supports:

```text
validate source environment.json by default
validate source run.jsonl by default
validate source summary.json by default
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
allow --no-validate-sources for scratch/debug packaging
```

Current prepare-submission limitations:

```text
does not run aggregate before packaging
does not regenerate summary.json from run.jsonl
does not produce report files
```

### Model validation

`validate model` currently checks:

```text
model.toml file existence
TOML parseability
[model] table presence
selected required model fields
model_id format
selected optional model fields
[policy] table presence
policy.one_model_repo = true
policy.allow_mixed_model_ids is not true
optional default_condition prompt/generation/parser checks
```

### Model repository validation

`validate model-repo` currently checks the local model repository shape enough for MVP use. The intended invariant is:

```text
environment.json.model_id == model.toml.model.model_id
all result records model_id == model.toml.model.model_id
summary.json.model_id == model.toml.model.model_id
```

### Report generation

`report` currently supports:

```text
load submissions/*/*/summary.json
write reports/run_index.csv
write reports/blank_fills.csv
```

Reports are derived artifacts. Raw submissions remain the source of truth.

## Defined but not fully implemented

| Area | Requirement | Status | Notes |
|---|---|---|---|
| Item | Full `schemas/item.schema.json` validation | partially implemented | Current validator is schema-like, not full JSON Schema |
| Item | Warning for `missing_expected_error_patterns` | specified | Not implemented |
| Item | `not_equivalent_variant_aggregation` warning | specified | Not implemented |
| Environment | Full `schemas/environment.schema.json` validation | partially implemented | Current validator is schema-like, not full JSON Schema |
| Environment | Generation config hash recomputation | specified | Not implemented |
| Environment | Backend/provider compatibility checks | deferred | Not part of v0 core |
| Result | Full `schemas/result.schema.json` validation | partially implemented | Current validator is schema-like, not full JSON Schema |
| Result | Generation config canonical hash validation | specified | Not implemented |
| Result | Sharded run JSONL validation | specified | Not implemented |
| Summary | Full `schemas/summary.schema.json` validation | partially implemented | Current validator is schema-like, not full JSON Schema |
| Summary | Standalone source `run.jsonl` rate/count cross-check | specified | Submission validation already performs regenerated-summary checking |
| Manifest/submission | Full `schemas/manifest.schema.json` validation | partially implemented | Current validator is schema-like, not full JSON Schema |
| Manifest/submission | Standalone manifest generation | partially implemented | Implemented through `prepare-submission`, but no standalone `write-manifest` command |
| Manifest/submission | Signature / ledger optional artifacts | deferred | Not part of v0 core |
| Model | Full `schemas/model.schema.json` validation | partially implemented | Current validator is schema-like TOML validation |
| Model repo | Full one-model repository rule | partially implemented | Local validator exists; CI/PR policy integration is not complete |
| Report | Full report suite | partially implemented | Current report command writes `run_index.csv` and `blank_fills.csv` only |
| Collect | end-to-end convenience command | specified | No implementation |
| Run | robust model execution | partially implemented | Minimal OpenAI-compatible runner exists and keeps backend failures; retry/resume/sharding policy is not complete |

## Data and schema status

| Area | Status | Current state | Gap |
|---|---|---|---|
| Item schema | specified | `schemas/item.schema.json` exists | Full runtime validation not implemented |
| Environment schema | partially implemented | `schemas/environment.schema.json` exists; minimal environment validator exists | Full runtime schema validation not implemented |
| Result schema | partially implemented | `schemas/result.schema.json` exists and includes `known_wrong` fill class | Full runtime schema validation not implemented |
| Summary schema | partially implemented | `schemas/summary.schema.json` exists; summary aggregation and validation cores exist | Full runtime schema validation and standalone source cross-check not implemented |
| Manifest schema | partially implemented | `schemas/manifest.schema.json` exists; manifest validation and local integrity/semantic/regeneration verification cores exist | Full runtime schema validation not implemented |
| Model schema | partially implemented | `schemas/model.schema.json` exists; minimal TOML validator exists | Full runtime schema validation not implemented |
| Validation output schema | specified | `schemas/validation_output.schema.json` exists | No JSON Schema execution test yet |
| smoke dataset | implemented as data | `datasets/smoke_v0/items.jsonl` exists and is covered by tests | Only one item; not broad evaluation data |
| reference example package | specified fixture | `examples/smoke_v0` exists | Hash, semantic identity, and regenerated-summary verification exist |
| model repository skeleton | specified template | `examples/model_repository` exists | No copier or scaffold command |

## Parser, scoring, and result-record status

| Area | Status | Defined behavior | Current state / gap |
|---|---|---|---|
| raw output preservation | partially implemented | Result records should preserve `raw_output` | Pure parser/scorer and result-record helper preserve it for successful backend calls; backend failure records intentionally use empty raw output plus `backend_error` metadata |
| normalization | partially implemented | v0 minimal normalization is intended | Implements newline normalization and trim only |
| exact full-text extraction | partially implemented | v0 extraction mode | Implemented in pure parser/scorer function and fixture-tested |
| segment extraction | partially implemented | v0 extraction mode | Implemented for simple ordered segment extraction and fixture-tested |
| fallback extraction | deferred | Not in MVP | No implementation, intentionally |
| fill classification | partially implemented | accepted / near_miss / known_wrong / wrong / parse_fail | Implemented and fixture-tested for initial cases |
| strict-pass formula | partially implemented | `instruction_following_pass and item_format_pass and all content_pass` | Implemented in pure function and result validator checks consistency |
| result-record assembly | partially implemented | parser/scorer output plus run/model/prompt/generation metadata | Implemented as a pure helper and used by the minimal runner |
| backend failure record assembly | partially implemented | backend failures should remain in the denominator | Implemented as trial-level parse-fail records |
| repeated fill counting | implemented | Do not deduplicate repeated fills | Implemented in single-run aggregation |

## Integrity status

| Area | Status | Defined behavior | Gap |
|---|---|---|---|
| file hash | implemented | SHA-256 over raw file bytes | Used for local manifest verification and prepare-submission |
| package hash | implemented | canonical compact UTF-8 JSON over selected fields | Used for verification and prepare-submission |
| manifest generation | partially implemented | Write manifest for prepared submission package and runner output | No standalone manifest generation command |
| manifest verification | partially implemented | verify per-file and package hash | Implemented for local package directory |
| semantic identity verification | partially implemented | environment/run/summary identity fields must agree | Implemented for local submission package validation |
| regenerated-summary verification | partially implemented | summary.json must match regenerated summary from run.jsonl | Implemented for local submission package validation |
| model authentication | deferred / out of scope | Explicitly not provided | No implementation by design |
| execution attestation | deferred / out of scope | Explicitly not provided | No implementation by design |

## Model repository and submission workflow status

| Area | Status | Defined behavior | Gap |
|---|---|---|---|
| local submission packaging | partially implemented | create local package from existing validated artifacts | Packaging does not regenerate summary itself |
| submitter identity | partially implemented | manifest must match local submission package path | No PR-author enforcement implementation |
| run ID | partially implemented | dataset + UTC timestamp + random suffix | Runner can generate one; policy still needs broader tests |
| result PR scope | specified | one new submission package only | No CI path classifier implementation |
| PR author check | specified | submitter_id should match PR author for normal public PR | No CI implementation |
| main CI report update | specified | regenerate reports after merge | No implementation |

## CI status

| Area | Status | Current state | Gap |
|---|---|---|---|
| unit test workflow | implemented | `.github/workflows/ci.yml` runs unittest | Recheck after each command-surface change |
| item fixture regression | implemented | unittest checks valid/invalid item fixtures | No full schema validator test |
| environment validation regression | implemented | unittest checks example environment, missing field, zero/f_shot conflict, duplicate extraction mode, and output contract | No full JSON Schema validation |
| parser fixture regression | implemented | unittest checks parser fixtures against pure parser/scorer output | No result schema validation yet |
| result-record assembly regression | implemented | unittest checks required fields, preserved parser output, identity metadata, missing metadata error, and backend failure record assembly | No result schema execution test yet |
| runner regression | implemented | unittest patches backend calls and checks successful package writing plus backend failure persistence | No live backend test in CI |
| result validation regression | implemented | unittest checks valid/invalid result fixtures and expected codes | No full JSON Schema validation yet |
| summary aggregation regression | implemented | unittest checks repeated fills, rates, sentinel parse failures, entropy, top fill fields, and aggregate CLI input validation | Single-run fixture only |
| summary validation regression | implemented | unittest checks valid/invalid summary fixtures and expected codes | No full JSON Schema validation or standalone source cross-check |
| manifest validation regression | implemented | unittest checks file/package hash, path traversal, missing manifest, path identity, required artifacts, semantic identity, and regenerated-summary mismatch | No full JSON Schema validation |
| prepare-submission regression | implemented | unittest checks package copy, source validation, manifest verification, invalid source rejection, non-empty output rejection, and manifest skip mode | No report generation |
| model validation regression | implemented | unittest coverage exists for minimal model metadata validation | No full schema validation |
| model repository regression | implemented | unittest coverage exists for minimal one-model repository checks | No PR integration |
| report regression | implemented | unittest coverage exists for minimal CSV report generation | No derived metadata report |
| expected error-code registry regression | implemented | unittest checks fixture expected codes are registered in docs/error_codes.md | Applies to item, result, and summary fixtures; manifest/environment tests use direct assertions |
| validation output contract regression | partially implemented | Tests check `status/errors/warnings/info` shape without JSON Schema execution | No schema execution test yet |
| changed-path PR classification | specified | CI policy defines it | No implementation |
| result PR restrictions | specified | CI policy defines it | No implementation |
| report regeneration on main | specified | CI policy defines it | No implementation |
