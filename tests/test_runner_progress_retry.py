from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from llmclozestat.manifest_validation import validate_submission_manifest
from llmclozestat.runner import run_from_config


EXPECTED_FULL_TEXT = "あなたが鏡の前で現実の右手を上げる。鏡の中の像で上がっている手は、現実のあなたの右手に対応する。"


class RunnerProgressRetryTests(unittest.TestCase):
    def test_run_from_config_emits_progress_events(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_project_files(root)
            progress_events: list[dict[str, object]] = []

            with patch("llmclozestat.runner._make_client", return_value=object()), patch(
                "llmclozestat.runner._call_chat_completion",
                return_value=EXPECTED_FULL_TEXT,
            ):
                result = run_from_config(root / "run.toml", progress_callback=progress_events.append)

            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["total_trials"], 1)
            self.assertEqual(result["retry_max_attempts"], 1)
            self.assertEqual(result["retried_trial_count"], 0)
            event_names = [event["event"] for event in progress_events]
            self.assertEqual(event_names[0], "run_started")
            self.assertIn("trial_started", event_names)
            self.assertIn("trial_passed", event_names)
            self.assertIn("artifact_written", event_names)
            self.assertEqual(event_names[-1], "run_completed")

    def test_run_from_config_retries_backend_call_before_success(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_project_files(root, retry_table=True)
            progress_events: list[dict[str, object]] = []
            responses: list[object] = [RuntimeError("temporary failure"), EXPECTED_FULL_TEXT]

            def fail_once_then_succeed(*args: object, **kwargs: object) -> str:
                del args, kwargs
                value = responses.pop(0)
                if isinstance(value, Exception):
                    raise value
                return str(value)

            with patch("llmclozestat.runner._make_client", return_value=object()), patch(
                "llmclozestat.runner._call_chat_completion",
                side_effect=fail_once_then_succeed,
            ):
                result = run_from_config(root / "run.toml", progress_callback=progress_events.append)

            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["backend_error_count"], 0)
            self.assertEqual(result["retried_trial_count"], 1)
            self.assertEqual(result["retry_max_attempts"], 3)

            retry_event = next(event for event in progress_events if event["event"] == "trial_retry")
            self.assertEqual(retry_event["attempt"], 1)
            self.assertEqual(retry_event["next_attempt"], 2)
            self.assertEqual(retry_event["max_attempts"], 3)

            submission_path = Path(result["submission_path"])
            records = [json.loads(line) for line in (submission_path / "run.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records[0]["backend_attempts"], 2)
            self.assertTrue(records[0]["item_strict_pass"])
            validation = validate_submission_manifest(submission_path)
            self.assertFalse(validation.failed, validation.to_dict())


def _write_project_files(root: Path, retry_table: bool = False) -> None:
    dataset_dir = root / "datasets" / "smoke_v0"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "items.jsonl").write_text(json.dumps(_valid_item(), ensure_ascii=False) + "\n", encoding="utf-8")

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

    retry_section = """

[retry]
max_attempts = 3
retry_delay_seconds = 0
backoff_factor = 1
""" if retry_table else ""
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
        + retry_section
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
