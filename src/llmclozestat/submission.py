from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llmclozestat.environment_validation import validate_environment_file
from llmclozestat.manifest_validation import (
    PACKAGE_HASH_INPUT_DESCRIPTION,
    compute_package_hash,
    sha256_file,
    validate_manifest_file,
)
from llmclozestat.result_validation import validate_results_file
from llmclozestat.summary_validation import validate_summary_file


class PrepareSubmissionError(ValueError):
    """Raised when a submission package cannot be prepared safely."""


REQUIRED_PACKAGE_FILENAMES = {
    "environment_json": "environment.json",
    "run_jsonl": "run.jsonl",
    "summary_json": "summary.json",
}


def prepare_submission_package(
    *,
    submitter_id: str,
    run_id: str,
    environment_json: Path,
    run_jsonl: Path,
    summary_json: Path,
    out_dir: Path,
    summary_md: Path | None = None,
    write_manifest: bool = True,
    overwrite: bool = False,
    validate_sources: bool = True,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Copy run artifacts into a submission package directory.

    This function intentionally does not run a model or aggregate results. By
    default, it validates the existing environment/run/summary artifacts before
    copying them, then optionally writes a v0 manifest for package-level integrity.
    Full submission semantic validation belongs to validate-submission.
    """

    _require_non_empty("submitter_id", submitter_id)
    _require_non_empty("run_id", run_id)
    _ensure_source_file("environment_json", environment_json)
    _ensure_source_file("run_jsonl", run_jsonl)
    _ensure_source_file("summary_json", summary_json)
    if summary_md is not None:
        _ensure_source_file("summary_md", summary_md)

    if validate_sources:
        _validate_source_artifacts(
            environment_json=environment_json,
            run_jsonl=run_jsonl,
            summary_json=summary_json,
        )

    if out_dir.exists() and any(out_dir.iterdir()) and not overwrite:
        raise PrepareSubmissionError(f"Output directory is not empty: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    copied_paths = {
        "environment.json": _copy_artifact(environment_json, out_dir / "environment.json"),
        "run.jsonl": _copy_artifact(run_jsonl, out_dir / "run.jsonl"),
        "summary.json": _copy_artifact(summary_json, out_dir / "summary.json"),
    }
    if summary_md is not None:
        copied_paths["summary.md"] = _copy_artifact(summary_md, out_dir / "summary.md")

    manifest_written = False
    if write_manifest:
        manifest = build_manifest(
            submitter_id=submitter_id,
            run_id=run_id,
            package_dir=out_dir,
            relative_paths=sorted(copied_paths),
            created_at=created_at,
        )
        manifest_path = out_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        validation = validate_manifest_file(manifest_path, package_dir=out_dir, verify_files=True)
        if validation.failed:
            raise PrepareSubmissionError(f"Prepared manifest failed file verification: {validation.to_dict()}")
        manifest_written = True

    return {
        "status": "passed",
        "submission_path": str(out_dir),
        "file_count": len(copied_paths) + (1 if manifest_written else 0),
        "manifest_written": manifest_written,
        "source_validation": "validated" if validate_sources else "skipped",
        "files": sorted([*copied_paths, *( ["manifest.json"] if manifest_written else [] )]),
    }


def build_manifest(
    *,
    submitter_id: str,
    run_id: str,
    package_dir: Path,
    relative_paths: list[str],
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build a v0 manifest for files already present in package_dir."""

    if created_at is None:
        created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    files = []
    for relative_path in sorted(relative_paths, key=lambda value: value.encode("utf-8")):
        if relative_path == "manifest.json":
            raise PrepareSubmissionError("manifest.json must not be included as a manifest input file")
        file_path = package_dir / relative_path
        _ensure_source_file(relative_path, file_path)
        files.append(
            {
                "path": relative_path,
                "sha256": sha256_file(file_path),
                "size_bytes": file_path.stat().st_size,
            }
        )

    manifest: dict[str, Any] = {
        "manifest_version": "0.1",
        "submitter_id": submitter_id,
        "run_id": run_id,
        "created_at": created_at,
        "hash_algorithm": "sha256",
        "files": files,
        "package_hash": "sha256:" + "0" * 64,
        "package_hash_input": PACKAGE_HASH_INPUT_DESCRIPTION,
        "notes": "Generated by llmclozestat prepare-submission. Manifest verifies package files, not model execution authenticity.",
    }
    manifest["package_hash"] = compute_package_hash(manifest)
    return manifest


def _validate_source_artifacts(
    *,
    environment_json: Path,
    run_jsonl: Path,
    summary_json: Path,
) -> None:
    environment_result = validate_environment_file(environment_json)
    if environment_result.failed:
        raise PrepareSubmissionError(f"environment_json failed validation: {environment_result.to_dict()}")

    result_validation = validate_results_file(run_jsonl)
    if result_validation.failed:
        raise PrepareSubmissionError(f"run_jsonl failed validation: {result_validation.to_dict()}")

    summary_validation = validate_summary_file(summary_json)
    if summary_validation.failed:
        raise PrepareSubmissionError(f"summary_json failed validation: {summary_validation.to_dict()}")


def _copy_artifact(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return destination


def _ensure_source_file(name: str, path: Path) -> None:
    if not path.exists():
        raise PrepareSubmissionError(f"{name} does not exist: {path}")
    if not path.is_file():
        raise PrepareSubmissionError(f"{name} is not a file: {path}")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise PrepareSubmissionError(f"{name} must be a non-empty string")
