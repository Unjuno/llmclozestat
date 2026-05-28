from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 only
    import tomli as tomllib  # type: ignore[no-redef]

from llmclozestat.model_validation import validate_model_file


@dataclass(frozen=True)
class ValidationMessage:
    code: str
    message: str
    path: str
    severity: str = "ERROR"

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


class ModelRepositoryValidationResult:
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


def validate_model_repository(repo_dir: Path) -> ModelRepositoryValidationResult:
    result = ModelRepositoryValidationResult()
    if not repo_dir.exists():
        result.add_error("model_schema_validation_error", "Model repository path does not exist", str(repo_dir))
        return result
    if not repo_dir.is_dir():
        result.add_error("model_schema_validation_error", "Model repository path is not a directory", str(repo_dir))
        return result

    model_path = repo_dir / "model.toml"
    model_result = validate_model_file(model_path)
    _merge_result(model_result, result)
    if result.failed:
        return result

    model_toml = _load_model_toml(model_path, result)
    if model_toml is None:
        return result

    model = model_toml.get("model")
    if not isinstance(model, dict):
        result.add_error("model_schema_validation_error", "Missing [model] table", str(model_path))
        return result
    model_id = model.get("model_id")
    if not isinstance(model_id, str) or not model_id:
        result.add_error("model_schema_validation_error", "model.model_id must be a non-empty string", str(model_path))
        return result

    checked = _check_submission_model_ids(repo_dir / "submissions", model_id, result)
    result.info.append({"code": "model_repository_checked", "message": f"Checked {checked} submission metadata artifact(s)"})
    return result


def _merge_result(source: Any, target: ModelRepositoryValidationResult) -> None:
    for error in getattr(source, "errors", []):
        target.add_error(error.code, error.message, error.path)
    for warning in getattr(source, "warnings", []):
        target.add_warning(warning.code, warning.message, warning.path)
    target.info.extend(getattr(source, "info", []))


def _load_model_toml(model_path: Path, result: ModelRepositoryValidationResult) -> dict[str, Any] | None:
    try:
        parsed = tomllib.loads(model_path.read_text(encoding="utf-8"))
    except Exception as exc:
        result.add_error("toml_parse_error", f"Invalid TOML: {exc}", str(model_path))
        return None
    if not isinstance(parsed, dict):
        result.add_error("model_schema_validation_error", "model.toml must parse to a table", str(model_path))
        return None
    return parsed


def _check_submission_model_ids(submissions_dir: Path, expected_model_id: str, result: ModelRepositoryValidationResult) -> int:
    if not submissions_dir.exists():
        return 0
    if not submissions_dir.is_dir():
        result.add_error("model_schema_validation_error", "submissions path exists but is not a directory", str(submissions_dir))
        return 0

    checked = 0
    for artifact_path in sorted(submissions_dir.glob("*/*/environment.json")) + sorted(submissions_dir.glob("*/*/summary.json")):
        artifact = _load_json_object(artifact_path, result)
        if artifact is None:
            continue
        checked += 1
        artifact_model_id = artifact.get("model_id")
        if artifact_model_id != expected_model_id:
            result.add_error(
                "mixed_model_submission",
                f"{artifact_path.name} model_id {artifact_model_id!r} does not match model.toml model_id {expected_model_id!r}",
                str(artifact_path),
            )
    return checked


def _load_json_object(path: Path, result: ModelRepositoryValidationResult) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.add_error("json_parse_error", f"Invalid JSON: {exc.msg}", str(path))
        return None
    if not isinstance(value, dict):
        result.add_error("schema_validation_error", "Submission metadata artifact must be a JSON object", str(path))
        return None
    return value
