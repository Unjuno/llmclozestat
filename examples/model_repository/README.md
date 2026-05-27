# Example Model Repository

This directory is a copyable skeleton for a model-specific `llmclozestat` data repository.

It is not a real measured model repository.

## Rule

```text
one model repository = one model identity
```

Do not mix unrelated models in one model repository.

## Files

```text
model.toml
README.md
DATA_LICENSE.md

datasets/
  pinned/

submissions/
reports/
```

## How to use this example

1. Create a new GitHub repository for one model.
2. Copy this directory's contents into that repository.
3. Edit `model.toml`.
4. Pin or copy datasets under `datasets/pinned/`.
5. Run `llmclozestat` locally when the CLI implementation exists.
6. Store publishable outputs under `submissions/<submitter_id>/<run_id>/`.
7. Generate derived reports under `reports/`.

## Edit model.toml

At minimum, update:

```toml
[model]
model_id = "example-model-q4km"
family = "example"
source = "local"
source_repo = "unknown"
revision = "unknown"
quantization = "Q4_K_M"
backend = "lm_studio"
```

If the repository already contains real submissions, do not change `model.model_id` to another model. Create a new model repository instead.

## Submission layout

Preferred layout:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run-shards/
    run-000001.jsonl
  summary.json
  summary.md
  manifest.json
```

Small examples may use `run.jsonl`, but long runs should use `run-shards/`.

## Reports

`reports/` should contain derived files only.

Examples:

```text
reports/run_index.csv
reports/blank_fills.csv
reports/fill_distribution.csv
reports/position_pass_rate.csv
```

Raw results remain the source of truth.

## Not authentication

`model.toml` and `manifest.json` do not prove that the claimed model generated the outputs. They provide provenance metadata and package-level tamper detection.
