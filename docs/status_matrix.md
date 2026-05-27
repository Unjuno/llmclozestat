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

Implemented runtime surface:

```text
llmclozestat version
llmclozestat validate items --dataset <items.jsonl>
```

Most other behavior is specified but not implemented.

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
| `validate results` | specified | Result validation design exists | No implementation |
| `validate summary` | specified | Summary validation design exists | No implementation |
| `validate manifest` | specified | Manifest validation design exists | No implementation |
| `validate submission` | specified | Submission validation design exists | No implementation |
| `validate model` | specified | `model.toml` validation design exists | No implementation |
| `validate model-repo` | specified | one-model repository invariant is defined | No implementation |
| `run` | specified | CLI shape and runner constraints exist | No implementation |
| `aggregate` | specified | grouping keys and summary shape exists | No implementation |
| `prepare-submission` | specified | package layout and manifest requirement exist | No implementation |
| `verify-integrity` | specified | canonical package hash is defined | No implementation |
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

Current tests cover:

```text
smoke_v0 passes
valid item fixture passes
invalid item fixtures fail with expected metadata codes
fixture expected codes are registered in docs/error_codes.md
validation output contract shape for pass/fail
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

## Data and schema status

| Area | Status | Current state | Gap |
|---|---|---|---|
| Item schema | specified | `schemas/item.schema.json` exists | Full runtime validation not implemented |
| Result schema | specified | `schemas/result.schema.json` exists | No result validator |
| Environment schema | specified | `schemas/environment.schema.json` exists | No environment validator |
| Summary schema | specified | `schemas/summary.schema.json` exists | No summary validator/regenerator |
| Manifest schema | specified | `schemas/manifest.schema.json` exists | No manifest validator/verifier |
| Model schema | specified | `schemas/model.schema.json` exists | No TOML parser/validator |
| Validation output schema | specified | `schemas/validation_output.schema.json` exists | No JSON Schema execution test yet |
| smoke dataset | implemented as data | `datasets/smoke_v0/items.jsonl` exists and is covered by tests | Only one item; not broad evaluation data |
| reference example package | specified fixture | `examples/smoke_v0` exists | Not verified by implemented manifest/summary code |
| model repository skeleton | specified template | `examples/model_repository` exists | No copier or scaffold command |

## Parser and scoring status

| Area | Status | Defined behavior | Gap |
|---|---|---|---|
| raw output preservation | specified | Result records should preserve `raw_output` | No runner/parser implementation |
| normalization | specified | v0 minimal normalization is intended | No implementation |
| exact full-text extraction | specified | v0 extraction mode | No implementation |
| segment extraction | specified | v0 extraction mode | No implementation |
| fallback extraction | deferred | Not in MVP | No implementation, intentionally |
| fill classification | specified | accepted / near_miss / wrong / parse_fail etc. | No implementation |
| strict-pass formula | specified | `instruction_following_pass and item_format_pass and all content_pass` | No implementation |
| repeated fill counting | specified | Do not deduplicate repeated fills | No aggregation implementation |

## Aggregation and reporting status

| Area | Status | Defined behavior | Gap |
|---|---|---|---|
| summary shape | specified | array-form `fill_distribution` with `fill_key` | No generator/validator |
| parse-fail sentinel | specified | `__PARSE_FAIL__` | No generator/validator |
| grouping keys | specified | model/dataset/item/blank/prompt/parser/generation keys | No aggregator |
| repeated fill counting | specified | count every occurrence | No aggregator |
| report files | specified | `reports/run_index.csv`, `blank_fills.csv`, etc. | No report generator |
| main CI report regeneration | specified | regenerate after merge | No implementation |

## Integrity status

| Area | Status | Defined behavior | Gap |
|---|---|---|---|
| file hash | specified | SHA-256 over raw file bytes | No implementation |
| package hash | specified | canonical compact UTF-8 JSON over selected fields | No implementation |
| manifest schema | specified | `schemas/manifest.schema.json` | No validator |
| manifest verification | specified | verify per-file and package hash | No implementation |
| model authentication | deferred / out of scope | Explicitly not provided | No implementation by design |
| execution attestation | deferred / out of scope | Explicitly not provided | No implementation by design |

## Model repository and submission workflow status

| Area | Status | Defined behavior | Gap |
|---|---|---|---|
| one model repository rule | specified | one repo = one model identity | No validator |
| `model.toml` | specified | schema exists | No TOML validation implementation |
| submitter identity | specified | lowercase GitHub username slug for normal PRs | No CI enforcement implementation |
| run ID | specified | dataset + UTC timestamp + random suffix | No generator implementation |
| result PR scope | specified | one new submission package only | No CI path classifier implementation |
| PR author check | specified | submitter_id should match PR author for normal public PR | No CI implementation |
| main CI report update | specified | regenerate reports after merge | No implementation |

## CI status

| Area | Status | Current state | Gap |
|---|---|---|---|
| unit test workflow | implemented | `.github/workflows/ci.yml` runs unittest | User visually confirmed no current failures |
| item fixture regression | implemented | unittest checks valid/invalid item fixtures | No full schema validator test |
| expected error-code registry regression | implemented | unittest checks fixture expected codes are registered in docs/error_codes.md | None for current item fixtures |
| validation output contract regression | partially implemented | Tests check `status/errors/warnings/info` shape without JSON Schema execution | No schema execution test yet |
| changed-path PR classification | specified | CI policy defines it | No implementation |
| result PR restrictions | specified | CI policy defines it | No implementation |
| report regeneration on main | specified | CI policy defines it | No implementation |
| manifest verification in CI | specified | CI policy defines it | No implementation |

## Undefined or insufficiently defined areas

These are not blockers for current `validate items`, but they are blockers before later phases.

### Provider contract

Status: partially specified.

Known need:

```text
openai-compatible chat endpoint request shape
response text extraction path
error handling
retry policy
timeout policy
rate limit handling
backend metadata fields
```

Until this is defined, `run` should not be implemented beyond a narrow local prototype.

### Full JSON Schema execution strategy

Status: partially specified.

Open choice:

```text
add jsonschema dependency
or keep a custom validator
or use a CLI schema checker in CI only
```

Current implementation is schema-like, not complete JSON Schema execution.

### Normalization policy

Status: partially specified.

Current item validation uses `strip()` for normalized fill duplicate detection. Parser/scorer normalization is not implemented.

Needs definition before parser/scorer:

```text
Unicode normalization
whitespace handling
Japanese punctuation handling
case handling for English
whether normalization differs for extraction vs classification
```

### Validation output schema execution

Status: specified but not fully enforced.

Current output contract has a schema:

```text
schemas/validation_output.schema.json
```

The CLI currently emits the required top-level fields:

```text
status/errors/warnings/info
```

But tests do not yet run a JSON Schema validator against this schema.

### Resume / overwrite behavior

Status: partially specified.

Policy says publishable submissions should not be silently overwritten. Exact local scratch resume behavior is not yet defined.

### Dataset contribution lifecycle

Status: partially specified.

Existing docs define item policy and validation, but not the full contributor workflow for adding new datasets or probes.

Needs later:

```text
new dataset PR flow
review checklist
minimum metadata
translation/equivalence review
versioning policy
```

## Explicitly deferred areas

These should not be implemented in the current phase:

```text
automatic repository creation
automatic fork creation
automatic PR creation
long-running multi-process worker
same-run parallel execution
distributed task leasing
model execution authentication
execution attestation
hosted web dashboard
global leaderboard
```

## Current implementation boundary

The current executable boundary is:

```text
local CLI can validate item JSONL enough to protect the smoke dataset and item fixtures
```

The current non-executable design boundary is:

```text
result format
parser/scoring rules
summary format
manifest integrity
model repository workflow
submitter/run identity
CI policy
collection workflow
```

Do not present the non-executable design boundary as working CLI behavior.

## Recommended next work

Before moving to parser/scorer, finish Phase 1 cleanup:

```text
1. Decide whether to introduce jsonschema for full item.schema.json validation.
2. Implement warnings for missing_expected_error_patterns if needed before broader datasets.
```

Then move to Phase 2:

```text
parser/scorer fixture design
raw_output preservation tests
exact_full_text extraction
segment extraction
fill_class/content_pass consistency
```
