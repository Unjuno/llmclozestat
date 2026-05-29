from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from llmclozestat.environment_validation import validate_environment_file


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ENVIRONMENT = ROOT / "examples" / "smoke_v0" / "environment.json"


class EnvironmentValidationTests(unittest.TestCase):
    def test_example_environment_passes(self) -> None:
        result = validate_environment_file(EXAMPLE_ENVIRONMENT)
        self.assertFalse(result.failed, result.to_dict())

    def test_missing_required_field_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            del environment["parser_config"]
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("environment_schema_validation_error", {error.code for error in result.errors})

    def test_prompt_condition_hash_mismatch_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["blank_rendering"] = "___"
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            messages = "\n".join(error.message for error in result.errors)
            self.assertIn("prompt_condition_hash does not match prompt condition fields", messages)

    def test_invalid_prompt_condition_hash_format_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["prompt_condition_hash"] = "sha256:BAD"
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("environment_schema_validation_error", {error.code for error in result.errors})

    def test_parser_config_hash_mismatch_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["parser_config"]["fallback_extraction_enabled"] = True
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            messages = "\n".join(error.message for error in result.errors)
            self.assertIn("parser_config_hash does not match parser_config", messages)

    def test_invalid_parser_config_hash_format_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["parser_config_hash"] = "sha256:BAD"
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("environment_schema_validation_error", {error.code for error in result.errors})

    def test_generation_config_hash_mismatch_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["generation_config"]["max_tokens"] = 128
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            messages = "\n".join(error.message for error in result.errors)
            self.assertIn("generation_config_hash does not match generation_config", messages)

    def test_invalid_generation_config_hash_format_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["generation_config_hash"] = "sha256:BAD"
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("environment_schema_validation_error", {error.code for error in result.errors})

    def test_condition_hash_mismatch_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["dataset_sha256"] = "sha256:" + "b" * 64
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            messages = "\n".join(error.message for error in result.errors)
            self.assertIn("condition_hash does not match dataset/prompt/parser/generation hashes", messages)

    def test_invalid_condition_hash_format_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["condition_hash"] = "sha256:BAD"
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("environment_schema_validation_error", {error.code for error in result.errors})

    def test_experiment_hash_mismatch_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["model_id"] = "other-model"
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            messages = "\n".join(error.message for error in result.errors)
            self.assertIn("experiment_hash does not match condition/model/backend/provider fields", messages)

    def test_invalid_experiment_hash_format_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["experiment_hash"] = "sha256:BAD"
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("environment_schema_validation_error", {error.code for error in result.errors})

    def test_zero_support_mode_requires_zero_f_shot(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["support_mode"] = "zero"
            environment["f_shot"] = 1
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("zero_support_mode_with_f_shot", {error.code for error in result.errors})

    def test_duplicate_extraction_mode_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "environment.json"
            environment = json.loads(EXAMPLE_ENVIRONMENT.read_text(encoding="utf-8"))
            environment["parser_config"]["extraction_modes_enabled"] = ["segment", "segment"]
            path.write_text(json.dumps(environment) + "\n", encoding="utf-8")

            result = validate_environment_file(path)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("environment_schema_validation_error", {error.code for error in result.errors})

    def test_validation_output_contract_shape(self) -> None:
        result = validate_environment_file(EXAMPLE_ENVIRONMENT)
        output = result.to_dict()
        self.assertEqual(set(output.keys()), {"status", "errors", "warnings", "info"})
        self.assertEqual(output["status"], "passed")
        self.assertIsInstance(output["errors"], list)
        self.assertIsInstance(output["warnings"], list)
        self.assertIsInstance(output["info"], list)


if __name__ == "__main__":
    unittest.main()
