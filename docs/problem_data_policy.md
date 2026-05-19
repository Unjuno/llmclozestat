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
  "item_id": "mirror_perspective_0001",
  "version": "0.0.1",
  "item_type": "probe",
  "primary_skill": "spatial_perspective",
  "secondary_tags": ["mirror_reasoning", "left_right", "viewpoint_control"],
  "validation_target": {
    "main_question": "モデルが鏡像における現実の身体部位との対応を正しく扱えるか。",
    "hypothesis": "弱いモデルは『鏡は左右反転する』という表層知識に引きずられ、現実の右手に対応するものを左手と誤補完しやすい。",
    "success_condition": "現実の右手に対応する手として『右』を補完する。",
    "why_this_item_exists": "鏡像・左右・視点変換の混同を局所的に観測するため。"
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
