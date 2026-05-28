from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_ENVIRONMENT_FIELDS = {
    "submitter_id",
    "run_id",
    "tool_version",
    "dataset_id",
    "model_id",
    "backend",
    "provider",
    "prompt_template_id",
    "prompt_language",
    "support_mode",
    "f_shot",
    "blank_rendering",
    "parser_config",
    "generation_config",
}

SUPPORTED_SUPPORT_MODES = {"zero", "format_shot", "task_shot", "control_shot", "mixed_shot"}
SUPPORTED_EXTRACTION_MODES = {"exact_full_text", "segment", "fallback_answer_phrase"}


@dataclass(frozen=True)
class ValidationMessage:
    code: str
    message: str
    path: str
    severity: str = "ERROR"

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


class EnvironmentValidationResult:
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


def validate_environment_file(input_path: Path) -> EnvironmentValidationResult:
    result = EnvironmentValidationResult()
    if not input_path.exists():
        result.add_error("file_not_found", "Environment file does not exist", str(input_path))
        return result

    try:
        environment = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.add_error("json_parse_error", f"Invalid environment JSON: {exc.msg}", str(input_path))
        return result

    if not isinstance(environment, dict):
        result.add_error("environment_schema_validation_error", "Environment JSON must be an object", str(input_path))
        return result

    validate_environment_object(environment, str(input_path), result)
    return result


def validate_environment_object(
    environment: dict[str, Any],
    path: str = "environment",
    result: EnvironmentValidationResult | None = None,
) -> EnvironmentValidationResult:
    validation = result or EnvironmentValidationResult()

    for field in sorted(REQUIRED_ENVIRONMENT_FIELDS):
        if field not in environment:
            validation.add_error("environment_schema_validation_error", f"Missing environment field: {field}", path)

    _validate_non_empty_string(environment, "submitter_id", path, validation)
    _validate_non_empty_string(environment, "run_id", path, validation)
    _validate_non_empty_string(environment, "tool_version", path, validation)
    _validate_non_empty_string(environment, "dataset_id", path, validation)
    _validate_non_empty_string(environment, "model_id", path, validation)
    _validate_non_empty_string(environment, "backend", path, validation)
    _validate_non_empty_string(environment, "provider", path, validation)
    _validate_non_empty_string(environment, "prompt_template_id", path, validation)
    _validate_non_empty_string(environment, "blank_rendering", path, validation)

    prompt_language = environment.get("prompt_language")
    if not isinstance(prompt_language, str) or len(prompt_language) < 2:
        validation.add_error("environment_schema_validation_error", "prompt_language must be a string with length >= 2", path)

    support_mode = environment.get("support_mode")
    if support_mode not in SUPPORTED_SUPPORT_MODES:
        validation.add_error("environment_schema_validation_error", f"Unsupported support_mode: {support_mode!r}", path)

    f_shot = environment.get("f_shot")
    if not isinstance(f_shot, int) or f_shot < 0:
        validation.add_error("environment_schema_validation_error", "f_shot must be a non-negative integer", path)
    if support_mode == "zero" and f_shot != 0:
        validation.add_error("zero_support_mode_with_f_shot", "support_mode zero requires f_shot = 0", path)

    parser_config = environment.get("parser_config")
    if not isinstance(parser_config, dict):
        validation.add_error("environment_schema_validation_error", "parser_config must be an object", path)
    else:
        _validate_parser_config(parser_config, f"{path}:parser_config", validation)

    generation_config = environment.get("generation_config")
    if not isinstance(generation_config, dict):
        validation.add_error("environment_schema_validation_error", "generation_config must be an object", path)
    else:
        _validate_generation_config(generation_config, f"{path}:generation_config", validation)

    validation.info.append({"code": "environment_validated", "message": "Validated one environment object"})
    return validation


def _validate_parser_config(
    parser_config: dict[str, Any],
    path: str,
    result: EnvironmentValidationResult,
) -> None:
    normalization = parser_config.get("normalization")
    if not isinstance(normalization, str) or not normalization:
        result.add_error("environment_schema_validation_error", "parser_config.normalization must be a non-empty string", path)

    extraction_modes = parser_config.get("extraction_modes_enabled")
    if not isinstance(extraction_modes, list) or not extraction_modes:
        result.add_error("environment_schema_validation_error", "parser_config.extraction_modes_enabled must be a non-empty array", path)
        return

    seen_modes: set[str] = set()
    for index, mode in enumerate(extraction_modes):
        mode_path = f"{path}:extraction_modes_enabled[{index}]"
        if not isinstance(mode, str):
            result.add_error("environment_schema_validation_error", "extraction mode must be a string", mode_path)
            continue
        if mode not in SUPPORTED_EXTRACTION_MODES:
            result.add_error("environment_schema_validation_error", f"Unsupported extraction mode: {mode!r}", mode_path)
        if mode in seen_modes:
            result.add_error("environment_schema_validation_error", f"Duplicate extraction mode: {mode!r}", mode_path)
        seen_modes.add(mode)


def _validate_generation_config(
    generation_config: dict[str, Any],
    path: str,
    result: EnvironmentValidationResult,
) -> None:
    if "temperature" not in generation_config:
        result.add_error("environment_schema_validation_error", "generation_config.temperature is required", path)
    temperature = generation_config.get("temperature")
    if temperature is not None and (not isinstance(temperature, (int, float)) or temperature < 0):
        result.add_error("environment_schema_validation_error", "generation_config.temperature must be null or a non-negative number", path)

    max_tokens = generation_config.get("max_tokens")
    if not isinstance(max_tokens, int) or max_tokens < 1:
        result.add_error("environment_schema_validation_error", "generation_config.max_tokens must be an integer >= 1", path)

    top_p = generation_config.get("top_p")
    if top_p is not None and (not isinstance(top_p, (int, float)) or top_p < 0 or top_p > 1):
        result.add_error("environment_schema_validation_error", "generation_config.top_p must be null or a number in [0, 1]", path)


def _validate_non_empty_string(
    obj: dict[str, Any],
    field: str,
    path: str,
    result: EnvironmentValidationResult,
) -> None:
    value = obj.get(field)
    if not isinstance(value, str) or not value:
        result.add_error("environment_schema_validation_error", f"{field} must be a non-empty string", path)
