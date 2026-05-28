# Current Status Notes

This note records implementation status changes that should be folded back into `docs/status_matrix.md` when the next status-matrix cleanup is performed.

As of the latest sync, the summary and manifest implementation notes have already been reflected in `docs/status_matrix.md`. Keep this file short and delete sections once they become redundant.

## Newly implemented CLI surface

```text
llmclozestat aggregate --input <run.jsonl> --out <summary.json>
llmclozestat validate summary --input <summary.json>
llmclozestat validate manifest --input <manifest.json> [--verify-files]
llmclozestat verify-integrity --path <submission-package-dir>
```

## Newly implemented library core

```text
summary aggregation helper
summary JSON validation core
manifest JSON validation helper
file SHA-256 helper
canonical package hash helper
local manifest integrity verification helper
```

## Summary aggregation scope

Current scope:

```text
one result JSONL input
one summary JSON output
overall pass/fail/parse-fail/latency rates
one or more blank groups
array-form fill_distribution
repeated fills counted without deduplication
parse failures represented with fill_key = __PARSE_FAIL__
Shannon entropy over fill counts
```

Current limitations:

```text
no sharded input
no multi-run aggregation
no exclusion filters
no report generation
no manifest writing
```

## Summary validation scope

Current scope:

```text
summary JSON parse
required top-level summary fields
required group fields
required fill_distribution fields
object-form fill_distribution rejection
count total consistency
rate total consistency
parse-fail sentinel consistency
```

Current limitations:

```text
not a full JSON Schema validator
no source run.jsonl cross-check
no summary identity cross-check against environment.json
```

## Manifest validation and integrity scope

Current scope:

```text
manifest JSON parse
required manifest fields
required manifest file-entry fields
safe relative path checks
manifest self-reference rejection
listed file SHA-256 verification
canonical package_hash verification
missing manifest detection for package directories
```

Current limitations:

```text
not a full JSON Schema validator
no manifest generation
no prepare-submission command
no submitter_id/run_id path identity check
no environment/result/summary identity cross-check
no regenerated-summary cross-check
no signature or ledger verification
```

## Current executable pipeline

```text
run.jsonl
  -> llmclozestat validate results --input run.jsonl
  -> llmclozestat aggregate --input run.jsonl --out summary.json
  -> llmclozestat validate summary --input summary.json
  -> llmclozestat validate manifest --input manifest.json --verify-files
  -> llmclozestat verify-integrity --path submissions/<submitter_id>/<run_id>
```

## Still not implemented

```text
run
prepare-submission
validate submission
validate model
validate model-repo
report
collect
```
