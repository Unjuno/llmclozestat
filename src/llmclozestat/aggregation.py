from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SUMMARY_VERSION = "summary_v0"
PARSE_FAIL_FILL_KEY = "__PARSE_FAIL__"

GROUP_FIELDS = (
    "probe_id",
    "variant_id",
    "language",
    "item_id",
    "prompt_template_id",
    "prompt_language",
    "support_mode",
    "f_shot",
    "blank_rendering",
    "extraction_mode",
    "generation_config_hash",
)

TOP_LEVEL_IDENTITY_FIELDS = (
    "submitter_id",
    "run_id",
    "dataset_id",
    "model_id",
)


def aggregate_results_file(input_path: Path) -> dict[str, Any]:
    """Aggregate one result JSONL file into a summary dictionary.

    This function is intentionally small. It does not validate the input file;
    callers should run result validation separately.
    """

    records = list(_load_result_records(input_path))
    return aggregate_result_records(records)


def aggregate_result_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    n_trials = len(records)
    identity = _top_level_identity(records)

    summary: dict[str, Any] = {
        "summary_version": SUMMARY_VERSION,
        "submitter_id": identity.get("submitter_id", ""),
        "run_id": identity.get("run_id", ""),
        "dataset_id": identity.get("dataset_id", ""),
        "model_id": identity.get("model_id", ""),
        "n_trials": n_trials,
        "content_pass_rate": _blank_rate(records, "content_pass"),
        "instruction_following_pass_rate": _record_rate(records, "instruction_following_pass"),
        "item_format_pass_rate": _record_rate(records, "item_format_pass"),
        "strict_pass_rate": _record_rate(records, "item_strict_pass"),
        "parse_fail_rate": _blank_rate(records, "parse_fail"),
        "avg_latency_ms": _average_latency(records),
        "groups": _build_groups(records),
    }
    return summary


def _load_result_records(input_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            if isinstance(record, dict):
                records.append(record)
    return records


def _top_level_identity(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {}
    return {field: records[0].get(field, "") for field in TOP_LEVEL_IDENTITY_FIELDS}


def _record_rate(records: list[dict[str, Any]], field: str) -> float:
    if not records:
        return 0.0
    return sum(1 for record in records if record.get(field) is True) / len(records)


def _blank_rate(records: list[dict[str, Any]], field: str) -> float:
    values: list[bool] = []
    for record in records:
        blank_results = record.get("blank_results", [])
        if not isinstance(blank_results, list):
            continue
        for blank in blank_results:
            if isinstance(blank, dict):
                values.append(blank.get(field) is True)
    if not values:
        return 0.0
    return sum(1 for value in values if value) / len(values)


def _average_latency(records: list[dict[str, Any]]) -> float | None:
    values = [record.get("latency_ms") for record in records]
    numeric_values = [float(value) for value in values if isinstance(value, (int, float))]
    if not numeric_values:
        return None
    return sum(numeric_values) / len(numeric_values)


def _build_groups(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)

    for record in records:
        blank_results = record.get("blank_results", [])
        if not isinstance(blank_results, list):
            continue
        for blank in blank_results:
            if not isinstance(blank, dict):
                continue
            key = _group_key(record, blank)
            grouped[key].append((record, blank))

    return [_build_group(entries) for _, entries in sorted(grouped.items(), key=lambda item: item[0])]


def _group_key(record: dict[str, Any], blank: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(record.get(field) for field in GROUP_FIELDS) + (blank.get("blank_id"),)


def _build_group(entries: list[tuple[dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    first_record, first_blank = entries[0]
    n_trials = len(entries)

    counts: Counter[tuple[str | None, str, str]] = Counter()
    for _, blank in entries:
        extracted_fill = blank.get("extracted_fill")
        fill_class = str(blank.get("fill_class", "wrong"))
        fill_key = PARSE_FAIL_FILL_KEY if extracted_fill is None else str(extracted_fill)
        counts[(extracted_fill if isinstance(extracted_fill, str) else None, fill_key, fill_class)] += 1

    fill_distribution = [
        {
            "extracted_fill": extracted_fill,
            "fill_key": fill_key,
            "count": count,
            "rate": count / n_trials if n_trials else 0.0,
            "fill_class": fill_class,
        }
        for (extracted_fill, fill_key, fill_class), count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0][1], item[0][2]),
        )
    ]

    return {
        "probe_id": first_record.get("probe_id", ""),
        "variant_id": first_record.get("variant_id", ""),
        "language": first_record.get("language", ""),
        "item_id": first_record.get("item_id", ""),
        "blank_id": first_blank.get("blank_id", ""),
        "position": first_blank.get("position"),
        "prompt_template_id": first_record.get("prompt_template_id", ""),
        "prompt_language": first_record.get("prompt_language", ""),
        "support_mode": first_record.get("support_mode", ""),
        "f_shot": first_record.get("f_shot", 0),
        "blank_rendering": first_record.get("blank_rendering", ""),
        "extraction_mode": first_record.get("extraction_mode", ""),
        "generation_config_hash": first_record.get("generation_config_hash"),
        "n_trials": n_trials,
        "fill_distribution": fill_distribution,
        "unique_fill_count": len(fill_distribution),
        "top_fill": fill_distribution[0]["fill_key"] if fill_distribution else None,
        "top_wrong_fill": _top_wrong_fill(fill_distribution),
        "mean_entropy": _entropy_from_counts(counts.values()),
    }


def _top_wrong_fill(fill_distribution: list[dict[str, Any]]) -> str | None:
    wrong_classes = {"near_miss", "known_wrong", "wrong"}
    for entry in fill_distribution:
        if entry.get("fill_class") in wrong_classes:
            return str(entry.get("fill_key"))
    return None


def _entropy_from_counts(counts: Any) -> float:
    count_list = [int(count) for count in counts]
    total = sum(count_list)
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in count_list:
        probability = count / total
        if probability > 0:
            entropy -= probability * math.log2(probability)
    return entropy
