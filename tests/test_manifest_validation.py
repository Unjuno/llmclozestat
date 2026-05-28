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

            manifest = {
                "manifest_version": "0.1",
                "submitter_id": "local-user",
                "run_id": "fixture-run",
                "created_at": "2026-05-26T00:00:00Z",
                "hash_algorithm": "sha256",
                "files": [
                    {"path": "summary.json", "sha256": sha256_file(summary_path)},
                    {"path": "environment.json", "sha256": sha256_file(environment_path)},
                    {"path": "run.jsonl", "sha256": sha256_file(run_path)},
                ],
                "package_hash": "sha256:" + "0" * 64,
                "package_hash_input": (
                    "canonical_json(v0: keys sorted; files sorted by path; file fields path,sha256; "
                    "exclude manifest/signature/ledger; utf-8; compact)"
                ),
            }
            manifest["package_hash"] = compute_package_hash(manifest)
            manifest_path = package_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = validate_manifest_file(manifest_path, verify_files=True)
            self.assertFalse(result.failed, result.to_dict())

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

        result = validate_manifest_file(_write_manifest_to_temp(manifest), verify_files=False)
        self.assertTrue(result.failed, result.to_dict())
        self.assertIn("path_traversal", {error.code for error in result.errors})

    def test_missing_submission_manifest_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = validate_submission_manifest(Path(temp_dir))
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("missing_manifest", {error.code for error in result.errors})


def _write_manifest_to_temp(manifest: dict[str, object]) -> Path:
    temp_dir = TemporaryDirectory()
    # Keep the temporary directory alive by attaching it to the returned Path object owner module.
    _TEMP_DIRS.append(temp_dir)
    manifest_path = Path(temp_dir.name) / "manifest.json"
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    return manifest_path


_TEMP_DIRS: list[TemporaryDirectory[str]] = []


if __name__ == "__main__":
    unittest.main()
