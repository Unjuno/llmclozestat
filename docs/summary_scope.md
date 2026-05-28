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

## Compression policy

Normal statistical values should be compressed into aggregate counts, rates, and compact distributions.

For example:

```text
count
rate
unique_fill_count
top_fill
top_wrong_fill
mean_entropy
avg_latency_ms
```

Do not retain every successful ordinary trial in derived report artifacts when the same information can be reconstructed from aggregate statistics or from the raw run file.

`summary.json` is a compressed materialized view of one run. It is not the raw event log.

## Failure and exception retention policy

Failures are exceptions and should be preserved more carefully than ordinary successful trials.

Examples:

```text
parse_fail examples
instruction-following failures
item-format failures
validator failures
unexpected extraction ambiguity
unexpected backend errors
```

These examples have diagnostic value and may reveal systematic model or parser behavior.

However, publishable `summary.json` should not become an unbounded dump of every failure. Prefer a compact design such as:

```text
failure_count
failure_rate
failure_distribution
sample_failure_examples with a small cap
```

A later diagnostics artifact may retain richer examples outside `summary.json`, for example:

```text
results/<run_id>/failed/
results/<run_id>/notes.md
reports/failure_examples.jsonl
```

This preserves failure evidence without exploding the canonical summary artifact.

## What does not belong in summary.json

Do not use `summary.json` for:

```text
cross-run aggregation
cross-submitter aggregation
cross-model comparison
leaderboard tables
repository-wide reports
unbounded raw failure dumps
```

Those should be separate artifacts, for example:

```text
reports/run_index.csv
reports/blank_fills.csv
reports/model_comparison.csv
reports/aggregate_summary.json
reports/failure_examples.jsonl
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

The same applies to storage density. Ordinary statistics can be compressed, but failures are sparse, high-information exceptions. They should be retained as capped examples or diagnostics rather than merged into opaque aggregate numbers only.

## Current command mapping

Current implemented command:

```bash
llmclozestat aggregate --input run.jsonl --out summary.json
```

This command writes a single-run `summary.json`.

Future multi-run reporting should use a separate command or mode, not silently change the meaning of `summary.json`.
