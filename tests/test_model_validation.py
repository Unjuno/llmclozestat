from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from llmclozestat.model_validation import validate_model_file


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_MODEL = ROOT / "examples" / "model_repository" / "model.toml"


class ModelValidationTests(unittest.TestCase):
    def test_example_model_toml_passes(self) -> None:
        result = validate_model_file(EXAMPLE_MODEL)
        self.assertFalse(result.failed, result.to_dict())
        self.assertIn("model_validated", {info["code"] for info in result.info})

    def test_missing_model_table_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "model.toml"
            path.write_text("[policy]\none_model_repo = true\n", encoding="utf-8")
            result = validate_model_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("model_schema_validation_error", {error.code for error in result.errors})

    def test_missing_one_model_repo_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "model.toml"
            path.write_text(
                """
[model]
model_id = "fixture-model"
family = "fixture"
source = "local"
source_repo = "unknown"
revision = "unknown"
quantization = "unknown"
backend = "unknown"

[policy]
one_model_repo = false
""".strip()
                + "\n",
                encoding="utf-8",
            )
            result = validate_model_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("missing_one_model_repo", {error.code for error in result.errors})

    def test_zero_support_mode_with_nonzero_f_shot_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "model.toml"
            path.write_text(
                """
[model]
model_id = "fixture-model"
family = "fixture"
source = "local"
source_repo = "unknown"
revision = "unknown"
quantization = "unknown"
backend = "unknown"

[policy]
one_model_repo = true

[default_condition.prompt]
prompt_template_id = "strict-v0-en"
prompt_language = "en"
support_mode = "zero"
f_shot = 1
blank_rendering = "placeholder"
""".strip()
                + "\n",
                encoding="utf-8",
            )
            result = validate_model_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("zero_support_mode_with_f_shot", {error.code for error in result.errors})

    def test_validation_output_contract_shape(self) -> None:
        result = validate_model_file(EXAMPLE_MODEL)
        output = result.to_dict()
        self.assertEqual(set(output.keys()), {"status", "errors", "warnings", "info"})
        self.assertEqual(output["status"], "passed")
        self.assertIsInstance(output["errors"], list)
        self.assertIsInstance(output["warnings"], list)
        self.assertIsInstance(output["info"], list)


if __name__ == "__main__":
    unittest.main()
