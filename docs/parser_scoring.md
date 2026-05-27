# Parser and Scoring Design

This document defines how `llmclozestat` should parse model outputs and score cloze results.

Parsing and scoring must be deterministic. The same raw output, item, parser configuration, and scoring configuration should produce the same result record.

## Goals

Parser and scorer should:

- preserve raw output;
- apply minimal normalization;
- extract fills from completed full-sentence outputs;
- record the active `extraction_mode`;
- score each blank independently;
- distinguish instruction-following failure, item-format failure, and blank-level parse failure;
- distinguish known wrong fills from generic unknown wrong fills;
- avoid LLM-based judging in v0.x;
- record enough metadata for later aggregation.

## Non-goals

Parser and scorer should not:

- rewrite model outputs to make them correct;
- infer unstated answers aggressively;
- use another LLM as judge;
- silently deduplicate repeated fills;
- collapse all behavior into one score;
- hide extraction fallbacks.

## Inputs

Parser/scorer input:

```text
item JSON object
raw_output string
parser_config
scoring_config
```

The item must contain:

- `segments`;
- `blanks`;
- `expected_full_texts`;
- `accepted_fills` per blank;
- `near_miss_fills` per blank;
- `known_wrong_fills` per blank.

`parser_config` should record at least:

- `normalization`;
- `extraction_modes_enabled`;
- whether Unicode width normalization is enabled;
- whether fallback extraction is enabled.

## Outputs

Parser/scorer output becomes one result record containing:

- `raw_output`;
- `normalized_output`;
- `extraction_mode`;
- `blank_results`;
- `instruction_following_pass`;
- `item_format_pass`;
- `item_partial_score`;
- `item_strict_pass`;
- diagnostic similarity scores if implemented.

## Parsing pipeline

Use this order:

```text
1. Preserve raw_output exactly.
2. Normalize minimally.
3. Check exact match against expected_full_texts.
4. If exact match succeeds, set extraction_mode = exact_full_text.
5. Otherwise try segment-based extraction.
6. If segment extraction succeeds, set extraction_mode = segment.
7. Evaluate output-instruction following.
8. Classify each blank fill.
9. Compute item-level scores.
10. Store diagnostics.
```

If no extraction method succeeds, affected blanks should use:

```json
{
  "blank_parse_pass": false,
  "parse_fail": true,
  "extracted_fill": null,
  "fill_class": "parse_fail"
}
```

## Normalization

Normalization should be minimal.

Recommended v0 normalization:

- trim leading/trailing whitespace;
- normalize line endings to `\n`;
- collapse repeated surrounding blank lines;
- optionally normalize Unicode width only if explicitly configured.

Do not normalize away meaningful content by default. Extra answer text may be an instruction-following and format failure.

## Output instruction following

The prompt explicitly instructs the model to output the completed full sentence.

Therefore, failure to output the completed full sentence is an output-instruction-following failure under this task.

For v0:

```text
instruction_following_pass = item_format_pass
```

This does not claim to measure general instruction-following ability. It measures whether the model followed this task's explicit output contract.

Examples that should usually fail `instruction_following_pass`:

- explanations before or after the completed sentence;
- multiple alternatives;
- Markdown bullets when not requested;
- JSON when not requested;
- only the filled word when the prompt asks for the full sentence.

## Extraction modes

Required result field:

```json
{
  "extraction_mode": "segment"
}
```

Supported result values:

- `exact_full_text`
- `segment`
- `fallback_answer_phrase`

v0 should implement only:

- `exact_full_text`
- `segment`

`fallback_answer_phrase` is reserved for a later policy and must be grouped separately during aggregation.

## Exact full-text match

If `normalized_output` exactly matches one entry in `expected_full_texts`, extraction can be marked as successful with:

```json
{
  "extraction_mode": "exact_full_text"
}
```

Exact match should imply:

```text
instruction_following_pass = true
item_format_pass = true
blank_parse_pass = true for all blanks
content_pass = true for all blanks
item_strict_pass = true
```

unless a later policy explicitly defines multiple accepted full texts with partial scoring.

## Segment-based extraction

Segment-based extraction is the canonical v0 extraction method when exact full-text match does not apply.

For an item with `n` blanks, there must be `n + 1` segments:

```text
segments[0] + fill_1 + segments[1] + fill_2 + ... + fill_n + segments[n]
```

The parser should find each segment in order inside `normalized_output` and extract the text between adjacent segments.

When segment extraction succeeds, store:

```json
{
  "extraction_mode": "segment"
}
```

For repeated segment text, use a shortest-forward match strategy. If ambiguity remains, mark parse failure rather than guessing.

## Instruction failure vs format failure vs parse failure

These are related but not identical.

- Instruction-following failure: the model did not follow the prompt's explicit output contract.
- Format failure: the output does not match the requested completed-sentence format.
- Parse failure: the parser cannot extract a fill for a blank.

In v0, instruction-following failure and item-format failure usually align because the instruction is specifically to output the completed full sentence.

If fallback extraction is later enabled and extracts a correct fill from a non-compliant output, the result can have:

```text
instruction_following_pass = false
item_format_pass = false
blank_parse_pass = true
parse_fail = false
content_pass = true
extraction_mode = fallback_answer_phrase
```

Such records must not be mixed with strict v0 extraction records unless grouped by `extraction_mode`.

## Fill classification

The v0 fill-class vocabulary is defined in `docs/fill_class_policy.md`.

For each blank:

```text
if parse_fail:
  fill_class = parse_fail
elif extracted_fill in accepted_fills:
  fill_class = accepted
elif extracted_fill in near_miss_fills:
  fill_class = near_miss
elif extracted_fill in known_wrong_fills:
  fill_class = known_wrong
else:
  fill_class = wrong
```

`known_wrong` is distinct from generic `wrong`. It marks expected, interpretable error patterns from `known_wrong_fills`.

`format_fail` is reserved for output-contract problems. In v0, prefer item-level `instruction_following_pass = false` and `item_format_pass = false`; if a blank-specific fill cannot be extracted, use `fill_class = parse_fail` for that blank.

## Content pass

`content_pass` is true only when `fill_class = accepted`.

```text
content_pass = (fill_class == accepted)
```

Near-miss, known-wrong, generic wrong, parse-fail, and reserved format-fail fills are not content-pass unless a later policy explicitly defines partial credit.

## Item partial score

For item `i` with blank set `B_i`:

```text
item_partial_score = accepted_blank_count / blank_count
```

Example:

```text
2 blanks, 1 accepted -> item_partial_score = 0.5
```

## Item strict pass

`item_strict_pass` is true only when:

```text
instruction_following_pass = true
item_format_pass = true
and every blank has content_pass = true
```

This means a model that gives the right word but not the completed sentence can have `content_pass = true` only if fallback extraction is enabled, but still fails `item_strict_pass` because `instruction_following_pass = false` and `item_format_pass = false`.

## Item format pass

`item_format_pass` should mean:

```text
the whole output follows the requested completed-sentence format
```

In v0 segment extraction, `item_format_pass` should usually be true if all segments are found in order and no significant extra answer wrapper is present.

Potential wrappers should make `item_format_pass = false` and `instruction_following_pass = false`.

## Similarity scores

Similarity scores are diagnostics, not primary correctness.

Optional metrics:

- `format_score_f1`;
- `format_score_edit`;
- `content_score_f1`.

Do not use similarity scores as the primary pass/fail rule in v0.

## Repeated fills

Do not deduplicate repeated fills across trials.

If the same wrong or known-wrong fill appears 100 times, count it 100 times. Repeated wrong fills are evidence of a systematic tendency.

## Determinism

Parser and scorer must be deterministic.

Given:

```text
item + raw_output + parser_config + scoring_config
```

The output result record must be the same.

`parser_config` and `extraction_mode` must be recorded enough to explain how the record was produced.

## Error handling

Parsing errors should not crash the full run.

For one failed trial:

- store raw output;
- set parse failure fields;
- continue to the next item/trial;
- include the failure in aggregate statistics.

Only structural dataset errors should stop a run before model calls.

## Minimal v0 policy

v0 should implement:

- exact full-text match;
- segment-based extraction;
- required `extraction_mode` recording;
- output-instruction-following flag;
- explicit accepted/near-miss/known-wrong/wrong classification;
- item partial score;
- item strict pass;
- repeated fill counting;
- no fallback answer extraction;
- no LLM judge.

This keeps early statistics strict and interpretable.
