# Parser/Scorer Fixture Policy

This document defines the minimal fixture set for Phase 2 parser/scorer implementation.

The goal is to fix expected parser/scorer behavior before implementing model execution.

## Scope

Phase 2 fixtures cover deterministic transformation from:

```text
item JSON object + raw_output
```

to parser/scorer fields such as:

```text
normalized_output
extraction_mode
blank_results
instruction_following_pass
item_format_pass
item_partial_score
item_strict_pass
```

They do not call any model backend.

## Fixture layout

Current layout:

```text
tests/fixtures/parser/
  README.md
  accepted_exact_full_text.json
  accepted_segment.json
  classify_near_miss.json
  classify_known_wrong.json
  classify_wrong.json
  instruction_wrapper_parse_fail.json
  segment_parse_fail.json
```

Each fixture should contain:

```json
{
  "name": "accepted_exact_full_text",
  "item": {},
  "raw_output": "...",
  "parser_config": {},
  "expected": {}
}
```

`parser_config` may be omitted in minimal fixtures only when the default strict-v0 parser configuration is intended.

## Required initial fixtures

| Fixture | Purpose |
|---|---|
| `accepted_exact_full_text.json` | exact full-text match produces accepted strict pass |
| `accepted_segment.json` | segment extraction can extract an accepted fill |
| `classify_near_miss.json` | near-miss is classified but not content-pass |
| `classify_known_wrong.json` | known wrong is separate from generic wrong and not content-pass |
| `classify_wrong.json` | unknown wrong fill is generic `wrong` and not content-pass |
| `instruction_wrapper_parse_fail.json` | output wrapper fails item format and parsing in strict v0 |
| `segment_parse_fail.json` | missing required segments produces parse failure |

## Expected v0 behavior

### Accepted exact full text

Expected:

```text
extraction_mode = exact_full_text
fill_class = accepted
blank_parse_pass = true
content_pass = true
parse_fail = false
instruction_following_pass = true
item_format_pass = true
item_strict_pass = true
item_partial_score = 1.0
```

### Accepted segment extraction

Expected:

```text
extraction_mode = segment
fill_class = accepted
blank_parse_pass = true
content_pass = true
parse_fail = false
instruction_following_pass = true
item_format_pass = true
item_strict_pass = true
item_partial_score = 1.0
```

### Near miss

Expected:

```text
fill_class = near_miss
content_pass = false
item_strict_pass = false
item_partial_score = 0.0
```

### Known wrong

Expected:

```text
fill_class = known_wrong
content_pass = false
item_strict_pass = false
item_partial_score = 0.0
```

### Generic wrong

Expected:

```text
fill_class = wrong
content_pass = false
item_strict_pass = false
item_partial_score = 0.0
```

### Instruction wrapper parse failure

For output wrappers such as:

```text
Answer: alpha
```

Expected in strict v0 without fallback extraction:

```text
instruction_following_pass = false
item_format_pass = false
extraction_mode = segment
extracted_fill = null
fill_class = parse_fail
blank_parse_pass = false
content_pass = false
parse_fail = true
item_strict_pass = false
item_partial_score = 0.0
```

### Segment parse failure

If required segments cannot be found in order:

```text
extracted_fill = null
fill_class = parse_fail
blank_parse_pass = false
content_pass = false
parse_fail = true
item_strict_pass = false
```

## Strict v0 constraints

Do not implement these for initial parser fixtures:

```text
fallback answer phrase extraction
LLM judge
semantic similarity scoring as pass/fail
partial credit for near_miss
blank-level format_fail emission
```

## Fill class source of truth

Use:

```text
docs/fill_class_policy.md
```

for the allowed fill classes and classification order.

## Implementation order

Recommended order:

```text
1. Add parser fixtures.
2. Add parser/scorer module with deterministic pure functions.
3. Add tests that read fixture expected fields.
4. Only then connect parser/scorer to result JSONL writing.
```
