# Current Status Notes

This note records implementation status changes that should be folded back into `docs/status_matrix.md` when the next status-matrix cleanup is performed.

`docs/status_matrix.md` is mostly synchronized, but the current run-progress/retry work should be re-folded after review.

## Newly implemented in this branch

```text
llmclozestat run --config <run.toml> [--progress/--no-progress]
```

Runner changes:

```text
human-readable progress is printed to stderr by default
final machine-readable JSON remains on stdout
--no-progress disables progress output
progress callback events are available inside the runner
[retry] table is supported in run.toml
backend_attempts is written to each result record
retried_trial_count is returned in the final run result
backend_error_count remains in the final run result
final backend failures are still retained as trial-level parse_fail records
```

Supported retry config:

```toml
[retry]
max_attempts = 3
retry_delay_seconds = 0.5
backoff_factor = 2.0
```

Defaults when `[retry]` is omitted:

```text
max_attempts = 1
retry_delay_seconds = 0.0
backoff_factor = 1.0
```

Validation rules:

```text
retry.max_attempts >= 1
retry.retry_delay_seconds >= 0
retry.backoff_factor >= 1
[retry] must be a table if provided
```

## Still not implemented

```text
resume from partial run.jsonl
sharded run output
formal backend error taxonomy
retry allow/deny policy by error kind
jitter
deadline or max elapsed time
full JSON Schema execution for all schemas
collect command
```

## Status-matrix sync note

`docs/status_matrix.md` should be updated to remove the old implication that there is no retry policy at all. The accurate wording is:

```text
Minimal retry exists. Resume, sharding, error taxonomy, and execution attestation remain incomplete.
```
