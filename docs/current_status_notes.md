# Current Status Notes

This note records implementation status changes that should be folded back into `docs/status_matrix.md` when the next status-matrix cleanup is performed.

As of the latest sync, the summary, environment, manifest, submission semantic identity, and prepare-submission implementation notes have already been reflected in `docs/status_matrix.md`. Keep this file short and delete sections once they become redundant.

## Newly implemented CLI surface

```text
llmclozestat aggregate --input <run.jsonl> --out <summary.json>
llmclozestat validate environment --input <environment.json>
llmclozestat validate summary --input <summary.json>
llmclozestat prepare-submission --submitter-id <id> --run-id <id> --environment-json <environment.json> --run-jsonl <run.jsonl> --summary-json <summary.json> --out-dir <submission-dir>
llmclozestat validate manifest --input <manifest.json> [--verify-files]
llmclozestat validate submission --path <submission-package-dir>
llmclozestat verify-integrity --path <submission-package-dir>
```

## Newly implemented library core

```text
environment JSON validation helper
summary aggregation helper
summary JSON validation core
manifest JSON validation helper
file SHA-256 helper
canonical package hash helper
local manifest integrity verification helper
prepare-submission package helper
source artifact validation before packaging
submission path identity checker
submission artifact manifest-inclusion checker
submission semantic identity checker
```

## Environment validation scope

Current scope:

```text
environment JSON parse
selected required environment fields
support_mode / f_shot consistency
parser_config shape
extraction_modes_enabled shape and uniqueness
generation_config temperature / max_tokens / top_p checks
```

Current limitations:

```text
not a full JSON Schema validator
no generation_config_hash recomputation
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
no manifest writing inside aggregate
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
no source run.jsonl regenerated-summary cross-check
```

## Manifest, submission, and integrity scope

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
submitter_id path identity check for submission packages
run_id path identity check for submission packages
required artifact manifest-inclusion check for environment.json/run.jsonl/summary.json
required artifact existence check for environment.json/run.jsonl/summary.json
semantic identity check across environment.json/run.jsonl/summary.json for submitter_id/run_id/dataset_id/model_id
```

Current limitations:

```text
not a full JSON Schema validator
no regenerated-summary cross-check
no signature or ledger verification
```

## Prepare-submission scope

Current scope:

```text
validate source environment.json by default
validate source run.jsonl by default
validate source summary.json by default
copy existing environment.json
copy existing run.jsonl
copy existing summary.json
optionally copy existing summary.md
write manifest.json by default
verify written manifest
reject non-empty output directories unless --overwrite is passed
```

Current limitations:

```text
does not run model execution
does not aggregate run.jsonl
does not regenerate summary.json from run.jsonl
```

## Current executable pipeline

```text
environment.json
run.jsonl
  -> llmclozestat validate environment --input environment.json
  -> llmclozestat validate results --input run.jsonl
  -> llmclozestat aggregate --input run.jsonl --out summary.json
  -> llmclozestat validate summary --input summary.json
  -> llmclozestat prepare-submission --submitter-id <id> --run-id <id> --environment-json environment.json --run-jsonl run.jsonl --summary-json summary.json --out-dir submissions/<submitter_id>/<run_id>
  -> llmclozestat validate submission --path submissions/<submitter_id>/<run_id>
  -> llmclozestat verify-integrity --path submissions/<submitter_id>/<run_id>
```

## Still not implemented

```text
run
validate model
validate model-repo
report
collect
```
