# Fill Class Policy

This document fixes the v0 `fill_class` vocabulary for parser/scorer implementation.

## Purpose

Item data has three fill lists per blank:

```text
accepted_fills
near_miss_fills
known_wrong_fills
```

The parser/scorer must not collapse known wrong fills into generic wrong fills. Known wrong fills are diagnostically useful because they represent expected, interpretable error patterns.

## v0 fill_class values

Use these values:

| fill_class | Meaning | content_pass |
|---|---|---:|
| `accepted` | Extracted fill is in `accepted_fills` | true |
| `near_miss` | Extracted fill is in `near_miss_fills` | false |
| `known_wrong` | Extracted fill is in `known_wrong_fills` | false |
| `wrong` | Extracted fill is not accepted, near-miss, or known-wrong | false |
| `parse_fail` | No fill could be extracted for this blank | false |
| `format_fail` | Reserved for future blank-level output-contract policy | false |

## Classification order

Classification order is:

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

## Content pass rule

For v0:

```text
content_pass = (fill_class == accepted)
```

`near_miss`, `known_wrong`, `wrong`, `parse_fail`, and `format_fail` are not content-pass.

## Reserved format_fail rule

`format_fail` is reserved.

In strict v0 parser/scorer implementation, prefer item-level flags:

```text
instruction_following_pass = false
item_format_pass = false
```

If no blank fill can be extracted, use blank-level:

```text
fill_class = parse_fail
parse_fail = true
extracted_fill = null
```

Do not emit blank-level `format_fail` unless a later explicit policy enables it.

## Aggregation implication

Aggregates should preserve `known_wrong` separately from generic `wrong`.

This allows analysis such as:

```text
model X repeatedly produces the expected mirror-left/right error
```

rather than only:

```text
model X was wrong
```
