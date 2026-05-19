# Design

`llmclozestat` is a CLI for cloze-based statistical profiling of LLM outputs.

The tool asks a model to fill blanks and output the completed full sentence. It records raw outputs, extracts filled spans, classifies each fill, and aggregates statistics such as content pass rate, format pass rate, strict pass rate, parse failure rate, fill distribution, repeated wrong fills, and latency.

This project is not an official leaderboard. The goal is to observe model behavior statistically.

## Scope

### v0.0

- Use a small smoke dataset.
- Read cloze items from `datasets/<dataset_id>/items.jsonl`.
- Send prompts to an OpenAI-compatible endpoint.
- Save one JSONL record per trial.
- Extract fills by using item segments.
- Score each blank independently.
- Aggregate basic statistics.

### v0.1

- Add more probe items.
- Add lightweight TUI progress display.
- Add Markdown report generation.
- Add validation for item/result files.

## Non-goals for early versions

- Four-choice multiple-choice evaluation.
- Official leaderboard.
- Anti-tamper design.
- Signatures or attestations.
- LLM-as-a-judge scoring.
- Complex IRT or clustering.
- Web dashboard.

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
```

## Core concepts

### Item

An item is a cloze problem with one or more blanks. Each item must declare what it is intended to test.

### Blank

Each blank is scored independently. For multi-blank items, the item-level score is derived from blank-level scores.

### Fill

A fill is the text extracted from a model's completed sentence at a blank position.

### Repeated fills

Repeated identical fills are not deduplicated. If the same model repeatedly gives the same wrong fill at the same blank, every occurrence is counted as evidence of a systematic tendency.
