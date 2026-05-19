# smoke_v0

`smoke_v0` is the first minimal dataset for `llmclozestat`.

It has two purposes:

1. Verify the full pipeline.
2. Produce local probe statistics for a single controlled item.

It is not intended to estimate general model ability.

## Pipeline target

```text
item
  -> prompt
  -> model output
  -> fill extraction
  -> blank-level scoring
  -> JSONL logging
  -> aggregation
```

## Current probe

The dataset currently contains one mirror-perspective item:

```text
あなたが鏡の前で現実の右手を上げる。
鏡の中の像で上がっている手は、現実のあなたの（blank_1）手に対応する。
```

Expected fill:

```text
右
```

This item tests whether a model can distinguish actual body-part correspondence from the common surface rule that mirrors “reverse left and right.”

## Interpretation limit

This dataset can show local behavior on this specific probe. Do not generalize from this item to broad spatial reasoning ability.

For broader claims, add more probe items with explicit `validation_target` fields.
