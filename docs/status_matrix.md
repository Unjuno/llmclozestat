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
```

Implemented library core:

```text
item JSONL validation core
strict-v0 parser/scorer pure function core
result-record assembly helper
result JSONL validation core
```

Most command-level behavior beyond item/result validation is still specified but not implemented.

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

## Data and schema status

| Area | Status | Current state | Gap |
|---|---|---|---|
| Item schema | specified | `schemas/item.schema.json` exists | Full runtime validation not implemented |
| Result schema | partially implemented | `schemas/result.schema.json` exists and includes `known_wrong` fill class | Full runtime schema validation not implemented |
| Environment schema | specified | `schemas/environment.schema.json` exists | No environment validator |
| Summary schema | specified | `schemas/summary.schema.json` exists | No summary validator/regenerator |
| Manifest schema | specified | `schemas/manifest.schema.json` | No manifest validator/verifier |
| Model schema | specified | `schemas/model.schema.json` exists | No TOML parser/validator |
| Validation output schema | specified | `schemas/validation_output.schema.json` exists | No JSON Schema execution test yet |
| smoke dataset | implemented as data | `datasets/smoke_v0/items.jsonl` exists and is covered by tests | Only one item; not broad evaluation data |
| reference example package | specified fixture | `examples/smoke_v0` exists | Not verified by implemented manifest/summary code |
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
| repeated fill counting | specified | Do not deduplicate repeated fills | No aggregation implementation |

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
| unit test workflow | implemented | `.github/workflows/ci.yml` runs unittest | Recheck after latest result validation changes |
| item fixture regression | implemented | unittest checks valid/invalid item fixtures | No full schema validator test |
| parser fixture regression | implemented | unittest checks parser fixtures against pure parser/scorer output | No result schema validation yet |
| result-record assembly regression | implemented | unittest checks required fields, preserved parser output, and missing metadata error | No result schema execution test yet |
| result validation regression | implemented | unittest checks valid/invalid result fixtures and expected codes | No full JSON Schema validation yet |
| expected error-code registry regression | implemented | unittest checks fixture expected codes are registered in docs/error_codes.md | Applies to item and result fixtures |
| validation output contract regression | partially implemented | Tests check `status/errors/warnings/info` shape without JSON Schema execution | No schema execution test yet |
| changed-path PR classification | specified | CI policy defines it | No implementation |
| result PR restrictions | specified | CI policy defines it | No implementation |
| report regeneration on main | specified | CI policy defines it | No implementation |
| manifest verification in CI | specified | CI policy defines it | No implementation |

## Undefined or insufficiently defined areas

These are not blockers for current `validate items`, `validate results`, pure parser/scorer fixtures, or result-record assembly, but they are blockers before later phases.

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

Current validators are schema-like, not complete JSON Schema execution.

### Normalization policy

Status: partially specified.

The parser/scorer core currently implements only strict v0 minimal normalization:

```text
CRLF/CR -> LF
trim leading/trailing whitespace
```

Needs definition before broader parser/scorer expansion:

```text
Unicode normalization
whitespace collapsing beyond edges
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

The current executable CLI boundary is:

```text
local CLI can validate item JSONL enough to protect the smoke dataset and item fixtures
local CLI can validate result JSONL scoring consistency for initial v0 fixtures
```

The current library-core boundary is:

```text
strict-v0 parser/scorer can parse and score simple one-blank fixture outputs
result-record helper can assemble parser/scorer output with required run metadata
```

The current non-executable design boundary is:

```text
run command
summary generation
manifest integrity
model repository workflow
submitter/run identity enforcement
CI policy beyond unittest
collection workflow
```

Do not present non-executable design boundaries as working CLI behavior.

## Recommended next work

Before expanding runner or collect, finish the next validation layer:

```text
1. Recheck GitHub Actions after validate results changes.
2. Add summary aggregation fixtures.
3. Implement minimal aggregate summary generation.
4. Add validate summary after summary generation is fixture-backed.
```

Do not start model execution yet.
