from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidationMessage:
    code: str
    message: str
    path: str
    severity: str = "ERROR"

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
        }


class ResultValidationResult:
    def __init__(self) -> None:
        self.errors: list[ValidationMessage] = []
        self.warnings: list[ValidationMessage] = []
        self.info: list[dict[str, Any]] = []

    @property
    def failed(self) -> bool:
        return bool(self.errors)

    def add_error(self, code: str, message: str, path: str) -> None:
        self.errors.append(ValidationMessage(code=code, message=message, path=path))

    def add_warning(self, code: str, message: str, path: str) -> None:
        self.warnings.append(ValidationMessage(code=code, message=message, path=path, severity="WARNING"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "failed" if self.failed else "passed",
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "info": self.info,
        }


REQUIRED_RESULT_FIELDS = {
    "submitter_id",
    "run_id",
    "dataset_id",
    "model_id",
    "backend",
    "provider",
    "probe_id",
    "variant_id",
    "language",
    "primary_skill",
    "item_id",
    "trial_id",
    "prompt_template_id",
    "prompt_language",
    "support_mode",
    "f_shot",
    "blank_rendering",
    "generation_config",
    "raw_output",
    "normalized_output",
    "extraction_mode",
    "blank_results",
    "instruction_following_pass",
    "item_format_pass",
    "item_strict_pass",
    "item_partial_score",
    "latency_ms",
}

CONDITION_FIELDS = {
    "prompt_template_id",
    "prompt_language",
    "support_mode",
    "f_shot",
    "blank_rendering",
    "extraction_mode",
    "generation_config",
}

SUPPORTED_V0_EXTRACTION_MODES = {"exact_full_text", "segment"}

RESULT_IDENTITY_FIELDS = (
    "submitter_id",
    "run_id",
    "dataset_id",
    "model_id",
    "item_id",
    "trial_id",
    "prompt_template_id",
    "support_mode",
    "f_shot",
    "blank_rendering",
    "extraction_mode",
)


def validate_results_file(input_path: Path) -> ResultValidationResult:
    result = ResultValidationResult()

    if not input_path.exists():
        result.add_error("file_not_found", "Result file does not exist", str(input_path))
        return result

    record_count = 0
    identities: dict[tuple[Any, ...], int] = {}

    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw_line = line.strip()
            if not raw_line:
                continue

            record_path = f"{input_path}:{line_number}"
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                result.add_error("json_parse_error", f"Invalid JSONL line: {exc.msg}", record_path)
                continue

            if not isinstance(record, dict):
                result.add_error("schema_validation_error", "Each result JSONL line must be a JSON object", record_path)
                continue

            record_count += 1
            _validate_result_record(record, record_path, result)
            _validate_result_identity(record, record_path, line_number, identities, result)

    result.info.append({"code": "result_count", "message": f"Loaded {record_count} result record(s)"})
    return result


def _validate_result_record(record: dict[str, Any], record_path: str, result: ResultValidationResult) -> None:
    for field in sorted(REQUIRED_RESULT_FIELDS):
        if field not in record:
            result.add_error("schema_validation_error", f"Missing required result field: {field}", record_path)

    for field in sorted(CONDITION_FIELDS):
        if field not in record:
            result.add_error("missing_condition_field", f"Missing condition field: {field}", record_path)

    extraction_mode = record.get("extraction_mode")
    if isinstance(extraction_mode, str) and extraction_mode not in SUPPORTED_V0_EXTRACTION_MODES:
        result.add_error(
            "unsupported_extraction_mode",
            f"Unsupported v0 extraction_mode: {extraction_mode}",
            record_path,
        )

    support_mode = record.get("support_mode")
    f_shot = record.get("f_shot")
    if support_mode == "zero" and f_shot != 0:
        result.add_error("zero_support_mode_with_f_shot", "support_mode zero requires f_shot = 0", record_path)

    item_partial_score = record.get("item_partial_score")
    if isinstance(item_partial_score, (int, float)):
        if item_partial_score < 0 or item_partial_score > 1:
            result.add_error(
                "invalid_item_partial_score",
                "item_partial_score must be in [0, 1]",
                record_path,
            )

    blank_results = record.get("blank_results")
    if not isinstance(blank_results, list):
        result.add_error("schema_validation_error", "blank_results must be an array", record_path)
        return
    if not blank_results:
        result.add_error("empty_blank_results", "Result record has no blank_results", record_path)
        return

    _validate_blank_results(blank_results, record_path, result)
    _validate_item_level_scores(record, blank_results, record_path, result)


def _validate_blank_results(blank_results: list[Any], record_path: str, result: ResultValidationResult) -> None:
    blank_ids: set[str] = set()

    for index, blank_result in enumerate(blank_results):
        blank_path = f"{record_path}:blank_results[{index}]"
        if not isinstance(blank_result, dict):
            result.add_error("schema_validation_error", "Each blank result must be an object", blank_path)
            continue

        blank_id = blank_result.get("blank_id")
        if isinstance(blank_id, str):
            if blank_id in blank_ids:
                result.add_error("duplicate_result_blank_id", f"Duplicate blank_id {blank_id!r}", blank_path)
            else:
                blank_ids.add(blank_id)

        fill_class = blank_result.get("fill_class")
        content_pass = blank_result.get("content_pass")
        parse_fail = blank_result.get("parse_fail")
        blank_parse_pass = blank_result.get("blank_parse_pass")
        extracted_fill = blank_result.get("extracted_fill")

        if content_pass is True and fill_class != "accepted":
            result.add_error(
                "content_pass_fill_class_inconsistent",
                "content_pass true requires fill_class accepted in v0",
                blank_path,
            )
            if fill_class == "near_miss":
                result.add_error("content_pass_near_miss", "near_miss is not content-pass in v0", blank_path)

        if parse_fail is True and blank_parse_pass is True:
            result.add_error(
                "parse_fail_with_blank_parse_pass",
                "parse_fail true conflicts with blank_parse_pass true",
                blank_path,
            )

        if parse_fail is True and extracted_fill is not None:
            result.add_warning(
                "parse_fail_with_extracted_fill",
                "parse_fail true should normally have extracted_fill null",
                blank_path,
            )

        if fill_class == "format_fail":
            result.add_warning(
                "format_fail_v0",
                "blank-level format_fail is reserved in strict v0 data",
                blank_path,
            )


def _validate_item_level_scores(
    record: dict[str, Any],
    blank_results: list[Any],
    record_path: str,
    result: ResultValidationResult,
) -> None:
    expected_strict = (
        record.get("instruction_following_pass") is True
        and record.get("item_format_pass") is True
        and all(isinstance(blank, dict) and blank.get("content_pass") is True for blank in blank_results)
    )
    if record.get("item_strict_pass") != expected_strict:
        result.add_error(
            "strict_pass_inconsistent",
            "item_strict_pass does not match the strict-pass formula",
            record_path,
        )


def _validate_result_identity(
    record: dict[str, Any],
    record_path: str,
    line_number: int,
    identities: dict[tuple[Any, ...], int],
    result: ResultValidationResult,
) -> None:
    if not all(field in record for field in RESULT_IDENTITY_FIELDS):
        return
    identity = tuple(record.get(field) for field in RESULT_IDENTITY_FIELDS)
    if identity in identities:
        result.add_error(
            "duplicate_result_identity",
            f"Duplicate result identity; first seen on line {identities[identity]}",
            record_path,
        )
    else:
        identities[identity] = line_number
