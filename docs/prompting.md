# Prompting Design

This document defines prompt construction for `llmclozestat`.

Prompting is separate from scoring. A prompt asks the model to produce a completed sentence. The parser and scorer decide whether the output can be extracted and accepted.

## Goals

The prompt should make the required output format clear while avoiding unnecessary assistance that changes the tested capability.

The prompt should:

- present the cloze task clearly;
- request the completed full sentence;
- avoid four-choice style options;
- keep prompt templates stable across model comparisons;
- record the prompt template used in each result record;
- separate format support from task support.

## Non-goals

The prompt should not:

- ask the model to explain its reasoning;
- ask the model to list alternatives;
- ask the model to output only the filled word unless a later mode explicitly tests that;
- use LLM judging;
- silently adapt prompts per model;
- hide prompt changes from result metadata.

## Prompt template identity

Each prompt template must have a stable `prompt_template_id`.

Example:

```text
fill_full_sentence_v1
```

Result records must store:

```json
{
  "prompt_template_id": "fill_full_sentence_v1"
}
```

Changing the prompt wording changes the experimental condition. A changed prompt should receive a new template ID.

## Base prompt structure

The initial template should be minimal and stable.

```text
# Task
Fill in the blank.
When answering, output the full completed sentence.

# Problem
{text_with_rendered_blank}
```

For Japanese datasets, a Japanese prompt can be used if the template ID records it.

```text
# 指示
穴埋めを埋めてください。
回答するときは、穴埋め後の全文だけを出力してください。

# 問題
{text_with_rendered_blank}
```

## Output contract

The preferred output is exactly one completed full sentence or full item text.

For the smoke item:

```text
あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの右手に対応する。
```

The model should not output:

```text
答えは右です。
```

That output may contain the right content, but it does not follow the completed-sentence format.

## Blank rendering

`text_with_blanks` is for authoring and review. Prompt builders may render blank markers differently.

Recommended initial rendering:

```text
（　　　）
```

Example authoring text:

```text
現実のあなたの（blank_1）手に対応する。
```

Rendered prompt text:

```text
現実のあなたの（　　　）手に対応する。
```

Scoring must rely on `segments`, not the rendered blank marker.

## Support modes

Prompt support must be explicit. It should be recorded in result records.

Recommended modes:

| support_mode | Meaning |
|---|---|
| `zero` | No examples. Only task instruction and problem. |
| `format_shot` | Examples only teach the output format, not the target skill. |
| `task_shot` | Examples teach the same or similar task skill. |
| `control_shot` | Examples test whether generic examples change behavior. |
| `mixed_shot` | Combination of format and task examples. |

Early implementation should start with `zero` and `format_shot`.

## Format-shot examples

Format-shot examples should teach only that the model must output the completed full sentence.

They should not overlap with the target probe's skill.

Example:

```text
# Examples
1. 彼は毎日トレーニングをして体力を（　　　）している。
1. 彼は毎日トレーニングをして体力を維持している。

2. 問題を正確に理解するには、前提条件を（　　　）必要がある。
2. 問題を正確に理解するには、前提条件を確認する必要がある。
```

These examples help the model learn the required response shape. They should not be counted as evidence for the target capability.

## Task-shot caution

Task-shot examples may improve performance by teaching the skill being tested.

That is allowed only when the run explicitly records:

```json
{
  "support_mode": "task_shot",
  "f_shot": 3
}
```

Do not mix zero-shot and task-shot results in the same aggregate without grouping by `support_mode`.

## Prompt stability rules

For comparable runs:

- use the same `prompt_template_id`;
- use the same rendered blank style;
- use the same examples for shot-based modes;
- use the same language prompt policy;
- record `support_mode` and `f_shot`;
- do not silently patch the prompt for weak models.

If a model cannot follow the output format under the fixed prompt, that is part of the measurement.

## Language policy

Language-specific variants may use prompts in the same language as the item.

However, prompt language is an experimental condition. Record it in the template ID or metadata.

Examples:

```text
fill_full_sentence_v1.ja
fill_full_sentence_v1.en
```

Do not compare prompt-language changes as if they were only item-language effects.

## Prompt metadata

Result records should preserve at least:

```json
{
  "prompt_template_id": "fill_full_sentence_v1.ja",
  "support_mode": "zero",
  "f_shot": 0
}
```

Optional later fields:

```json
{
  "prompt_hash": "sha256:...",
  "rendered_prompt_path": "optional/path.txt"
}
```

Storing full rendered prompts for every trial may be expensive. A prompt hash can be enough if templates and inputs are versioned.

## Initial recommendation

Start with:

```text
prompt_template_id = fill_full_sentence_v1.ja
support_mode = zero
f_shot = 0
blank_rendering = （　　　）
```

Add `format_shot` only if too many models fail to produce parseable output.

Do not add `task_shot` until the zero-shot and format-shot baselines are established.
