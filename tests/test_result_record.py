from __future__ import annotations

import unittest

from llmclozestat.result_record import build_result_record


class ResultRecordTests(unittest.TestCase):
    def test_build_result_record_contains_required_fields(self) -> None:
        record = build_result_record(
            item=self.sample_item(),
            raw_output="AxB",
            metadata=self.sample_metadata(),
            latency_ms=12.5,
        )

        for field in (
            "submitter_id",
            "run_id",
            "dataset_id",
            "model_id",
            "backend",
            "provider",
            "probe_id",
            "variant_id",
            "language",
            "primary_skill",
            "item_id",
            "trial_id",
            "prompt_template_id",
            "prompt_language",
            "support_mode",
            "f_shot",
            "blank_rendering",
            "generation_config",
            "raw_output",
            "normalized_output",
            "extraction_mode",
            "blank_results",
            "instruction_following_pass",
            "item_format_pass",
            "item_strict_pass",
            "item_partial_score",
            "latency_ms",
        ):
            self.assertIn(field, record)

    def test_build_result_record_preserves_parser_output(self) -> None:
        record = build_result_record(
            item=self.sample_item(),
            raw_output="AxB",
            metadata=self.sample_metadata(),
        )

        self.assertEqual(record["raw_output"], "AxB")
        self.assertEqual(record["normalized_output"], "AxB")
        self.assertEqual(record["extraction_mode"], "exact_full_text")
        self.assertTrue(record["instruction_following_pass"])
        self.assertTrue(record["item_format_pass"])
        self.assertTrue(record["item_strict_pass"])
        self.assertEqual(record["item_partial_score"], 1.0)
        self.assertEqual(record["blank_results"][0]["extracted_fill"], "x")
        self.assertEqual(record["blank_results"][0]["fill_class"], "accepted")

    def test_build_result_record_rejects_missing_metadata(self) -> None:
        metadata = self.sample_metadata()
        del metadata["submitter_id"]

        with self.assertRaises(ValueError):
            build_result_record(
                item=self.sample_item(),
                raw_output="AxB",
                metadata=metadata,
            )

    def sample_item(self) -> dict:
        return {
            "dataset_id": "fixture_dataset",
            "probe_id": "fixture_probe",
            "variant_id": "fixture_probe.en",
            "language": "en",
            "primary_skill": "parser_fixture",
            "item_id": "fixture_item_1",
            "segments": ["A", "B"],
            "blanks": [
                {
                    "blank_id": "blank_1",
                    "position": 1,
                    "accepted_fills": ["x"],
                    "near_miss_fills": ["X"],
                    "known_wrong_fills": ["y"],
                }
            ],
            "expected_full_texts": ["AxB"],
        }

    def sample_metadata(self) -> dict:
        return {
            "submitter_id": "local-user",
            "run_id": "fixture-run",
            "model_id": "fixture-model",
            "backend": "openai-compatible",
            "provider": "fixture",
            "trial_id": 1,
            "prompt_template_id": "fill_full_sentence_v1.en",
            "prompt_language": "en",
            "support_mode": "zero",
            "f_shot": 0,
            "blank_rendering": "(___)",
            "generation_config": {
                "temperature": 0,
                "top_p": None,
                "seed": None,
                "max_tokens": 64,
                "context_window": None,
                "repeat_penalty": None,
                "stop": [],
            },
            "generation_config_hash": None,
        }


if __name__ == "__main__":
    unittest.main()
