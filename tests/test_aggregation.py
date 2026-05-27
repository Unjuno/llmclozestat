from __future__ import annotations

from pathlib import Path
import unittest

from llmclozestat.aggregation import PARSE_FAIL_FILL_KEY, aggregate_results_file


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_FIXTURES = ROOT / "tests" / "fixtures" / "summaries"


class AggregationTests(unittest.TestCase):
    def test_aggregate_repeated_fills_without_deduplication(self) -> None:
        summary = aggregate_results_file(SUMMARY_FIXTURES / "source" / "repeated_fills_run.jsonl")

        self.assertEqual(summary["summary_version"], "summary_v0")
        self.assertEqual(summary["submitter_id"], "local-user")
        self.assertEqual(summary["run_id"], "summary-fixture-run")
        self.assertEqual(summary["dataset_id"], "fixture_dataset")
        self.assertEqual(summary["model_id"], "fixture-model")
        self.assertEqual(summary["n_trials"], 4)

        self.assertEqual(summary["content_pass_rate"], 0.5)
        self.assertEqual(summary["instruction_following_pass_rate"], 0.75)
        self.assertEqual(summary["item_format_pass_rate"], 0.75)
        self.assertEqual(summary["strict_pass_rate"], 0.5)
        self.assertEqual(summary["parse_fail_rate"], 0.25)
        self.assertEqual(summary["avg_latency_ms"], 25.0)

        self.assertEqual(len(summary["groups"]), 1)
        group = summary["groups"][0]
        self.assertEqual(group["blank_id"], "blank_1")
        self.assertEqual(group["n_trials"], 4)
        self.assertEqual(group["unique_fill_count"], 3)
        self.assertEqual(group["top_fill"], "alpha")
        self.assertEqual(group["top_wrong_fill"], "gamma")
        self.assertAlmostEqual(group["mean_entropy"], 1.5)

        distribution_by_key = {entry["fill_key"]: entry for entry in group["fill_distribution"]}
        self.assertEqual(distribution_by_key["alpha"]["count"], 2)
        self.assertEqual(distribution_by_key["alpha"]["rate"], 0.5)
        self.assertEqual(distribution_by_key["alpha"]["fill_class"], "accepted")

        self.assertEqual(distribution_by_key["gamma"]["count"], 1)
        self.assertEqual(distribution_by_key["gamma"]["rate"], 0.25)
        self.assertEqual(distribution_by_key["gamma"]["fill_class"], "known_wrong")

        self.assertEqual(distribution_by_key[PARSE_FAIL_FILL_KEY]["count"], 1)
        self.assertEqual(distribution_by_key[PARSE_FAIL_FILL_KEY]["rate"], 0.25)
        self.assertEqual(distribution_by_key[PARSE_FAIL_FILL_KEY]["extracted_fill"], None)
        self.assertEqual(distribution_by_key[PARSE_FAIL_FILL_KEY]["fill_class"], "parse_fail")


if __name__ == "__main__":
    unittest.main()
