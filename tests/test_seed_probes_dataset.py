from __future__ import annotations

import json
from pathlib import Path
import unittest

from llmclozestat.item_validation import validate_items_file


ROOT = Path(__file__).resolve().parents[1]
SEED_DATASET = ROOT / "datasets" / "seed_probes_v0" / "items.jsonl"


class SeedProbeDatasetTests(unittest.TestCase):
    def test_seed_probe_dataset_passes_item_validation(self) -> None:
        result = validate_items_file(SEED_DATASET)
        self.assertFalse(result.failed, result.to_dict())

    def test_seed_probe_dataset_has_expected_minimum_shape(self) -> None:
        items = _load_items()
        self.assertGreaterEqual(len(items), 4)
        self.assertEqual({item["dataset_id"] for item in items}, {"seed_probes_v0"})
        self.assertEqual(len({item["item_id"] for item in items}), len(items))
        self.assertEqual(len({item["variant_id"] for item in items}), len(items))

        primary_skills = {item["primary_skill"] for item in items}
        self.assertIn("causal_direction", primary_skills)
        self.assertIn("spatial_perspective", primary_skills)
        self.assertIn("temporal_order", primary_skills)
        self.assertIn("quantity_comparison", primary_skills)

    def test_each_seed_item_has_interpretable_claim_boundary(self) -> None:
        for item in _load_items():
            with self.subTest(item_id=item["item_id"]):
                validation_target = item["validation_target"]
                self.assertTrue(validation_target["main_question"])
                self.assertTrue(validation_target["hypothesis"])
                self.assertTrue(validation_target["success_condition"])
                self.assertTrue(validation_target["why_this_item_exists"])

                claim_scope = item["claim_scope"]
                self.assertTrue(claim_scope["supports_claim"])
                self.assertGreaterEqual(len(claim_scope["does_not_support"]), 1)
                self.assertGreaterEqual(len(claim_scope["required_conditions"]), 1)
                self.assertTrue(claim_scope["generalization_limit"])

                blanks = item["blanks"]
                self.assertEqual(len(item["segments"]), len(blanks) + 1)
                for blank in blanks:
                    self.assertGreaterEqual(len(blank["accepted_fills"]), 1)
                    self.assertGreaterEqual(len(blank["known_wrong_fills"]), 1)
                    self.assertGreaterEqual(len(blank["expected_error_patterns"]), 1)


def _load_items() -> list[dict]:
    with SEED_DATASET.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


if __name__ == "__main__":
    unittest.main()
