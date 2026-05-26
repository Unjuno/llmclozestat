# smoke_v0 example summary

This is a schema-compliant reference example, not a real benchmark result.

## Run

- submitter_id: `example-local`
- run_id: `smoke-v0-example-20260526`
- dataset_id: `smoke_v0`
- model_id: `example-model`
- prompt_template_id: `fill_full_sentence_v1.ja`
- prompt_language: `ja`
- support_mode: `zero`
- f_shot: `0`
- blank_rendering: `（　　　）`
- extraction_mode: `exact_full_text`

## Aggregate

| Metric | Value |
|---|---:|
| n_trials | 1 |
| content_pass_rate | 1.0 |
| instruction_following_pass_rate | 1.0 |
| item_format_pass_rate | 1.0 |
| strict_pass_rate | 1.0 |
| parse_fail_rate | 0.0 |
| avg_latency_ms | 0 |

## Fill distribution

| item_id | blank_id | fill | count | rate | class |
|---|---|---|---:|---:|---|
| `mirror_perspective_0001` | `blank_1` | `右` | 1 | 1.0 | accepted |
