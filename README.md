# llmclozestat

`llmclozestat` is a CLI project for cloze-based statistical profiling of LLM outputs.

It asks language models to complete fill-in-the-blank sentences and output the completed full sentence. The tool records raw outputs, extracts filled spans, classifies each fill, and aggregates statistics such as content pass rate, format compliance, strict pass rate, parse failure rate, fill distribution, repeated wrong fills, and latency.

This is not an official leaderboard. The goal is to observe model behavior statistically.

## Current status

The project starts with `smoke_v0`, a one-item dataset. This initial dataset is for pipeline validation and local probe statistics, not broad model evaluation.

## Core idea

```text
cloze item
  -> completed sentence output
  -> fill extraction
  -> blank-level scoring
  -> fill distribution
  -> model behavior profile
```

## What this is not

- Not a four-choice benchmark.
- Not an official leaderboard.
- Not an anti-tamper evaluation system.
- Not an LLM-judge scoring framework.

## Initial dataset

See:

- `datasets/smoke_v0/items.jsonl`
- `docs/problem_data_policy.md`

## Documentation

- `docs/design.md`
- `docs/problem_data_policy.md`
- `docs/result_format.md`

## Early development plan

1. Define item/result formats.
2. Implement parser and scorer.
3. Implement aggregation.
4. Add OpenAI-compatible runner for LM Studio and similar local servers.
5. Add lightweight terminal progress display.
6. Add report generation.

## License

- Code: Apache-2.0
- Dataset/docs: see `DATA_LICENSE.md`
