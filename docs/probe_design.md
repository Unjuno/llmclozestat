# Probe Design Taxonomy

This document defines the first item-design policy for `llmclozestat`.

The project should not start by copying broad multiple-choice benchmarks. It should build small cloze probes where each item has one explicit failure hypothesis and one measurable blank-level outcome.

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

## Initial probe families

| Family | What it detects | Good cloze shape | Failure signal |
|---|---|---|---|
| `negation_scope` | Whether the model tracks what a negation does and does not assert | short sentence with one blank before a predicate | negation word or over-strong certainty word |
| `causal_direction` | Whether the model reverses cause and effect | condition/result sentence, blank before `できない` | proof/certainty fill where only possibility exists |
| `temporal_order` | Whether the model preserves event order | three explicit events, blank asks earliest/latest event | last-mentioned event or salient wrong noun |
| `spatial_perspective` | Whether the model changes viewpoint | facing-agent left/right relation | original viewpoint answer |
| `class_inclusion` | Whether the model reverses category inclusion | all A are B, blank tests whether B implies A | proof/certainty fill |
| `quantity_comparison` | Whether the model handles small numeric comparison and label binding | two labeled counts, blank is label | wrong label or non-existent label |
| `idiom_literalness` | Whether the model over-literalizes idioms | quoted idiom, blank tests literal claim | literal acceptance fill |
| `coreference` | Whether the model resolves a referent using causal/common-sense cue | two candidate nouns, blank asks resolved object | nearby distractor noun |

## Item authoring rules

Each item must satisfy the following:

1. One item, one primary failure hypothesis.
2. The blank should be short: usually one noun, adjective, label, or polarity word.
3. `accepted_fills` must be narrow enough to aggregate.
4. `known_wrong_fills` must correspond to interpretable error hypotheses.
5. `claim_scope.does_not_support` must explicitly say what the item does **not** prove.
6. Avoid high-stakes factual claims in seed items unless the source is pinned and cited.
7. Avoid ambiguous blanks whose correct answer depends on unstated pragmatic assumptions.
8. Prefer adversarial pairs later, but do not require pairs in the seed dataset.

## Why cloze rather than multiple choice

Multiple-choice tasks can confound reasoning with option-order bias, option-token prior, and test-taking heuristics. Cloze tasks expose the actual filled string, making repeated wrong fills and parse failures observable. The trade-off is that item authors must define accepted, near-miss, and known-wrong fills carefully.

## Initial seed dataset policy

`datasets/seed_probes_v0/items.jsonl` is a design seed, not a benchmark.

It should be used to verify that:

- the item schema can represent several probe families;
- the parser/scorer can aggregate nontrivial blank classes;
- repeated wrong fills are interpretable;
- future dataset expansion has a concrete authoring pattern.

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
