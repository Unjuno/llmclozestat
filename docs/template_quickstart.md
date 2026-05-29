# Template Quickstart

Goal:

Clone this repository, change a small number of settings, and obtain reproducible statistical measurements for one model.

This repository is intentionally designed around:

- one repository = one model identity;
- fixed prompt conditions;
- explicit metadata;
- reproducible run outputs;
- validation before aggregation.

---

# 1. Clone

```bash
git clone https://github.com/YOUR_NAME/llmclozestat.git
cd llmclozestat
```

---

# 2. Create Python environment

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

# 3. Configure API key

Copy:

```bash
cp .env.example .env
```

Set:

```text
OPENAI_API_KEY=...
```

For LM Studio / llama.cpp OpenAI-compatible servers, many servers accept any non-empty dummy value.

---

# 4. Configure model identity

Edit:

```text
model.toml
```

You must set at least:

```toml
[model]
model_id = "your-model"
family = "your-family"
source = "huggingface-or-local"
source_repo = "..."
revision = "..."
quantization = "..."
backend = "vllm-or-lmstudio-or-openai"
```

Important:

- One repository should represent one model identity.
- Do not mix different model IDs in the same repository.

Validation:

```bash
llmclozestat validate model --input model.toml
```

---

# 5. Configure run

Copy:

```bash
cp run.toml.example run.toml
```

Edit:

```toml
[run]
submitter_id = "your-name"

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

OpenAI:

- omit `base_url`
- set `model_name`
- set `OPENAI_API_KEY`

---

# 6. Validate dataset

```bash
llmclozestat validate items --dataset datasets/smoke_v0/items.jsonl
```

---

# 7. Run measurement

```bash
llmclozestat run --config run.toml
```

Generated files:

```text
runs/<run_id>/environment.json
runs/<run_id>/run.jsonl
runs/<run_id>/summary.json
```

---

# 8. Validate outputs

```bash
llmclozestat validate submission --path runs/<run_id>
```

This checks:

- environment schema;
- result schema;
- summary schema;
- identity consistency;
- regenerated summary consistency.

---

# 9. Generate CSV reports

```bash
llmclozestat report \
  --submissions-dir runs \
  --out-dir reports
```

Generated:

```text
reports/run_index.csv
reports/blank_fills.csv
```

---

# Recommended initial workflow

Start with:

- bundled smoke dataset;
- temperature = 0;
- zero-shot;
- one trial per item.

Do not:

- silently change prompts per model;
- mix incompatible prompt conditions;
- compare runs with different prompt metadata as if they were identical.
