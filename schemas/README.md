# Schemas

This directory contains loose JSON Schemas for early `llmclozestat` records.

The schemas are intended to prevent obvious data breakage while the project is still in the v0.0 design and smoke-test phase.

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

It checks that each item has the core fields needed for probe identity, language variant tracking, validation intent, parser structure, and scoring.

### result.schema.json

Validates one JSON object from:

```text
run.jsonl
```

It checks that each trial record contains provenance, model identity, item metadata, raw output, normalized output, blank-level scoring, and item-level scoring.

### environment.schema.json

Validates:

```text
environment.json
```

It records run-level metadata such as submitter, model, backend, provider, generation parameters, OS, and hardware notes.

## Design stance

The schemas are intentionally permissive:

- `additionalProperties` is allowed.
- The schemas check core structure, not every future field.
- Cross-field constraints are left to validation code.

Examples of checks that should be handled by code rather than schema alone:

- `segments.length == blanks.length + 1`
- blank IDs are unique inside an item
- blank positions are consecutive
- `item_id` is unique inside a dataset
- `variant_id` is unique inside a dataset
- `expected_full_texts` can be reconstructed from `segments` and accepted fills

## Validation policy

The CLI should eventually provide:

```bash
llmclozestat validate items --dataset datasets/smoke_v0/items.jsonl
llmclozestat validate results --input results/example/run.jsonl
llmclozestat validate environment --input submissions/example/run/environment.json
```

Until implementation is added, these schemas document the intended shape of records.
