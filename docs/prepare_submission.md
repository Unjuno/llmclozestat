# Prepare Submission MVP

`prepare-submission` assembles a publishable single-run submission directory.

## Scope

MVP input:

```text
run.jsonl
summary.json
submitter_id
run_id
```

MVP output:

```text
submissions/<submitter_id>/<run_id>/
  run.jsonl
  summary.json
```

MVP does not create:

```text
environment.json
summary.md
manifest.json
```

Those are later phases.

## Safety rules

The command must not silently overwrite an existing submission directory.

If the target directory already exists, fail unless a later explicit resume or overwrite policy is implemented.

The command should create parent directories when needed.

## Preserve mistakes and failed artifacts

Do not delete failed outputs, rejected intermediate files, or notes about earlier mistakes merely because a later corrected artifact exists.

Mistakes are useful diagnostic data for:

```text
implementation debugging
CI regression analysis
validator design
reproducibility review
```

For MVP, `prepare-submission` should not copy arbitrary local scratch files into the publishable package. However, documentation should preserve known mistakes and unresolved issues in docs or test fixtures instead of silently rewriting history.

Later versions may support an explicit non-publishable diagnostics area such as:

```text
results/<run_id>/notes.md
results/<run_id>/failed/
```

Publishable submissions should remain minimal and validated.

## Validation expectation

Before preparing a publishable package, users should run:

```bash
llmclozestat validate results --input run.jsonl
llmclozestat validate summary --input summary.json
```

The MVP assembler may copy files only. Full cross-file validation is a later `validate submission` concern.

## Future package layout

The target full layout remains:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
  manifest.json
```

For larger runs, a later version may support:

```text
submissions/<submitter_id>/<run_id>/
  run-shards/
    run-000001.jsonl
    run-000002.jsonl
```

## Integrity boundary

`prepare-submission` MVP does not verify model execution and does not implement tamper detection.

`manifest.json` will provide package-level tamper detection in a later phase.
