# Design

`llmclozestat` is a CLI for cloze-based statistical profiling of LLM outputs.

The tool asks a model to fill blanks and output the completed full sentence. It records raw outputs, extracts filled spans, classifies each fill, and aggregates statistics such as content pass rate, item format pass rate, strict pass rate, parse failure rate, fill distribution, repeated wrong fills, and latency.

This project is not an official leaderboard. The goal is to observe model behavior statistically.

## Design position

`llmclozestat` is a measurement-log tool, not a ranking site.

The primary artifact is raw JSONL. Reports and summaries are derived artifacts. A user should be able to re-aggregate results from raw records.

The intended operating model is local-first:

```text
git clone
  -> run evaluations locally
  -> accumulate raw JSONL
  -> aggregate summaries
  -> prepare a submission package
  -> commit or open a pull request
```

The repository may accumulate submitted results through ordinary Git history. These are self-reported measurement logs, not authenticated model certificates.

Package-level manifest hashing is in scope for publishable submissions. It is used only for post-packaging tamper detection. It does not authenticate model execution and does not prove that a claimed model produced a result.

## Scope

### v0.0

- Use a one-item smoke dataset.
- Read cloze items from `datasets/<dataset_id>/items.jsonl`.
- Treat JSONL as the canonical item format.
- Support one or more blanks in the item schema.
- Extract fills by using item `segments`.
- Score each blank independently.
- Save one JSONL record per trial.
- Aggregate basic statistics from raw records.

### v0.1

- Add a small probe dataset.
- Add validation for item/result files.
- Add OpenAI-compatible runner for LM Studio and similar local servers.
- Add lightweight terminal progress display.
- Add Markdown report generation.
- Add a command or documented process for preparing `submissions/<submitter_id>/<run_id>/` packages.
- Add package-level manifest generation and local integrity verification for publishable submissions.

### Later

- Add more probe categories.
- Add long-context and dependent multi-blank probes.
- Add optional task-shot and control-shot conditions.
- Consider advanced statistics outside the core v0.x path.

## Non-goals for early versions

- Four-choice multiple-choice evaluation.
- Official leaderboard.
- Model-output authentication.
- Model execution attestation.
- Proof that a claimed model truly generated a result.
- Mandatory signatures.
- Per-trial ledger anchoring.
- LLM-as-a-judge scoring.
- Complex IRT or clustering.
- Web dashboard.

## Integrity boundary

The project distinguishes these concepts:

| Concept | In scope? | Meaning |
|---|---:|---|
| Model authentication | No | Proving that a claimed model generated a result. |
| Execution attestation | No | Proving the local runtime, backend, or model file was honest. |
| Package tamper detection | Yes | Detecting later changes to a prepared submission package. |
| Optional signatures | Later | Showing that a key holder claimed responsibility for a package hash. |

A verified manifest means the submitted files still match the package hash. It does not mean the run was honestly produced.

## Data flow

```text
items.jsonl
  -> prompt builder
  -> model provider
  -> raw output
  -> parser
  -> scorer
  -> run.jsonl
  -> aggregate summary
  -> report
  -> optional submission package
  -> manifest.json for publishable submissions
```

## Core concepts

### Item

An item is a cloze problem with one or more blanks. Each item must declare what it is intended to test through `validation_target`.

### Blank

A blank is a single missing span in an item. Each blank is scored independently. For multi-blank items, the item-level score is derived from blank-level scores.

### Segment

Segments are the fixed text parts around blanks. For `n` blanks, an item must have `n + 1` segments.

```text
segments[0] + blank_1 + segments[1] + blank_2 + ... + segments[n]
```

### Fill

A fill is the text extracted from a model's completed sentence at a blank position.

### Repeated fills

Repeated identical fills are not deduplicated. If the same model repeatedly gives the same wrong fill at the same blank, every occurrence is counted as evidence of a systematic tendency.

## Scoring levels

### Blank-level

- `blank_parse_pass`: whether a fill could be extracted for the blank.
- `content_pass`: whether the extracted fill is accepted.
- `parse_fail`: whether no fill could be extracted for the blank.
- `fill_class`: accepted, near_miss, wrong, format_fail, or parse_fail.

Do not use `format_pass` at the blank level. Format is an item-level property; extraction is a blank-level property.

### Item-level

- `instruction_following_pass`: whether the explicit completed-sentence output instruction was followed.
- `item_format_pass`: whether the whole output followed the requested completed-sentence format.
- `item_partial_score`: accepted blank count divided by blank count.
- `item_strict_pass`: true only when all blanks pass content, `instruction_following_pass` is true, and `item_format_pass` is true.

## Provider strategy

The first backend target is OpenAI-compatible HTTP APIs. This includes LM Studio local server usage. Provider-specific expansion is intentionally delayed.

## Result strategy

There are two result locations:

```text
results/
  local scratch outputs, ignored by Git

submissions/<submitter_id>/<run_id>/
  publishable result package, intended for commit or pull request
```

Recommended publishable submission package:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
  manifest.json
```

Submitted results are self-reported. The project does not authenticate that a claimed model produced a given run.

`manifest.json` is required for publishable submissions and optional for local scratch results. If a submission intentionally omits `manifest.json`, reports should mark it as unverified rather than treating it as integrity-checked.
