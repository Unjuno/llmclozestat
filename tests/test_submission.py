from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from llmclozestat.manifest_validation import validate_submission_manifest
from llmclozestat.submission import PrepareSubmissionError, prepare_submission_package


class PrepareSubmissionTests(unittest.TestCase):
    def test_prepare_submission_copies_files_and_writes_verified_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "source"
            source_dir.mkdir()
            environment_json = source_dir / "environment.json"
            run_jsonl = source_dir / "run.jsonl"
            summary_json = source_dir / "summary.json"
            summary_md = source_dir / "summary.md"

            environment_json.write_text('{"model_id":"fixture-model"}\n', encoding="utf-8")
            run_jsonl.write_text('{"trial_id":"trial-1"}\n', encoding="utf-8")
            summary_json.write_text('{"summary_version":"summary_v0"}\n', encoding="utf-8")
            summary_md.write_text('# Summary\n', encoding="utf-8")

            out_dir = root / "submissions" / "local-user" / "fixture-run"
            result = prepare_submission_package(
                submitter_id="local-user",
                run_id="fixture-run",
                environment_json=environment_json,
                run_jsonl=run_jsonl,
                summary_json=summary_json,
                summary_md=summary_md,
                out_dir=out_dir,
                created_at="2026-05-26T00:00:00Z",
            )

            self.assertEqual(result["status"], "passed")
            self.assertTrue((out_dir / "environment.json").exists())
            self.assertTrue((out_dir / "run.jsonl").exists())
            self.assertTrue((out_dir / "summary.json").exists())
            self.assertTrue((out_dir / "summary.md").exists())
            self.assertTrue((out_dir / "manifest.json").exists())

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["submitter_id"], "local-user")
            self.assertEqual(manifest["run_id"], "fixture-run")
            self.assertEqual(manifest["created_at"], "2026-05-26T00:00:00Z")
            self.assertEqual(
                {entry["path"] for entry in manifest["files"]},
                {"environment.json", "run.jsonl", "summary.json", "summary.md"},
            )

            validation = validate_submission_manifest(out_dir)
            self.assertFalse(validation.failed, validation.to_dict())

    def test_prepare_submission_rejects_non_empty_output_without_overwrite(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "source"
            source_dir.mkdir()
            environment_json = source_dir / "environment.json"
            run_jsonl = source_dir / "run.jsonl"
            summary_json = source_dir / "summary.json"
            environment_json.write_text('{}\n', encoding="utf-8")
            run_jsonl.write_text('{}\n', encoding="utf-8")
            summary_json.write_text('{}\n', encoding="utf-8")

            out_dir = root / "out"
            out_dir.mkdir()
            (out_dir / "existing.txt").write_text('do not overwrite\n', encoding="utf-8")

            with self.assertRaises(PrepareSubmissionError):
                prepare_submission_package(
                    submitter_id="local-user",
                    run_id="fixture-run",
                    environment_json=environment_json,
                    run_jsonl=run_jsonl,
                    summary_json=summary_json,
                    out_dir=out_dir,
                )

    def test_prepare_submission_can_skip_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "source"
            source_dir.mkdir()
            environment_json = source_dir / "environment.json"
            run_jsonl = source_dir / "run.jsonl"
            summary_json = source_dir / "summary.json"
            environment_json.write_text('{}\n', encoding="utf-8")
            run_jsonl.write_text('{}\n', encoding="utf-8")
            summary_json.write_text('{}\n', encoding="utf-8")

            out_dir = root / "out"
            result = prepare_submission_package(
                submitter_id="local-user",
                run_id="fixture-run",
                environment_json=environment_json,
                run_jsonl=run_jsonl,
                summary_json=summary_json,
                out_dir=out_dir,
                write_manifest=False,
            )

            self.assertEqual(result["status"], "passed")
            self.assertFalse((out_dir / "manifest.json").exists())
            self.assertEqual(set(result["files"]), {"environment.json", "run.jsonl", "summary.json"})


if __name__ == "__main__":
    unittest.main()
