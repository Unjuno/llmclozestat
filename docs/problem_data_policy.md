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

## Claim scope

Items should define what a successful result can and cannot support.

Recommended field:

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

This prevents overclaiming. Passing one item should not be interpreted as general ability.

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

A good item should not test many unrelated things at once. If an item needs to test multiple responsibilities, use multiple blanks and assign each blank its own `primary_skill` and error interpretation.

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

Many models have different strengths and weaknesses by language. A probe may need multiple language variants.

Do not treat translation as automatic equivalence. A translated item can change difficulty, ambiguity, grammar, cultural assumptions, tokenization, or expected fills.

Use this distinction:

```text
probe_id:
  abstract validation target shared across languages

variant_id:
  concrete language-specific item wording
```

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

## Item construction patterns

Items may be factual, mathematical, logical, procedural, causal, spatial, or multilingual. The format is flexible, but the validation target must stay explicit.

### Formula or definition probe

Use this when testing whether the model can complete a formula, definition, or symbolic relation.

Example authoring pattern:

```text
A rectangle with width w and height h has area （blank_1）.
```

The item should state whether it tests formula recall, variable-role binding, unit consistency, or symbolic completion. Do not simply add formulas because they look technical.

### Causal or explanatory probe

Use this when testing whether the model can preserve a causal relation.

Example authoring pattern:

```text
Because the cache reduces repeated database reads, server load tends to （blank_1）.
```

The item should state the expected causal direction and the common reversal error.

### Procedure or reasoning-step probe

Use this when testing whether the model can complete a required step in a method.

Example authoring pattern:

```text
Before comparing two measurements, the units should be （blank_1）.
```

The item should state whether it tests procedural ordering, prerequisite recognition, or method discipline.

### Long-context or dependency probe

Use this when later blanks require earlier context.

Example authoring pattern:

```text
Mina put the red box on the desk. She moved the blue box to the shelf. The box left on the desk is the （blank_1） box, and the box on the shelf is the （blank_2） box.
```

Each blank should define `context_distance`, `depends_on` if relevant, and a separate error interpretation.

### Multilingual variant probe

Use this when the same abstract probe should be checked across languages.

Example structure:

```json
{
  "probe_id": "mirror_perspective_body_correspondence_0001",
  "variant_id": "mirror_perspective_body_correspondence_0001.ja",
  "language": "ja",
  "translation_relation": "original",
  "equivalence_level": "strict"
}
```

An English variant would share `probe_id` but use a different `variant_id`, language-specific wording, and language-specific accepted fills.

## Item principles

1. Use cloze tasks, not four-choice tasks.
2. Ask the model to output the completed full sentence.
3. Support one or more blanks per item.
4. Score each blank independently.
5. Keep `segments.length == blanks.length + 1`.
6. Each blank must define non-empty `accepted_fills`.
7. Use `near_miss_fills` only for manually declared close-but-not-accepted fills.
8. Record expected error patterns when known.
9. Avoid latest-news or time-sensitive facts in early datasets.
10. Avoid copied text with unclear rights.
11. Prefer short, controlled items before long-context items.
12. Do not add items whose failure interpretation is unclear.
13. Do not combine unrelated skills in a single blank.
14. Prefer one clear validation target per blank.
15. For multilingual probes, do not assume translated variants are equivalent unless documented.
16. Record `claim_scope` when an item could be overinterpreted.

## Required top-level fields

Early items should include:

- `dataset_id`
- `item_id`
- `version`
- `item_type`
- `primary_skill`
- `secondary_tags`
- `validation_target`
- `text_with_blanks`
- `segments`
- `blanks`
- `expected_full_texts`
- `ambiguity_level`
- `source_type`
- `review_status`

For multilingual variants, also include:

- `probe_id`
- `variant_id`
- `language`
- `translation_relation`
- `equivalence_level`

Recommended for interpretation:

- `claim_scope`

## Required blank fields

Each blank should include:

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
- `format_fail`: the output does not follow the requested completed-sentence format.
- `parse_fail`: the fill cannot be extracted.

Do not use LLM judging in v0.x. Prefer explicit accepted and near-miss lists.

## Repeated fills

Do not deduplicate repeated fills during scoring. Repeated identical wrong fills at the same blank are a signal of systematic model behavior.

Frequency-based statistics count all occurrences. Diversity statistics, such as `unique_fill_count`, count distinct fills separately.

## Example item

```json
{
  "dataset_id": "smoke_v0",
  "probe_id": "mirror_perspective_body_correspondence_0001",
  "variant_id": "mirror_perspective_body_correspondence_0001.ja",
  "item_id": "mirror_perspective_0001",
  "version": "0.0.1",
  "language": "ja",
  "translation_relation": "original",
  "equivalence_level": "strict",
  "item_type": "probe",
  "primary_skill": "spatial_perspective",
  "secondary_tags": ["mirror_reasoning", "left_right", "viewpoint_control"],
  "validation_target": {
    "main_question": "モデルが鏡像における現実の身体部位との対応を正しく扱えるか。",
    "hypothesis": "弱いモデルは『鏡は左右反転する』という表層知識に引きずられ、現実の右手に対応するものを左手と誤補完しやすい。",
    "success_condition": "現実の右手に対応する手として『右』を補完する。",
    "why_this_item_exists": "鏡像・左右・視点変換の混同を局所的に観測するため。"
  },
  "claim_scope": {
    "supports_claim": "日本語の短文・明示条件における鏡像の現実身体部位対応を扱えるか。",
    "does_not_support": [
      "一般的な空間推論能力",
      "長距離文脈での空間推論",
      "鏡の中の人物を正面の別人として見る視点変換"
    ],
    "required_conditions": [
      "language=ja",
      "context_distance=sentence",
      "explicit body-correspondence wording"
    ],
    "generalization_limit": "このitemは鏡像左右対応の局所probeであり、空間推論全体を代表しない。"
  },
  "text_with_blanks": "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの（blank_1）手に対応する。",
  "segments": [
    "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの",
    "手に対応する。"
  ],
  "blanks": [
    {
      "blank_id": "blank_1",
      "position": 1,
      "primary_skill": "mirror_body_correspondence",
      "context_distance": "sentence",
      "accepted_fills": ["右"],
      "near_miss_fills": [],
      "known_wrong_fills": ["左", "反対"]
    }
  ],
  "expected_full_texts": [
    "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの右手に対応する。"
  ],
  "ambiguity_level": "low",
  "source_type": "human_designed",
  "review_status": "reviewed"
}
```
