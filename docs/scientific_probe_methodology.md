# Scientific Probe Methodology

This document defines the minimum scientific design standard for `llmclozestat` probe items.

A probe item is not scientifically useful merely because it resembles an existing benchmark task. It must state what construct it attempts to observe, how the construct is operationalized as blanks, what result would support or fail the hypothesis, and what alternative explanations remain.

## Why this document exists

The repository already contains cloze items and a probe taxonomy. That is not enough.

A scientifically useful item needs a traceable path:

```text
construct -> operationalization -> observable blank outcomes -> decision rule -> uncertainty statement
```

Without this path, a failure can be over-interpreted. For example, a wrong formula blank may indicate formula confusion, parsing failure, symbol-format mismatch, or ambiguity in accepted fills.

## Design standard: H/T/D/C/U

Each non-smoke template item should include a `scientific_design` object with these fields:

| Field | Meaning |
|---|---|
| `construct` | The latent capability or failure mode being probed |
| `operationalization` | How the construct is turned into observable blank outcomes |
| `H` | Falsifiable hypothesis with measurement target and threshold |
| `T` | Minimal validation plan: data, environment, minimum trials, stopping rule |
| `D` | Decision rule: PASS / FAIL / UNCERTAIN conditions |
| `C` | Competing explanations and expected failure modes |
| `U` | Uncertainty sources and current mitigation |

This is not full psychometrics. It is a minimum design discipline for avoiding ungrounded benchmark claims.

## Required interpretation discipline

Use these rules when writing or reviewing items:

1. Do not claim broad ability from one item.
2. Do not claim causal model behavior from one fill distribution alone.
3. Separate target blank and supporting blanks.
4. Prefer multi-blank designs when a task has intermediate structure.
5. For formula blanks, record whether scoring is exact string matching, enumerated equivalence, or symbolic normalization.
6. Include plausible competing explanations.
7. Include an uncertainty statement before expanding the dataset.

## Decision-rule example

For a two-blank quantity comparison item:

```text
H: Under fixed prompt/generation settings, a model that can perform the target comparison should produce accepted fills for both the intermediate difference blank and final label blank in at least 95% of trials.
T: Run n_min=20 trials, temperature=0 when supported, fixed dataset/hash/model/prompt/generation settings, no early PASS before n_min.
D: PASS if both blanks pass in >=95% of trials; FAIL if target blank pass rate <80%; UNCERTAIN otherwise or if parse_fail_rate >10%.
C: failure may be arithmetic error, label-binding error, output-format mismatch, or prompt misunderstanding.
U: uncertainty comes from parser strictness, sampling nondeterminism, backend differences, and accepted-fill incompleteness.
```

Thresholds are item-family defaults, not universal truth. They should be revised after pilot data.

## Relation to existing benchmark research

The methodology borrows broad evaluation lessons without copying task format:

- MMLU demonstrates the value of broad subject coverage but also motivates avoiding overclaiming from narrow items.
- BIG-bench motivates diverse task families and explicit capability boundaries.
- HELM motivates scenario/metric separation and multi-metric reporting rather than a single score.
- TruthfulQA motivates adversarial construction around common false beliefs and explicit misconception targets.
- WinoGrande and HellaSwag motivate adversarial commonsense and continuation-style probes, but cloze items should expose the actual fill string.
- DROP and GSM8K motivate separating reading, intermediate quantities, and final answer.
- BBQ motivates distinguishing under-informative from informative contexts when testing bias-sensitive items.

## Dataset policy

- `smoke_v0`: pipeline smoke data. It may be very small and should not be interpreted scientifically.
- `seed_probes_v0`: small seed examples. They should not be used for ranking claims.
- `template_probes_v0`: item-shape templates. Items here should carry `scientific_design`.

Future benchmark-like datasets should not be created until template items have been pilot-tested and revised.

## Known limitations

Current implementation still lacks:

- symbolic formula equivalence normalization;
- dimensional/unit consistency scoring;
- item response modeling;
- inter-annotator review workflow;
- contamination analysis;
- confidence intervals and sequential testing in reports.

Until these exist, results should be framed as local diagnostic observations, not as general model capability rankings.
