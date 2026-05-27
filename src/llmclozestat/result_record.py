from __future__ import annotations

from typing import Any

from llmclozestat.parser_scoring import parse_and_score_item


REQUIRED_METADATA_FIELDS = (
    "submitter_id",
    "run_id",
    "model_id",
    "backend",
    "provider",
    "trial_id",
    "prompt_template_id",
    "prompt_language",
    "support_mode",
    "f_shot",
    "blank_rendering",
    "generation_config",
)


def build_result_record(
    *,
    item: dict[str, Any],
    raw_output: str,
    metadata: dict[str, Any],
    parser_config: dict[str, Any] | None = None,
    latency_ms: float = 0,
) -> dict[str, Any]:
    """Build one result JSONL record from item, raw output, and run metadata.

    This helper assembles a record. It does not call a model backend and does
    not write JSONL. The caller remains responsible for persistence.
    """

    missing = [field for field in REQUIRED_METADATA_FIELDS if field not in metadata]
    if missing:
        raise ValueError(f"missing result metadata fields: {', '.join(missing)}")

    parsed = parse_and_score_item(item, raw_output, parser_config or {})

    record: dict[str, Any] = {
        "submitter_id": metadata["submitter_id"],
        "run_id": metadata["run_id"],
        "dataset_id": item.get("dataset_id", metadata.get("dataset_id", "")),
        "model_id": metadata["model_id"],
        "model_source": metadata.get("model_source"),
        "quantization": metadata.get("quantization"),
        "backend": metadata["backend"],
        "backend_version": metadata.get("backend_version"),
        "provider": metadata["provider"],
        "probe_id": item.get("probe_id", ""),
        "variant_id": item.get("variant_id", ""),
        "language": item.get("language", metadata.get("language", "")),
        "primary_skill": item.get("primary_skill", ""),
        "item_id": item.get("item_id", ""),
        "trial_id": metadata["trial_id"],
        "prompt_template_id": metadata["prompt_template_id"],
        "prompt_language": metadata["prompt_language"],
        "support_mode": metadata["support_mode"],
        "f_shot": metadata["f_shot"],
        "blank_rendering": metadata["blank_rendering"],
        "generation_config": metadata["generation_config"],
        "generation_config_hash": metadata.get("generation_config_hash"),
        "latency_ms": latency_ms,
    }
    record.update(parsed)
    return record
