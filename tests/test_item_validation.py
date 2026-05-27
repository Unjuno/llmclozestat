from __future__ import annotations

import json
from pathlib import Path
import unittest

from llmclozestat.item_validation import validate_items_file


ROOT = Path(__file__).resolve().parents[1]
ITEM_FIXTURES = ROOT / "tests" / "fixtures" / "items"


class ItemValidationTests(unittest.TestCase):
    def test_smoke_dataset_passes(self) -> None:
        result = validate_items_file(ROOT / "datasets" / "smoke_v0" / "items.jsonl")
        self.assertFalse(result.failed, result.to_dict())

    def test_valid_fixtures_pass(self) -> None:
        for fixture_path in sorted((ITEM_FIXTURES / "valid").glob("*.jsonl")):
            with self.subTest(fixture=fixture_path.name):
                result = validate_items_file(fixture_path)
                self.assertFalse(result.failed, result.to_dict())

    def test_invalid_fixtures_fail_with_expected_codes(self) -> None:
        invalid_paths = sorted((ITEM_FIXTURES / "invalid").glob("*.jsonl"))
        self.assertGreater(len(invalid_paths), 0, "No invalid item fixtures found")

        for fixture_path in invalid_paths:
            with self.subTest(fixture=fixture_path.name):
                expected = self.load_expected_metadata(fixture_path)
                result = validate_items_file(fixture_path)
                self.assertTrue(result.failed, result.to_dict())
                actual_codes = {error.code for error in result.errors}
                expected_codes = {entry["code"] for entry in expected["expected_errors"]}
                self.assertTrue(
                    expected_codes.issubset(actual_codes),
                    {
                        "fixture": fixture_path.name,
                        "expected_codes": sorted(expected_codes),
                        "actual_codes": sorted(actual_codes),
                        "result": result.to_dict(),
                    },
                )

    def test_invalid_fixtures_have_expected_metadata(self) -> None:
        for fixture_path in sorted((ITEM_FIXTURES / "invalid").glob("*.jsonl")):
            with self.subTest(fixture=fixture_path.name):
                expected_path = fixture_path.with_suffix(".expected.json")
                self.assertTrue(expected_path.exists(), f"Missing expected metadata: {expected_path}")
                expected = self.load_expected_metadata(fixture_path)
                self.assertEqual(expected.get("expected_status"), "failed")
                self.assertIsInstance(expected.get("expected_errors"), list)
                self.assertGreater(len(expected["expected_errors"]), 0)
                for entry in expected["expected_errors"]:
                    self.assertIn("code", entry)
                    self.assertIsInstance(entry["code"], str)
                    self.assertTrue(entry["code"])

    def load_expected_metadata(self, fixture_path: Path) -> dict:
        expected_path = fixture_path.with_suffix(".expected.json")
        with expected_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)


if __name__ == "__main__":
    unittest.main()
