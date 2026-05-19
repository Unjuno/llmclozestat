# Contributing

This project is in an early design and smoke-test phase.

## Current contribution priorities

1. Improve item format and result format documents.
2. Add or revise small probe items with clear validation targets.
3. Implement parser, scorer, aggregate, and CLI components.

## Problem item requirements

Do not add a problem only because it reads naturally. Every item must state what it tests.

Required intent fields:

- `validation_target.main_question`
- `validation_target.hypothesis`
- `validation_target.success_condition`
- `validation_target.why_this_item_exists`

Each blank must define accepted fills.

## Result submissions

Community result submissions are not collected in this repository yet.

For now, keep local outputs under `results/`, which is ignored by Git. A separate results repository may be created later.
