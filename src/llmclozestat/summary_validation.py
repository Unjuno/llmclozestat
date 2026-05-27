from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llmclozestat.aggregation import PARSE_FAIL_FILL_KEY


@dataclass(frozen=True)
class ValidationMessage:
    code: str
    message: str
    path: str
    severity: str = "ERROR"

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


class SummaryValidationResult:
    def __init__(self) -> None:
        self.errors: list[ValidationMessage] = []
        self.warnings: list[ValidationMessage] = []
        self.info: list[dict[str, Any]] = []

    @property
    def failed(self) -> bool:
        return bool(self.errors)

    def add_error(self, code: str, message: str, path: str) -> None:
        self.errors.append(ValidationMessage(code=code, message=message, path=path))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "failed" if self.failed else "passed",
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "info": self.info,
        }


REQUIRED_SUMMARY_FIELDS = {
    "summary_version",
    "submitter_id",
    "run_id",
    "dataset_id",
    "model_id",
    "n_trials",
    "content_pass_rate",
    "instruction_following_pass_rate",
    "item_format_pass_rate",
    "strict_pass_rate",
    "parse_fail_rate",
    "groups",
}

REQUIRED_GROUP_FIELDS = {
    "probe_id",
    "variant_id",
    "language",
    "item_id",
    "blank_id",
    "prompt_template_id",
    "prompt_language",
    "support_mode",
    "f_shot",
    "blank_rendering",
    "extraction_mode",
    "n_trials",
    "fill_distribution",
    "unique_fill_count",
}

REQUIRED_FILL_FIELDS = {"extracted_fill", "fill_key", "count", "rate", "fill_class"}


def validate_summary_file(input_path: Path) -> SummaryValidationResult:
    result = SummaryValidationResult()
    if not input_path.exists():
        result.add_error("file_not_found", "Summary file does not exist", str(input_path))
        return result

    try:
        summary = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.add_error("json_parse_error", f"Invalid summary JSON: {exc.msg}", str(input_path))
        return result

    if not isinstance(summary, dict):
        result.add_error("summary_schema_validation_error", "Summary JSON must be an object", str(input_path))
        return result

    validate_summary_object(summary, str(input_path), result)
    return result


def validate_summary_object(
    summary: dict[str, Any],
    path: str = "summary",
    result: SummaryValidationResult | None = None,
) -> SummaryValidationResult:
    validation = result or SummaryValidationResult()

    for field in sorted(REQUIRED_SUMMARY_FIELDS):
        if field not in summary:
            validation.add_error("summary_schema_validation_error", f"Missing summary field: {field}", path)

    groups = summary.get("groups")
    if not isinstance(groups, list):
        validation.add_error("summary_schema_validation_error", "groups must be an array", path)
        return validation
    if not groups:
        validation.add_error("summary_schema_validation_error", "groups must not be empty", path)
        return validation

    for index, group in enumerate(groups):
        group_path = f"{path}:groups[{index}]"
        if not isinstance(group, dict):
            validation.add_error("summary_schema_validation_error", "Each group must be an object", group_path)
            continue
        _validate_group(group, group_path, validation)

    validation.info.append({"code": "summary_group_count", "message": f"Loaded {len(groups)} summary group(s)"})
    return validation


def _validate_group(group: dict[str, Any], group_path: str, result: SummaryValidationResult) -> None:
    for field in sorted(REQUIRED_GROUP_FIELDS):
        if field not in group:
            result.add_error("summary_schema_validation_error", f"Missing group field: {field}", group_path)

    fill_distribution = group.get("fill_distribution")
    if isinstance(fill_distribution, dict):
        result.add_error("object_fill_distribution", "fill_distribution must be an array, not an object", group_path)
        return
    if not isinstance(fill_distribution, list):
        result.add_error("summary_schema_validation_error", "fill_distribution must be an array", group_path)
        return

    n_trials = group.get("n_trials")
    if not isinstance(n_trials, int):
        result.add_error("summary_schema_validation_error", "group n_trials must be an integer", group_path)
        return

    total_count = 0
    total_rate = 0.0
    for index, entry in enumerate(fill_distribution):
        entry_path = f"{group_path}:fill_distribution[{index}]"
        if not isinstance(entry, dict):
            result.add_error("summary_schema_validation_error", "Each fill_distribution entry must be an object", entry_path)
            continue
        for field in sorted(REQUIRED_FILL_FIELDS):
            if field not in entry:
                result.add_error("summary_schema_validation_error", f"Missing fill_distribution field: {field}", entry_path)
        _validate_fill_entry(entry, entry_path, result)
        count = entry.get("count")
        rate = entry.get("rate")
        if isinstance(count, int):
            total_count += count
        if isinstance(rate, (int, float)):
            total_rate += float(rate)

    if total_count != n_trials:
        result.add_error(
            "summary_wrong_counts",
            f"fill_distribution counts sum to {total_count}, expected {n_trials}",
            group_path,
        )
    if fill_distribution and abs(total_rate - 1.0) > 1e-9:
        result.add_error(
            "summary_wrong_rates",
            f"fill_distribution rates sum to {total_rate}, expected 1.0",
            group_path,
        )


def _validate_fill_entry(entry: dict[str, Any], entry_path: str, result: SummaryValidationResult) -> None:
    fill_class = entry.get("fill_class")
    extracted_fill = entry.get("extracted_fill")
    fill_key = entry.get("fill_key")

    if fill_class == "parse_fail":
        if extracted_fill is not None or fill_key != PARSE_FAIL_FILL_KEY:
            result.add_error(
                "parse_fail_missing_sentinel",
                "parse_fail entries must use extracted_fill null and fill_key __PARSE_FAIL__",
                entry_path,
            )
