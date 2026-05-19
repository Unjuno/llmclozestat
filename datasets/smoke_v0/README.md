# smoke_v0

`smoke_v0` is the first minimal dataset for `llmclozestat`.

It is not intended to estimate general model ability. It is used to verify the full pipeline:

```text
item -> prompt -> model output -> fill extraction -> scoring -> JSONL logging -> aggregation
```

The dataset currently contains a mirror-perspective probe. It can produce useful local statistics, but it should not be overgeneralized to broad model capability.
