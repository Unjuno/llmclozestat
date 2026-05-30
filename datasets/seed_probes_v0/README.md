# seed_probes_v0

`seed_probes_v0` is a small human-designed seed dataset for testing the cloze-probe format.

It is **not** a benchmark and must not be used for leaderboard-style claims.

## Purpose

This dataset exists to verify that the project can represent and validate several probe families in one JSONL dataset.

Current families:

| Probe | Primary skill | Intended detection |
|---|---|---|
| `causal_direction_0001` | `causal_direction` | over-confident reverse causal inference |
| `spatial_perspective_0001` | `spatial_perspective` | failure to convert left/right under facing perspective |
| `temporal_order_0001` | `temporal_order` | failure to preserve explicit event order |
| `quantity_comparison_0001` | `quantity_comparison` | failure in small numeric comparison or label binding |

## Use

Validate with:

```bash
llmclozestat validate items --dataset datasets/seed_probes_v0/items.jsonl
```

Run with an explicit `run.toml` that points `run.dataset_path` at this file.

## Interpretation boundary

Each item has a narrow `validation_target` and `claim_scope`.

Passing one item does not prove the broad skill. Failing one item does not prove the model lacks the broad skill. The useful signal is the distribution of fills across repeated trials and comparable fixed conditions.

## Expansion policy

Add new items only when they satisfy all of the following:

1. One primary skill per item.
2. One explicit failure hypothesis.
3. A short blank with a narrow accepted-fill set.
4. At least one known-wrong fill tied to an interpretable error pattern.
5. Explicit `claim_scope.does_not_support` to prevent overclaiming.
6. `segments.length == blanks.length + 1`.
7. Unique `item_id` and `variant_id`.

See `docs/probe_design.md` for the taxonomy and design rationale.
