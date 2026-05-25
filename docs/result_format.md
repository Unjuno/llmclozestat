# Result Format

The primary artifact is raw JSONL. Each line represents one model trial for one item.

Reports and summaries are derived artifacts. They should be reproducible from raw JSONL.

## Result record

A result record should contain:

```json
{
  "submitter_id": "github-username-or-local-name",
  "run_id": "smoke-local-model-20260525",
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
      "blank_parse_pass": true,
      "content_pass": true,
      "parse_fail": false,
      "content_score_f1": 1.0
    }
  ],
  "item_format_pass": true,
  "item_strict_pass": true,
  "item_partial_score": 1.0,
  "format_score_f1": 1.0,
  "format_score_edit": 1.0,
  "latency_ms": 0,
  "temperature": 0,
  "max_tokens": 64
}
```

## Record identity

Recommended identity fields:

- `submitter_id`
- `run_id`
- `dataset_id`
- `model_id`
- `backend`
- `item_id`
- `trial_id`
- `prompt_template_id`
- `support_mode`

For repeated trials, do not overwrite earlier rows. Append a new JSONL row.

## Provenance and filtering

`submitter_id` and `run_id` are not authentication fields. They are provenance fields for filtering and re-aggregation.

They allow later analysis to:

- include all submissions;
- filter by submitter;
- exclude a suspicious submitter;
- exclude a broken run;
- compare repeated runs by the same submitter;
- keep raw logs unchanged while changing aggregate filters.

Aggregators should support exclusion lists such as:

```json
{
  "exclude_submitter_ids": ["example-user"],
  "exclude_run_ids": ["broken-run-001"]
}
```

## Scoring precedence

Use this order when turning a model output into a result record:

1. Preserve `raw_output` exactly.
2. Produce `normalized_output` by applying minimal normalization.
3. Check exact match against `expected_full_texts`.
4. Try segment-based extraction.
5. If segment extraction succeeds, classify each extracted fill.
6. If no fill can be extracted, set `parse_fail = true` for the affected blank.
7. Compute similarity scores as diagnostic metrics only.

Early versions should prefer segment-based extraction only. Fallback extractors may be added later, but they must store their extraction mode explicitly.

## Format failure and parse failure

`format_fail` and `parse_fail` are different.

- `format_fail`: the model did not follow the requested completed-sentence format.
- `parse_fail`: no fill could be extracted for a blank.

A model output may be a format failure while still allowing a fill to be extracted.

Example:

```text
答えは右です。
```

This is not the requested completed full sentence. It may be `item_format_pass = false`, but if a future fallback extractor extracts `右`, the blank does not have to be `parse_fail`.

For v0.0, fallback extraction is not required. Segment-based extraction is the canonical path.

## Blank-level scoring

Each blank is scored independently.

- `blank_parse_pass`: a fill was extracted for this blank by the active extraction method.
- `content_pass`: the extracted fill is in `accepted_fills`.
- `parse_fail`: the fill could not be extracted.
- `fill_class`: one of `accepted`, `near_miss`, `wrong`, `format_fail`, `parse_fail`.

Do not use `format_pass` at the blank level. Use `blank_parse_pass` to avoid confusion with item-level format compliance.

## Item-level scoring

- `item_format_pass`: true when the whole output follows the requested completed-sentence format.
- `item_partial_score`: accepted blank count divided by blank count.
- `item_strict_pass`: true only when all blanks are content-pass and `item_format_pass` is true.

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
- `item_format_pass_rate`
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
- `item_format_pass_rate`
- `parse_fail_rate`

For repository-wide reports, aggregators should preserve counts by `submitter_id` and `run_id` so results can be recomputed with exclusion filters.

## Repeated fills

Repeated identical fills must be counted. They are not duplicates to remove. If the same wrong fill repeatedly appears at the same blank, it is evidence of a systematic tendency.
