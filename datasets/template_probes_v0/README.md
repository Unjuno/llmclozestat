# template_probes_v0

`template_probes_v0` is a small template dataset for multi-blank cloze probes.

Unlike `seed_probes_v0`, this dataset is not just a smoke seed. It demonstrates the intended item shape for diagnostic probes where a single blank is too weak.

## Purpose

The core rule is:

```text
one item = one measurement target
one item may contain multiple blanks
```

Multiple blanks are useful when the task has internal structure, such as context-sensitive completion, formula expression, variable binding, or consistency across several slots.

A single blank often hides where the model failed. For example, a model may know one expected fill while producing an inconsistent fill elsewhere in the same completed sentence.

## Current templates

| Probe | Primary skill | What the template demonstrates |
|---|---|---|
| `quantity_comparison_multiblank_0001` | `quantity_comparison` | multiple numeric/label observation slots in one sentence |
| `formula_area_multiblank_0001` | `formula_representation` | formula text as one observed fill among several blanks |

## Formula blank policy

Formula blanks are allowed and encouraged for math/physics probes when the intended capability is symbolic representation.

For formula blanks:

- `accepted_fills` should include common equivalent textual forms.
- `near_miss_fills` may include spacing variants.
- `known_wrong_fills` should map to interpretable confusions, such as area vs perimeter.
- The item should not claim full mathematical ability from one formula.

## Validation

Run:

```bash
llmclozestat validate items --dataset datasets/template_probes_v0/items.jsonl
```

The dataset is covered by:

```text
tests/test_template_probes_dataset.py
tests/test_dataset_item_consistency.py
```

The consistency test checks that:

- `text_with_blanks` matches `segments` plus blank markers;
- `expected_full_texts` can be generated from `accepted_fills`;
- `known_wrong_fills` do not generate expected full texts;
- `expected_error_patterns[*].fill` is listed in `known_wrong_fills`.

## Interpretation boundary

This is not a benchmark. It is a template library for item shape, parser compatibility, and aggregation behavior.

Passing these items does not prove mathematical or physical reasoning ability. It only shows that the model can complete these narrow cloze structures under fixed prompting and generation settings.
