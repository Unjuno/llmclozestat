# Summary Scope Policy

`summary.json` is a single-run summary artifact.

It summarizes one logical run produced by one model identity under one fixed set of run conditions.

## Scope

A `summary.json` file is derived from:

```text
one run.jsonl
```

or, later:

```text
one run-shards/ directory for the same run_id
```

It is not a cross-run, cross-submitter, or cross-model report.

## Required identity

A single-run `summary.json` must have one value for each of:

```text
submitter_id
run_id
dataset_id
model_id
```

The summary generator should copy these fields from the source result records.

A later validator should reject a summary if these fields do not match the source run records.

## What belongs in summary.json

`summary.json` may include:

```text
overall run rates
blank-level groups
fill_distribution
parse-fail sentinel counts
entropy over fill counts
latency aggregates
```

It may group within a run by:

```text
probe_id
variant_id
language
item_id
blank_id
prompt_template_id
prompt_language
support_mode
f_shot
blank_rendering
extraction_mode
generation_config_hash
```

## What does not belong in summary.json

Do not use `summary.json` for:

```text
cross-run aggregation
cross-submitter aggregation
cross-model comparison
leaderboard tables
repository-wide reports
```

Those should be separate artifacts, for example:

```text
reports/run_index.csv
reports/blank_fills.csv
reports/model_comparison.csv
reports/aggregate_summary.json
```

## Reason

Single-run summaries and repository-wide reports have different identities.

A single-run summary has one:

```text
submitter_id
run_id
model_id
dataset_id
```

A cross-run report may contain many of each. Forcing both into one schema would make identity and grouping rules ambiguous.

## Current command mapping

Current implemented command:

```bash
llmclozestat aggregate --input run.jsonl --out summary.json
```

This command writes a single-run `summary.json`.

Future multi-run reporting should use a separate command or mode, not silently change the meaning of `summary.json`.
