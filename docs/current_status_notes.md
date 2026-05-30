# Current Status Notes

This note records implementation status changes that should be folded back into `docs/status_matrix.md` when the next status-matrix cleanup is performed.

`docs/status_matrix.md` is mostly synchronized, but the current run-progress/retry and multi-blank probe-design work should be re-folded after review.

## Newly implemented in recent branches

```text
llmclozestat run --config <run.toml> [--progress/--no-progress]
datasets/template_probes_v0/items.jsonl
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

## Probe-design correction

The previous seed-only framing could be misread as:

```text
one item = one blank
```

That is not the correct design rule.

The corrected rule is:

```text
one item = one measurement target
one item may contain as many blanks as needed
```

Reason:

```text
A diagnostic probe often needs to observe intermediate state, concept binding, formula representation, substitution, and final answer separately.
```

Examples now represented in `template_probes_v0`:

```text
quantity comparison: difference blank + final label blank
formula representation: concept-name blank + formula blank
```

Formula blanks are valid when the intended target is symbolic representation, such as:

```text
context defines variables -> concept name -> formula expression
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
formula equivalence normalization beyond listed accepted_fills
unit/dimensional analysis scoring
```

## Status-matrix sync note

`docs/status_matrix.md` should be updated to remove old implications that there is no retry policy or that real probes are single-blank only. The accurate wording is:

```text
Minimal retry exists. Multi-blank template probes exist. Resume, sharding, formula equivalence, error taxonomy, and execution attestation remain incomplete.
```
