from __future__ import annotations

from pathlib import Path
import unittest

from llmclozestat.item_validation import validate_items_file


ROOT = Path(__file__).resolve().parents[1]


class ItemValidationTests(unittest.TestCase):
    def test_smoke_dataset_passes(self) -> None:
        result = validate_items_file(ROOT / "datasets" / "smoke_v0" / "items.jsonl")
        self.assertFalse(result.failed, result.to_dict())

    def test_valid_fixture_passes(self) -> None:
        result = validate_items_file(
            ROOT / "tests" / "fixtures" / "items" / "valid" / "smoke_v0_minimal.jsonl"
        )
        self.assertFalse(result.failed, result.to_dict())

    def test_segments_blanks_mismatch_fixture_fails_with_expected_code(self) -> None:
        result = validate_items_file(
            ROOT / "tests" / "fixtures" / "items" / "invalid" / "segments_blanks_mismatch.jsonl"
        )
        self.assert_error_code(result, "segments_blanks_mismatch")

    def test_empty_accepted_fills_fixture_fails_with_expected_code(self) -> None:
        result = validate_items_file(
            ROOT / "tests" / "fixtures" / "items" / "invalid" / "empty_accepted_fills.jsonl"
        )
        self.assert_error_code(result, "empty_accepted_fills")

    def test_duplicate_blank_id_fixture_fails_with_expected_code(self) -> None:
        result = validate_items_file(
            ROOT / "tests" / "fixtures" / "items" / "invalid" / "duplicate_blank_id.jsonl"
        )
        self.assert_error_code(result, "duplicate_blank_id")

    def test_position_not_consecutive_fixture_fails_with_expected_code(self) -> None:
        result = validate_items_file(
            ROOT / "tests" / "fixtures" / "items" / "invalid" / "position_not_consecutive.jsonl"
        )
        self.assert_error_code(result, "position_not_consecutive")

    def test_missing_claim_scope_fixture_fails_with_expected_code(self) -> None:
        result = validate_items_file(
            ROOT / "tests" / "fixtures" / "items" / "invalid" / "missing_claim_scope.jsonl"
        )
        self.assert_error_code(result, "missing_claim_scope")

    def test_empty_expected_full_texts_fixture_fails_with_expected_code(self) -> None:
        result = validate_items_file(
            ROOT / "tests" / "fixtures" / "items" / "invalid" / "empty_expected_full_texts.jsonl"
        )
        self.assert_error_code(result, "empty_expected_full_texts")

    def test_duplicate_normalized_fill_fixture_fails_with_expected_code(self) -> None:
        result = validate_items_file(
            ROOT / "tests" / "fixtures" / "items" / "invalid" / "duplicate_normalized_fill.jsonl"
        )
        self.assert_error_code(result, "duplicate_normalized_fill")

    def test_depends_on_unknown_blank_fixture_fails_with_expected_code(self) -> None:
        result = validate_items_file(
            ROOT / "tests" / "fixtures" / "items" / "invalid" / "depends_on_unknown_blank.jsonl"
        )
        self.assert_error_code(result, "depends_on_unknown_blank")

    def assert_error_code(self, result, expected_code: str) -> None:
        self.assertTrue(result.failed, result.to_dict())
        codes = {error.code for error in result.errors}
        self.assertIn(expected_code, codes, result.to_dict())


if __name__ == "__main__":
    unittest.main()
