# Parser and Scoring Design

This document defines how `llmclozestat` should parse model outputs and score cloze results.

Parsing and scoring must be deterministic. The same raw output, item, and configuration should produce the same result record.

## Goals

Parser and scorer should:

- preserve raw output;
- apply minimal normalization;
- extract fills from completed full-sentence outputs;
- score each blank independently;
- distinguish instruction-following failure, format failure, and parse failure;
- avoid LLM-based judging in v0.x;
- record enough information for later aggregation.

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
- `near_miss_fills` per blank.

## Outputs

Parser/scorer output becomes one result record containing:

- `raw_output`;
- `normalized_output`;
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
4. Try segment-based extraction.
5. Evaluate output-instruction following.
6. Classify each blank fill.
7. Compute item-level scores.
8. Store diagnostics.
```

## Normalization

Normalization should be minimal.

Recommended v0 normalization:

- trim leading/trailing whitespace;
- normalize line endings to `\n`;
- collapse repeated surrounding blank lines;
- optionally normalize Unicode width only if explicitly configured.

Do not normalize away meaningful content by default.

Do not silently remove explanations, bullet points, or extra answer text. Extra text may be an instruction-following and format failure.

## Output instruction following

The prompt explicitly instructs the model to output the completed full sentence.

Therefore, failure to output the completed full sentence is not merely a cosmetic formatting issue. It is an output-instruction-following failure under this task.

Recommended field:

```json
{
  "instruction_following_pass": true
}
```

For v0:

```text
instruction_following_pass = item_format_pass
```

This does not claim to measure general instruction-following ability. It measures whether the model followed this task's explicit output contract.

Examples that should usually fail `instruction_following_pass`:

- `答えは右です。`
- explanations before or after the completed sentence;
- multiple alternatives;
- Markdown bullets when not requested;
- JSON when not requested;
- only the filled word when the prompt asks for the full sentence.

## Exact full-text match

If `normalized_output` exactly matches one entry in `expected_full_texts`, extraction can be marked as successful.

For each blank, the accepted fill can be derived from the matching expected full text or from segment extraction.

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

Segment-based extraction is the canonical v0 extraction method.

For an item with `n` blanks, there must be `n + 1` segments:

```text
segments[0] + fill_1 + segments[1] + fill_2 + ... + fill_n + segments[n]
```

The parser should find each segment in order inside `normalized_output` and extract the text between adjacent segments.

### One-blank example

Segments:

```json
[
  "現実のあなたの",
  "手に対応する。"
]
```

Output:

```text
現実のあなたの右手に対応する。
```

Extracted fill:

```text
右
```

### Failure cases

If required segments cannot be found in order, segment extraction fails.

If segment extraction fails in v0, the blank should usually be:

```json
{
  "blank_parse_pass": false,
  "parse_fail": true,
  "extracted_fill": null,
  "fill_class": "parse_fail"
}
```

## Instruction failure vs format failure vs parse failure

These are related but not identical.

### Instruction-following failure

The model did not follow the prompt's explicit output contract.

Example:

```text
答えは右です。
```

The content may be identifiable, but the model did not output the completed full sentence.

### Format failure

The output does not match the requested completed-sentence format.

In v0, this usually aligns with instruction-following failure because the instruction is specifically to output the completed full sentence.

### Parse failure

The parser cannot extract a fill for a blank.

In v0, if no fallback extractor is enabled, `答えは右です。` is also likely a parse failure because the required segments are missing.

Later versions may add fallback extraction. If fallback extraction extracts `右`, then:

```text
instruction_following_pass = false
item_format_pass = false
blank_parse_pass = true
parse_fail = false
content_pass = true
```

The extraction mode must be recorded if fallback is used.

## Extraction modes

Recommended field:

```json
{
  "extraction_mode": "segment"
}
```

Possible future values:

- `segment`
- `exact_full_text`
- `fallback_answer_phrase`
- `manual_review`

v0 should implement only:

- `exact_full_text`
- `segment`

Do not use `manual_review` for normal benchmark aggregation.

## Fill classification

For each blank:

```text
if parse_fail:
  fill_class = parse_fail
elif extracted_fill in accepted_fills:
  fill_class = accepted
elif extracted_fill in near_miss_fills:
  fill_class = near_miss
else:
  fill_class = wrong
```

`format_fail` may be used when an output fails the required format. However, if a blank-specific fill cannot be extracted, prefer `parse_fail` for that blank.

Recommended rule:

- explicit output-contract problem: use `instruction_following_pass = false`;
- item-level completed-sentence format problem: use `item_format_pass = false`;
- blank-level extraction problem: use `fill_class = parse_fail`;
- extracted but wrong content: use `fill_class = wrong`.

## Content pass

`content_pass` is true only when `fill_class = accepted`.

```text
content_pass = (fill_class == accepted)
```

Near-miss fills are not content-pass unless a later policy explicitly defines partial credit.

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

Potential wrappers that should make `item_format_pass = false` and `instruction_following_pass = false`:

- `答えは...です。`
- Markdown bullets when not requested;
- explanations before or after the sentence;
- multiple alternative answers;
- JSON output when not requested.

## Similarity scores

Similarity scores are diagnostics, not primary correctness.

Optional metrics:

- `format_score_f1`;
- `format_score_edit`;
- `content_score_f1`.

Do not use similarity scores as the primary pass/fail rule in v0.

## Multi-blank parsing

For multi-blank items, extract fills in order using segments.

The parser must not greedily consume text that prevents later segments from matching.

Recommended implementation strategy:

```text
for each segment in order:
  find the next segment occurrence after the current cursor
  extract the substring between current segment end and next segment start
```

For repeated segment text, the parser may need a shortest-forward match strategy.

If ambiguity remains, mark parse failure rather than guessing.

## Whitespace around fills

Trim whitespace around extracted fills by default.

Do not remove internal spaces unless configured.

Example:

```text
" 右 " -> "右"
"New York" -> "New York"
```

## Repeated fills

Do not deduplicate repeated fills across trials.

If the same wrong fill appears 100 times, count it 100 times.

Repeated wrong fills are evidence of a systematic tendency.

## Determinism

Parser and scorer must be deterministic.

Given:

```text
item + raw_output + parser_config + scoring_config
```

The output result record must be the same.

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
- output-instruction-following flag;
- explicit accepted/near-miss/wrong classification;
- item partial score;
- item strict pass;
- repeated fill counting;
- no fallback answer extraction;
- no LLM judge;
- no manual review in aggregates.

This keeps early statistics strict and interpretable.
