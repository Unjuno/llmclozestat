from __future__ import annotations

import json
import re
from pathlib import Path
import unittest

from llmclozestat.result_validation import validate_results_file


ROOT = Path(__file__).resolve().parents[1]
RESULT_FIXTURES = ROOT / "tests" / "fixtures" / "results"
ERROR_CODES_DOC = ROOT / "docs" / "error_codes.md"
ERROR_CODE_PATTERN = re.compile(r"\| `([^`]+)` \|")


class ResultValidationTests(unittest.TestCase):
    def test_valid_result_fixtures_pass(self) -> None:
        valid_paths = sorted((RESULT_FIXTURES / "valid").glob("*.jsonl"))
        self.assertGreater(len(valid_paths), 0, "No valid result fixtures found")

        for fixture_path in valid_paths:
            with self.subTest(fixture=fixture_path.name):
                result = validate_results_file(fixture_path)
                self.assertFalse(result.failed, result.to_dict())

    def test_invalid_result_fixtures_fail_with_expected_codes(self) -> None:
        invalid_paths = sorted((RESULT_FIXTURES / "invalid").glob("*.jsonl"))
        self.assertGreater(len(invalid_paths), 0, "No invalid result fixtures found")

        for fixture_path in invalid_paths:
            with self.subTest(fixture=fixture_path.name):
                expected = self.load_expected_metadata(fixture_path)
                result = validate_results_file(fixture_path)
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

    def test_invalid_result_fixtures_have_expected_metadata(self) -> None:
        for fixture_path in sorted((RESULT_FIXTURES / "invalid").glob("*.jsonl")):
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

    def test_result_fixture_expected_codes_are_registered(self) -> None:
        registered_codes = self.load_registered_error_codes()
        self.assertGreater(len(registered_codes), 0, "No registered error codes found")

        for fixture_path in sorted((RESULT_FIXTURES / "invalid").glob("*.jsonl")):
            with self.subTest(fixture=fixture_path.name):
                expected = self.load_expected_metadata(fixture_path)
                expected_codes = {entry["code"] for entry in expected["expected_errors"]}
                missing = expected_codes - registered_codes
                self.assertFalse(
                    missing,
                    {
                        "fixture": fixture_path.name,
                        "missing_registered_codes": sorted(missing),
                    },
                )

    def test_validation_output_contract_shape_for_success(self) -> None:
        result = validate_results_file(RESULT_FIXTURES / "valid" / "minimal_result.jsonl")
        self.assert_validation_output_contract(result.to_dict(), expected_status="passed")

    def test_validation_output_contract_shape_for_failure(self) -> None:
        result = validate_results_file(
            RESULT_FIXTURES / "invalid" / "strict_pass_inconsistent.jsonl"
        )
        self.assert_validation_output_contract(result.to_dict(), expected_status="failed")

    def assert_validation_output_contract(self, output: dict, expected_status: str) -> None:
        self.assertEqual(set(output.keys()), {"status", "errors", "warnings", "info"})
        self.assertEqual(output["status"], expected_status)
        self.assertIn(output["status"], {"passed", "failed"})
        self.assertIsInstance(output["errors"], list)
        self.assertIsInstance(output["warnings"], list)
        self.assertIsInstance(output["info"], list)

    def load_expected_metadata(self, fixture_path: Path) -> dict:
        expected_path = fixture_path.with_suffix(".expected.json")
        with expected_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def load_registered_error_codes(self) -> set[str]:
        content = ERROR_CODES_DOC.read_text(encoding="utf-8")
        return set(ERROR_CODE_PATTERN.findall(content))


if __name__ == "__main__":
    unittest.main()
