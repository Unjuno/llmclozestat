# Current Status Notes

This note records implementation status changes that should be folded back into `docs/status_matrix.md` when the next status-matrix cleanup is performed.

## Newly implemented CLI surface

```text
llmclozestat aggregate --input <run.jsonl> --out <summary.json>
llmclozestat validate summary --input <summary.json>
```

## Newly implemented library core

```text
summary aggregation helper
summary JSON validation core
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

## Current executable pipeline

```text
run.jsonl
  -> llmclozestat validate results --input run.jsonl
  -> llmclozestat aggregate --input run.jsonl --out summary.json
  -> llmclozestat validate summary --input summary.json
```

## Still not implemented

```text
run
prepare-submission
validate manifest
validate submission
validate model
validate model-repo
verify-integrity
report
collect
```
