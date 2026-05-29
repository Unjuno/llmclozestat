from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from llmclozestat.manifest_validation import validate_submission_manifest
from llmclozestat.runner import render_item_text, render_prompt, run_from_config


EXPECTED_FULL_TEXT = "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの右手に対応する。"


class RunnerTests(unittest.TestCase):
    def test_render_item_text_uses_segments_and_blank_rendering(self) -> None:
        item = {
            "segments": ["A", "B", "C"],
            "blanks": [{"blank_id": "b1"}, {"blank_id": "b2"}],
        }
        self.assertEqual(render_item_text(item, "___"), "A___B___C")

    def test_render_prompt_uses_japanese_template_for_ja_id(self) -> None:
        item = {
            "segments": ["空は", "です。"],
            "blanks": [{"blank_id": "b1"}],
        }
        prompt = render_prompt(
            item,
            {
                "prompt_template_id": "fill_full_sentence_v1.ja",
                "blank_rendering": "（　　　）",
            },
        )
        self.assertIn("# タスク", prompt)
        self.assertIn("空は（　　　）です。", prompt)

    def test_run_from_config_writes_valid_submission_package_without_external_api(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_project_files(root)

            with patch("llmclozestat.runner._make_client", return_value=object()), patch(
                "llmclozestat.runner._call_chat_completion",
                return_value=EXPECTED_FULL_TEXT,
            ):
                result = run_from_config(root / "run.toml")

            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["run_id"], "smoke_v0-20260528T120000Z-a1b2c3")
            self.assertTrue(result["dataset_sha256"].startswith("sha256:"))
            submission_path = Path(result["submission_path"])
            self.assertEqual(submission_path, root / "submissions" / "user-a" / "smoke_v0-20260528T120000Z-a1b2c3")

            for filename in ["environment.json", "run.jsonl", "summary.json", "manifest.json"]:
                self.assertTrue((submission_path / filename).is_file(), filename)

            environment = json.loads((submission_path / "environment.json").read_text(encoding="utf-8"))
            self.assertEqual(environment["submitter_id"], "user-a")
            self.assertEqual(environment["run_id"], "smoke_v0-20260528T120000Z-a1b2c3")
            self.assertEqual(environment["dataset_id"], "smoke_v0")
            self.assertEqual(environment["model_id"], "model-a")
            self.assertTrue(environment["dataset_sha256"].startswith("sha256:"))

            run_records = [json.loads(line) for line in (submission_path / "run.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(run_records), 1)
            self.assertTrue(run_records[0]["item_strict_pass"])
            self.assertEqual(run_records[0]["blank_results"][0]["extracted_fill"], "右")
            self.assertTrue(run_records[0]["metadata"]["dataset_sha256"].startswith("sha256:"))

            validation = validate_submission_manifest(submission_path)
            self.assertFalse(validation.failed, validation.to_dict())


def _write_project_files(root: Path) -> None:
    dataset_dir = root / "datasets" / "smoke_v0"
    dataset_dir.mkdir(parents=True)
    item = _valid_item()
    (dataset_dir / "items.jsonl").write_text(json.dumps(item, ensure_ascii=False) + "\n", encoding="utf-8")

    (root / "model.toml").write_text(
        """
[model]
model_id = "model-a"
family = "fixture"
source = "local"
source_repo = "unknown"
revision = "test"
quantization = "none"
backend = "fixture"
backend_version = "test"

[policy]
one_model_repo = true
allow_mixed_model_ids = false
""".strip()
        + "\n",
        encoding="utf-8",
    )

    (root / "run.toml").write_text(
        """
[run]
submitter_id = "user-a"
run_id = "smoke_v0-20260528T120000Z-a1b2c3"
dataset_path = "datasets/smoke_v0/items.jsonl"
trials_per_item = 1
output_dir = "submissions"
overwrite = false
model_toml = "model.toml"

[backend]
type = "openai_compatible"
provider = "fixture"
api_key_env = "OPENAI_API_KEY"
model_name = "fixture-model"

[prompt]
prompt_template_id = "fill_full_sentence_v1.ja"
prompt_language = "ja"
support_mode = "zero"
f_shot = 0
blank_rendering = "（　　　）"

[generation]
temperature = 0
top_p = 1.0
seed = 1
max_tokens = 64
stop = []

[parser]
normalization = "v0_minimal"
extraction_modes_enabled = ["exact_full_text", "segment"]
fallback_extraction_enabled = false
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _valid_item() -> dict[str, object]:
    return {
        "dataset_id": "smoke_v0",
        "probe_id": "probe-a",
        "variant_id": "variant-a.ja",
        "item_id": "item-a",
        "version": "1.0.0",
        "language": "ja",
        "translation_relation": "original",
        "equivalence_level": "same_claim",
        "item_type": "single_blank_cloze",
        "primary_skill": "mirror_body_correspondence",
        "secondary_tags": ["spatial_reasoning"],
        "validation_target": "body-part correspondence in mirror perspective",
        "claim_scope": "A mirror image of a raised real right hand corresponds to the person's real right hand.",
        "text_with_blanks": "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの（　　　）手に対応する。",
        "segments": [
            "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの",
            "手に対応する。",
        ],
        "blanks": [
            {
                "blank_id": "blank_1",
                "position": 1,
                "primary_skill": "mirror_body_correspondence",
                "context_distance": "local",
                "accepted_fills": ["右"],
                "near_miss_fills": [],
                "known_wrong_fills": ["左"],
                "expected_error_patterns": ["mirror_left_right_surface_rule"],
            }
        ],
        "expected_full_texts": [EXPECTED_FULL_TEXT],
        "ambiguity_level": "low",
        "source_type": "synthetic",
        "review_status": "reviewed",
    }


if __name__ == "__main__":
    unittest.main()
