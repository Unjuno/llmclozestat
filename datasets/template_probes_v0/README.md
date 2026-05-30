# template_probes_v0

`template_probes_v0` is a small template dataset for multi-blank cloze probes.

Unlike `seed_probes_v0`, this dataset is not just a smoke seed. It demonstrates the intended item shape for diagnostic probes where a single blank is too weak.

## Purpose

The core rule is:

```text
one item = one measurement target
one item may contain multiple blanks
```

Multiple blanks are useful when the task has an internal structure such as:

```text
context -> concept name -> formula -> substitution/binding -> final answer
```

A single blank often hides where the model failed. For example, a model may know the final answer label while failing the intermediate calculation, or it may write a plausible formula while binding it to the wrong concept.

## Current templates

| Probe | Primary skill | Blank structure |
|---|---|---|
| `quantity_comparison_multiblank_0001` | `quantity_comparison` | difference value + final label |
| `formula_area_multiblank_0001` | `formula_representation` | concept name + symbolic formula |

## Formula blank policy

Formula blanks are allowed and encouraged for math/physics probes when the intended capability is symbolic representation.

Example pattern:

```text
context defines variables -> blank_1 asks concept name -> blank_2 asks formula
```

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

The dataset is covered by `tests/test_template_probes_dataset.py`.

## Interpretation boundary

This is not a benchmark. It is a template library for item shape, parser compatibility, and aggregation behavior.

Passing these items does not prove mathematical or physical reasoning ability. It only shows that the model can complete these narrow cloze structures under fixed prompting and generation settings.
