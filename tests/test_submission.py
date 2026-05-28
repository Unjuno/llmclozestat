from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from llmclozestat.aggregation import aggregate_result_records
from llmclozestat.submission import PrepareSubmissionError, prepare_submission_package


class PrepareSubmissionTests(unittest.TestCase):
    def test_prepare_submission_copies_files_and_writes_verified_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = _write_valid_sources(root)

            out_dir = root / "submissions" / "local-user" / "fixture-run"
            result = prepare_submission_package(
                submitter_id="local-user",
                run_id="fixture-run",
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
            self.assertEqual(manifest["submitter_id"], "local-user")
            self.assertEqual(manifest["run_id"], "fixture-run")
            self.assertEqual(manifest["created_at"], "2026-05-26T00:00:00Z")
            self.assertEqual(
                {entry["path"] for entry in manifest["files"]},
                {"environment.json", "run.jsonl", "summary.json", "summary.md"},
            )

    def test_prepare_submission_rejects_invalid_source_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = _write_valid_sources(root)
            (source_dir / "run.jsonl").write_text('{}\n', encoding="utf-8")

            out_dir = root / "submissions" / "local-user" / "fixture-run"
            with self.assertRaises(PrepareSubmissionError) as context:
                prepare_submission_package(
                    submitter_id="local-user",
                    run_id="fixture-run",
                    environment_json=source_dir / "environment.json",
                    run_jsonl=source_dir / "run.jsonl",
                    summary_json=source_dir / "summary.json",
                    out_dir=out_dir,
                )
            self.assertIn("run_jsonl failed validation", str(context.exception))

    def test_prepare_submission_rejects_non_empty_output_without_overwrite(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = _write_valid_sources(root)

            out_dir = root / "submissions" / "local-user" / "fixture-run"
            out_dir.mkdir(parents=True)
            (out_dir / "existing.txt").write_text('existing\n', encoding="utf-8")

            with self.assertRaises(PrepareSubmissionError):
                prepare_submission_package(
                    submitter_id="local-user",
                    run_id="fixture-run",
                    environment_json=source_dir / "environment.json",
                    run_jsonl=source_dir / "run.jsonl",
                    summary_json=source_dir / "summary.json",
                    out_dir=out_dir,
                )

    def test_prepare_submission_can_skip_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = _write_valid_sources(root)

            out_dir = root / "out"
            result = prepare_submission_package(
                submitter_id="local-user",
                run_id="fixture-run",
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


def _write_valid_sources(root: Path) -> Path:
    source_dir = root / "source"
    source_dir.mkdir()
    result_record = _build_valid_result_record()
    environment = {
        "submitter_id": "local-user",
        "run_id": "fixture-run",
        "tool_version": "0.0.0-test",
        "dataset_id": "fixture_dataset",
        "model_id": "fixture-model",
        "backend": "test-backend",
        "provider": "test-provider",
        "prompt_template_id": "strict-v0-en",
        "prompt_language": "en",
        "support_mode": "zero",
        "f_shot": 0,
        "blank_rendering": "placeholder",
        "parser_config": {
            "normalization": "v0",
            "extraction_modes_enabled": ["segment"],
        },
        "generation_config": {
            "temperature": 0,
            "top_p": None,
            "max_tokens": 32,
        },
    }
    summary = aggregate_result_records([result_record])

    (source_dir / "environment.json").write_text(json.dumps(environment) + "\n", encoding="utf-8")
    (source_dir / "run.jsonl").write_text(json.dumps(result_record) + "\n", encoding="utf-8")
    (source_dir / "summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")
    (source_dir / "summary.md").write_text("# Summary\n", encoding="utf-8")
    return source_dir


def _build_valid_result_record() -> dict[str, object]:
    return {
        "submitter_id": "local-user",
        "run_id": "fixture-run",
        "dataset_id": "fixture_dataset",
        "model_id": "fixture-model",
        "backend": "test-backend",
        "provider": "test-provider",
        "probe_id": "probe-1",
        "variant_id": "variant-1",
        "language": "en",
        "primary_skill": "fixture_skill",
        "item_id": "item-1",
        "trial_id": 1,
        "prompt_template_id": "strict-v0-en",
        "prompt_language": "en",
        "support_mode": "zero",
        "f_shot": 0,
        "blank_rendering": "placeholder",
        "generation_config": {
            "temperature": 0,
            "top_p": None,
            "max_tokens": 32,
        },
        "generation_config_hash": "sha256:" + "1" * 64,
        "raw_output": "ok",
        "normalized_output": "ok",
        "extraction_mode": "segment",
        "blank_results": [
            {
                "blank_id": "b1",
                "position": 1,
                "extracted_fill": "ok",
                "fill_class": "accepted",
                "blank_parse_pass": True,
                "content_pass": True,
                "parse_fail": False,
            }
        ],
        "instruction_following_pass": True,
        "item_format_pass": True,
        "item_strict_pass": True,
        "item_partial_score": 1.0,
        "latency_ms": 10.0,
    }


if __name__ == "__main__":
    unittest.main()
