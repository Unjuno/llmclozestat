from __future__ import annotations

import json
from pathlib import Path
import unittest

from llmclozestat.parser_scoring import parse_and_score_item


ROOT = Path(__file__).resolve().parents[1]
PARSER_FIXTURES = ROOT / "tests" / "fixtures" / "parser"


class ParserFixtureStructureTests(unittest.TestCase):
    def test_parser_fixtures_exist(self) -> None:
        fixture_paths = sorted(PARSER_FIXTURES.glob("*.json"))
        self.assertGreater(len(fixture_paths), 0, "No parser fixtures found")

    def test_parser_fixtures_have_required_shape(self) -> None:
        for fixture_path in self.fixture_paths():
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

    def test_parser_scorer_matches_fixtures(self) -> None:
        for fixture_path in self.fixture_paths():
            with self.subTest(fixture=fixture_path.name):
                fixture = self.load_fixture(fixture_path)
                actual = parse_and_score_item(
                    fixture["item"],
                    fixture["raw_output"],
                    fixture.get("parser_config", {}),
                )
                self.assert_expected_subset(fixture["expected"], actual)

    def assert_expected_subset(self, expected: dict, actual: dict) -> None:
        for key, expected_value in expected.items():
            self.assertIn(key, actual)
            if key == "blank_results":
                self.assert_blank_results(expected_value, actual[key])
            else:
                self.assertEqual(actual[key], expected_value, {"key": key, "actual": actual})

    def assert_blank_results(self, expected: list[dict], actual: list[dict]) -> None:
        self.assertEqual(len(actual), len(expected), {"expected": expected, "actual": actual})
        for expected_blank, actual_blank in zip(expected, actual, strict=True):
            for key, expected_value in expected_blank.items():
                self.assertIn(key, actual_blank)
                self.assertEqual(
                    actual_blank[key],
                    expected_value,
                    {"key": key, "expected_blank": expected_blank, "actual_blank": actual_blank},
                )

    def fixture_paths(self) -> list[Path]:
        return sorted(PARSER_FIXTURES.glob("*.json"))

    def load_fixture(self, fixture_path: Path) -> dict:
        with fixture_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)


if __name__ == "__main__":
    unittest.main()
