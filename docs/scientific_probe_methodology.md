# Scientific Probe Methodology

This document defines a lightweight review protocol for `llmclozestat` probe items.

It is intentionally small. The goal is not to make every item look scientific by adding long metadata. The goal is to prevent overclaiming and catch weak item designs before they enter a dataset.

## Core rule

A probe item should have a traceable path:

```text
measurement target -> blanks -> scoring rule -> interpretation limit
```

If this path is unclear, the item is not ready.

## Minimum review checklist

Before adding or expanding a probe item, answer these five questions in the PR description or dataset README:

1. **Target**: What specific behavior or failure mode is this item trying to observe?
2. **Blank roles**: What does each blank measure?
3. **Wrong fills**: What does each known-wrong fill mean?
4. **Decision rule**: What result would count as usable evidence, failure, or uncertainty?
5. **Limit**: What must not be concluded from this item?

Do not force these answers into every JSONL record unless there is a clear implementation need. Long item records become hard to audit.

## Multi-blank policy

Use multiple blanks when the target has internal structure:

```text
context -> concept -> formula -> binding/substitution -> final answer
```

A single blank is acceptable only when the target is genuinely local, such as one polarity word, one label, or one side relation.

## Formula blank policy

Formula blanks are valid for math and physics-style probes.

However, current scoring is still based on listed accepted fills. Therefore:

- list common equivalent spellings explicitly;
- mark near-miss formatting variants separately;
- include known-wrong fills that represent interpretable confusions;
- do not claim full formula reasoning until symbolic equivalence and unit checks exist.

## Current limitations

The current implementation still lacks:

- symbolic formula equivalence normalization;
- unit or dimensional consistency scoring;
- confidence intervals in reports;
- item contamination checks;
- inter-reviewer agreement tracking.

Until these exist, results should be described as local diagnostic observations, not broad model capability rankings.
