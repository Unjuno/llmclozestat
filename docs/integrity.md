# Integrity and Tamper Detection

This document defines the integrity layer for `llmclozestat` submissions.

The project does not try to prove that a claimed model truly generated a result. For normal local execution, that is not reliably provable.

Instead, the project should support tamper detection for submitted result packages.

## Design boundary

This layer can help show:

- the submitted files have not changed since the manifest was created;
- `run.jsonl` or `run-shards/*.jsonl`, `summary.json`, `summary.md`, and `environment.json` belong to the same package;
- later reviewers can detect accidental or intentional file modifications;
- aggregation can reject packages whose hashes no longer match.

This layer cannot prove:

- the claimed model actually generated the output;
- all trials were submitted;
- bad trials were not omitted before packaging;
- the local backend was honest;
- the model file was unmodified;
- the submitter executed the run honestly.

Therefore this is integrity checking, not model authentication.

## Why not per-trial ledger anchoring

Hashing or anchoring every trial individually is not the right default.

Reasons:

- it adds complexity without proving model authenticity;
- it makes the CLI harder to use;
- it can create false confidence;
- it increases cost if an external ledger is used;
- it distracts from the main goal: structured model behavior measurement.

The useful target is package-level tamper detection.

## Recommended package layout

A shareable submission package should contain:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
  manifest.json
```

For larger runs, the package may contain sharded raw results:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run-shards/
    run-000001.jsonl
    run-000002.jsonl
  summary.json
  summary.md
  manifest.json
```

Optional future files:

```text
  signature.json
  ledger_receipt.json
```

These optional files should never be required for ordinary local use.

## Manifest

`manifest.json` records deterministic hashes of the package files.

Recommended manifest fields:

```json
{
  "manifest_version": "0.1",
  "submitter_id": "github-username-or-local-name",
  "run_id": "smoke-local-model-20260525",
  "created_at": "2026-05-26T00:00:00Z",
  "hash_algorithm": "sha256",
  "files": [
    {
      "path": "environment.json",
      "sha256": "..."
    },
    {
      "path": "run.jsonl",
      "sha256": "..."
    },
    {
      "path": "summary.json",
      "sha256": "..."
    },
    {
      "path": "summary.md",
      "sha256": "..."
    }
  ],
  "package_hash": "sha256:...",
  "package_hash_input": "canonical_json(files sorted by path; fields path,sha256 only; utf-8; no extra whitespace)"
}
```

## File hash calculation

For each listed file:

```text
file_sha256 = SHA256(raw file bytes)
```

The hash input is the exact byte content of the file as stored in the package.

Do not normalize line endings or JSON formatting before hashing individual files.

## Package hash canonicalization

`package_hash` must be computed deterministically from a canonical JSON object, not from filesystem metadata.

Canonical package hash input object:

```json
{
  "files": [
    {"path": "environment.json", "sha256": "..."},
    {"path": "run.jsonl", "sha256": "..."},
    {"path": "summary.json", "sha256": "..."},
    {"path": "summary.md", "sha256": "..."}
  ],
  "hash_algorithm": "sha256",
  "manifest_version": "0.1",
  "run_id": "smoke-local-model-20260525",
  "submitter_id": "github-username-or-local-name"
}
```

Canonicalization rules:

```text
1. Exclude manifest.json from files.
2. Exclude signature.json and ledger_receipt.json from v0 package_hash input.
3. Include only these file entry fields: path, sha256.
4. Do not include size_bytes in package_hash input.
5. Sort files by path using bytewise ascending UTF-8 path order.
6. Sort JSON object keys lexicographically at every object level.
7. Serialize as UTF-8 JSON with no insignificant whitespace.
8. Do not escape non-ASCII characters unless required by the JSON encoder for correctness.
9. Hash the resulting UTF-8 bytes with SHA-256.
10. Store the result as package_hash = "sha256:<64 lowercase hex>".
```

Recommended `package_hash_input` description string:

```text
canonical_json(v0: keys sorted; files sorted by path; file fields path,sha256; exclude manifest/signature/ledger; utf-8; compact)
```

This description is not itself hashed. It documents the intended algorithm.

## Verification

A verifier should check:

- each listed file exists;
- listed paths are relative and do not escape the package directory;
- each file hash matches the manifest;
- `package_hash` matches the deterministic manifest calculation;
- `submitter_id` and `run_id` match the submission path;
- `summary.json` can be regenerated from `run.jsonl` or `run-shards/*.jsonl` when aggregation code is available.

If any hash check fails, the package should be excluded from trusted aggregate reports.

## CLI shape

### Prepare package with manifest

Target command shape:

```bash
llmclozestat prepare-submission \
  --submitter-id github-username-or-local-name \
  --run-id smoke-local-model-20260525 \
  --run-jsonl results/smoke-local-model-20260525/run.jsonl \
  --summary-json results/smoke-local-model-20260525/summary.json \
  --out-dir submissions/github-username-or-local-name/smoke-local-model-20260525 \
  --write-manifest
```

### Verify package integrity

Target command shape:

```bash
llmclozestat verify-integrity \
  --path submissions/<submitter_id>/<run_id>
```

## Optional future extensions

### signed_manifest

A submitter may sign `package_hash` with a local key.

This can show that a key holder claimed responsibility for a package. It still does not prove honest model execution.

### ledger_anchor

A package hash may be anchored to an external ledger.

This can strengthen timestamp and later tamper detection. It still does not prove the claimed model generated the output.

Ledger anchoring should remain optional and outside the core v0 path.

## Aggregation policy

Aggregators should be able to filter by integrity status:

```text
all submissions
manifest present
hash verified
signed
ledger anchored
exclude failed integrity checks
```

Integrity status must not be interpreted as model authenticity.

## Recommended v0 path

Implement only:

1. `manifest.json` generation;
2. deterministic package hash calculation;
3. `verify-integrity` for local hash checks.

Do not implement blockchain anchoring in v0.
