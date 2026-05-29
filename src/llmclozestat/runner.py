from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from openai import OpenAI

from llmclozestat import __version__
from llmclozestat.aggregation import write_summary_file
from llmclozestat.item_validation import validate_items_file
from llmclozestat.manifest_validation import validate_manifest_file
from llmclozestat.model_validation import validate_model_file
from llmclozestat.result_record import build_result_record
from llmclozestat.submission import build_manifest


class RunConfigurationError(ValueError):
    pass


class RunExecutionError(RuntimeError):
    pass


def run_from_config(config_path: Path) -> dict[str, Any]:
    config = _load_toml(config_path)
    root = config_path.parent

    run_cfg = _table(config, "run")
    model_path = _resolve(root, str(run_cfg.get("model_toml", "model.toml")))
    _ensure_valid_model(model_path)
    model_toml = _load_toml(model_path)
    model_cfg = _table(model_toml, "model")

    dataset_path = _resolve(root, _required_str(run_cfg, "dataset_path", "run"))
    _ensure_valid_items(dataset_path)
    dataset_sha256 = _sha256_file(dataset_path)
    items = _load_items(dataset_path)
    if not items:
        raise RunConfigurationError(f"dataset has no items: {dataset_path}")

    dataset_id = str(items[0].get("dataset_id", ""))
    if not dataset_id:
        raise RunConfigurationError("first dataset item has no dataset_id")
    if any(item.get("dataset_id") != dataset_id for item in items):
        raise RunConfigurationError("all items in one run must share dataset_id")

    run_id = str(run_cfg.get("run_id") or _generate_run_id(dataset_id))
    submitter_id = _required_str(run_cfg, "submitter_id", "run")
    trials_per_item = int(run_cfg.get("trials_per_item", 1))
    if trials_per_item < 1:
        raise RunConfigurationError("run.trials_per_item must be >= 1")

    output_root = _resolve(root, str(run_cfg.get("output_dir", "submissions")))
    run_dir = output_root / submitter_id / run_id
    if run_dir.exists() and any(run_dir.iterdir()) and not bool(run_cfg.get("overwrite", False)):
        raise RunExecutionError(f"output submission directory is not empty: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)

    backend = _table(config, "backend")
    prompt_cfg = _table(config, "prompt")
    generation_cfg = _table(config, "generation")
    parser_cfg = _table(config, "parser") if isinstance(config.get("parser"), dict) else {
        "normalization": "v0_minimal",
        "extraction_modes_enabled": ["exact_full_text", "segment"],
    }

    generation_config_hash = _hash_json(generation_cfg)
    environment = _build_environment(
        submitter_id=submitter_id,
        run_id=run_id,
        dataset_id=dataset_id,
        dataset_sha256=dataset_sha256,
        generation_config_hash=generation_config_hash,
        model=model_cfg,
        backend=backend,
        prompt=prompt_cfg,
        parser=parser_cfg,
        generation=generation_cfg,
    )
    environment_path = run_dir / "environment.json"
    environment_path.write_text(json.dumps(environment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run_jsonl_path = run_dir / "run.jsonl"
    client = _make_client(backend)
    model_name = _required_str(backend, "model_name", "backend")

    trial_id = 0
    with run_jsonl_path.open("w", encoding="utf-8") as handle:
        for item in items:
            for _ in range(trials_per_item):
                trial_id += 1
                prompt_text = render_prompt(item, prompt_cfg)
                started = time.perf_counter()
                raw_output = _call_chat_completion(client, model_name, prompt_text, generation_cfg)
                latency_ms = (time.perf_counter() - started) * 1000.0
                metadata = {
                    "submitter_id": submitter_id,
                    "run_id": run_id,
                    "dataset_id": dataset_id,
                    "dataset_sha256": dataset_sha256,
                    "model_id": _required_str(model_cfg, "model_id", "model"),
                    "model_source": model_cfg.get("source"),
                    "quantization": model_cfg.get("quantization"),
                    "backend": _required_str(model_cfg, "backend", "model"),
                    "backend_version": model_cfg.get("backend_version"),
                    "provider": str(backend.get("provider", backend.get("type", "openai_compatible"))),
                    "trial_id": trial_id,
                    "prompt_template_id": _required_str(prompt_cfg, "prompt_template_id", "prompt"),
                    "prompt_language": _required_str(prompt_cfg, "prompt_language", "prompt"),
                    "support_mode": str(prompt_cfg.get("support_mode", "zero")),
                    "f_shot": int(prompt_cfg.get("f_shot", 0)),
                    "blank_rendering": _required_str(prompt_cfg, "blank_rendering", "prompt"),
                    "generation_config": generation_cfg,
                    "generation_config_hash": generation_config_hash,
                }
                record = build_result_record(item=item, raw_output=raw_output, metadata=metadata, parser_config=parser_cfg, latency_ms=latency_ms)
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

    summary_path = run_dir / "summary.json"
    summary = write_summary_file(run_jsonl_path, summary_path)
    manifest_path = _write_manifest(run_dir, submitter_id, run_id)
    return {
        "status": "passed",
        "run_id": run_id,
        "submission_path": str(run_dir),
        "environment_json": str(environment_path),
        "run_jsonl": str(run_jsonl_path),
        "summary_json": str(summary_path),
        "manifest_json": str(manifest_path),
        "dataset_sha256": dataset_sha256,
        "generation_config_hash": generation_config_hash,
        "n_trials": summary.get("n_trials"),
    }


def render_prompt(item: dict[str, Any], prompt_cfg: dict[str, Any]) -> str:
    template_id = str(prompt_cfg.get("prompt_template_id", "fill_full_sentence_v1.ja"))
    blank_rendering = _required_str(prompt_cfg, "blank_rendering", "prompt")
    text = render_item_text(item, blank_rendering)
    if template_id.endswith(".ja"):
        return "# タスク\n空欄を埋めてください。回答では、完成した全文だけを出力してください。\n\n# 問題\n" + text
    return "# Task\nFill in the blank. When answering, output the full completed sentence only.\n\n# Problem\n" + text


def render_item_text(item: dict[str, Any], blank_rendering: str) -> str:
    segments = item.get("segments")
    blanks = item.get("blanks")
    if not isinstance(segments, list) or not isinstance(blanks, list) or len(segments) != len(blanks) + 1:
        value = item.get("text_with_blanks")
        if isinstance(value, str):
            return value
        raise RunConfigurationError("item has invalid segments/blanks and no text_with_blanks fallback")
    parts: list[str] = []
    for index, segment in enumerate(segments):
        if not isinstance(segment, str):
            raise RunConfigurationError("item segment must be a string")
        parts.append(segment)
        if index < len(blanks):
            parts.append(blank_rendering)
    return "".join(parts)


def _ensure_valid_items(dataset_path: Path) -> None:
    result = validate_items_file(dataset_path)
    if result.failed:
        raise RunConfigurationError(f"dataset failed validation: {result.to_dict()}")


def _ensure_valid_model(model_path: Path) -> None:
    result = validate_model_file(model_path)
    if result.failed:
        raise RunConfigurationError(f"model metadata failed validation: {result.to_dict()}")


def _write_manifest(run_dir: Path, submitter_id: str, run_id: str) -> Path:
    manifest = build_manifest(
        submitter_id=submitter_id,
        run_id=run_id,
        package_dir=run_dir,
        relative_paths=["environment.json", "run.jsonl", "summary.json"],
    )
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validation = validate_manifest_file(manifest_path, package_dir=run_dir, verify_files=True)
    if validation.failed:
        raise RunExecutionError(f"generated manifest failed verification: {validation.to_dict()}")
    return manifest_path


def _call_chat_completion(client: OpenAI, model_name: str, prompt_text: str, generation: dict[str, Any]) -> str:
    kwargs: dict[str, Any] = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt_text}],
    }
    for key in ["temperature", "top_p", "max_tokens", "seed", "stop"]:
        if key in generation and generation[key] is not None:
            kwargs[key] = generation[key]
    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content
    if content is None:
        raise RunExecutionError("backend returned empty message content")
    return content


def _make_client(backend: dict[str, Any]) -> OpenAI:
    backend_type = str(backend.get("type", "openai_compatible"))
    if backend_type != "openai_compatible":
        raise RunConfigurationError(f"unsupported backend.type: {backend_type}")
    api_key_env = str(backend.get("api_key_env", "OPENAI_API_KEY"))
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RunConfigurationError(f"environment variable is not set: {api_key_env}")
    base_url = backend.get("base_url")
    if base_url:
        return OpenAI(api_key=api_key, base_url=str(base_url))
    return OpenAI(api_key=api_key)


def _build_environment(
    *,
    submitter_id: str,
    run_id: str,
    dataset_id: str,
    dataset_sha256: str,
    generation_config_hash: str,
    model: dict[str, Any],
    backend: dict[str, Any],
    prompt: dict[str, Any],
    parser: dict[str, Any],
    generation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "submitter_id": submitter_id,
        "run_id": run_id,
        "tool_version": __version__,
        "dataset_id": dataset_id,
        "dataset_sha256": dataset_sha256,
        "model_id": _required_str(model, "model_id", "model"),
        "backend": _required_str(model, "backend", "model"),
        "provider": str(backend.get("provider", backend.get("type", "openai_compatible"))),
        "prompt_template_id": _required_str(prompt, "prompt_template_id", "prompt"),
        "prompt_language": _required_str(prompt, "prompt_language", "prompt"),
        "support_mode": str(prompt.get("support_mode", "zero")),
        "f_shot": int(prompt.get("f_shot", 0)),
        "blank_rendering": _required_str(prompt, "blank_rendering", "prompt"),
        "parser_config": parser,
        "generation_config": generation,
        "generation_config_hash": generation_config_hash,
    }


def _load_items(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise RunConfigurationError(f"dataset line {line_number} is not a JSON object: {path}")
            records.append(value)
    return records


def _generate_run_id(dataset_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{dataset_id}-{timestamp}-{secrets.token_hex(3)}"


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RunConfigurationError(f"TOML file does not exist: {path}")
    value = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RunConfigurationError(f"TOML root must be a table: {path}")
    return value


def _table(obj: dict[str, Any], name: str) -> dict[str, Any]:
    value = obj.get(name)
    if not isinstance(value, dict):
        raise RunConfigurationError(f"missing or invalid [{name}] table")
    return value


def _required_str(obj: dict[str, Any], key: str, table_name: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value:
        raise RunConfigurationError(f"{table_name}.{key} must be a non-empty string")
    return value


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path
