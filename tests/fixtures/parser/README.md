# Parser/Scorer Fixtures

These fixtures define expected deterministic parser/scorer behavior for Phase 2.

They do not call a model backend.

Each fixture has this shape:

```json
{
  "name": "fixture_name",
  "item": {},
  "raw_output": "...",
  "parser_config": {},
  "expected": {}
}
```

## Rules

- `raw_output` must be preserved exactly by the parser/scorer.
- `normalized_output` should use v0 minimal normalization.
- v0 supports only `exact_full_text` and `segment` extraction.
- Fallback extraction is intentionally disabled.
- `known_wrong` must remain distinct from generic `wrong`.
- `content_pass` is true only for `fill_class = accepted`.

See:

```text
docs/parser_fixture_policy.md
docs/fill_class_policy.md
docs/parser_scoring.md
```
