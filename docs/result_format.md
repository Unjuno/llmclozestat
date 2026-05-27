# Result Format

The primary artifact is raw JSONL. Each line represents one model trial for one item.

Reports and summaries are derived artifacts. They should be reproducible from raw JSONL.

## Result record

A result record should contain enough item metadata, prompt metadata, parser metadata, and run metadata to remain analyzable even when inspected outside the original dataset file.

```json
{
  "submitter_id": "github-username-or-local-name",
  "run_id": "smoke-local-model-20260525",
  "dataset_id": "smoke_v0",
  "model_id": "local-model",
  "backend": "openai-compatible",
  "provider": "lm_studio",
  "probe_id": "mirror_perspective_body_correspondence_0001",
  "variant_id": "mirror_perspective_body_correspondence_0001.ja",
  "language": "ja",
  "primary_skill": "spatial_perspective",
  "item_id": "mirror_perspective_0001",
  "trial_id": 1,
  "prompt_template_id": "fill_full_sentence_v1.ja",
  "prompt_language": "ja",
  "support_mode": "zero",
  "f_shot": 0,
  "blank_rendering": "（　　　）",
  "generation_config": {
    "temperature": 0,
    "top_p": null,
    "seed": null,
    "max_tokens": 64,
    "context_window": null,
    "stop": []
  },
  "generation_config_hash": null,
  "raw_output": "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの右手に対応する。",
  "normalized_output": "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの右手に対応する。",
  "extraction_mode": "exact_full_text",
  "blank_results": [
    {
      "blank_id": "blank_1",
      "position": 1,
      "primary_skill": "mirror_body_correspondence",
      "context_distance": "sentence",
      "extracted_fill": "右",
      "fill_class": "accepted",
      "blank_parse_pass": true,
      "content_pass": true,
      "parse_fail": false,
      "content_score_f1": 1.0
    }
  ],
  "instruction_following_pass": true,
  "item_format_pass": true,
  "item_strict_pass": true,
  "item_partial_score": 1.0,
  "format_score_f1": 1.0,
  "format_score_edit": 1.0,
  "latency_ms": 0
}
```

## Record identity

Recommended identity fields:

- `submitter_id`
- `run_id`
- `dataset_id`
- `model_id`
- `backend`
- `provider`
- `probe_id`
- `variant_id`
- `language`
- `item_id`
- `trial_id`
- `prompt_template_id`
- `prompt_language`
- `support_mode`
- `f_shot`
- `blank_rendering`
- `extraction_mode`

For repeated trials, do not overwrite earlier rows. Append a new JSONL row.

## Why result records duplicate item metadata

A result record should include `probe_id`, `variant_id`, `language`, and relevant skill/context fields even though they can be obtained from the dataset.

Reason:

- submissions may be analyzed outside the original working tree;
- datasets may evolve;
- old result records should remain interpretable;
- repository-wide aggregation should not depend on fragile joins only;
- language and probe-level filtering should be possible from result logs.

The dataset remains the source of truth for item authoring. The result record stores a run-time copy of key metadata for analysis stability.

## Prompt and parser metadata

Prompt and parser settings are experimental conditions. They must be recorded rather than inferred.

Required prompt metadata:

- `prompt_template_id`
- `prompt_language`
- `support_mode`
- `f_shot`
- `blank_rendering`

Required parser metadata:

- `extraction_mode`

Supported v0 extraction modes:

- `exact_full_text`
- `segment`

Future fallback mode:

- `fallback_answer_phrase`

Fallback extraction must not be mixed with strict v0 extraction in the same aggregate unless grouped by `extraction_mode`.

## Generation config identity

Aggregates should not rely on raw object key order when grouping generation settings.

Recommended canonicalization:

- serialize `generation_config` as canonical JSON;
- sort object keys;
- preserve explicit nulls;
- avoid insignificant whitespace;
- compute `generation_config_hash` when a compact grouping key is needed.

Example:

```json
{
  "generation_config_hash": "sha256:..."
}
```

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
5. Record `extraction_mode`.
6. Evaluate whether the model followed the explicit completed-sentence output instruction.
7. If extraction succeeds, classify each extracted fill.
8. If no fill can be extracted, set `parse_fail = true` for the affected blank.
9. Compute similarity scores as diagnostic metrics only.

Early versions should prefer exact full-text and segment-based extraction only. Fallback extractors may be added later, but they must store their extraction mode explicitly.

## Instruction following, format failure, and parse failure

The prompt explicitly asks the model to output the completed full sentence. Therefore, failing to output the completed full sentence is an output-instruction-following failure for this task.

Recommended item-level fields:

- `instruction_following_pass`: true when the model followed the explicit output contract.
- `item_format_pass`: true when the whole output follows the requested completed-sentence format.
- `parse_fail`: blank-level failure to extract a fill.

For v0:

```text
instruction_following_pass = item_format_pass
```

This measures compliance with this task's output instruction. It does not claim to measure general instruction-following ability.

Example:

```text
答えは右です。
```

This may contain the right content, but it does not follow the requested completed full-sentence output. In v0, it should usually have:

```json
{
  "instruction_following_pass": false,
  "item_format_pass": false
}
```

If no fallback extractor is enabled, it may also produce blank-level `parse_fail = true` because the expected segments are missing.

## Blank-level scoring

Each blank is scored independently.

- `blank_parse_pass`: a fill was extracted for this blank by the active extraction method.
- `content_pass`: the extracted fill is in `accepted_fills`.
- `parse_fail`: the fill could not be extracted.
- `fill_class`: one of `accepted`, `near_miss`, `wrong`, `format_fail`, `parse_fail`.

Do not use `format_pass` at the blank level. Use `blank_parse_pass` to avoid confusion with item-level format compliance.

`fill_class = format_fail` is reserved. In v0, validators should reject or warn on blank-level `format_fail` unless an explicit later policy enables it. Prefer item-level `instruction_following_pass = false` and `item_format_pass = false`; if a blank-specific fill cannot be extracted, use `fill_class = parse_fail` for that blank.

## Item-level scoring

- `instruction_following_pass`: true when the model followed the explicit completed-sentence output instruction.
- `item_format_pass`: true when the whole output follows the requested completed-sentence format.
- `item_partial_score`: accepted blank count divided by blank count.
- `item_strict_pass`: true only when all blanks are content-pass, `instruction_following_pass` is true, and `item_format_pass` is true.

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

Recommended grouping keys:

- `model_id`
- `dataset_id`
- `probe_id`
- `variant_id`
- `language`
- `item_id`
- `blank_id`
- `prompt_template_id`
- `prompt_language`
- `support_mode`
- `f_shot`
- `blank_rendering`
- `extraction_mode`
- `generation_config` or `generation_config_hash`

`fill_distribution` should be an array of entries, not a JSON object keyed only by fill text. This supports `extracted_fill = null` for parse failures.

Recommended parse-fail key:

```text
__PARSE_FAIL__
```

Example:

```json
{
  "probe_id": "mirror_perspective_body_correspondence_0001",
  "variant_id": "mirror_perspective_body_correspondence_0001.ja",
  "language": "ja",
  "item_id": "mirror_perspective_0001",
  "blank_id": "blank_1",
  "n_trials": 10,
  "fill_distribution": [
    {"extracted_fill": "右", "fill_key": "右", "count": 7, "rate": 0.7, "fill_class": "accepted"},
    {"extracted_fill": "左", "fill_key": "左", "count": 2, "rate": 0.2, "fill_class": "wrong"},
    {"extracted_fill": null, "fill_key": "__PARSE_FAIL__", "count": 1, "rate": 0.1, "fill_class": "parse_fail"}
  ],
  "unique_fill_count": 3,
  "top_fill": "右",
  "top_wrong_fill": "左"
}
```

## Recommended aggregate fields

Overall:

- `n_trials`
- `content_pass_rate`
- `instruction_following_pass_rate`
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

- `probe_id`
- `variant_id`
- `language`
- `primary_skill`
- `context_distance`
- `prompt_template_id`
- `prompt_language`
- `support_mode`
- `f_shot`
- `blank_rendering`
- `extraction_mode`
- `content_pass_rate`
- `instruction_following_pass_rate`
- `item_format_pass_rate`
- `parse_fail_rate`

For repository-wide reports, aggregators should preserve counts by `submitter_id` and `run_id` so results can be recomputed with exclusion filters.

## Repeated fills

Repeated identical fills must be counted. They are not duplicates to remove. If the same wrong fill repeatedly appears at the same blank, it is evidence of a systematic tendency.
