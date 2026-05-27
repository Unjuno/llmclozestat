# Model Repository Usage

This guide explains how to create a model-specific data repository and how to adapt it for another model.

The intended rule is:

```text
one model repository = one model identity
```

Do not mix unrelated models in the same model repository.

## When to use a model repository

Use a model repository when you want to repeatedly collect results for one model over time.

Examples:

```text
llmclozestat-model-qwen3-4b-instruct-q4km
llmclozestat-model-gemma3-4b-it-q4km
llmclozestat-model-llama32-3b-instruct-q4km
```

The core `llmclozestat` repository should stay focused on:

- CLI implementation;
- schemas;
- docs;
- smoke dataset;
- small examples.

Large or repeated model measurements should live in model repositories.

## Minimal repository layout

A model repository should start with:

```text
model.toml
README.md
DATA_LICENSE.md

datasets/
  pinned/

submissions/
reports/
```

Optional later:

```text
conditions/
.github/workflows/
```

## Step 1: create or copy a model repository

For MVP, repository creation is manual.

You may:

- create a new empty GitHub repository;
- copy files from a future template repository;
- copy `examples/model_repository/model.toml` and edit it.

Do not automate repository creation in the initial CLI.

## Step 2: edit model.toml

Start from:

```text
examples/model_repository/model.toml
```

Set the model identity fields.

Example:

```toml
[model]
model_id = "qwen3-4b-instruct-q4km"
family = "qwen"
source = "huggingface"
source_repo = "Qwen/Qwen3-4B-Instruct"
revision = "unknown"
quantization = "Q4_K_M"
backend = "lm_studio"
backend_version = "unknown"
context_window = 32768
notes = "Local LM Studio run. Replace unknown values when known."

[policy]
one_model_repo = true
allow_mixed_model_ids = false
```

`revision` should be a source revision, tag, commit, local file hash, or `unknown`.

Do not leave it blank.

## Step 3: set the default condition

For MVP, keep the default condition in `model.toml`.

Example zero-shot condition:

```toml
[default_condition.prompt]
prompt_template_id = "fill_full_sentence_v1.ja"
prompt_language = "ja"
support_mode = "zero"
f_shot = 0
blank_rendering = "（　　　）"

[default_condition.generation]
temperature = 0
top_p = 1
seed = 1
max_tokens = 64
repeat_penalty = 1.0

[default_condition.parser]
normalization = "v0_minimal"
extraction_modes_enabled = ["exact_full_text", "segment"]
fallback_extraction_enabled = false
```

Example format-shot condition:

```toml
[default_condition.prompt]
prompt_template_id = "fill_full_sentence_v1.ja"
prompt_language = "ja"
support_mode = "format_shot"
f_shot = 2
blank_rendering = "（　　　）"
```

Do not compare zero-shot and format-shot results as the same condition.

## Step 4: pin or copy datasets

The model repository should keep enough information to know which dataset snapshot was measured.

MVP options:

```text
datasets/pinned/smoke_v0/items.jsonl
```

or record the dataset commit in `environment.json`.

Do not silently compare results from different dataset snapshots as if they were the same condition.

## Step 5: collect results

The future convenience command is expected to be:

```bash
llmclozestat collect \
  --dataset datasets/pinned/smoke_v0/items.jsonl \
  --provider openai-compatible \
  --base-url http://localhost:1234/v1 \
  --model qwen3-4b-instruct-q4km \
  --submitter-id your-name \
  --target-trials 20 \
  --prepare-submission \
  --write-manifest \
  --validate
```

Until `collect` exists, the equivalent workflow is:

```text
run
  -> aggregate
  -> prepare-submission
  -> verify-integrity
  -> validate submission
```

The final publishable result should look like:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run-shards/
    run-000001.jsonl
  summary.json
  summary.md
  manifest.json
```

Small examples may use `run.jsonl`, but long runs should use `run-shards/`.

## Step 6: open a result PR

A result PR should add only:

```text
submissions/<submitter_id>/<run_id>/**
```

Do not update global reports, README score tables, or datasets in a result PR.

Reports should be regenerated after merge by CI or manually from merged submissions.

## Changing the repository to another model

There are two cases.

### Case A: no real submissions yet

If the repository has no real submissions, you may edit `model.toml` to the new model.

Also update:

- repository name;
- README title;
- default condition if needed;
- pinned dataset notes if they are model-specific.

### Case B: submissions already exist

If the repository already contains real submissions, do not change `model.toml` to another model.

Create a new model repository instead.

Reason:

```text
old submissions would no longer match model.toml
```

This breaks the one-model repository invariant.

## What counts as another model?

Treat these as distinct model identities unless a future policy explicitly says otherwise:

- different base model;
- different instruct/chat/base variant;
- different source revision;
- different quantization or precision;
- different backend with known behavior differences;
- different context-window configuration when it affects the run condition.

Examples:

```text
qwen3-4b-instruct-q4km
qwen3-4b-instruct-q8
qwen3-8b-instruct-q4km
```

These should normally be separate model repositories.

## Validation checklist

Before submitting results, check:

```text
[ ] model.toml exists
[ ] model.toml matches schemas/model.schema.json after TOML parsing
[ ] policy.one_model_repo = true
[ ] environment.json.model_id matches model.toml.model.model_id
[ ] every result record uses the same model_id
[ ] prompt condition is stable within the run
[ ] generation condition is stable within the run
[ ] parser condition is stable within the run
[ ] manifest.json exists
[ ] manifest hashes match package files
[ ] summary.json can be regenerated from raw results
```

## What this does not prove

`model.toml`, `manifest.json`, and CI validation do not prove model execution authenticity.

They only make the package structurally valid, reproducible enough for analysis, and resistant to later accidental or malicious file changes.
