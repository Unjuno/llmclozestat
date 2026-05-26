# smoke_v0 reference example

This directory contains a schema-compliant reference package for the `smoke_v0` dataset.

It is **not** a real benchmark result. It exists so implementers have a concrete target when building:

- schema validation;
- parser/scorer output;
- aggregation output;
- submission package validation;
- manifest verification.

## Files

```text
examples/smoke_v0/
  environment.json
  run.jsonl
  summary.json
  summary.md
  manifest.json
```

## Important constraints demonstrated

- `claim_scope` is required in item data.
- Result records include prompt condition metadata:
  - `prompt_template_id`
  - `prompt_language`
  - `support_mode`
  - `f_shot`
  - `blank_rendering`
- Result records include parser metadata:
  - `extraction_mode`
- Publishable-style packages include `manifest.json`.
- The manifest verifies package file hashes only; it does not authenticate model execution.

## Expected use

Use this directory as a fixture target while implementing validation and aggregation.

Do not treat the included `example-model` output as a real model result.
