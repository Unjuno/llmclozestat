# Pinned Datasets

Place dataset snapshots used by this model repository here.

Recommended layout:

```text
datasets/pinned/<dataset_id>/
  items.jsonl
  README.md
```

Example:

```text
datasets/pinned/smoke_v0/items.jsonl
```

## Why pin datasets?

A model repository should preserve enough information to know exactly which items were measured.

If the upstream dataset changes later, old results must still be interpretable.

## Minimum requirements

For each pinned dataset, preserve:

- `dataset_id`;
- `items.jsonl` or equivalent item file;
- source repository or source note;
- source commit, tag, release, or `unknown`;
- data license when relevant.

## Do not silently mix snapshots

Results from different dataset snapshots should not be aggregated as the same condition unless the aggregation key includes the dataset version or commit.
