# Submissions

This directory is for shareable result packages produced by local CLI runs.

The expected workflow is:

```text
git clone
  -> run llmclozestat locally
  -> accumulate raw JSONL under results/
  -> aggregate summaries
  -> copy or prepare a clean package under submissions/<user>/<run_id>/
  -> commit or open a pull request
```

## Layout

Recommended layout:

```text
submissions/<user>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
```

## Meaning

Submissions are self-reported measurement logs. They are useful for comparison and analysis, but they are not authenticated proof that a claimed model produced the output.

## What to include

### environment.json

Record enough information to understand how the run was produced:

```json
{
  "tool_version": "0.0.1",
  "dataset_id": "smoke_v0",
  "model_id": "local-model",
  "backend": "openai-compatible",
  "provider": "lm_studio",
  "temperature": 0,
  "max_tokens": 64,
  "os": "Windows 11",
  "hardware": "optional"
}
```

### run.jsonl

Raw trial records. This is the primary artifact.

### summary.json

Machine-readable aggregate summary derived from `run.jsonl`.

### summary.md

Human-readable short report.

## Review rule

Do not edit `run.jsonl` by hand to improve scores. This repository does not verify honesty, but analysis becomes useless if submitted logs are manually curated.
