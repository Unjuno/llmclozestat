from __future__ import annotations

from typing import Any

from llmclozestat.parser_scoring import parse_and_score_item, parse_fail_blank


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

IDENTITY_METADATA_FIELDS = (
    "dataset_sha256",
    "prompt_condition_hash",
    "parser_config_hash",
    "generation_config_hash",
    "condition_hash",
    "experiment_hash",
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

    record = _base_result_record(item=item, metadata=metadata, latency_ms=latency_ms)
    parsed = parse_and_score_item(item, raw_output, parser_config or {})
    record.update(parsed)
    return record


def build_backend_failure_record(
    *,
    item: dict[str, Any],
    metadata: dict[str, Any],
    latency_ms: float,
    error_type: str,
    error_message: str,
) -> dict[str, Any]:
    """Build a result record for a trial where the backend call failed.

    Backend failures are experimental observations. The record is intentionally
    a parse-fail result so aggregation keeps the failed trial instead of
    silently shrinking the denominator.
    """

    record = _base_result_record(item=item, metadata=metadata, latency_ms=latency_ms)
    blanks = item.get("blanks", [])
    blank_results = [parse_fail_blank(blank).to_dict() for blank in blanks if isinstance(blank, dict)]
    if not blank_results:
        blank_results = [
            {
                "blank_id": "backend_error",
                "position": 1,
                "extracted_fill": None,
                "fill_class": "parse_fail",
                "blank_parse_pass": False,
                "content_pass": False,
                "parse_fail": True,
            }
        ]
    record.update(
        {
            "raw_output": "",
            "normalized_output": "",
            "extraction_mode": "segment",
            "blank_results": blank_results,
            "instruction_following_pass": False,
            "item_format_pass": False,
            "item_strict_pass": False,
            "item_partial_score": 0.0,
            "trial_status": "backend_error",
            "backend_error": {
                "type": error_type,
                "message": error_message,
            },
        }
    )
    return record


def _base_result_record(*, item: dict[str, Any], metadata: dict[str, Any], latency_ms: float) -> dict[str, Any]:
    missing = [field for field in REQUIRED_METADATA_FIELDS if field not in metadata]
    if missing:
        raise ValueError(f"missing result metadata fields: {', '.join(missing)}")

    record: dict[str, Any] = {
        "submitter_id": metadata["submitter_id"],
        "run_id": metadata["run_id"],
        "dataset_id": item.get("dataset_id", metadata.get("dataset_id", "")),
        "dataset_sha256": metadata.get("dataset_sha256", ""),
        "condition_hash": metadata.get("condition_hash", ""),
        "experiment_hash": metadata.get("experiment_hash", ""),
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
        "prompt_condition_hash": metadata.get("prompt_condition_hash"),
        "parser_config": metadata.get("parser_config"),
        "parser_config_hash": metadata.get("parser_config_hash"),
        "generation_config": metadata["generation_config"],
        "generation_config_hash": metadata.get("generation_config_hash"),
        "latency_ms": latency_ms,
        "metadata": {field: metadata.get(field) for field in sorted(set(metadata))},
    }
    for field in IDENTITY_METADATA_FIELDS:
        if field in metadata:
            record[field] = metadata[field]
    return record
