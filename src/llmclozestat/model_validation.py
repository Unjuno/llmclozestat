from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 only
    import tomli as tomllib  # type: ignore[no-redef]


MODEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SUPPORTED_SUPPORT_MODES = {"zero", "format_shot", "task_shot", "control_shot", "mixed_shot"}
REQUIRED_MODEL_FIELDS = {
    "model_id",
    "family",
    "source",
    "source_repo",
    "revision",
    "quantization",
    "backend",
}
REQUIRED_PROMPT_FIELDS = {
    "prompt_template_id",
    "prompt_language",
    "support_mode",
    "f_shot",
    "blank_rendering",
}


@dataclass(frozen=True)
class ValidationMessage:
    code: str
    message: str
    path: str
    severity: str = "ERROR"

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


class ModelValidationResult:
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


def validate_model_file(input_path: Path) -> ModelValidationResult:
    result = ModelValidationResult()
    if not input_path.exists():
        result.add_error("model_toml_missing", "model.toml does not exist", str(input_path))
        return result
    if not input_path.is_file():
        result.add_error("model_schema_validation_error", "model.toml path is not a file", str(input_path))
        return result

    try:
        parsed = tomllib.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:
        result.add_error("toml_parse_error", f"Invalid TOML: {exc}", str(input_path))
        return result

    if not isinstance(parsed, dict):
        result.add_error("model_schema_validation_error", "model.toml must parse to a table", str(input_path))
        return result

    validate_model_object(parsed, str(input_path), result)
    return result


def validate_model_object(
    model_toml: dict[str, Any],
    path: str = "model.toml",
    result: ModelValidationResult | None = None,
) -> ModelValidationResult:
    validation = result or ModelValidationResult()

    model = model_toml.get("model")
    if not isinstance(model, dict):
        validation.add_error("model_schema_validation_error", "Missing [model] table", path)
    else:
        _validate_model_table(model, f"{path}:model", validation)

    policy = model_toml.get("policy")
    if not isinstance(policy, dict):
        validation.add_error("model_schema_validation_error", "Missing [policy] table", path)
    else:
        _validate_policy_table(policy, f"{path}:policy", validation)

    default_condition = model_toml.get("default_condition")
    if default_condition is not None:
        if not isinstance(default_condition, dict):
            validation.add_error("model_schema_validation_error", "default_condition must be a table", path)
        else:
            _validate_default_condition(default_condition, f"{path}:default_condition", validation)

    if isinstance(model, dict):
        model_id = model.get("model_id")
        validation.info.append({"code": "model_validated", "message": f"Validated model metadata for {model_id!r}"})
    return validation


def _validate_model_table(model: dict[str, Any], path: str, result: ModelValidationResult) -> None:
    for field in sorted(REQUIRED_MODEL_FIELDS):
        if field not in model:
            result.add_error("model_schema_validation_error", f"Missing model field: {field}", path)

    for field in sorted(REQUIRED_MODEL_FIELDS - {"model_id"}):
        _validate_non_empty_string(model, field, path, result)

    model_id = model.get("model_id")
    if not isinstance(model_id, str) or not MODEL_ID_RE.fullmatch(model_id):
        result.add_error("model_schema_validation_error", f"Invalid model_id: {model_id!r}", path)

    backend_version = model.get("backend_version")
    if backend_version is not None and not isinstance(backend_version, str):
        result.add_error("model_schema_validation_error", "backend_version must be string or null", path)

    context_window = model.get("context_window")
    if context_window is not None and (not isinstance(context_window, int) or context_window < 1):
        result.add_error("model_schema_validation_error", "context_window must be integer >= 1 or null", path)

    notes = model.get("notes")
    if notes is not None and not isinstance(notes, str):
        result.add_error("model_schema_validation_error", "notes must be string or null", path)


def _validate_policy_table(policy: dict[str, Any], path: str, result: ModelValidationResult) -> None:
    if policy.get("one_model_repo") is not True:
        result.add_error("missing_one_model_repo", "policy.one_model_repo must be true", path)

    allow_mixed = policy.get("allow_mixed_model_ids")
    if allow_mixed is True:
        result.add_error("mixed_model_submission", "allow_mixed_model_ids=true is unsupported in the MVP", path)
    elif allow_mixed is not None and not isinstance(allow_mixed, bool):
        result.add_error("model_schema_validation_error", "allow_mixed_model_ids must be boolean when present", path)


def _validate_default_condition(condition: dict[str, Any], path: str, result: ModelValidationResult) -> None:
    prompt = condition.get("prompt")
    if prompt is not None:
        if not isinstance(prompt, dict):
            result.add_error("model_schema_validation_error", "default_condition.prompt must be a table", path)
        else:
            _validate_prompt_table(prompt, f"{path}:prompt", result)

    generation = condition.get("generation")
    if generation is not None:
        if not isinstance(generation, dict):
            result.add_error("model_schema_validation_error", "default_condition.generation must be a table", path)
        else:
            _validate_generation_table(generation, f"{path}:generation", result)

    parser = condition.get("parser")
    if parser is not None:
        if not isinstance(parser, dict):
            result.add_error("model_schema_validation_error", "default_condition.parser must be a table", path)
        else:
            _validate_parser_table(parser, f"{path}:parser", result)


def _validate_prompt_table(prompt: dict[str, Any], path: str, result: ModelValidationResult) -> None:
    for field in sorted(REQUIRED_PROMPT_FIELDS):
        if field not in prompt:
            result.add_error("model_schema_validation_error", f"Missing default prompt field: {field}", path)

    _validate_non_empty_string(prompt, "prompt_template_id", path, result)
    _validate_non_empty_string(prompt, "prompt_language", path, result)
    _validate_non_empty_string(prompt, "blank_rendering", path, result)

    support_mode = prompt.get("support_mode")
    if support_mode not in SUPPORTED_SUPPORT_MODES:
        result.add_error("model_schema_validation_error", f"Unsupported support_mode: {support_mode!r}", path)

    f_shot = prompt.get("f_shot")
    if not isinstance(f_shot, int) or f_shot < 0:
        result.add_error("model_schema_validation_error", "f_shot must be integer >= 0", path)
    if support_mode == "zero" and f_shot != 0:
        result.add_error("zero_support_mode_with_f_shot", "support_mode zero requires f_shot = 0", path)


def _validate_generation_table(generation: dict[str, Any], path: str, result: ModelValidationResult) -> None:
    temperature = generation.get("temperature")
    if temperature is not None and (not isinstance(temperature, (int, float)) or temperature < 0):
        result.add_error("model_schema_validation_error", "temperature must be number >= 0 or null", path)

    top_p = generation.get("top_p")
    if top_p is not None and (not isinstance(top_p, (int, float)) or top_p < 0 or top_p > 1):
        result.add_error("model_schema_validation_error", "top_p must be number in [0, 1] or null", path)

    seed = generation.get("seed")
    if seed is not None and not isinstance(seed, int):
        result.add_error("model_schema_validation_error", "seed must be integer or null", path)

    max_tokens = generation.get("max_tokens")
    if max_tokens is not None and (not isinstance(max_tokens, int) or max_tokens < 1):
        result.add_error("model_schema_validation_error", "max_tokens must be integer >= 1 or null", path)

    repeat_penalty = generation.get("repeat_penalty")
    if repeat_penalty is not None and not isinstance(repeat_penalty, (int, float)):
        result.add_error("model_schema_validation_error", "repeat_penalty must be number or null", path)


def _validate_parser_table(parser: dict[str, Any], path: str, result: ModelValidationResult) -> None:
    normalization = parser.get("normalization")
    if normalization is not None and (not isinstance(normalization, str) or not normalization):
        result.add_error("model_schema_validation_error", "normalization must be a non-empty string when present", path)

    extraction_modes = parser.get("extraction_modes_enabled")
    if extraction_modes is not None:
        if not isinstance(extraction_modes, list) or not extraction_modes:
            result.add_error("model_schema_validation_error", "extraction_modes_enabled must be a non-empty array when present", path)
        elif not all(isinstance(mode, str) and mode for mode in extraction_modes):
            result.add_error("model_schema_validation_error", "all extraction modes must be non-empty strings", path)

    fallback = parser.get("fallback_extraction_enabled")
    if fallback is not None and not isinstance(fallback, bool):
        result.add_error("model_schema_validation_error", "fallback_extraction_enabled must be boolean when present", path)


def _validate_non_empty_string(obj: dict[str, Any], field: str, path: str, result: ModelValidationResult) -> None:
    value = obj.get(field)
    if not isinstance(value, str) or not value:
        result.add_error("model_schema_validation_error", f"{field} must be a non-empty string", path)
