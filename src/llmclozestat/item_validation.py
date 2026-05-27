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


TOP_LEVEL_REQUIRED = {
    "dataset_id",
    "probe_id",
    "variant_id",
    "item_id",
    "version",
    "language",
    "translation_relation",
    "equivalence_level",
    "item_type",
    "primary_skill",
    "secondary_tags",
    "validation_target",
    "claim_scope",
    "text_with_blanks",
    "segments",
    "blanks",
    "expected_full_texts",
    "ambiguity_level",
    "source_type",
    "review_status",
}

BLANK_REQUIRED = {
    "blank_id",
    "position",
    "primary_skill",
    "context_distance",
    "accepted_fills",
    "near_miss_fills",
    "known_wrong_fills",
    "expected_error_patterns",
}


SCHEMA_DERIVED_REQUIRED_CODE = {
    "claim_scope": "missing_claim_scope",
}


class ItemValidationResult:
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


def validate_items_file(dataset_path: Path) -> ItemValidationResult:
    result = ItemValidationResult()

    if not dataset_path.exists():
        result.add_error(
            "file_not_found",
            "Dataset file does not exist",
            str(dataset_path),
        )
        return result

    item_ids: dict[str, int] = {}
    variant_ids: dict[str, int] = {}
    item_count = 0

    with dataset_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw_line = line.strip()
            if not raw_line:
                continue

            item_path = f"{dataset_path}:{line_number}"
            try:
                item = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                result.add_error(
                    "json_parse_error",
                    f"Invalid JSONL line: {exc.msg}",
                    item_path,
                )
                continue

            if not isinstance(item, dict):
                result.add_error(
                    "schema_validation_error",
                    "Each item JSONL line must be a JSON object",
                    item_path,
                )
                continue

            item_count += 1
            _validate_item_schema_like(item, item_path, result)
            _validate_item_cross_fields(item, item_path, result)

            item_id = item.get("item_id")
            if isinstance(item_id, str):
                if item_id in item_ids:
                    result.add_error(
                        "duplicate_item_id",
                        f"Duplicate item_id {item_id!r}; first seen on line {item_ids[item_id]}",
                        item_path,
                    )
                else:
                    item_ids[item_id] = line_number

            variant_id = item.get("variant_id")
            if isinstance(variant_id, str):
                if variant_id in variant_ids:
                    result.add_error(
                        "duplicate_variant_id",
                        f"Duplicate variant_id {variant_id!r}; first seen on line {variant_ids[variant_id]}",
                        item_path,
                    )
                else:
                    variant_ids[variant_id] = line_number

    result.info.append({"code": "item_count", "message": f"Loaded {item_count} item(s)"})
    return result


def _validate_item_schema_like(item: dict[str, Any], item_path: str, result: ItemValidationResult) -> None:
    for field in sorted(TOP_LEVEL_REQUIRED):
        if field not in item:
            result.add_error(
                SCHEMA_DERIVED_REQUIRED_CODE.get(field, "schema_validation_error"),
                f"Missing required field: {field}",
                item_path,
            )

    expected_full_texts = item.get("expected_full_texts")
    if isinstance(expected_full_texts, list) and not expected_full_texts:
        result.add_error(
            "empty_expected_full_texts",
            "expected_full_texts must contain at least one entry",
            item_path,
        )

    segments = item.get("segments")
    if "segments" in item and not isinstance(segments, list):
        result.add_error("schema_validation_error", "segments must be an array", item_path)

    blanks = item.get("blanks")
    if "blanks" in item and not isinstance(blanks, list):
        result.add_error("schema_validation_error", "blanks must be an array", item_path)
        return

    if not isinstance(blanks, list):
        return

    for index, blank in enumerate(blanks):
        blank_path = f"{item_path}:blanks[{index}]"
        if not isinstance(blank, dict):
            result.add_error("schema_validation_error", "Each blank must be an object", blank_path)
            continue

        for field in sorted(BLANK_REQUIRED):
            if field not in blank:
                result.add_error(
                    "schema_validation_error",
                    f"Missing required blank field: {field}",
                    blank_path,
                )

        accepted_fills = blank.get("accepted_fills")
        if isinstance(accepted_fills, list) and not accepted_fills:
            result.add_error(
                "empty_accepted_fills",
                "accepted_fills must contain at least one entry",
                blank_path,
            )


def _validate_item_cross_fields(item: dict[str, Any], item_path: str, result: ItemValidationResult) -> None:
    segments = item.get("segments")
    blanks = item.get("blanks")

    if isinstance(segments, list) and isinstance(blanks, list):
        if len(segments) != len(blanks) + 1:
            result.add_error(
                "segments_blanks_mismatch",
                "segments.length must equal blanks.length + 1",
                item_path,
            )

    if not isinstance(blanks, list):
        return

    blank_ids: dict[str, int] = {}
    positions: dict[int, int] = {}
    position_values: list[int] = []

    for index, blank in enumerate(blanks):
        if not isinstance(blank, dict):
            continue
        blank_path = f"{item_path}:blanks[{index}]"

        blank_id = blank.get("blank_id")
        if isinstance(blank_id, str):
            if blank_id in blank_ids:
                result.add_error(
                    "duplicate_blank_id",
                    f"Duplicate blank_id {blank_id!r}; first seen at blanks[{blank_ids[blank_id]}]",
                    blank_path,
                )
            else:
                blank_ids[blank_id] = index

        depends_on = blank.get("depends_on")
        if isinstance(depends_on, str):
            if depends_on not in blank_ids:
                result.add_error(
                    "depends_on_unknown_blank",
                    f"depends_on references unknown or later blank_id {depends_on!r}",
                    blank_path,
                )

        position = blank.get("position")
        if isinstance(position, int):
            position_values.append(position)
            if position in positions:
                result.add_error(
                    "duplicate_blank_position",
                    f"Duplicate blank position {position}; first seen at blanks[{positions[position]}]",
                    blank_path,
                )
            else:
                positions[position] = index

        _validate_fill_lists(blank, blank_path, result)

    if position_values:
        expected_positions = list(range(1, len(position_values) + 1))
        if sorted(position_values) != expected_positions:
            result.add_error(
                "position_not_consecutive",
                f"Blank positions must be consecutive from 1; got {sorted(position_values)}",
                item_path,
            )


def _validate_fill_lists(blank: dict[str, Any], blank_path: str, result: ItemValidationResult) -> None:
    seen: dict[str, str] = {}
    for field in ("accepted_fills", "near_miss_fills", "known_wrong_fills"):
        values = blank.get(field)
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, str):
                continue
            normalized = value.strip()
            if normalized in seen:
                result.add_error(
                    "duplicate_normalized_fill",
                    f"Fill {value!r} appears in both {seen[normalized]} and {field}",
                    blank_path,
                )
            else:
                seen[normalized] = field
