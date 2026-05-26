# Model Repository

This document defines the minimal metadata expected in a model-specific `llmclozestat` data repository.

A model repository is intended to store measurements for exactly one model identity.

## Rule

```text
one model repository = one model identity
```

This keeps result collection, validation, storage, and per-model reporting simple.

Cross-model comparison should happen later by reading multiple model repositories, not by mixing multiple models inside one submission package.

## Required file

A model repository should contain:

```text
model.toml
```

The TOML file can be converted to a JSON-like object and validated against:

```text
schemas/model.schema.json
```

## Minimal model.toml

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
notes = "Example only. Replace with the actual local/runtime configuration."

[policy]
one_model_repo = true
allow_mixed_model_ids = false
```

## Recommended default condition

For MVP, the default measurement condition may also live in `model.toml`.

```toml
[default_condition.prompt]
prompt_template_id = "fill_full_sentence_v1.ja"
prompt_language = "ja"
support_mode = "format_shot"
f_shot = 2
blank_rendering = "（　　　）"

[default_condition.generation]
temperature = 0
top_p = 1
seed = 1
max_tokens = 128
repeat_penalty = 1.0

[default_condition.parser]
normalization = "v0_minimal"
extraction_modes_enabled = ["exact_full_text", "segment"]
fallback_extraction_enabled = false
```

Later, condition profiles may move to:

```text
conditions/default.toml
conditions/zero_shot.toml
conditions/format_shot_v1.toml
```

## Field meanings

### model.model_id

Stable model identity used by result records in this model repository.

It should be filesystem- and URL-friendly.

Recommended pattern:

```text
<family>-<size>-<variant>-<quantization>
```

Examples:

```text
qwen3-4b-instruct-q4km
gemma3-4b-it-q4km
llama32-3b-instruct-q4km
```

### model.family

Model family or lineage, such as:

```text
qwen
llama
gemma
mistral
phi
unknown
```

### model.source

Where the model came from.

Examples:

```text
huggingface
local
vendor
converted
unknown
```

### model.source_repo

Source repository, model card, local source label, or `unknown`.

Examples:

```text
Qwen/Qwen3-4B-Instruct
google/gemma-3-4b-it
unknown
```

### model.revision

Commit SHA, tag, release, model-card revision, local file hash, or `unknown`.

Do not leave this empty. If the revision is unknown, write `unknown` explicitly.

### model.quantization

Precision or quantization label.

Examples:

```text
FP16
BF16
Q8_0
Q4_K_M
unknown
```

### model.backend

Runtime backend.

Examples:

```text
lm_studio
llama_cpp
ollama
openai_compatible
unknown
```

### policy.one_model_repo

Must be true for a standard model repository.

CI should reject a model repository where this is false unless a future explicit mixed-model repository policy is introduced.

## Validation expectations

A model-repository validator should check:

- `model.toml` exists;
- `model.toml` conforms to `schemas/model.schema.json` after TOML parsing;
- `policy.one_model_repo = true`;
- every submission uses the same `model_id` as `model.toml`;
- `environment.json.model_id` matches `model.toml.model.model_id`;
- all result records in each submission use that same `model_id`;
- condition metadata in each run is stable within a comparable run.

## What this does not prove

`model.toml` does not authenticate model execution.

It is provenance metadata for filtering, grouping, and re-aggregation.

The project still does not prove that a claimed model actually generated the submitted outputs.

## Storage relationship

A model repository may grow over time.

Large result logs should be sharded under submission packages:

```text
submissions/<submitter_id>/<run_id>/
  run-shards/
    run-000001.jsonl
    run-000002.jsonl
```

Old or large raw logs may be manually archived outside the Git repository, while summaries, manifests, and archive pointers remain in Git.
