from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


RUN_INDEX_FIELDS = [
    "submitter_id",
    "run_id",
    "dataset_id",
    "model_id",
    "n_trials",
    "content_pass_rate",
    "instruction_following_pass_rate",
    "item_format_pass_rate",
    "strict_pass_rate",
    "parse_fail_rate",
    "avg_latency_ms",
]

BLANK_FILL_FIELDS = [
    "submitter_id",
    "run_id",
    "dataset_id",
    "model_id",
    "probe_id",
    "variant_id",
    "language",
    "item_id",
    "blank_id",
    "position",
    "prompt_template_id",
    "prompt_language",
    "support_mode",
    "f_shot",
    "blank_rendering",
    "extraction_mode",
    "generation_config_hash",
    "group_n_trials",
    "extracted_fill",
    "fill_key",
    "fill_class",
    "count",
    "rate",
]


class ReportGenerationError(ValueError):
    pass


def generate_reports(submissions_dir: Path, out_dir: Path) -> dict[str, Any]:
    if not submissions_dir.exists():
        raise ReportGenerationError(f"submissions directory does not exist: {submissions_dir}")
    if not submissions_dir.is_dir():
        raise ReportGenerationError(f"submissions path is not a directory: {submissions_dir}")

    summaries = _load_summaries(submissions_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_index_path = out_dir / "run_index.csv"
    blank_fills_path = out_dir / "blank_fills.csv"
    _write_run_index(run_index_path, summaries)
    _write_blank_fills(blank_fills_path, summaries)

    return {
        "status": "passed",
        "summary_count": len(summaries),
        "run_index_path": str(run_index_path),
        "blank_fills_path": str(blank_fills_path),
    }


def _load_summaries(submissions_dir: Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for summary_path in sorted(submissions_dir.glob("*/*/summary.json")):
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ReportGenerationError(f"Invalid summary JSON {summary_path}: {exc.msg}") from exc
        if not isinstance(summary, dict):
            raise ReportGenerationError(f"summary.json must be an object: {summary_path}")
        summaries.append(summary)
    return summaries


def _write_run_index(path: Path, summaries: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_INDEX_FIELDS)
        writer.writeheader()
        for summary in summaries:
            writer.writerow({field: _csv_value(summary.get(field)) for field in RUN_INDEX_FIELDS})


def _write_blank_fills(path: Path, summaries: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BLANK_FILL_FIELDS)
        writer.writeheader()
        for summary in summaries:
            top = {field: summary.get(field) for field in ["submitter_id", "run_id", "dataset_id", "model_id"]}
            groups = summary.get("groups", [])
            if not isinstance(groups, list):
                continue
            for group in groups:
                if not isinstance(group, dict):
                    continue
                fill_distribution = group.get("fill_distribution", [])
                if not isinstance(fill_distribution, list):
                    continue
                for fill in fill_distribution:
                    if not isinstance(fill, dict):
                        continue
                    row = {
                        **top,
                        "probe_id": group.get("probe_id"),
                        "variant_id": group.get("variant_id"),
                        "language": group.get("language"),
                        "item_id": group.get("item_id"),
                        "blank_id": group.get("blank_id"),
                        "position": group.get("position"),
                        "prompt_template_id": group.get("prompt_template_id"),
                        "prompt_language": group.get("prompt_language"),
                        "support_mode": group.get("support_mode"),
                        "f_shot": group.get("f_shot"),
                        "blank_rendering": group.get("blank_rendering"),
                        "extraction_mode": group.get("extraction_mode"),
                        "generation_config_hash": group.get("generation_config_hash"),
                        "group_n_trials": group.get("n_trials"),
                        "extracted_fill": fill.get("extracted_fill"),
                        "fill_key": fill.get("fill_key"),
                        "fill_class": fill.get("fill_class"),
                        "count": fill.get("count"),
                        "rate": fill.get("rate"),
                    }
                    writer.writerow({field: _csv_value(row.get(field)) for field in BLANK_FILL_FIELDS})


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    return value
