from __future__ import annotations

import json
import re
from pathlib import Path
import unittest

from llmclozestat.summary_validation import validate_summary_file


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_FIXTURES = ROOT / "tests" / "fixtures" / "summaries"
ERROR_CODES_DOC = ROOT / "docs" / "error_codes.md"
ERROR_CODE_PATTERN = re.compile(r"\| `([^`]+)` \|")


class SummaryValidationTests(unittest.TestCase):
    def test_valid_summary_fixtures_pass(self) -> None:
        valid_paths = sorted((SUMMARY_FIXTURES / "valid").glob("*.json"))
        self.assertGreater(len(valid_paths), 0)

        for fixture_path in valid_paths:
            with self.subTest(fixture=fixture_path.name):
                result = validate_summary_file(fixture_path)
                self.assertFalse(result.failed, result.to_dict())

    def test_invalid_summary_fixtures_fail_with_expected_codes(self) -> None:
        invalid_paths = sorted((SUMMARY_FIXTURES / "invalid").glob("*.json"))
        invalid_paths = [path for path in invalid_paths if not path.name.endswith(".expected.json")]

        for fixture_path in invalid_paths:
            with self.subTest(fixture=fixture_path.name):
                expected_path = fixture_path.with_suffix(".expected.json")
                self.assertTrue(expected_path.exists(), f"Missing expected metadata: {expected_path}")
                expected = json.loads(expected_path.read_text(encoding="utf-8"))
                result = validate_summary_file(fixture_path)
                self.assertTrue(result.failed, result.to_dict())
                actual_codes = {error.code for error in result.errors}
                expected_codes = {entry["code"] for entry in expected["expected_errors"]}
                self.assertTrue(expected_codes.issubset(actual_codes))

    def test_summary_expected_codes_are_registered(self) -> None:
        registered_codes = set(ERROR_CODE_PATTERN.findall(ERROR_CODES_DOC.read_text(encoding="utf-8")))

        invalid_paths = sorted((SUMMARY_FIXTURES / "invalid").glob("*.expected.json"))
        for expected_path in invalid_paths:
            with self.subTest(fixture=expected_path.name):
                expected = json.loads(expected_path.read_text(encoding="utf-8"))
                for entry in expected["expected_errors"]:
                    self.assertIn(entry["code"], registered_codes)


if __name__ == "__main__":
    unittest.main()
