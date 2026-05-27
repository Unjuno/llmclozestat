# CI Policy

This document defines the intended GitHub Actions / CI responsibilities for `llmclozestat` repositories.

The policy applies to both the core repository and model-specific data repositories, with different scopes.

## Core idea

CI is the final gate for structural consistency.

Local CLI output is useful, but repository data should not be trusted merely because it was committed.

```text
local CLI:
  run / aggregate / package / manifest

CI:
  validate / verify / reject broken data
```

CI does not authenticate model execution. It only validates files and package integrity.

## Repository modes

### Core repository

The core repository contains:

```text
src/
schemas/
docs/
datasets/smoke_v0/
examples/
```

CI should focus on:

- schema validity;
- documentation link sanity where practical;
- smoke dataset validation;
- reference example validation;
- package integrity examples;
- Python package checks when implementation exists.

The core repository should not accumulate large raw result logs.

### Model repository

A model repository contains results for one model identity.

CI should focus on:

- `model.toml` validity;
- one-model repository invariant;
- pinned dataset validity;
- submission package validity;
- submitter/run identity consistency;
- manifest verification;
- report regeneration after merge.

## PR classes

CI should classify pull requests by changed path.

### Documentation PR

Typical paths:

```text
docs/**
README.md
schemas/README.md
examples/**/README.md
```

Required checks:

- Markdown is present and readable;
- no generated report expectation;
- no large raw result files accidentally included.

### Schema PR

Typical paths:

```text
schemas/**
```

Required checks:

- schema files are valid JSON;
- example files still validate against updated schemas or known migration notes exist;
- validation documentation is updated when schema requirements change.

### Dataset PR

Typical paths:

```text
datasets/**
examples/model_repository/datasets/pinned/**
```

Required checks:

- item JSONL parseability;
- item schema validity;
- cross-field item validation;
- `segments.length == blanks.length + 1`;
- blank IDs unique;
- positions consecutive from 1;
- non-empty `accepted_fills`;
- `claim_scope` present;
- dataset README or source note present for non-smoke datasets.

### Result submission PR

Typical paths:

```text
submissions/<submitter_id>/<run_id>/**
```

Required checks:

- the PR adds one submission package;
- the PR does not modify global reports;
- the PR does not modify datasets;
- required files exist;
- either `run.jsonl` or `run-shards/*.jsonl` exists;
- `environment.json` validates;
- result JSONL validates;
- `summary.json` validates and can be regenerated;
- `manifest.json` validates;
- manifest file hashes match;
- path submitter/run IDs match metadata;
- `submitter_id` follows the slug policy;
- for ordinary public PRs, `submitter_id` matches the lowercase PR author login;
- `run_id` follows the recommended unique run-id pattern;
- the target submission path does not already exist on the base branch;
- one-model submission policy holds.

### Report PR

Typical paths:

```text
reports/**
```

Report PRs should normally be produced by CI or a maintainer action after raw submissions are accepted.

Required checks:

- reports are reproducible from merged submissions;
- reports do not claim to be the source of truth;
- report metadata records source commit or source run set.

## Result PR restrictions

A result PR should add only:

```text
submissions/<submitter_id>/<run_id>/**
```

It should not modify:

```text
reports/**
datasets/**
README.md
schemas/**
docs/**
```

Reason:

```text
raw result PRs should not create conflicts by editing global derived files
```

If a contributor needs to add a dataset item and submit results for it, use two PRs:

```text
1. dataset PR
2. result PR after dataset PR is merged
```

## Submitter and run identity CI

For normal result PRs, CI should enforce the policy in `docs/submitter_identity.md`.

Recommended checks:

```text
1. The changed path contains exactly one submission package.
2. Path submitter_id matches environment.json.submitter_id.
3. Path run_id matches environment.json.run_id.
4. All result records use the same submitter_id and run_id.
5. summary.json uses the same submitter_id and run_id.
6. manifest.json uses the same submitter_id and run_id.
7. submitter_id is a safe lowercase slug.
8. For ordinary public PRs, submitter_id == lowercase(PR author login).
9. run_id has dataset_id + UTC timestamp + random suffix shape.
10. The submission path is new relative to the base branch.
```

CI must not treat this as execution authentication. It is conflict avoidance and provenance consistency only.

## Pull request CI

For pull requests, CI should validate only and not commit generated files back to the PR by default.

Recommended PR pipeline:

```text
checkout
  -> detect changed paths
  -> classify PR
  -> validate JSON / JSONL / TOML
  -> validate schemas
  -> validate changed datasets
  -> validate changed submissions
  -> verify changed manifests
  -> enforce submitter/run identity consistency for result PRs
  -> fail with clear diagnostics
```

The PR pipeline should not regenerate and commit `reports/**` automatically.

## Main branch CI

After merge to `main`, CI may regenerate derived reports.

Recommended main pipeline:

```text
checkout
  -> validate all known data
  -> regenerate reports from submissions
  -> write reports/metadata.json
  -> commit reports if changed
```

For MVP, report regeneration may remain manual.

## Derived reports

Raw result files are the source of truth:

```text
submissions/**/run.jsonl
submissions/**/run-shards/*.jsonl
```

Derived reports include:

```text
reports/run_index.csv
reports/blank_fills.csv
reports/fill_distribution.csv
reports/position_pass_rate.csv
reports/metadata.json
```

Reports should include enough metadata to identify the source commit or source run set.

Example `reports/metadata.json`:

```json
{
  "generated_from_commit": "unknown",
  "generated_at": "2026-05-27T00:00:00Z",
  "included_runs": 0,
  "excluded_runs": 0,
  "notes": "Example shape only."
}
```

## One-model repository CI

In a model repository, CI should check:

```text
model.toml
  -> schemas/model.schema.json
  -> policy.one_model_repo = true
```

Then for every submission:

```text
environment.json.model_id == model.toml.model.model_id
all result records model_id == model.toml.model.model_id
summary.json.model_id == model.toml.model.model_id
```

If a real submission already exists, a PR changing `model.toml.model.model_id` should fail unless it is a deliberate repository reset reviewed by maintainers.

## Size checks

CI should warn or fail before GitHub repository limits become a problem.

Recommended thresholds:

```text
run shard target: 25 MiB
run shard warning: 50 MiB
run shard hard stop: 90 MiB
submission warning: 100 MiB
PR warning: 250 MiB
repository warning: 1 GiB
repository danger zone: 5 GiB
```

CI may not always know the full repository size cheaply. At minimum, it should check changed file sizes and submission package size.

## Security and integrity boundaries

CI can check:

- file structure;
- schemas;
- deterministic cross-field consistency;
- manifest hashes;
- summary regeneration;
- submitter/run identity consistency;
- one-model invariants.

CI cannot prove:

- the claimed model actually generated the output;
- the local backend was honest;
- a submitter did not fabricate raw outputs before packaging.

Do not describe CI as model authentication or execution attestation.

## MVP CI checks

Minimum useful CI:

```text
1. JSON / JSONL parse
2. TOML parse for model.toml
3. schema validation
4. item cross-field validation
5. submission required-file check
6. submitter/run identity consistency check
7. manifest hash verification
8. one-model submission check when model.toml exists
```

## Later CI checks

Useful later:

```text
summary regeneration
report regeneration
changed-path PR classification
large-file / shard-size enforcement
dataset source/license checks
model repository registry checks
```
