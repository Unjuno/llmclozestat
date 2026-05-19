# Result Format

The primary artifact is raw JSONL. Each line represents one model trial for one item.

Reports and summaries are derived artifacts. They should be reproducible from raw JSONL.

## Result record

A result record should contain:

```json
{
  "dataset_id": "smoke_v0",
  "model_id": "local-model",
  "backend": "openai-compatible",
  "item_id": "mirror_perspective_0001",
  "trial_id": 1,
  "prompt_template_id": "fill_full_sentence_v1",
  "support_mode": "zero",
  "f_shot": 0,
  "raw_output": "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの右手に対応する。",
  "normalized_output": "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの右手に対応する。",
  "blank_results": [
    {
      "blank_id": "blank_1",
      "position": 1,
      "extracted_fill": "右",
      "fill_class": "accepted",
      "format_pass": true,
      "content_pass": true,
      "parse_fail": false,
      "format_score_f1": 1.0,
      "format_score_edit": 1.0,
      "content_score_f1": 1.0
    }
  ],
  "item_format_pass": true,
  "item_strict_pass": true,
  "item_partial_score": 1.0,
  "latency_ms": 0,
  "temperature": 0,
  "max_tokens": 64
}
```

## Record identity

Recommended identity fields:

- `dataset_id`
- `model_id`
- `backend`
- `item_id`
- `trial_id`
- `prompt_template_id`
- `support_mode`

For repeated trials, do not overwrite earlier rows. Append a new JSONL row.

## Blank-level scoring

Each blank is scored independently.

- `format_pass`: the output can be interpreted as the requested completed sentence format for this blank.
- `content_pass`: the extracted fill is in `accepted_fills`.
- `parse_fail`: the fill could not be extracted.
- `fill_class`: one of `accepted`, `near_miss`, `wrong`, `format_fail`, `parse_fail`.

## Item-level scoring

- `item_partial_score`: accepted blank count divided by blank count.
- `item_strict_pass`: true only when all blanks are content-pass and the item format is acceptable.
- `item_format_pass`: true when the completed sentence format can be parsed for the item.

## Similarity scores

Similarity scores are diagnostic metrics, not the primary correctness rule.

Recommended early metrics:

- `format_score_f1`: surface similarity between normalized output and expected completed sentence.
- `format_score_edit`: normalized edit-distance similarity.
- `content_score_f1`: surface similarity between extracted fill and accepted fills.

Do not use these scores as the only correctness rule. A wrong sentence may still have high surface similarity.

Primary correctness should come from extraction and explicit fill lists.

## Fill distribution

Aggregates should preserve counts, not only unique fills.

For each model/item/blank/condition, count every extracted fill occurrence.

Example:

```json
{
  "item_id": "mirror_perspective_0001",
  "blank_id": "blank_1",
  "n_trials": 10,
  "fill_distribution": {
    "右": {"count": 7, "rate": 0.7, "fill_class": "accepted"},
    "左": {"count": 3, "rate": 0.3, "fill_class": "wrong"}
  },
  "unique_fill_count": 2,
  "top_fill": "右",
  "top_wrong_fill": "左"
}
```

## Recommended aggregate fields

Overall:

- `n_trials`
- `content_pass_rate`
- `format_pass_rate`
- `strict_pass_rate`
- `parse_fail_rate`
- `avg_latency_ms`

Per item and blank:

- `fill_distribution`
- `unique_fill_count`
- `top_fill`
- `top_wrong_fill`
- `mean_entropy`

Per category:

- `primary_skill`
- `content_pass_rate`
- `format_pass_rate`
- `parse_fail_rate`

## Repeated fills

Repeated identical fills must be counted. They are not duplicates to remove. If the same wrong fill repeatedly appears at the same blank, it is evidence of a systematic tendency.
