from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from llmclozestat.reporting import ReportGenerationError, generate_reports


class ReportGenerationTests(unittest.TestCase):
    def test_generate_reports_writes_run_index_and_blank_fills(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            submissions = root / "submissions"
            package = submissions / "user-a" / "run-a"
            package.mkdir(parents=True)
            summary = _summary()
            (package / "summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")

            out_dir = root / "reports"
            result = generate_reports(submissions, out_dir)

            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["summary_count"], 1)
            self.assertTrue((out_dir / "run_index.csv").exists())
            self.assertTrue((out_dir / "blank_fills.csv").exists())

            with (out_dir / "run_index.csv").open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["submitter_id"], "user-a")
            self.assertEqual(rows[0]["model_id"], "model-a")

            with (out_dir / "blank_fills.csv").open("r", encoding="utf-8", newline="") as handle:
                fill_rows = list(csv.DictReader(handle))
            self.assertEqual(len(fill_rows), 1)
            self.assertEqual(fill_rows[0]["fill_key"], "blue")
            self.assertEqual(fill_rows[0]["count"], "1")

    def test_generate_reports_rejects_missing_submissions_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaises(ReportGenerationError):
                generate_reports(root / "missing", root / "reports")


def _summary() -> dict[str, object]:
    return {
        "summary_version": "summary_v0",
        "submitter_id": "user-a",
        "run_id": "run-a",
        "dataset_id": "dataset-a",
        "model_id": "model-a",
        "n_trials": 1,
        "content_pass_rate": 1.0,
        "instruction_following_pass_rate": 1.0,
        "item_format_pass_rate": 1.0,
        "strict_pass_rate": 1.0,
        "parse_fail_rate": 0.0,
        "avg_latency_ms": 10.0,
        "groups": [
            {
                "probe_id": "probe-a",
                "variant_id": "variant-a",
                "language": "en",
                "item_id": "item-a",
                "blank_id": "b1",
                "position": 1,
                "prompt_template_id": "strict-v0-en",
                "prompt_language": "en",
                "support_mode": "zero",
                "f_shot": 0,
                "blank_rendering": "placeholder",
                "extraction_mode": "segment",
                "generation_config_hash": "sha256:" + "1" * 64,
                "n_trials": 1,
                "fill_distribution": [
                    {
                        "extracted_fill": "blue",
                        "fill_key": "blue",
                        "count": 1,
                        "rate": 1.0,
                        "fill_class": "accepted",
                    }
                ],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
