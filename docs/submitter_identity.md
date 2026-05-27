# Submitter and Run Identity

This document defines how `submitter_id` and `run_id` should be assigned.

The goal is to allow many users, machines, and repeated runs to accumulate submissions without path conflicts.

## Core rule

Submission packages live under:

```text
submissions/<submitter_id>/<run_id>/
```

`submitter_id` identifies the submitter namespace.

`run_id` identifies one specific run under that submitter namespace.

The pair must be unique:

```text
submitter_id + run_id
```

## Not authentication

`submitter_id` is provenance metadata, not model execution authentication.

It helps with:

- grouping submissions;
- filtering submissions;
- excluding broken runs;
- regenerating reports;
- avoiding path conflicts between contributors.

It does not prove:

- the claimed user honestly ran the model;
- the claimed model generated the output;
- the local backend was honest.

## submitter_id

For public pull requests, the recommended value is:

```text
submitter_id = lowercase GitHub username slug
```

Examples:

```text
unjuno
alice
bob-dev
```

Recommended slug pattern:

```text
^[a-z0-9][a-z0-9-]{0,38}$
```

Disallow values that are unsafe as paths:

```text
../alice
alice/bob
alice bob
@alice
UnJuno
```

A validator should reject path traversal and slash-containing values.

## PR author matching

For normal public result PRs, CI should check:

```text
submitter_id == lowercase(PR author login)
```

This is not strong identity proof. It only prevents ordinary PRs from casually submitting under another user's namespace.

Maintainer, bot, team, or organization submissions may need a later explicit policy.

## submitter_id rename policy

Do not rename old submissions when a GitHub username changes.

Recommended policy:

```text
submitter_id is the submitter slug at submission creation time
```

Old submissions remain under the original path.

Future metadata may add optional aliases, but raw submission paths should remain stable.

## run_id

`run_id` must be unique within one `submitter_id` namespace.

The main collision risk is the same user running the tool on multiple machines at the same time.

Recommended run ID format:

```text
<dataset_id>-<UTC timestamp>-<short random>
```

Example:

```text
smoke_v0-20260527T143012Z-a7f3c9
ja_long_context_v0-20260527T143512Z-91bd20
```

Recommended components:

| Component | Meaning |
|---|---|
| `dataset_id` | dataset being measured |
| `UTC timestamp` | run creation time in `YYYYMMDDTHHMMSSZ` format |
| `short random` | at least 24 bits of randomness, encoded as lowercase hex or base32 |

A longer random suffix is safer for heavily parallel use.

Recommended MVP:

```text
short random = 6 lowercase hex chars
```

For high parallelism:

```text
short random = 10 to 12 lowercase hex chars
```

## machine_id

A separate machine ID is optional.

For MVP, do not require it.

Reason:

```text
timestamp + random suffix is enough for path conflict avoidance
```

If later needed, environment metadata may include:

```json
{
  "machine_id": "local-hash-or-user-defined-label"
}
```

Do not include a raw hostname by default because it may leak local information.

## Path consistency

For a submission package at:

```text
submissions/<submitter_id>/<run_id>/
```

Validation should check:

```text
path submitter_id == environment.json.submitter_id
path run_id == environment.json.run_id
all result records submitter_id == environment.json.submitter_id
all result records run_id == environment.json.run_id
summary.json.submitter_id == environment.json.submitter_id
summary.json.run_id == environment.json.run_id
manifest.json.submitter_id == environment.json.submitter_id
manifest.json.run_id == environment.json.run_id
```

## Multiple machines under one user

Multiple machines should use the same `submitter_id` and different `run_id` values.

Example:

```text
submissions/unjuno/smoke_v0-20260527T143012Z-a7f3c9/
submissions/unjuno/smoke_v0-20260527T143013Z-91bd20/
submissions/unjuno/smoke_v0-20260527T143013Z-f01a77/
```

This allows the same user to accumulate runs from many machines without conflicts.

## Result PR rule

A result PR should add exactly one new submission package:

```text
submissions/<submitter_id>/<run_id>/**
```

It should not update:

```text
reports/**
datasets/**
docs/**
schemas/**
README.md
```

Reports should be regenerated after merge by CI or by a maintainer action.

## CI report update model

Recommended flow:

```text
result PR
  -> adds one unique submission package
  -> CI validates package
  -> merge
  -> main CI regenerates reports from all accepted submissions
```

This prevents multiple result PRs from conflicting over derived report files.

## Safe defaults for collect

A future `collect` command should default to:

```text
submitter_id = explicit CLI argument, or lowercase GitHub username when safely detected
run_id = <dataset_id>-<UTC timestamp>-<random suffix>
```

It should not silently reuse an existing `run_id`.

If the target submission directory already exists, `collect` should fail unless the user explicitly passes a resume or overwrite option.

## Overwrite and resume policy

MVP should avoid in-place mutation of existing publishable submissions.

Recommended behavior:

```text
existing submissions/<submitter_id>/<run_id>/ -> error
```

Later, a controlled resume mode may be introduced for local scratch runs, but publishable submissions should remain append-only once packaged.

## Summary

Recommended MVP policy:

```text
submitter_id = lowercase GitHub username slug for public PRs
run_id = dataset_id + UTC timestamp + random suffix
path = submissions/<submitter_id>/<run_id>/
normal result PR = one new submission package only
main CI = regenerate derived reports after merge
```
