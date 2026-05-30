from __future__ import annotations

import json
from pathlib import Path
import unittest

from llmclozestat.item_validation import validate_items_file


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DATASET = ROOT / "datasets" / "template_probes_v0" / "items.jsonl"


class TemplateProbeDatasetTests(unittest.TestCase):
    def test_template_probe_dataset_passes_item_validation(self) -> None:
        result = validate_items_file(TEMPLATE_DATASET)
        self.assertFalse(result.failed, result.to_dict())

    def test_template_probe_dataset_uses_multiple_blanks_without_role_metadata(self) -> None:
        items = _load_items()
        self.assertGreaterEqual(len(items), 2)
        self.assertEqual({item["dataset_id"] for item in items}, {"template_probes_v0"})
        for item in items:
            with self.subTest(item_id=item["item_id"]):
                blanks = item["blanks"]
                self.assertGreaterEqual(len(blanks), 2)
                self.assertEqual(len(item["segments"]), len(blanks) + 1)
                self.assertNotIn("measurement_plan", item)
                self.assertTrue(item["validation_target"]["main_question"])
                self.assertTrue(item["claim_scope"]["generalization_limit"])

    def test_formula_template_keeps_formula_as_observed_fill_not_role_label(self) -> None:
        items = {item["item_id"]: item for item in _load_items()}
        formula_item = items["formula_area_multiblank_0001"]
        blank_2 = next(blank for blank in formula_item["blanks"] if blank["blank_id"] == "blank_2")
        self.assertEqual(blank_2["depends_on"], ["blank_1"])
        self.assertGreaterEqual(len(blank_2["accepted_fills"]), 2)
        self.assertIn("w*h", blank_2["accepted_fills"])
        self.assertIn("w+h", blank_2["known_wrong_fills"])
        self.assertNotIn("role", blank_2)


def _load_items() -> list[dict]:
    with TEMPLATE_DATASET.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


if __name__ == "__main__":
    unittest.main()
