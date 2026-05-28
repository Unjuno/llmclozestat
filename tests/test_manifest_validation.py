from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from llmclozestat.manifest_validation import (
    compute_package_hash,
    sha256_file,
    validate_manifest_file,
    validate_submission_manifest,
)


class ManifestValidationTests(unittest.TestCase):
    def test_valid_manifest_with_file_verification_passes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir)
            environment_path = package_dir / "environment.json"
            run_path = package_dir / "run.jsonl"
            summary_path = package_dir / "summary.json"

            environment_path.write_text('{"model_id":"fixture-model"}\n', encoding="utf-8")
            run_path.write_text('{"trial_id":"trial-1"}\n', encoding="utf-8")
            summary_path.write_text('{"summary_version":"summary_v0"}\n', encoding="utf-8")

            manifest = _build_single_file_manifest(
                package_dir=package_dir,
                submitter_id="local-user",
                run_id="fixture-run",
                paths=["environment.json", "run.jsonl", "summary.json"],
            )
            manifest_path = package_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = validate_manifest_file(manifest_path, verify_files=True)
            self.assertFalse(result.failed, result.to_dict())

    def test_submission_path_identity_passes_for_matching_parent_and_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir) / "submissions" / "local-user" / "fixture-run"
            package_dir.mkdir(parents=True)
            (package_dir / "run.jsonl").write_text('{"trial_id":"trial-1"}\n', encoding="utf-8")
            manifest = _build_single_file_manifest(
                package_dir=package_dir,
                submitter_id="local-user",
                run_id="fixture-run",
                paths=["run.jsonl"],
            )
            (package_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_submission_manifest(package_dir)
            self.assertFalse(result.failed, result.to_dict())

    def test_submission_path_identity_mismatch_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir) / "submissions" / "other-user" / "other-run"
            package_dir.mkdir(parents=True)
            (package_dir / "run.jsonl").write_text('{"trial_id":"trial-1"}\n', encoding="utf-8")
            manifest = _build_single_file_manifest(
                package_dir=package_dir,
                submitter_id="local-user",
                run_id="fixture-run",
                paths=["run.jsonl"],
            )
            (package_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_submission_manifest(package_dir)
            self.assertTrue(result.failed, result.to_dict())
            error_codes = {error.code for error in result.errors}
            self.assertIn("submitter_id_path_mismatch", error_codes)
            self.assertIn("run_id_path_mismatch", error_codes)

    def test_wrong_file_hash_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir)
            data_path = package_dir / "run.jsonl"
            data_path.write_text('{"trial_id":"trial-1"}\n', encoding="utf-8")

            manifest = {
                "manifest_version": "0.1",
                "submitter_id": "local-user",
                "run_id": "fixture-run",
                "created_at": "2026-05-26T00:00:00Z",
                "hash_algorithm": "sha256",
                "files": [{"path": "run.jsonl", "sha256": "0" * 64}],
                "package_hash": "sha256:" + "0" * 64,
                "package_hash_input": "canonical_json(v0)",
            }
            manifest["package_hash"] = compute_package_hash(manifest)
            manifest_path = package_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_manifest_file(manifest_path, verify_files=True)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("wrong_file_hash", {error.code for error in result.errors})

    def test_wrong_package_hash_fails_when_file_hashes_match(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir)
            data_path = package_dir / "run.jsonl"
            data_path.write_text('{"trial_id":"trial-1"}\n', encoding="utf-8")

            manifest = {
                "manifest_version": "0.1",
                "submitter_id": "local-user",
                "run_id": "fixture-run",
                "created_at": "2026-05-26T00:00:00Z",
                "hash_algorithm": "sha256",
                "files": [{"path": "run.jsonl", "sha256": sha256_file(data_path)}],
                "package_hash": "sha256:" + "0" * 64,
                "package_hash_input": "canonical_json(v0)",
            }
            manifest_path = package_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_manifest_file(manifest_path, verify_files=True)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("wrong_package_hash", {error.code for error in result.errors})

    def test_path_traversal_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir)
            manifest = {
                "manifest_version": "0.1",
                "submitter_id": "local-user",
                "run_id": "fixture-run",
                "created_at": "2026-05-26T00:00:00Z",
                "hash_algorithm": "sha256",
                "files": [{"path": "../run.jsonl", "sha256": "0" * 64}],
                "package_hash": "sha256:" + "0" * 64,
                "package_hash_input": "canonical_json(v0)",
            }
            manifest_path = package_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_manifest_file(manifest_path, verify_files=False)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("path_traversal", {error.code for error in result.errors})

    def test_missing_submission_manifest_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = validate_submission_manifest(Path(temp_dir))
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("missing_manifest", {error.code for error in result.errors})


def _build_single_file_manifest(
    *,
    package_dir: Path,
    submitter_id: str,
    run_id: str,
    paths: list[str],
) -> dict[str, object]:
    manifest: dict[str, object] = {
        "manifest_version": "0.1",
        "submitter_id": submitter_id,
        "run_id": run_id,
        "created_at": "2026-05-26T00:00:00Z",
        "hash_algorithm": "sha256",
        "files": [
            {"path": relative_path, "sha256": sha256_file(package_dir / relative_path)}
            for relative_path in paths
        ],
        "package_hash": "sha256:" + "0" * 64,
        "package_hash_input": (
            "canonical_json(v0: keys sorted; files sorted by path; file fields path,sha256; "
            "exclude manifest/signature/ledger; utf-8; compact)"
        ),
    }
    manifest["package_hash"] = compute_package_hash(manifest)  # type: ignore[arg-type]
    return manifest


if __name__ == "__main__":
    unittest.main()
