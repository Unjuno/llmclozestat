# Template Quickstart

Goal: clone this repository, change a small number of settings, and obtain reproducible statistical measurements for one model.

This repository is intentionally designed around:

- one repository = one model identity;
- fixed prompt conditions;
- explicit metadata;
- submission packages under `submissions/<submitter_id>/<run_id>/`;
- validation before report generation.

---

## 1. Clone

```bash
git clone https://github.com/YOUR_NAME/llmclozestat.git
cd llmclozestat
```

---

## 2. Create Python environment

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install:

```bash
pip install -U pip
pip install -e .
```

---

## 3. Configure API key

Copy:

```bash
cp .env.example .env
```

Set:

```text
OPENAI_API_KEY=...
```

For local OpenAI-compatible servers such as LM Studio or llama.cpp, many servers accept any non-empty dummy value.

---

## 4. Configure model identity

Copy:

```bash
cp model.toml.example model.toml
```

Edit:

```text
model.toml
```

At minimum, set:

```toml
[model]
model_id = "your-model"
family = "your-family"
source = "huggingface-or-local"
source_repo = "..."
revision = "..."
quantization = "..."
backend = "lmstudio-or-llama.cpp-or-vllm-or-openai"
```

Important:

- one repository should represent one model identity;
- do not mix different model IDs in the same repository;
- keep prompt/generation/parser defaults stable unless the run is intentionally a new condition.

Validate:

```bash
llmclozestat validate model --input model.toml
```

---

## 5. Configure run

Copy:

```bash
cp run.toml.example run.toml
```

Edit:

```toml
[run]
submitter_id = "your-name"
output_dir = "submissions"

[backend]
model_name = "your-backend-model-name"
# base_url = "http://localhost:1234/v1"
```

Examples:

LM Studio:

```toml
base_url = "http://localhost:1234/v1"
```

llama.cpp server:

```toml
base_url = "http://localhost:8080/v1"
```

OpenAI API:

- omit `base_url`;
- set `model_name`;
- set `OPENAI_API_KEY`.

---

## 6. Validate dataset

```bash
llmclozestat validate items --dataset datasets/smoke_v0/items.jsonl
```

---

## 7. Run measurement

```bash
llmclozestat run --config run.toml
```

Generated files:

```text
submissions/<submitter_id>/<run_id>/environment.json
submissions/<submitter_id>/<run_id>/run.jsonl
submissions/<submitter_id>/<run_id>/summary.json
submissions/<submitter_id>/<run_id>/manifest.json
```

The command output includes the concrete `submission_path`.

---

## 8. Validate output package

```bash
llmclozestat validate submission --path submissions/<submitter_id>/<run_id>
```

This checks:

- manifest presence;
- file hashes;
- package hash;
- path identity;
- environment/run/summary identity consistency;
- regenerated summary consistency.

---

## 9. Generate CSV reports

```bash
llmclozestat report \
  --submissions-dir submissions \
  --out-dir reports
```

Generated:

```text
reports/run_index.csv
reports/blank_fills.csv
```

---

## Recommended initial workflow

Start with:

- bundled smoke dataset;
- temperature = 0;
- zero-shot;
- one trial per item.

Do not:

- silently change prompts per model;
- mix incompatible prompt conditions;
- compare runs with different prompt metadata as if they were identical;
- commit private API keys or local `.env` files.
