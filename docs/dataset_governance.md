# Dataset Governance

This repository has two roles.

1. It is a template for one-model measurement repositories.
2. It is the upstream home for reviewed cloze datasets.

Forked or copied repositories should usually measure one model. They may add local datasets for private experiments, but reusable high-quality items should be proposed back to this upstream repository.

## Repository split

### Upstream repository

The upstream repository maintains:

- CLI implementation;
- schemas;
- validation rules;
- template files;
- reviewed public datasets;
- smoke datasets;
- documentation.

### Derived model repository

A derived model repository maintains:

- one `model.toml` identity;
- local `run.toml` configuration;
- generated submissions for that model;
- reports generated from those submissions.

A derived repository should not become a general mixed-model benchmark repository.

## Dataset policy

Datasets under `datasets/` are treated as reusable measurement assets.

Additions should satisfy:

- clear claim scope;
- explicit accepted fills;
- explicit near-miss fills when useful;
- explicit known-wrong fills when useful;
- stable IDs;
- no hidden answer ambiguity;
- no prompt-condition dependence;
- no copyrighted long passages unless license permits reuse;
- small enough examples for review.

## Local-only datasets

Private or experimental datasets can live outside Git-tracked paths, for example:

```text
data/local_items.jsonl
```

The default `.gitignore` excludes `data/`.

Use local datasets for exploration. Promote only reviewed, reusable items into `datasets/`.

## Contribution path for new items

Recommended path:

```text
1. Create or collect candidate items locally.
2. Validate them with `llmclozestat validate items`.
3. Run smoke measurements locally.
4. Inspect repeated wrong fills and ambiguity.
5. Promote stable items into `datasets/<dataset_id>/items.jsonl`.
6. Add or update `datasets/<dataset_id>/README.md`.
7. Open a PR to the upstream repository.
```

## What derived repositories should pull from upstream

Derived model repositories should periodically pull:

- CLI fixes;
- schema updates;
- validation updates;
- new reviewed datasets.

They should preserve their own:

- `model.toml`;
- local `run.toml`;
- submissions;
- generated reports.

## Non-goals

This repository does not try to prove that a model actually ran. It records and validates self-reported measurement artifacts. The goal is reproducible structure, not execution attestation.
