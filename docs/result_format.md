# Result Format

The primary artifact is raw JSONL. Each line represents one model trial for one item.

## Result record

A result record should contain:

```json
{
  "dataset_id": "smoke_v0",
  "model_id": "local-model",
  "backend": "openai-compatible",
  "item_id": "mirror_perspective_0001",
  "prompt_template_id": "fill_full_sentence_v1",
  "support_mode": "zero",
  "f_shot": 0,
  "raw_output": "...",
  "normalized_output": "...",
  "blank_results": [
    {
      "blank_id": "blank_1",
      "position": 1,
      "extracted_fill": "右",
      "fill_class": "accepted",
      "format_pass": true,
      "content_pass": true,
      "parse_fail": false
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

## Blank-level scoring

Each blank is scored independently.

- `format_pass`: the output can be interpreted as the requested completed sentence format.
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

- `format_score_f1`
- `format_score_edit`
- `content_score_f1`

Do not use these scores as the only correctness rule. For example, a wrong sentence may still have high surface similarity.

## Aggregation

Aggregates should preserve counts, not only unique fills.

Recommended aggregate fields:

- `n_trials`
- `content_pass_rate`
- `format_pass_rate`
- `strict_pass_rate`
- `parse_fail_rate`
- `fill_distribution`
- `unique_fill_count`
- `top_fill`
- `top_wrong_fill`
- `mean_entropy`
- `avg_latency_ms`

Repeated identical fills must be counted.
