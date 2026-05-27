from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PARSER_FIXTURES = ROOT / "tests" / "fixtures" / "parser"


class ParserFixtureStructureTests(unittest.TestCase):
    def test_parser_fixtures_exist(self) -> None:
        fixture_paths = sorted(PARSER_FIXTURES.glob("*.json"))
        self.assertGreater(len(fixture_paths), 0, "No parser fixtures found")

    def test_parser_fixtures_have_required_shape(self) -> None:
        for fixture_path in sorted(PARSER_FIXTURES.glob("*.json")):
            with self.subTest(fixture=fixture_path.name):
                fixture = self.load_fixture(fixture_path)
                self.assertIn("name", fixture)
                self.assertIn("item", fixture)
                self.assertIn("raw_output", fixture)
                self.assertIn("expected", fixture)
                self.assertIsInstance(fixture["item"], dict)
                self.assertIsInstance(fixture["raw_output"], str)
                self.assertIsInstance(fixture["expected"], dict)

                item = fixture["item"]
                self.assertIn("segments", item)
                self.assertIn("blanks", item)
                self.assertIn("expected_full_texts", item)
                self.assertIsInstance(item["segments"], list)
                self.assertIsInstance(item["blanks"], list)
                self.assertIsInstance(item["expected_full_texts"], list)

                expected = fixture["expected"]
                for key in (
                    "normalized_output",
                    "extraction_mode",
                    "blank_results",
                    "instruction_following_pass",
                    "item_format_pass",
                    "item_partial_score",
                    "item_strict_pass",
                ):
                    self.assertIn(key, expected)
                self.assertIsInstance(expected["blank_results"], list)
                self.assertGreater(len(expected["blank_results"]), 0)

    def load_fixture(self, fixture_path: Path) -> dict:
        with fixture_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)


if __name__ == "__main__":
    unittest.main()
