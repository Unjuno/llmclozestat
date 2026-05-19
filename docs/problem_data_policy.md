# Problem Data Policy

Problem data is the measurement instrument of this project. Do not add items only because they are grammatically valid. Every item must state what it is designed to test.

## Required item intent

Every item must include `validation_target` with at least:

- `main_question`: what the item tests.
- `hypothesis`: the expected failure hypothesis.
- `success_condition`: what counts as successful behavior.
- `why_this_item_exists`: why this item belongs in the dataset.

Items without a clear validation target should be rejected.

## Item principles

1. Use cloze tasks, not four-choice tasks.
2. Ask the model to output the completed full sentence.
3. Support one or more blanks per item.
4. Score each blank independently.
5. Keep `segments.length == blanks.length + 1`.
6. Each blank must define `accepted_fills`.
7. Use `near_miss_fills` only for manually declared close-but-not-accepted fills.
8. Record expected error patterns when known.
9. Avoid latest-news or time-sensitive facts in early datasets.
10. Avoid copied text with unclear rights.
11. Prefer short, controlled items before long-context items.

## Multi-blank items

Multi-blank items are allowed. They are useful for testing long-distance context use, dependency between blanks, and positional failure patterns.

Each blank may define:

- `primary_skill`
- `context_distance`
- `depends_on`
- `evidence_span`
- `expected_error_patterns`

Recommended `context_distance` values:

- `local`
- `sentence`
- `cross_sentence`
- `long_context`

## Fill classes

Early versions use these classes:

- `accepted`
- `near_miss`
- `wrong`
- `format_fail`
- `parse_fail`

Do not use LLM judging in v0.x. Prefer explicit accepted and near-miss lists.

## Repeated fills

Do not deduplicate repeated fills during scoring. Repeated identical wrong fills at the same blank are a signal of systematic model behavior.
