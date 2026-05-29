from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from llmclozestat.aggregation import aggregate_result_records
from llmclozestat.manifest_validation import (
    compute_package_hash,
    sha256_file,
    validate_manifest_file,
    validate_submission_manifest,
)


DATASET_SHA256 = "sha256:" + "a" * 64


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

            manifest = _build_manifest(
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
            _write_identity_artifacts(package_dir)
            manifest = _build_manifest(
                package_dir=package_dir,
                submitter_id="local-user",
                run_id="fixture-run",
                paths=["environment.json", "run.jsonl", "summary.json"],
            )
            (package_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_submission_manifest(package_dir)
            self.assertFalse(result.failed, result.to_dict())
            self.assertIn("summary_regeneration_checked", {info["code"] for info in result.info})

    def test_submission_path_identity_mismatch_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir) / "submissions" / "other-user" / "other-run"
            package_dir.mkdir(parents=True)
            _write_identity_artifacts(package_dir)
            manifest = _build_manifest(
                package_dir=package_dir,
                submitter_id="local-user",
                run_id="fixture-run",
                paths=["environment.json", "run.jsonl", "summary.json"],
            )
            (package_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_submission_manifest(package_dir)
            self.assertTrue(result.failed, result.to_dict())
            error_codes = {error.code for error in result.errors}
            self.assertIn("submitter_id_path_mismatch", error_codes)
            self.assertIn("run_id_path_mismatch", error_codes)

    def test_submission_artifact_identity_mismatch_fails_with_matching_hashes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir) / "submissions" / "local-user" / "fixture-run"
            package_dir.mkdir(parents=True)
            _write_identity_artifacts(package_dir)
            summary = json.loads((package_dir / "summary.json").read_text(encoding="utf-8"))
            summary["dataset_id"] = "other_dataset"
            (package_dir / "summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")

            manifest = _build_manifest(
                package_dir=package_dir,
                submitter_id="local-user",
                run_id="fixture-run",
                paths=["environment.json", "run.jsonl", "summary.json"],
            )
            (package_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_submission_manifest(package_dir)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("submission_identity_mismatch", {error.code for error in result.errors})

    def test_submission_dataset_hash_identity_mismatch_fails_with_matching_hashes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir) / "submissions" / "local-user" / "fixture-run"
            package_dir.mkdir(parents=True)
            _write_identity_artifacts(package_dir)
            environment = json.loads((package_dir / "environment.json").read_text(encoding="utf-8"))
            environment["dataset_sha256"] = "sha256:" + "b" * 64
            (package_dir / "environment.json").write_text(json.dumps(environment) + "\n", encoding="utf-8")

            manifest = _build_manifest(
                package_dir=package_dir,
                submitter_id="local-user",
                run_id="fixture-run",
                paths=["environment.json", "run.jsonl", "summary.json"],
            )
            (package_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_submission_manifest(package_dir)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("submission_identity_mismatch", {error.code for error in result.errors})

    def test_submission_summary_regeneration_mismatch_fails_with_matching_hashes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir) / "submissions" / "local-user" / "fixture-run"
            package_dir.mkdir(parents=True)
            _write_identity_artifacts(package_dir)
            summary = json.loads((package_dir / "summary.json").read_text(encoding="utf-8"))
            summary["n_trials"] = 999
            (package_dir / "summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")

            manifest = _build_manifest(
                package_dir=package_dir,
                submitter_id="local-user",
                run_id="fixture-run",
                paths=["environment.json", "run.jsonl", "summary.json"],
            )
            (package_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_submission_manifest(package_dir)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("summary_regeneration_mismatch", {error.code for error in result.errors})

    def test_submission_summary_dataset_hash_mismatch_fails_with_matching_hashes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir) / "submissions" / "local-user" / "fixture-run"
            package_dir.mkdir(parents=True)
            _write_identity_artifacts(package_dir)
            summary = json.loads((package_dir / "summary.json").read_text(encoding="utf-8"))
            summary["dataset_sha256"] = "sha256:" + "f" * 64
            (package_dir / "summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")

            manifest = _build_manifest(
                package_dir=package_dir,
                submitter_id="local-user",
                run_id="fixture-run",
                paths=["environment.json", "run.jsonl", "summary.json"],
            )
            (package_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_submission_manifest(package_dir)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("submission_identity_mismatch", {error.code for error in result.errors})

    def test_missing_required_submission_artifact_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir) / "submissions" / "local-user" / "fixture-run"
            package_dir.mkdir(parents=True)
            _write_identity_artifacts(package_dir)
            (package_dir / "summary.json").unlink()
            manifest = _build_manifest(
                package_dir=package_dir,
                submitter_id="local-user",
                run_id="fixture-run",
                paths=["environment.json", "run.jsonl"],
            )
            (package_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            result = validate_submission_manifest(package_dir)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("missing_submission_artifact", {error.code for error in result.errors})

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


def _write_identity_artifacts(package_dir: Path) -> None:
    environment = {
        "submitter_id": "local-user",
        "run_id": "fixture-run",
        "dataset_id": "fixture_dataset",
        "dataset_sha256": DATASET_SHA256,
        "model_id": "fixture-model",
    }
    run_record = _build_result_record()
    summary = aggregate_result_records([run_record])
    (package_dir / "environment.json").write_text(json.dumps(environment) + "\n", encoding="utf-8")
    (package_dir / "run.jsonl").write_text(json.dumps(run_record) + "\n", encoding="utf-8")
    (package_dir / "summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")


def _build_result_record() -> dict[str, object]:
    return {
        "submitter_id": "local-user",
        "run_id": "fixture-run",
        "dataset_id": "fixture_dataset",
        "dataset_sha256": DATASET_SHA256,
        "model_id": "fixture-model",
        "probe_id": "probe-1",
        "variant_id": "variant-1",
        "language": "ja",
        "item_id": "item-1",
        "prompt_template_id": "strict-v0-ja",
        "prompt_language": "ja",
        "support_mode": "zero",
        "f_shot": 0,
        "blank_rendering": "placeholder",
        "extraction_mode": "segment",
        "generation_config_hash": "sha256:" + "1" * 64,
        "instruction_following_pass": True,
        "item_format_pass": True,
        "item_strict_pass": True,
        "latency_ms": 10.0,
        "blank_results": [
            {
                "blank_id": "b1",
                "position": 1,
                "extracted_fill": "青",
                "fill_class": "accepted",
                "content_pass": True,
                "parse_fail": False,
            }
        ],
    }


def _build_manifest(
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
