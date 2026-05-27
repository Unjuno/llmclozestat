# Implementation Plan

This document defines the recommended implementation order for `llmclozestat`.

The goal is to avoid implementing convenience workflows before the underlying data format, validation, parser, summary, and integrity layers are stable.

## Principle

Implement from the inside out:

```text
schemas
  -> validators
  -> parser/scorer
  -> aggregation
  -> manifest integrity
  -> runner
  -> collect convenience command
  -> CI workflow
```

Do not start with the long-running worker or PR automation. Those depend on the lower layers being reliable.

## Phase 0: documentation and schema baseline

Status: complete as implementation specification; not yet implemented.

Scope:

- item schema;
- result schema;
- environment schema;
- summary schema;
- manifest schema;
- model repository schema;
- smoke dataset;
- reference example package;
- model repository skeleton;
- operating model;
- validation policy;
- CI policy.

Exit criteria:

```text
[x] schemas are present
[x] docs define result format and scoring policy
[x] smoke dataset exists
[x] examples/smoke_v0 exists
[x] examples/model_repository exists
[x] README links the main docs
```

## Phase 1: item loading and item validation

Implement first because every later stage depends on trustworthy item data.

Scope:

- load JSONL item files;
- validate each line against `schemas/item.schema.json`;
- perform item cross-field checks;
- report errors with file path and line number;
- support `llmclozestat validate items`.

Required checks:

- JSONL parseability;
- schema validity;
- `segments.length == blanks.length + 1`;
- blank IDs unique;
- blank positions consecutive from 1;
- non-empty `accepted_fills`;
- `claim_scope` present;
- item IDs unique inside dataset.

Exit criteria:

```text
[ ] smoke_v0 passes item validation
[ ] intentionally broken fixture fails clearly
[ ] validation output is machine-readable enough for CI
```

## Phase 2: deterministic parser and scorer

Implement parser/scorer before any model runner.

Scope:

- normalize output with v0 minimal normalization;
- check exact full-text match;
- perform segment-based extraction;
- classify fills as accepted / near_miss / known_wrong / other / parse_fail;
- compute blank-level and item-level fields;
- preserve raw output exactly.

MVP extraction modes:

```text
exact_full_text
segment
```

Do not implement fallback extraction in MVP.

Strict-pass rule:

```text
item_strict_pass =
  instruction_following_pass
  and item_format_pass
  and all blank content_pass
```

Exit criteria:

```text
[ ] accepted fill passes
[ ] near_miss does not content-pass
[ ] known_wrong is classified but does not content-pass
[ ] instruction prefix causes instruction_following_pass=false
[ ] raw_output is preserved
[ ] parse_fail behavior is deterministic
```

## Phase 3: result record writing and result validation

Once parser/scorer exists, implement result JSONL writing.

Scope:

- write one result record per trial;
- validate against `schemas/result.schema.json`;
- support `llmclozestat validate results`;
- support sharded input later, but single JSONL is enough for first implementation.

Required metadata:

- submitter_id;
- run_id;
- dataset_id;
- model_id;
- prompt_template_id;
- prompt_language;
- support_mode;
- f_shot;
- blank_rendering;
- extraction_mode;
- generation_config or generation_config_hash.

Exit criteria:

```text
[ ] examples/smoke_v0/run.jsonl validates
[ ] result records preserve prompt/parser/generation condition fields
[ ] result validation catches inconsistent content_pass/fill_class
```

## Phase 4: aggregation and summary regeneration

Aggregation should be implemented before manifest packaging because summaries are package artifacts.

Scope:

- read result JSONL;
- group by stable condition keys;
- count repeated fills without deduplication;
- compute pass rates;
- compute fill distributions;
- write `summary.json`;
- write `summary.md`;
- support `llmclozestat aggregate`;
- support `llmclozestat validate summary`.

Important grouping keys:

- model_id;
- dataset_id;
- item_id;
- blank_id;
- prompt_template_id;
- prompt_language;
- support_mode;
- f_shot;
- blank_rendering;
- extraction_mode;
- generation_config_hash.

Exit criteria:

```text
[ ] examples/smoke_v0/summary.json can be regenerated from run.jsonl
[ ] repeated fills are counted
[ ] near_miss is not counted as content_pass
[ ] summary validation fails if counts are edited incorrectly
```

## Phase 5: manifest generation and integrity verification

Package integrity should be implemented before PR or CI automation.

Scope:

- prepare `submissions/<submitter_id>/<run_id>/`;
- copy or generate required files;
- generate `manifest.json`;
- validate against `schemas/manifest.schema.json`;
- verify per-file hashes;
- verify deterministic package hash;
- support `llmclozestat prepare-submission`;
- support `llmclozestat verify-integrity`;
- support `llmclozestat validate manifest` and `validate submission`.

Boundary:

```text
manifest = package-level tamper detection
manifest != model authentication
```

Exit criteria:

```text
[ ] reference example manifest verifies
[ ] modifying any listed file causes verification failure
[ ] missing manifest is ERROR for publishable submissions
[ ] manifest never claims model execution authenticity
```

## Phase 6: model repository validation

After package validation exists, implement model-repository validation.

Scope:

- parse `model.toml`;
- validate parsed object against `schemas/model.schema.json`;
- support `llmclozestat validate model`;
- support `llmclozestat validate model-repo`;
- enforce one-model repository invariant when `model.toml` exists.

Required invariant:

```text
environment.json.model_id == model.toml.model.model_id
all result records model_id == model.toml.model.model_id
summary.json.model_id == model.toml.model.model_id
```

Exit criteria:

```text
[ ] examples/model_repository/model.toml validates
[ ] model-repo validation catches mixed model_id submissions
[ ] changing model.toml model_id with existing submissions is reported
```

## Phase 7: local OpenAI-compatible runner

Only implement model execution after parser, result, summary, and manifest layers are reliable.

Scope:

- support local OpenAI-compatible `/v1/chat/completions` or `/v1/responses` equivalent as selected by implementation;
- allow LM Studio-style local endpoints;
- record backend/provider metadata;
- render prompt from item and prompt template;
- run trials;
- pass raw output to parser/scorer;
- write JSONL incrementally.

MVP constraints:

```text
one command invocation = one model_id
one prompt condition
one dataset
single-process execution
```

No PR automation yet.

Exit criteria:

```text
[ ] can run smoke_v0 against a local OpenAI-compatible endpoint
[ ] records raw_output and parsed blank results
[ ] handles provider errors without writing fake successful records
[ ] writes valid run.jsonl
```

## Phase 8: collect command

`collect` is a convenience command. It should not exist until lower layers work.

Scope:

```text
run
  -> aggregate
  -> prepare-submission
  -> write manifest
  -> validate submission
```

Recommended MVP shape:

```bash
llmclozestat collect \
  --dataset datasets/pinned/smoke_v0/items.jsonl \
  --provider openai-compatible \
  --base-url http://localhost:1234/v1 \
  --model example-model-q4km \
  --submitter-id your-name \
  --target-trials 20 \
  --prepare-submission \
  --write-manifest \
  --validate
```

MVP constraints:

```text
one collect command = one model = one run = one submission
```

Exit criteria:

```text
[ ] collect produces a valid submission package
[ ] collect refuses to mix multiple model IDs
[ ] collect does not push by default
[ ] collect does not update reports by default
```

## Phase 9: CI workflow

Implement CI after local validators exist.

Scope:

- JSON / JSONL parse checks;
- TOML parse checks;
- schema validation;
- item validation;
- result validation;
- summary validation;
- manifest validation;
- submission validation;
- model repository validation where `model.toml` exists;
- result PR path restrictions.

MVP CI:

```text
pull_request:
  validate only

push to main:
  validate all
```

Report regeneration can remain manual at first.

Exit criteria:

```text
[ ] broken item PR fails
[ ] broken manifest PR fails
[ ] mixed-model submission PR fails in model repo
[ ] result PR that modifies reports fails or warns according to policy
```

## Phase 10: report generation and optional main-branch report updates

After CI validation is stable, add derived report generation.

Scope:

- generate `reports/run_index.csv`;
- generate `reports/blank_fills.csv`;
- generate `reports/fill_distribution.csv`;
- generate `reports/position_pass_rate.csv`;
- generate `reports/metadata.json`.

Policy:

```text
raw submissions are source of truth
reports are derived
result PRs should not update reports
```

Exit criteria:

```text
[ ] reports regenerate from merged submissions
[ ] reports include source commit metadata
[ ] reports can be deleted and regenerated
```

## Explicitly out of scope for early implementation

Do not implement these before the above layers are stable:

- automatic repository creation;
- automatic fork creation;
- automatic PR creation;
- long-running multi-process worker;
- same-run parallel execution;
- distributed task leasing;
- model execution authentication;
- execution attestation;
- hosted web dashboard;
- global leaderboard.

## Recommended first implementation target

The first useful implementation target is:

```text
validate items
  + parser/scorer fixture tests
  + aggregate examples/smoke_v0/run.jsonl
  + verify examples/smoke_v0/manifest.json
```

This creates the foundation for every later command.
