# Schemas

This directory contains JSON Schemas for early `llmclozestat` records, derived summaries, manifests, and repository metadata.

The schemas are intended to prevent obvious data breakage while the project is still in the v0.0 design and smoke-test phase. They define required record shape, while deeper consistency checks remain the responsibility of validation code.

## Files

```text
schemas/item.schema.json
schemas/result.schema.json
schemas/environment.schema.json
schemas/summary.schema.json
schemas/manifest.schema.json
schemas/model.schema.json
```

## Purpose

### item.schema.json

Validates one JSON object from:

```text
datasets/<dataset_id>/items.jsonl
```

It checks that each item has the core fields needed for:

- probe identity;
- language variant tracking;
- validation intent;
- claim scope;
- parser structure;
- scoring lists.

New items must include `claim_scope` so item-level conclusions stay scoped and do not become broad model-quality claims.

### result.schema.json

Validates one JSON object from:

```text
run.jsonl
run-shards/*.jsonl
```

It checks that each trial record contains:

- provenance;
- model identity;
- item metadata;
- prompt condition metadata;
- generation configuration;
- raw output;
- normalized output;
- extraction mode;
- blank-level scoring;
- item-level scoring.

Required prompt/parser condition fields include:

- `prompt_template_id`
- `prompt_language`
- `support_mode`
- `f_shot`
- `blank_rendering`
- `extraction_mode`

These fields are required because prompt wording, prompt language, shot support, blank rendering, and extraction mode are experimental conditions.

### environment.schema.json

Validates:

```text
environment.json
```

It records run-level metadata such as submitter, model, backend, provider, prompt settings, parser settings, generation parameters, OS, and hardware notes.

Required prompt/parser environment fields include:

- `prompt_template_id`
- `prompt_language`
- `support_mode`
- `f_shot`
- `blank_rendering`
- `parser_config`

### summary.schema.json

Validates:

```text
summary.json
```

It checks the shape of derived aggregate data such as:

- run identity;
- dataset identity;
- model identity;
- trial counts;
- pass rates;
- group-level fill distributions;
- prompt/parser/generation grouping keys.

`summary.json` is a derived file. It should be reproducible from raw results. Schema validity alone is not enough; validation code should also regenerate or cross-check it from `run.jsonl` or `run-shards/*.jsonl`.

### manifest.schema.json

Validates:

```text
manifest.json
```

It checks the shape of package-level integrity metadata:

- manifest version;
- submitter and run identity;
- creation timestamp;
- hash algorithm;
- listed files;
- per-file SHA-256 values;
- package hash.

`manifest.json` verifies package file hashes. It is not model authentication.

### model.schema.json

Validates the parsed object form of:

```text
model.toml
```

A model repository should use `model.toml` to describe exactly one model identity.

It checks core model-repository metadata such as:

- `model.model_id`
- `model.family`
- `model.source`
- `model.source_repo`
- `model.revision`
- `model.quantization`
- `model.backend`
- `policy.one_model_repo`

The schema also allows an optional `default_condition` object for prompt, generation, and parser defaults.

`model.schema.json` does not prove that the claimed model generated any output. It only makes model-repository metadata machine-checkable.

## Design stance

The schemas are intentionally permissive where future expansion is expected:

- `additionalProperties` is allowed.
- The schemas check core structure, not every future field.
- Cross-field constraints are left to validation code.

Examples of checks that should be handled by code rather than schema alone:

- `segments.length == blanks.length + 1`;
- blank IDs are unique inside an item;
- blank positions are consecutive;
- `item_id` is unique inside a dataset;
- `variant_id` is unique inside a dataset;
- normalized fill lists do not contain duplicates;
- `expected_full_texts` can be reconstructed from `segments` and accepted fills;
- `support_mode = zero` implies `f_shot = 0`;
- `content_pass = true` implies `fill_class = accepted` in v0;
- `item_strict_pass` matches the documented strict-pass formula;
- `generation_config_hash` matches canonical JSON for `generation_config` when present;
- `summary.json` matches regenerated aggregation;
- `manifest.json` hashes match package files;
- `environment.json.model_id` matches all result records;
- `model.toml.model.model_id` matches all submissions in a model repository.

## Submission package schema boundary

Submission package structure is validated by package-level validation, not by these record schemas alone.

Publishable submissions are expected to contain:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
  manifest.json
```

or, for larger runs:

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

`manifest.json` is for package-level tamper detection. It is not model authentication.

## Validation policy

The CLI should eventually provide:

```bash
llmclozestat validate items --dataset datasets/smoke_v0/items.jsonl
llmclozestat validate results --input results/example/run.jsonl
llmclozestat validate environment --input submissions/example/run/environment.json
llmclozestat validate summary --input submissions/example/run/summary.json
llmclozestat validate manifest --input submissions/example/run/manifest.json
llmclozestat validate model --input model.toml
llmclozestat validate submission --path submissions/<submitter_id>/<run_id>
llmclozestat verify-integrity --path submissions/<submitter_id>/<run_id>
```

Until implementation is added, these schemas document the intended shape of records and metadata.
