# Operating Model

This document defines the intended operating model for `llmclozestat` result collection.

The goal is to keep the core tool small while allowing measurement data to grow through Git repositories and pull requests.

## Core principle

The primary measurement loop is:

```text
fixed prompt condition
  -> cloze item
  -> model output
  -> blank-level fill extraction
  -> fill distribution
  -> model behavior profile
```

The project does not try to produce one global model score.

The useful unit is:

```text
model_id x condition_id x dataset_snapshot x item_id x blank_id -> fill_distribution
```

## Repository roles

`llmclozestat` should support more than one repository role.

### Core repository

The core repository contains:

```text
src/
schemas/
docs/
datasets/smoke_v0/
examples/
```

Its responsibilities are:

- CLI implementation;
- schemas;
- parser and scoring policy;
- validation policy;
- documentation;
- smoke dataset;
- small reference examples.

The core repository is not intended to become an unlimited raw-result warehouse.

### Model repository

A model repository is a data repository for one model identity.

Recommended rule:

```text
one model repository = one model identity
```

A model repository contains:

```text
model.toml
README.md
DATA_LICENSE.md

datasets/
submissions/
reports/
```

Its responsibilities are:

- storing measurement results for exactly one model identity;
- pinning or copying datasets used for measurement;
- generating per-model reports;
- accepting result pull requests for that model.

### Index repository

An optional index repository may list model repositories and generate cross-model reports.

Example:

```text
llmclozestat-index/
  model_repos.jsonl
  reports/
```

The index repository is optional in early development. It becomes useful when many model repositories exist.

## One model per repository

The recommended long-term data layout is:

```text
llmclozestat-model-<model-id>/
```

Examples:

```text
llmclozestat-model-qwen3-4b-instruct-q4km
llmclozestat-model-gemma3-4b-it-q4km
llmclozestat-model-llama32-3b-instruct-q4km
```

A model repository must not mix unrelated model identities.

CI should reject a submission if records in `run.jsonl` contain a `model_id` different from `model.toml`.

## Model identity

`model_id` alone is not enough to identify a measured model.

A model repository should define model identity using `model.toml`.

Recommended minimum:

```toml
[model]
model_id = "qwen3-4b-instruct-q4km"
family = "qwen"
source = "huggingface"
source_repo = "Qwen/Qwen3-4B-Instruct"
revision = "unknown"
quantization = "Q4_K_M"
backend = "lm_studio"
backend_version = "unknown"

[policy]
one_model_repo = true
```

Changes in model revision, quantization, backend, or major runtime condition should normally create a distinct model identity or at least a distinct condition profile.

## Fixed condition profile

A model repository should define a default measurement condition.

For MVP, the default condition may live in `model.toml`.

Later, condition profiles may move to:

```text
conditions/default.toml
conditions/zero_shot.toml
conditions/format_shot_v1.toml
```

Recommended condition fields:

```toml
[prompt]
prompt_template_id = "fill_full_sentence_v1.ja"
prompt_language = "ja"
support_mode = "format_shot"
f_shot = 2
blank_rendering = "（　　　）"

[generation]
temperature = 0
top_p = null
seed = null
max_tokens = 128
repeat_penalty = null

[parser]
normalization = "v0_minimal"
extraction_modes_enabled = ["exact_full_text", "segment"]
fallback_extraction_enabled = false
```

Results may be compared directly only when the relevant model, dataset, prompt, generation, and parser conditions match.

Recommended comparison key:

```text
model_id
+ model_revision
+ quantization
+ backend
+ dataset_id
+ dataset_version or dataset_commit
+ prompt_template_id
+ prompt_language
+ support_mode
+ f_shot
+ blank_rendering
+ generation_config_hash
+ extraction_mode
```

## Dataset snapshots

A model repository should keep the dataset snapshot used for measurement identifiable.

MVP options:

- copy the dataset under `datasets/pinned/`;
- record `dataset_git_commit` in `environment.json`;
- record `dataset_version` when available.

Do not silently compare results from different dataset snapshots as if they were the same condition.

## Submission package

A run submission is the portable result unit.

Recommended layout:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run-shards/
    run-000001.jsonl
    run-000002.jsonl
  summary.json
  summary.md
  manifest.json
```

Small examples may use a single `run.jsonl`, but long-running or shared submissions should support sharding.

A publishable submission must contain `manifest.json`.

The manifest verifies package file hashes. It does not authenticate model execution.

## Pull request model

Public contribution can be PR-only from the user's point of view.

Internally, a PR still requires branch and commit creation.

Recommended result PR rule:

```text
one result PR = one submission package
```

A result PR should add only:

```text
submissions/<submitter_id>/<run_id>/**
```

It should not update global reports, datasets, or README aggregate tables.

Dataset item PRs should be separate from result PRs.

## CI role

CI is the final gate.

Pull-request CI should validate:

- JSON and JSONL parseability;
- schema conformance;
- item cross-field checks;
- submission required files;
- path and metadata consistency;
- manifest hash consistency.

After merge, CI may regenerate derived reports from merged submissions.

Derived reports are not the source of truth.

Source of truth:

```text
submissions/**/run-shards/*.jsonl
submissions/**/run.jsonl
```

Derived outputs:

```text
reports/run_index.csv
reports/blank_fills.csv
reports/fill_distribution.csv
reports/position_pass_rate.csv
```

## Analysis policy

Analysis does not need to be built into the CLI.

The CLI should write clean JSONL and CSV-friendly reports. Users may analyze results with:

- R;
- Python;
- DuckDB;
- Polars;
- notebooks;
- other tools.

The repository should keep raw logs and derived reports separable.

## Storage policy

GitHub repositories are useful for small and medium result logs, not unlimited raw warehouses.

Recommended limits:

```text
run shard target: 25 MiB
run shard warning: 50 MiB
run shard hard stop: 90 MiB
submission warning: 100 MiB
PR warning: 250 MiB
repository warning: 1 GiB
repository danger zone: 5 GiB
```

Large or old raw logs may be manually moved to an external archive.

The CLI should produce portable packages. Repository splitting and archival migration can be manual operations.

## Out of scope for MVP

The following are useful later, but not required for MVP:

- automatic repository creation;
- automatic archive migration;
- automatic multi-repository index management;
- automatic PR creation;
- provider autodiscovery;
- multi-model runs inside one submission.

## MVP rule set

Recommended MVP constraints:

```text
one collect command = one model = one run = one submission
one model repository = one model identity
one result PR = one submission package
reports are generated after merge
large logs are sharded
archive migration is manual
```
