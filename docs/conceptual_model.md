# Conceptual Model

This document defines the conceptual model for `llmclozestat` before implementation.

The project is a local-first CLI for collecting cloze-task measurement logs. It does not authenticate model outputs. It records enough structure to support re-aggregation, filtering, and comparison.

## Goal

The goal is not to produce a single score.

The goal is to collect structured evidence about model behavior:

- what fills a model produces;
- where it produces repeated wrong fills;
- whether it follows the requested completed-sentence format;
- how behavior changes by language;
- how behavior changes by probe type;
- how results change across runs and submitters.

## Main entities

### Probe

A `probe` is the abstract validation target.

It answers:

```text
What are we trying to test?
```

Example:

```text
mirror_perspective_body_correspondence_0001
```

This probe tests whether a model can distinguish real body-part correspondence from the surface rule that mirrors reverse left and right.

### Variant

A `variant` is a concrete language-specific wording of a probe.

A probe may have many variants:

```text
mirror_perspective_body_correspondence_0001.ja
mirror_perspective_body_correspondence_0001.en
mirror_perspective_body_correspondence_0001.fr
```

Variants are not automatically equivalent. Each variant must declare:

- `language`
- `translation_relation`
- `equivalence_level`

### Item

An `item` is one cloze problem stored as one JSON object in `items.jsonl`.

It contains:

- `validation_target`
- `text_with_blanks`
- `segments`
- `blanks`
- `expected_full_texts`

### Blank

A `blank` is one missing span inside an item.

Each blank is scored independently.

A multi-blank item can test dependency, long-context use, and position-specific failures.

### Fill

A `fill` is the extracted text produced by the model for a blank.

Repeated fills are counted. They are not deduplicated.

### Trial

A `trial` is one model response for one item under one condition.

One trial creates one JSONL result record.

### Run

A `run` is a collection of trials produced with a shared environment and condition.

A run should have:

- `submitter_id`
- `run_id`
- dataset information
- model information
- backend information
- generation parameters

### Submission

A `submission` is a shareable package prepared for Git commit or pull request.

Recommended layout:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
```

Submissions are self-reported. They are not authenticated model certificates.

## Data path

```text
probe design
  -> language-specific variant
  -> item JSONL
  -> prompt
  -> model output
  -> raw result JSONL
  -> aggregate summary
  -> optional submission package
```

## Scoring model

Scoring is layered. Do not collapse it into one number.

### Blank-level values

Each blank records:

- `extracted_fill`
- `blank_parse_pass`
- `content_pass`
- `parse_fail`
- `fill_class`

Recommended fill classes:

- `accepted`
- `near_miss`
- `wrong`
- `format_fail`
- `parse_fail`

### Item-level values

Each item records:

- `item_format_pass`
- `item_partial_score`
- `item_strict_pass`

### Run-level values

A run aggregates item and blank results into:

- pass rates;
- parse-fail rates;
- fill distributions;
- repeated wrong fills;
- entropy and diversity statistics;
- latency statistics.

## Variable table

| Symbol | Meaning | Unit | Definition | Domain / Assumption | Type |
|---|---|---:|---|---|---|
| `m` | model | none | evaluated model identifier | finite set of model IDs | categorical |
| `u` | submitter | none | submitter identifier | stable local or GitHub name | categorical |
| `r` | run | none | run identifier | unique within submitter | categorical |
| `i` | item | none | cloze item identifier | item in dataset | categorical |
| `b` | blank | none | blank identifier inside item | blank in item | categorical |
| `t` | trial | count | repeated trial index | positive integer | integer |
| `z_{m,r,i,b,t}` | extracted fill | none | fill extracted from model output | string or null | categorical/string |
| `A_{i,b}` | accepted fill set | none | accepted fills for item `i`, blank `b` | non-empty finite set | set |
| `Y_{m,r,i,b,t}` | blank content pass | none | 1 if extracted fill is accepted, else 0 | `{0,1}` | Bernoulli |
| `F_{m,r,i,t}` | item format pass | none | 1 if whole output follows completed-sentence format | `{0,1}` | Bernoulli |
| `B_i` | blank set | count | blanks belonging to item `i` | non-empty finite set | set |
| `S_{m,r,i,t}` | item partial score | ratio | accepted blank count divided by blank count | `[0,1]` | scalar |
| `Q_{m,r,i,t}` | item strict pass | none | 1 if all blanks pass and item format passes | `{0,1}` | Bernoulli |
| `n_{m,i,b,z}` | fill count | count | number of times fill `z` appears for model/item/blank | non-negative integer | integer |
| `N_{m,i,b}` | trial count | count | number of trials for model/item/blank | positive integer | integer |
| `P_m(z | i,b)` | fill probability estimate | ratio | empirical probability of fill `z` | `[0,1]` | scalar |

## Basic equations

### Blank content pass

```text
Y_{m,r,i,b,t} = 1 if z_{m,r,i,b,t} is in A_{i,b}, otherwise 0
```

### Item partial score

```text
S_{m,r,i,t} = (1 / |B_i|) * sum over b in B_i of Y_{m,r,i,b,t}
```

### Item strict pass

```text
Q_{m,r,i,t} = F_{m,r,i,t} * product over b in B_i of Y_{m,r,i,b,t}
```

### Fill distribution

```text
n_{m,i,b,z} = count of trials where z_{m,r,i,b,t} = z
P_m(z | i,b) = n_{m,i,b,z} / N_{m,i,b}
```

Repeated identical fills increase `n_{m,i,b,z}`. They are not removed.

## Unit check

- `n_{m,i,b,z}` is a count.
- `N_{m,i,b}` is a count.
- `n / N` is a ratio.
- `Y`, `F`, and `Q` are 0/1 values.
- `S` is a ratio from 0 to 1.

The scoring values are dimensionless and suitable for aggregation.

## Interpretation rules

### Good evidence

A repeated pattern is stronger than a single output.

Example:

```text
right: 90%
left: 10%
```

This suggests the model usually handles the probe but sometimes falls into the expected error pattern.

### Systematic error

```text
left: 70%
right: 30%
```

If `left` is a known wrong fill, this suggests a systematic confusion for that probe.

### Language-specific effect

If a model succeeds in one language variant but fails in another, do not immediately infer a general reasoning failure. Check:

- variant equivalence;
- wording differences;
- accepted fills;
- grammar constraints;
- tokenization or script effects.

### Submitter/run filtering

Because submissions are self-reported, aggregation must preserve `submitter_id` and `run_id` so later reports can exclude suspicious or broken runs without editing raw logs.

## Research use

For a graduation research project, the defensible claim is not:

```text
This tool proves model X is better.
```

A better claim is:

```text
This tool collects structured cloze-task logs and estimates model-specific fill distributions, repeated error patterns, format-following behavior, and language-variant effects under documented conditions.
```

That claim is measurable and falsifiable.
