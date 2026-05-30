# Probe Design Taxonomy

This document defines the item-design policy for `llmclozestat`.

The project should not start by copying broad multiple-choice benchmarks. It should build cloze probes where each item has one explicit measurement target, one interpretable failure hypothesis, and enough blanks to expose useful output variation without over-structuring the answer.

The previous seed-only rule of using a single blank per item is not a general design rule. It is acceptable for smoke tests, but it is too weak for real diagnostic templates because it often measures lexical prior or local phrase completion rather than the intended reasoning structure.

## Research basis

Representative benchmark families show that LLM evaluation usually targets several recurring dimensions:

- broad multitask knowledge and problem solving, as in MMLU;
- diverse emergent or unusual capabilities, as in BIG-bench;
- multi-metric scenario evaluation, as in HELM;
- truthfulness and common misconception resistance, as in TruthfulQA;
- commonsense continuation and adversarial filtering, as in HellaSwag;
- pronoun/coreference commonsense reasoning, as in WinoGrande;
- discrete reading and numerical reasoning, as in DROP;
- multi-step arithmetic, as in GSM8K;
- bias under under-informative or stereotype-aligned contexts, as in BBQ.

For `llmclozestat`, these should be compressed into cloze-style probes rather than copied as multiple-choice tasks.

## Probe unit

A probe item should be designed around this unit:

```text
one item = one measurement target
one measurement target = one interpretable failure hypothesis
one item may contain multiple blanks
```

The number of blanks is determined by the measurement target.

Use one blank only when the target is a single local distinction, such as polarity, left/right, or one label. Use multiple blanks when the target needs context-sensitive completion, formula expression, variable binding, or a visible path from context to final answer.

## Blank slots, not blank roles

A blank is an observation slot, not a guaranteed semantic unit.

Do not require every blank to have a fixed conceptual role such as `concept_name`, `formula`, or `final_answer`. The model may fill the blanks in unexpected ways, and forcing a role per blank can overfit the item format before pilot data exists.

The item should carry the measurement responsibility. The blanks should remain lightweight slots with accepted, near-miss, and known-wrong fills where those are known.

Use item-level fields such as `validation_target`, `claim_scope`, and `notes` to explain what the whole item is intended to observe. Avoid adding per-blank plans unless an implementation feature actually needs them.

## Initial probe families

| Family | What it detects | Good cloze shape | Failure signal |
|---|---|---|---|
| `negation_scope` | Whether the model tracks what a negation does and does not assert | short sentence or two-step certainty probe | negation word or over-strong certainty word |
| `causal_direction` | Whether the model reverses cause and effect | condition/result sentence with final certainty slot | proof/certainty fill where only possibility exists |
| `temporal_order` | Whether the model preserves event order | ordered events with enough slots to expose ordering errors | last-mentioned event or salient wrong noun |
| `spatial_perspective` | Whether the model changes viewpoint | facing-agent relation with side-completion slots | original viewpoint answer |
| `class_inclusion` | Whether the model reverses category inclusion | all A are B plus entailment/certainty slot | proof/certainty fill |
| `quantity_comparison` | Whether the model handles numeric comparison and label binding | quantity and label slots when useful | wrong label or non-existent label |
| `idiom_literalness` | Whether the model over-literalizes idioms | quoted idiom plus literalness slot | literal acceptance fill |
| `coreference` | Whether the model resolves a referent using causal/common-sense cue | cause cue plus referent-completion slot | nearby distractor noun |

## Item authoring rules

Each item must satisfy the following:

1. One item has one primary measurement target.
2. One item may have one or more blanks; do not force single-blank form.
3. Do not require per-blank semantic roles before pilot data shows they are useful.
4. `accepted_fills` must be narrow enough to aggregate.
5. `known_wrong_fills` must correspond to interpretable error hypotheses when possible.
6. `claim_scope.does_not_support` must explicitly say what the item does **not** prove.
7. Avoid high-stakes factual claims in seed items unless the source is pinned and cited.
8. Avoid ambiguous blanks whose correct answer depends on unstated pragmatic assumptions.
9. Prefer adversarial pairs later, but do not require pairs in the seed dataset.

## Why cloze rather than multiple choice

Multiple-choice tasks can confound reasoning with option-order bias, option-token prior, and test-taking heuristics. Cloze tasks expose the actual filled string, making repeated wrong fills and parse failures observable. The trade-off is that item authors must define accepted, near-miss, and known-wrong fills carefully.

## Seed dataset policy

`datasets/seed_probes_v0/items.jsonl` is a design seed, not a benchmark.

It should be used to verify that:

- the item schema can represent several probe families;
- the parser/scorer can aggregate nontrivial blank classes;
- repeated wrong fills are interpretable;
- future dataset expansion has a concrete authoring pattern.

Single-blank seed items are acceptable only as smoke examples. Multi-blank template items should be used when testing whether the framework can represent richer diagnostic structures without requiring per-blank role metadata.

It should not be used to claim model capability rankings.

## References

- Hendrycks et al., `Measuring Massive Multitask Language Understanding`, arXiv:2009.03300.
- Srivastava et al., `Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models`, arXiv:2206.04615.
- Liang et al., `Holistic Evaluation of Language Models`, arXiv:2211.09110.
- Lin, Hilton, Evans, `TruthfulQA: Measuring How Models Mimic Human Falsehoods`, arXiv:2109.07958.
- Zellers et al., `HellaSwag: Can a Machine Really Finish Your Sentence?`, arXiv:1905.07830.
- Sakaguchi et al., `WinoGrande: An Adversarial Winograd Schema Challenge at Scale`, arXiv:1907.10641.
- Dua et al., `DROP: A Reading Comprehension Benchmark Requiring Discrete Reasoning Over Paragraphs`, arXiv:1903.00161.
- Cobbe et al., `Training Verifiers to Solve Math Word Problems`, arXiv:2110.14168.
- Parrish et al., `BBQ: A Hand-Built Bias Benchmark for Question Answering`, arXiv:2110.08193.
