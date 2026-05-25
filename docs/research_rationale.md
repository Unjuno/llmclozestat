# Research Rationale

`llmclozestat` is useful because a well-designed probe set can be reused across many models.

Once the probe definitions, scoring rules, and result format are fixed, different models can be evaluated under the same documented conditions. The goal is not to say only that a model is good or bad. The goal is to describe where and how it behaves differently.

## Main advantage

Many evaluations collapse model behavior into a single score. That is useful for rough comparison, but it hides the structure of model behavior.

`llmclozestat` instead records:

- which fills the model produces;
- how often it repeats each fill;
- whether errors cluster by probe;
- whether errors cluster by language;
- whether errors cluster by field or skill;
- whether failures increase with longer context;
- whether failures appear in short controlled items;
- whether the model follows the requested output format.

This makes the result more diagnostic.

## Intended comparison style

A weak comparison says:

```text
Model A is better than Model B.
```

A more useful comparison says:

```text
Model A is stable on short factual probes in Japanese but fails more often on long-context dependency probes.
Model B follows format well in English but has repeated wrong fills in Japanese spatial-perspective probes.
Model C has high near-miss rates in technical terminology but low parse-fail rates.
```

This project is designed for the second kind of comparison.

## Scoped capability claims

The project should avoid broad unqualified claims such as:

```text
This model understands space.
This model is good at reasoning.
This model is bad at Japanese.
```

A stronger claim is scoped by field, probe, language, context condition, and observed failure distribution.

Preferred style:

```text
Under probe P, in language L, with context condition C, model M shows high content pass rate and low repeated wrong-fill rate.
```

Or:

```text
Model M handles vertical/hierarchical spatial identification under condition C, but this evidence only supports that specific condition. It does not prove general spatial understanding.
```

This matters because a model may appear strong under one condition and weak under another:

- short context vs long context;
- local blank vs cross-sentence blank;
- Japanese variant vs English variant;
- formula completion vs causal explanation;
- body-correspondence perspective vs observer-perspective perspective.

The correct output is a conditional profile, not a global label.

## Dimensions of analysis

### By probe

A probe represents a specific validation target.

Example:

```text
mirror_perspective_body_correspondence_0001
```

This allows analysis such as:

```text
This model often confuses real body-part correspondence with the surface rule that mirrors reverse left and right.
```

### By field or skill

Items and blanks can define `primary_skill` and `secondary_tags`.

This allows analysis such as:

```text
The model is reliable on lexical completion but unstable on causal-direction probes.
```

### By language

Each language-specific item variant records:

- `probe_id`
- `variant_id`
- `language`
- `translation_relation`
- `equivalence_level`

This allows analysis such as:

```text
The model handles the same abstract probe in English but fails more often in Japanese.
```

Do not assume translated variants are automatically equivalent.

### By context length

Items can record `context_distance`:

- `local`
- `sentence`
- `cross_sentence`
- `long_context`

This allows analysis such as:

```text
The model succeeds on short local completions but fails when later blanks depend on earlier context.
```

### By output behavior

The result format separates:

- `item_format_pass`
- `blank_parse_pass`
- `content_pass`
- `item_strict_pass`
- `parse_fail`
- `fill_distribution`

This allows analysis such as:

```text
The model often knows the answer but fails to follow the requested completed-sentence format.
```

## Reusability

Once a probe is created and reviewed, it can be reused across:

- many models;
- many model sizes;
- quantized and non-quantized variants;
- local and API-based endpoints;
- multiple languages;
- multiple prompt support modes;
- repeated runs over time.

This makes the probe set a reusable measurement instrument.

## What this can support in research

A defensible research claim is:

```text
A reusable cloze-probe framework can reveal model-specific behavior patterns that are hidden by single aggregate scores, including field-specific errors, language-specific errors, context-length sensitivity, format-following failures, and repeated wrong-fill distributions.
```

The claim is stronger than a simple leaderboard claim because it preserves the structure of the errors.

## Limits

This method does not automatically prove general intelligence or global model quality.

It depends on:

- probe quality;
- clear validation targets;
- language variant equivalence;
- enough trials;
- stable generation conditions;
- careful aggregation;
- preserving raw logs.

If probes are vague, the analysis will be vague. If translated variants are not equivalent, cross-language comparison becomes weak. If only a few probes are used, conclusions must remain local.

## Summary

The project should not aim for:

```text
one model, one score
```

It should aim for:

```text
model x probe x language x context-length x fill-distribution
```

The final interpretation should be:

```text
model x capability x condition
```

not:

```text
model x global ability label
```

That is the core value of the tool.
