from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from llmclozestat.model_repository_validation import validate_model_repository


VALID_MODEL_TOML = """
[model]
model_id = "model-a"
family = "fixture"
source = "local"
source_repo = "unknown"
revision = "unknown"
quantization = "unknown"
backend = "unknown"

[policy]
one_model_repo = true
allow_mixed_model_ids = false
""".strip() + "\n"


class ModelRepositoryValidationTests(unittest.TestCase):
    def test_valid_model_repository_without_submissions_passes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            (repo_dir / "model.toml").write_text(VALID_MODEL_TOML, encoding="utf-8")

            result = validate_model_repository(repo_dir)
            self.assertFalse(result.failed, result.to_dict())
            self.assertIn("model_repository_checked", {info["code"] for info in result.info})

    def test_model_repository_missing_model_toml_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = validate_model_repository(Path(temp_dir))
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("model_toml_missing", {error.code for error in result.errors})

    def test_model_repository_mixed_model_submission_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            (repo_dir / "model.toml").write_text(VALID_MODEL_TOML, encoding="utf-8")
            submission_dir = repo_dir / "submissions" / "user-a" / "run-a"
            submission_dir.mkdir(parents=True)
            (submission_dir / "environment.json").write_text(json.dumps({"model_id": "model-b"}) + "\n", encoding="utf-8")
            (submission_dir / "summary.json").write_text(json.dumps({"model_id": "model-a"}) + "\n", encoding="utf-8")

            result = validate_model_repository(repo_dir)
            self.assertTrue(result.failed, result.to_dict())
            self.assertIn("mixed_model_submission", {error.code for error in result.errors})


if __name__ == "__main__":
    unittest.main()
