from __future__ import annotations

import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from llmclozestat.manifest_validation import validate_submission_manifest
from llmclozestat.submission import PrepareSubmissionError, prepare_submission_package


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SMOKE = ROOT / "examples" / "smoke_v0"


class PrepareSubmissionTests(unittest.TestCase):
    def test_prepare_submission_copies_files_and_writes_verified_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = _copy_example_sources(root)

            out_dir = root / "submissions" / "example-local" / "smoke-v0-example-20260526"
            result = prepare_submission_package(
                submitter_id="example-local",
                run_id="smoke-v0-example-20260526",
                environment_json=source_dir / "environment.json",
                run_jsonl=source_dir / "run.jsonl",
                summary_json=source_dir / "summary.json",
                summary_md=source_dir / "summary.md",
                out_dir=out_dir,
                created_at="2026-05-26T00:00:00Z",
            )

            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["source_validation"], "validated")
            self.assertTrue((out_dir / "environment.json").exists())
            self.assertTrue((out_dir / "run.jsonl").exists())
            self.assertTrue((out_dir / "summary.json").exists())
            self.assertTrue((out_dir / "summary.md").exists())
            self.assertTrue((out_dir / "manifest.json").exists())

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["submitter_id"], "example-local")
            self.assertEqual(manifest["run_id"], "smoke-v0-example-20260526")
            self.assertEqual(manifest["created_at"], "2026-05-26T00:00:00Z")
            self.assertEqual(
                {entry["path"] for entry in manifest["files"]},
                {"environment.json", "run.jsonl", "summary.json", "summary.md"},
            )

            validation = validate_submission_manifest(out_dir)
            self.assertFalse(validation.failed, validation.to_dict())

    def test_prepare_submission_rejects_invalid_source_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = _copy_example_sources(root)
            (source_dir / "run.jsonl").write_text('{}\n', encoding="utf-8")

            out_dir = root / "submissions" / "example-local" / "smoke-v0-example-20260526"
            with self.assertRaises(PrepareSubmissionError) as context:
                prepare_submission_package(
                    submitter_id="example-local",
                    run_id="smoke-v0-example-20260526",
                    environment_json=source_dir / "environment.json",
                    run_jsonl=source_dir / "run.jsonl",
                    summary_json=source_dir / "summary.json",
                    out_dir=out_dir,
                )
            self.assertIn("run_jsonl failed validation", str(context.exception))

    def test_prepare_submission_rejects_non_empty_output_without_overwrite(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = _copy_example_sources(root)

            out_dir = root / "submissions" / "example-local" / "smoke-v0-example-20260526"
            out_dir.mkdir(parents=True)
            (out_dir / "existing.txt").write_text('do not overwrite\n', encoding="utf-8")

            with self.assertRaises(PrepareSubmissionError):
                prepare_submission_package(
                    submitter_id="example-local",
                    run_id="smoke-v0-example-20260526",
                    environment_json=source_dir / "environment.json",
                    run_jsonl=source_dir / "run.jsonl",
                    summary_json=source_dir / "summary.json",
                    out_dir=out_dir,
                )

    def test_prepare_submission_can_skip_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = _copy_example_sources(root)

            out_dir = root / "out"
            result = prepare_submission_package(
                submitter_id="example-local",
                run_id="smoke-v0-example-20260526",
                environment_json=source_dir / "environment.json",
                run_jsonl=source_dir / "run.jsonl",
                summary_json=source_dir / "summary.json",
                out_dir=out_dir,
                write_manifest=False,
            )

            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["source_validation"], "validated")
            self.assertFalse((out_dir / "manifest.json").exists())
            self.assertEqual(set(result["files"]), {"environment.json", "run.jsonl", "summary.json"})


def _copy_example_sources(root: Path) -> Path:
    source_dir = root / "source"
    source_dir.mkdir()
    for filename in ["environment.json", "run.jsonl", "summary.json", "summary.md"]:
        shutil.copyfile(EXAMPLE_SMOKE / filename, source_dir / filename)
    return source_dir


if __name__ == "__main__":
    unittest.main()
