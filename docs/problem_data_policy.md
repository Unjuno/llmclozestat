# Problem Data Policy

Problem data is the measurement instrument of this project. Do not add items only because they are grammatically valid. Every item must state what it is designed to test.

## Canonical item format

The canonical item format is JSONL.

```text
datasets/<dataset_id>/items.jsonl
```

Each line is one JSON object. YAML or Markdown authoring formats may be added later, but JSONL remains the normalized format read by the CLI.

## text_with_blanks and segments

`text_with_blanks` is for authoring, review, and display.

`segments` is the canonical parser input.

Prompt builders may render blank markers differently, for example as `（　　　）`, but scoring must rely on `segments` rather than the visual blank marker in `text_with_blanks`.

For `n` blanks:

```text
segments.length == blanks.length + 1
```

The reconstructed completed sentence is:

```text
segments[0] + fill_1 + segments[1] + fill_2 + ... + fill_n + segments[n]
```

## Required item intent

Every item must include `validation_target` with at least:

- `main_question`: what the item tests.
- `hypothesis`: the expected failure hypothesis.
- `success_condition`: what counts as successful behavior.
- `why_this_item_exists`: why this item belongs in the dataset.

Items without a clear validation target should be rejected.

## Required claim scope

Every new item must include `claim_scope`.

`claim_scope` defines what a successful result can and cannot support. This is required because the project is designed for scoped behavior claims, not broad global claims about a model.

Required shape:

```json
{
  "claim_scope": {
    "supports_claim": "short Japanese mirror body-correspondence handling under explicit wording",
    "does_not_support": [
      "general spatial reasoning",
      "long-context spatial reasoning",
      "observer-perspective transformation"
    ],
    "required_conditions": [
      "language=ja",
      "context_distance=sentence",
      "explicit body-correspondence wording"
    ],
    "generalization_limit": "This item supports only a local claim about this probe variant."
  }
}
```

Passing one item must not be interpreted as general ability.

## Identity fields

Problem identity is layered:

```text
probe_id    = abstract validation target
variant_id  = language-specific or wording-specific realization
item_id     = concrete JSONL item identifier inside a dataset
```

Rules:

- `probe_id` should remain stable across comparable language variants.
- `variant_id` should include the probe identity and language or wording variant.
- `item_id` must be unique inside a dataset.
- For multilingual variants, `item_id` should include or derive from `variant_id` unless there is a documented reason not to.

Recommended item ID pattern:

```text
<probe_id>.<language>.item_<serial>
```

Example:

```text
mirror_perspective_body_correspondence_0001.ja.item_001
mirror_perspective_body_correspondence_0001.en.item_001
```

The existing smoke item keeps its historical `item_id`, but new datasets should use the more explicit pattern.

## Responsibility separation

Do not mix every concern into the sentence itself. Problem authoring must separate these responsibilities:

| Responsibility | Stored in | Purpose |
|---|---|---|
| Validation intent | `validation_target` | Explain what the item tests and why it exists. |
| Claim scope | `claim_scope` | Explain what can and cannot be concluded from the item. |
| Surface wording | `text_with_blanks` | Provide a human-readable item. |
| Parser structure | `segments` and `blanks` | Define how fills are extracted. |
| Scoring rule | `accepted_fills`, `near_miss_fills` | Define what counts as accepted or close. |
| Error interpretation | `expected_error_patterns`, `known_wrong_fills` | Explain what repeated wrong fills may mean. |
| Context dependency | `context_distance`, `depends_on`, `evidence_span` | Explain what information must be used. |
| Language variant | `language`, `probe_id`, `variant_id`, `translation_relation` | Separate the abstract probe from a language-specific wording. |

A good item should not test many unrelated things at once.

## Probe design workflow

Do not start from a random sentence. Start from a testable reason.

Recommended workflow:

```text
1. Decide the capability or failure mode to test.
2. Write the hypothesis.
3. Write the shortest item that isolates that hypothesis.
4. Define the claim scope.
5. Define accepted fills.
6. Define known wrong or near-miss fills.
7. Explain what each expected error means.
8. Check whether a wrong answer would be interpretable.
9. Decide whether the item needs language variants.
10. Only then add the item.
```

A good item should answer these questions:

- What does this item test?
- Why does this item belong in the dataset?
- What does the accepted fill demonstrate?
- What would a common wrong fill suggest?
- What can be concluded if the model passes?
- What must not be concluded from this item alone?
- Is the item testing one main thing, or several unrelated things?
- Can the fill be extracted mechanically from `segments`?
- Is the result language-dependent?
- If translated, is the translated item still testing the same thing?

## Multilingual probe design

Do not treat translation as automatic equivalence. A translated item can change difficulty, ambiguity, grammar, cultural assumptions, tokenization, or expected fills.

Recommended fields for language-aware items:

- `probe_id`: stable ID for the abstract probe.
- `variant_id`: stable ID for this language-specific variant.
- `language`: BCP-47-style language tag, such as `ja`, `en`, `fr`, `de`, `zh-Hans`.
- `source_variant_id`: variant this item was derived from, if any.
- `translation_relation`: `original`, `human_translation`, `adapted_translation`, or `non_equivalent_probe`.
- `translation_notes`: what changed during translation or adaptation.
- `equivalence_level`: `strict`, `near`, `adapted`, or `not_equivalent`.

### Equivalence levels

| Level | Meaning |
|---|---|
| `strict` | Same validation target, same relevant ambiguity, same expected reasoning. |
| `near` | Same main target, but wording or grammar changes difficulty slightly. |
| `adapted` | Same broad skill, but language-specific adaptation changes the exact probe. |
| `not_equivalent` | Similar topic, but should not be aggregated as the same probe. |

Repository-wide analysis should aggregate by `probe_id` only when language variants are marked `strict` or explicitly accepted as comparable.

Language-specific analysis should aggregate by `language` and `variant_id`.

## Required top-level fields

Items must include:

- `dataset_id`
- `probe_id`
- `variant_id`
- `item_id`
- `version`
- `language`
- `translation_relation`
- `equivalence_level`
- `item_type`
- `primary_skill`
- `secondary_tags`
- `validation_target`
- `claim_scope`
- `text_with_blanks`
- `segments`
- `blanks`
- `expected_full_texts`
- `ambiguity_level`
- `source_type`
- `review_status`

## Required blank fields

Each blank must include:

- `blank_id`
- `position`
- `primary_skill`
- `accepted_fills`
- `near_miss_fills`

Recommended fields:

- `known_wrong_fills`
- `expected_error_patterns`
- `context_distance`
- `depends_on`
- `evidence_span`

If `known_wrong_fills` is non-empty, `expected_error_patterns` should normally explain at least the important expected wrong fills.

## Fill lists

- `accepted_fills` must be non-empty.
- `near_miss_fills` contains close but not accepted fills.
- `known_wrong_fills` contains expected wrong fills useful for interpretation.
- Repeated strings inside a fill list should be rejected.
- Normalized duplicates should be detected by validation code, not only by schema.

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

For dependent blanks, `depends_on` should name the earlier blank IDs whose results or surrounding context are needed.

## Fill classes

Early versions use these classes:

- `accepted`: the extracted fill is in `accepted_fills`.
- `near_miss`: the extracted fill is in `near_miss_fills`.
- `wrong`: the fill is extracted but not accepted or near-miss.
- `format_fail`: reserved for output-contract problems.
- `parse_fail`: the fill cannot be extracted.

Do not use LLM judging in v0.x. Prefer explicit accepted and near-miss lists.

## Repeated fills

Do not deduplicate repeated fills during scoring. Repeated identical wrong fills at the same blank are a signal of systematic model behavior.

Frequency-based statistics count all occurrences. Diversity statistics, such as `unique_fill_count`, count distinct fills separately.

## Example item

The smoke dataset contains the current reference example:

```text
datasets/smoke_v0/items.jsonl
```

New examples should follow the required-field list above and use explicit `claim_scope` and stable identity fields.
