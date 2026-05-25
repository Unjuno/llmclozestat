# Submissions

This directory is for shareable result packages produced by local CLI runs.

The expected workflow is:

```text
git clone
  -> run llmclozestat locally
  -> accumulate raw JSONL under results/
  -> aggregate summaries
  -> copy or prepare a clean package under submissions/<submitter_id>/<run_id>/
  -> commit or open a pull request
```

## Layout

Recommended layout:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
```

## Why submitter and run IDs matter

Submission paths intentionally include `<submitter_id>` and `<run_id>`.

This is not authentication. It is provenance metadata for later analysis.

Keeping submitter and run boundaries makes it possible to:

- aggregate all submissions;
- filter by submitter;
- exclude a suspicious or broken submitter later;
- compare repeated runs by the same submitter;
- identify environment-specific anomalies;
- re-aggregate without modifying raw logs.

If a submitter is later found to be unreliable, analysis tools should be able to exclude that submitter's directory from aggregate reports.

## Meaning

Submissions are self-reported measurement logs. They are useful for comparison and analysis, but they are not authenticated proof that a claimed model produced the output.

## What to include

### environment.json

Record enough information to understand how the run was produced:

```json
{
  "submitter_id": "github-username-or-local-name",
  "run_id": "smoke-local-model-20260525",
  "tool_version": "0.0.1",
  "dataset_id": "smoke_v0",
  "model_id": "local-model",
  "model_source": null,
  "quantization": null,
  "backend": "openai-compatible",
  "backend_version": null,
  "provider": "lm_studio",
  "generation_config": {
    "temperature": 0,
    "top_p": null,
    "seed": null,
    "max_tokens": 64,
    "context_window": null,
    "repeat_penalty": null,
    "stop": []
  },
  "os": "Windows 11",
  "hardware": "optional"
}
```

### run.jsonl

Raw trial records. This is the primary artifact.

Recommended record-level provenance fields:

- `submitter_id`
- `run_id`
- `dataset_id`
- `model_id`
- `backend`
- `provider`
- `probe_id`
- `variant_id`
- `language`
- `item_id`
- `trial_id`

### summary.json

Machine-readable aggregate summary derived from `run.jsonl`.

### summary.md

Human-readable short report.

## Review rule

Do not edit `run.jsonl` by hand to improve scores. This repository does not verify honesty, but analysis becomes useless if submitted logs are manually curated.
