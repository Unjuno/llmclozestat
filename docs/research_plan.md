# Research Plan

This document outlines a research and evaluation plan for `llmclozestat`.

The purpose is to design a reusable local CLI workflow for collecting structured cloze-task logs and using them to compare model behavior under documented task conditions.

## 1. Background

Local LLM users often choose models through scattered impressions, short trials, benchmark summaries, or community reputation.

However, a model that is good for one task may be weak under another condition:

- language;
- field or skill;
- context length;
- output-format strictness;
- local hardware constraints;
- quantization setting;
- prompt support mode.

This makes model selection difficult when the user needs a model for a specific task.

## 2. Problem

Current local model testing is often fragmented.

Typical problems:

1. Users test models individually.
2. Results are not saved in a common format.
3. Prompts and datasets differ across users.
4. Logs are often not reusable.
5. Single aggregate scores hide field-specific and language-specific behavior.
6. Repeated trial-and-error wastes compute time and user time.

The central problem is:

```text
How can local model trials be recorded in a structured format that supports later comparison, filtering, and task-conditioned model selection?
```

## 3. Proposed approach

`llmclozestat` uses cloze probes.

A model receives a fill-in-the-blank item and must output the completed full sentence. The CLI records the raw output, extracts the fill, classifies the fill, and aggregates the result.

The method emphasizes distributions rather than one score.

It records:

- accepted fills;
- near-miss fills;
- repeated wrong fills;
- parse failures;
- format-following failures;
- language-specific behavior;
- context-distance effects;
- submitter and run provenance.

## 4. Research questions

### RQ1: Structured logging

Can local cloze-task evaluations be stored as raw JSONL records that are reusable for later aggregation?

### RQ2: Diagnostic comparison

Can fill distributions reveal behavior differences that are hidden by a single aggregate score?

### RQ3: Conditional capability profiles

Can model behavior be described as a conditional profile rather than a global label?

Example:

```text
model x probe x language x context-distance x fill-distribution
```

### RQ4: Task-conditioned model selection

Can these profiles support choosing a model for a specific task condition?

Example:

```text
task requirements -> relevant probes -> model behavior profile -> model choice
```

## 5. Core design

### Probe

A probe is the abstract validation target.

It defines what is being tested and why the item exists.

### Variant

A variant is a language-specific or wording-specific realization of a probe.

A probe may have variants such as:

```text
probe_id.ja
probe_id.en
probe_id.fr
```

Variants must not be assumed equivalent without documentation.

### Item

An item is one JSON object in `items.jsonl`.

It contains:

- `validation_target`;
- `text_with_blanks`;
- `segments`;
- `blanks`;
- `expected_full_texts`.

### Blank

A blank is the unit of extraction and content scoring.

Each blank can have:

- `accepted_fills`;
- `near_miss_fills`;
- `known_wrong_fills`;
- `expected_error_patterns`;
- `context_distance`;
- `depends_on`.

### Run

A run is a collection of trials produced under shared conditions.

Each run records:

- `submitter_id`;
- `run_id`;
- model information;
- dataset information;
- backend information;
- generation parameters.

## 6. Scoring design

The system should not collapse results into one score.

### Blank-level scoring

Each blank records:

- `extracted_fill`;
- `blank_parse_pass`;
- `content_pass`;
- `parse_fail`;
- `fill_class`.

### Item-level scoring

Each item records:

- `item_format_pass`;
- `item_partial_score`;
- `item_strict_pass`.

### Aggregate-level statistics

Aggregates include:

- `content_pass_rate`;
- `item_format_pass_rate`;
- `strict_pass_rate`;
- `parse_fail_rate`;
- `fill_distribution`;
- `unique_fill_count`;
- `top_wrong_fill`;
- `mean_entropy`;
- `avg_latency_ms`.

Repeated fills are counted. If a wrong fill appears repeatedly at the same blank, that repetition is treated as evidence of a systematic tendency.

## 7. Experimental plan

### Phase 1: Smoke test

Use a one-item dataset to verify the pipeline:

```text
item -> prompt -> model output -> extraction -> scoring -> JSONL -> aggregate
```

The current smoke item is a mirror-perspective probe in Japanese.

### Phase 2: Probe expansion

Add a small set of controlled probes across several categories:

- factual completion;
- lexical context;
- causal direction;
- logical relation;
- spatial perspective;
- technical terminology;
- output format following.

### Phase 3: Language variants

Create language-specific variants for selected probes.

Each variant must record:

- `probe_id`;
- `variant_id`;
- `language`;
- `translation_relation`;
- `equivalence_level`.

### Phase 4: Context-distance probes

Add probes that vary by context requirement:

- `local`;
- `sentence`;
- `cross_sentence`;
- `long_context`.

### Phase 5: Model comparison

Run the same dataset against multiple models under documented conditions.

Compare:

- fill distributions;
- repeated wrong fills;
- language effects;
- context-distance effects;
- format-following behavior;
- latency and local execution constraints.

## 8. Data collection workflow

The intended workflow is local-first:

```text
git clone
  -> run locally
  -> store raw JSONL under results/
  -> aggregate locally
  -> prepare submissions/<submitter_id>/<run_id>/
  -> commit or open a pull request
```

Recommended shareable package:

```text
submissions/<submitter_id>/<run_id>/
  environment.json
  run.jsonl
  summary.json
  summary.md
```

Submissions are self-reported and not authenticated. `submitter_id` and `run_id` allow later filtering and re-aggregation.

## 9. Analysis plan

Analysis should avoid broad global claims.

Weak claim:

```text
Model A is good.
```

Preferred claim:

```text
Under probe P, language L, and context condition C, Model A shows high content pass rate and low repeated wrong-fill rate.
```

Recommended analysis tables:

- model x probe;
- model x language;
- model x context_distance;
- model x primary_skill;
- model x fill_distribution;
- model x parse_fail_rate;
- model x item_format_pass_rate.

## 10. Expected contribution

The expected contribution is a reusable evaluation-log framework, not a universal benchmark score.

The project can show that:

```text
structured cloze probes + raw JSONL logs + re-aggregatable summaries
```

can support more detailed model behavior comparison than a single leaderboard-style score.

## 11. Limitations

The method depends on:

- probe quality;
- clear validation targets;
- enough trials;
- stable generation parameters;
- language variant equivalence;
- careful interpretation;
- raw log preservation.

It does not prove global model quality. It supports scoped claims under documented conditions.

## 12. Near-term milestones

1. Finalize schema for item/result/environment records.
2. Implement parser and scorer.
3. Implement aggregation.
4. Add validation commands.
5. Add OpenAI-compatible local runner.
6. Add submission package preparation.
7. Expand probes by skill, language, and context condition.
