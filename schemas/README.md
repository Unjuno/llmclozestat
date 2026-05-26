# Schemas

This directory contains JSON Schemas for early `llmclozestat` records.

The schemas are intended to prevent obvious data breakage while the project is still in the v0.0 design and smoke-test phase. They define required record shape, while deeper consistency checks remain the responsibility of validation code.

## Files

```text
schemas/item.schema.json
schemas/result.schema.json
schemas/environment.schema.json
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
- `generation_config_hash` matches canonical JSON for `generation_config` when present.

## Submission package schema boundary

Submission package structure is validated by package-level validation, not by these three record schemas.

Publishable submissions are expected to contain:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
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
llmclozestat validate submission --path submissions/<submitter_id>/<run_id>
llmclozestat verify-integrity --path submissions/<submitter_id>/<run_id>
```

Until implementation is added, these schemas document the intended shape of records.
