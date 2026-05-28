from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PACKAGE_HASH_INPUT_DESCRIPTION = (
    "canonical_json(v0: keys sorted; files sorted by path; file fields path,sha256; "
    "exclude manifest/signature/ledger; utf-8; compact)"
)

EXCLUDED_PACKAGE_HASH_INPUT_PATHS = {"manifest.json", "signature.json", "ledger_receipt.json"}
REQUIRED_MANIFEST_FIELDS = {
    "manifest_version",
    "submitter_id",
    "run_id",
    "created_at",
    "hash_algorithm",
    "files",
    "package_hash",
    "package_hash_input",
}
REQUIRED_FILE_FIELDS = {"path", "sha256"}


@dataclass(frozen=True)
class ValidationMessage:
    code: str
    message: str
    path: str
    severity: str = "ERROR"

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


class ManifestValidationResult:
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


def validate_manifest_file(
    input_path: Path,
    package_dir: Path | None = None,
    *,
    verify_files: bool = False,
) -> ManifestValidationResult:
    """Validate a manifest and optionally verify package file hashes.

    This is a schema-like v0 validator, not a complete JSON Schema validator.
    When verify_files=True, package_dir defaults to the manifest parent directory.
    """

    result = ManifestValidationResult()
    if not input_path.exists():
        result.add_error("file_not_found", "Manifest file does not exist", str(input_path))
        return result

    try:
        manifest = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.add_error("json_parse_error", f"Invalid manifest JSON: {exc.msg}", str(input_path))
        return result

    if not isinstance(manifest, dict):
        result.add_error("manifest_schema_validation_error", "Manifest JSON must be an object", str(input_path))
        return result

    validate_manifest_object(manifest, str(input_path), result)

    if verify_files and not result.failed:
        verify_manifest_integrity(
            manifest,
            package_dir or input_path.parent,
            str(input_path),
            result,
        )

    return result


def validate_submission_manifest(package_dir: Path) -> ManifestValidationResult:
    """Validate and verify package_dir/manifest.json."""

    manifest_path = package_dir / "manifest.json"
    if not manifest_path.exists():
        result = ManifestValidationResult()
        result.add_error("missing_manifest", "Submission package has no manifest.json", str(manifest_path))
        return result
    return validate_manifest_file(manifest_path, package_dir=package_dir, verify_files=True)


def validate_manifest_object(
    manifest: dict[str, Any],
    path: str = "manifest",
    result: ManifestValidationResult | None = None,
) -> ManifestValidationResult:
    validation = result or ManifestValidationResult()

    for field in sorted(REQUIRED_MANIFEST_FIELDS):
        if field not in manifest:
            validation.add_error("manifest_schema_validation_error", f"Missing manifest field: {field}", path)

    if manifest.get("hash_algorithm") != "sha256":
        validation.add_error("manifest_schema_validation_error", "hash_algorithm must be sha256", path)

    package_hash = manifest.get("package_hash")
    if not isinstance(package_hash, str) or not _is_package_hash(package_hash):
        validation.add_error(
            "manifest_schema_validation_error",
            "package_hash must have the form sha256:<64 lowercase hex>",
            path,
        )

    files = manifest.get("files")
    if not isinstance(files, list):
        validation.add_error("manifest_schema_validation_error", "files must be an array", path)
        return validation
    if not files:
        validation.add_error("manifest_schema_validation_error", "files must not be empty", path)
        return validation

    seen_paths: set[str] = set()
    for index, file_entry in enumerate(files):
        file_path = f"{path}:files[{index}]"
        if not isinstance(file_entry, dict):
            validation.add_error("manifest_schema_validation_error", "Each file entry must be an object", file_path)
            continue
        _validate_file_entry(file_entry, file_path, seen_paths, validation)

    validation.info.append({"code": "manifest_file_count", "message": f"Loaded {len(files)} manifest file entry/entries"})
    return validation


def verify_manifest_integrity(
    manifest: dict[str, Any],
    package_dir: Path,
    path: str,
    result: ManifestValidationResult,
) -> None:
    files = manifest.get("files")
    if not isinstance(files, list):
        return

    for index, file_entry in enumerate(files):
        file_path = f"{path}:files[{index}]"
        if not isinstance(file_entry, dict):
            continue
        rel_path = file_entry.get("path")
        expected_sha256 = file_entry.get("sha256")
        if not isinstance(rel_path, str) or not isinstance(expected_sha256, str):
            continue
        if not _is_safe_relative_path(rel_path):
            continue

        actual_path = package_dir / rel_path
        if not actual_path.exists() or not actual_path.is_file():
            result.add_error("missing_listed_file", f"Listed file does not exist: {rel_path}", file_path)
            continue

        actual_sha256 = sha256_file(actual_path)
        if actual_sha256 != expected_sha256:
            result.add_error(
                "wrong_file_hash",
                f"Listed SHA-256 for {rel_path} does not match raw file bytes",
                file_path,
            )

    if result.failed:
        return

    expected_package_hash = manifest.get("package_hash")
    actual_package_hash = compute_package_hash(manifest)
    if expected_package_hash != actual_package_hash:
        result.add_error(
            "wrong_package_hash",
            "package_hash does not match the canonical manifest calculation",
            path,
        )


def compute_package_hash(manifest: dict[str, Any]) -> str:
    files = manifest.get("files")
    canonical_files: list[dict[str, str]] = []
    if isinstance(files, list):
        for file_entry in files:
            if not isinstance(file_entry, dict):
                continue
            rel_path = file_entry.get("path")
            sha256 = file_entry.get("sha256")
            if isinstance(rel_path, str) and isinstance(sha256, str):
                if rel_path not in EXCLUDED_PACKAGE_HASH_INPUT_PATHS:
                    canonical_files.append({"path": rel_path, "sha256": sha256})

    canonical = {
        "files": sorted(canonical_files, key=lambda entry: entry["path"].encode("utf-8")),
        "hash_algorithm": manifest.get("hash_algorithm"),
        "manifest_version": manifest.get("manifest_version"),
        "run_id": manifest.get("run_id"),
        "submitter_id": manifest.get("submitter_id"),
    }
    encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_file_entry(
    file_entry: dict[str, Any],
    path: str,
    seen_paths: set[str],
    result: ManifestValidationResult,
) -> None:
    for field in sorted(REQUIRED_FILE_FIELDS):
        if field not in file_entry:
            result.add_error("manifest_schema_validation_error", f"Missing file field: {field}", path)

    rel_path = file_entry.get("path")
    if not isinstance(rel_path, str) or not rel_path:
        result.add_error("manifest_schema_validation_error", "file path must be a non-empty string", path)
    elif not _is_safe_relative_path(rel_path):
        result.add_error("path_traversal", "file path must be relative and must not contain parent traversal", path)
    else:
        if rel_path in seen_paths:
            result.add_error("manifest_schema_validation_error", f"Duplicate manifest file path: {rel_path}", path)
        seen_paths.add(rel_path)
        if rel_path in EXCLUDED_PACKAGE_HASH_INPUT_PATHS:
            result.add_error(
                "unexpected_manifest_self_reference",
                f"{rel_path} must not be included in v0 package hash input",
                path,
            )

    sha256 = file_entry.get("sha256")
    if not isinstance(sha256, str) or not _is_sha256_hex(sha256):
        result.add_error("manifest_schema_validation_error", "sha256 must be 64 lowercase hex characters", path)

    size_bytes = file_entry.get("size_bytes")
    if size_bytes is not None and (not isinstance(size_bytes, int) or size_bytes < 0):
        result.add_error("manifest_schema_validation_error", "size_bytes must be a non-negative integer or null", path)


def _is_safe_relative_path(path: str) -> bool:
    path_obj = Path(path)
    if path_obj.is_absolute():
        return False
    if "" in path.split("/"):
        return False
    return ".." not in path_obj.parts


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _is_package_hash(value: str) -> bool:
    prefix = "sha256:"
    return value.startswith(prefix) and _is_sha256_hex(value[len(prefix) :])
