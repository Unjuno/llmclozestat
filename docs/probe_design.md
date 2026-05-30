# Probe Design Taxonomy

This document defines the item-design policy for `llmclozestat`.

The project should not start by copying broad multiple-choice benchmarks. It should build cloze probes where each item has one explicit measurement target, one interpretable failure hypothesis, and as many blanks as needed to expose the path from input evidence to final answer.

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

Use one blank only when the target is a single local distinction, such as polarity, left/right, or one label. Use multiple blanks when the target requires an intermediate state, a binding step, or a final answer that can be separated from the evidence extraction step.

## Blank roles

Multi-blank items should assign roles to blanks in a `measurement_plan` field.

Recommended roles:

| Role | Purpose |
|---|---|
| `evidence_extraction` | checks whether the model copies or identifies the relevant fact |
| `intermediate_state` | checks an intermediate inferred value |
| `binding` | checks whether the inferred value is attached to the correct label/entity |
| `final_answer` | checks the final answer the item is mainly about |
| `calibration` | checks whether the model says certainty/possibility correctly |

Example:

```json
{
  "measurement_plan": {
    "target_blank_id": "blank_2",
    "blank_roles": {
      "blank_1": "intermediate_state",
      "blank_2": "final_answer"
    }
  }
}
```

## Initial probe families

| Family | What it detects | Good cloze shape | Failure signal |
|---|---|---|---|
| `negation_scope` | Whether the model tracks what a negation does and does not assert | short sentence or two-step certainty probe | negation word or over-strong certainty word |
| `causal_direction` | Whether the model reverses cause and effect | condition/result sentence with final certainty blank | proof/certainty fill where only possibility exists |
| `temporal_order` | Whether the model preserves event order | ordered events plus intermediate/latest/earliest blanks | last-mentioned event or salient wrong noun |
| `spatial_perspective` | Whether the model changes viewpoint | facing-agent relation plus viewpoint/final-side blanks | original viewpoint answer |
| `class_inclusion` | Whether the model reverses category inclusion | all A are B plus intermediate/final entailment blanks | proof/certainty fill |
| `quantity_comparison` | Whether the model handles numeric comparison and label binding | quantity blank plus label blank | wrong label or non-existent label |
| `idiom_literalness` | Whether the model over-literalizes idioms | quoted idiom plus literal/figurative blank | literal acceptance fill |
| `coreference` | Whether the model resolves a referent using causal/common-sense cue | cause cue plus referent/final object blanks | nearby distractor noun |

## Item authoring rules

Each item must satisfy the following:

1. One item has one primary measurement target.
2. One item may have one or more blanks; do not force single-blank form.
3. Each blank must have a role when the item has multiple blanks.
4. At least one blank should be the target blank used for the primary interpretation.
5. `accepted_fills` must be narrow enough to aggregate.
6. `known_wrong_fills` must correspond to interpretable error hypotheses.
7. `claim_scope.does_not_support` must explicitly say what the item does **not** prove.
8. Avoid high-stakes factual claims in seed items unless the source is pinned and cited.
9. Avoid ambiguous blanks whose correct answer depends on unstated pragmatic assumptions.
10. Prefer adversarial pairs later, but do not require pairs in the seed dataset.

## Why cloze rather than multiple choice

Multiple-choice tasks can confound reasoning with option-order bias, option-token prior, and test-taking heuristics. Cloze tasks expose the actual filled string, making repeated wrong fills and parse failures observable. The trade-off is that item authors must define accepted, near-miss, and known-wrong fills carefully.

## Seed dataset policy

`datasets/seed_probes_v0/items.jsonl` is a design seed, not a benchmark.

It should be used to verify that:

- the item schema can represent several probe families;
- the parser/scorer can aggregate nontrivial blank classes;
- repeated wrong fills are interpretable;
- future dataset expansion has a concrete authoring pattern.

Single-blank seed items are acceptable only as smoke examples. Multi-blank template items should be used when testing whether the framework can represent the actual diagnostic structure of a task.

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
