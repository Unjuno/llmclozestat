from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer

from llmclozestat.aggregation import write_summary_file
from llmclozestat.environment_validation import validate_environment_file
from llmclozestat.item_validation import validate_items_file
from llmclozestat.manifest_validation import validate_manifest_file, validate_submission_manifest
from llmclozestat.model_repository_validation import validate_model_repository
from llmclozestat.model_validation import validate_model_file
from llmclozestat.reporting import ReportGenerationError, generate_reports
from llmclozestat.result_validation import validate_results_file
from llmclozestat.runner import run_from_config
from llmclozestat.submission import PrepareSubmissionError, prepare_submission_package
from llmclozestat.summary_validation import validate_summary_file

app = typer.Typer(help="Cloze-based statistical profiling for LLM outputs.")
validate_app = typer.Typer(help="Validate llmclozestat artifacts.")
app.add_typer(validate_app, name="validate")


@app.command()
def version() -> None:
    from llmclozestat import __version__
    typer.echo(__version__)


@app.command("run")
def run(
    config: Path = typer.Option(..., "--config", exists=False, file_okay=True, dir_okay=False),
    progress: bool = typer.Option(True, "--progress/--no-progress", help="Print human-readable run progress to stderr."),
) -> None:
    try:
        result = run_from_config(config, progress_callback=_stderr_progress if progress else None)
    except Exception as exc:
        typer.echo(json.dumps({"status": "failed", "errors": [{"code": "run_error", "message": str(exc)}]}, ensure_ascii=False, indent=2))
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("aggregate")
def aggregate(
    input_path: Path = typer.Option(..., "--input", exists=False, file_okay=True, dir_okay=False),
    out: Path = typer.Option(..., "--out", file_okay=True, dir_okay=False),
    validate_input: bool = typer.Option(True, "--validate-input/--no-validate-input"),
) -> None:
    if validate_input:
        validation = validate_results_file(input_path)
        if validation.failed:
            typer.echo(json.dumps(validation.to_dict(), ensure_ascii=False, indent=2))
            raise typer.Exit(code=1)
    summary = write_summary_file(input_path, out)
    typer.echo(json.dumps({"status": "passed", "summary_path": str(out), "n_trials": summary["n_trials"]}, ensure_ascii=False))


@app.command("report")
def report(submissions_dir: Path = typer.Option(..., "--submissions-dir", exists=False, file_okay=False, dir_okay=True), out_dir: Path = typer.Option(..., "--out-dir", exists=False, file_okay=False, dir_okay=True)) -> None:
    try:
        result = generate_reports(submissions_dir, out_dir)
    except ReportGenerationError as exc:
        typer.echo(json.dumps({"status": "failed", "errors": [{"code": "report_generation_error", "message": str(exc)}]}, ensure_ascii=False, indent=2))
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("prepare-submission")
def prepare_submission(submitter_id: str = typer.Option(..., "--submitter-id"), run_id: str = typer.Option(..., "--run-id"), environment_json: Path = typer.Option(..., "--environment-json", exists=False, file_okay=True, dir_okay=False), run_jsonl: Path = typer.Option(..., "--run-jsonl", exists=False, file_okay=True, dir_okay=False), summary_json: Path = typer.Option(..., "--summary-json", exists=False, file_okay=True, dir_okay=False), out_dir: Path = typer.Option(..., "--out-dir", exists=False, file_okay=False, dir_okay=True), summary_md: Path | None = typer.Option(None, "--summary-md", exists=False, file_okay=True, dir_okay=False), write_manifest: bool = typer.Option(True, "--write-manifest/--no-write-manifest"), overwrite: bool = typer.Option(False, "--overwrite"), validate_sources: bool = typer.Option(True, "--validate-sources/--no-validate-sources")) -> None:
    try:
        result = prepare_submission_package(submitter_id=submitter_id, run_id=run_id, environment_json=environment_json, run_jsonl=run_jsonl, summary_json=summary_json, summary_md=summary_md, out_dir=out_dir, write_manifest=write_manifest, overwrite=overwrite, validate_sources=validate_sources)
    except PrepareSubmissionError as exc:
        typer.echo(json.dumps({"status": "failed", "errors": [{"code": "prepare_submission_error", "message": str(exc)}]}, ensure_ascii=False, indent=2))
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("verify-integrity")
def verify_integrity(path: Path = typer.Option(..., "--path", exists=False, file_okay=False, dir_okay=True)) -> None:
    result = validate_submission_manifest(path)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        raise typer.Exit(code=1)


@validate_app.command("environment")
def validate_environment(input_path: Path = typer.Option(..., "--input", exists=False, file_okay=True, dir_okay=False)) -> None:
    result = validate_environment_file(input_path)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        raise typer.Exit(code=1)


@validate_app.command("items")
def validate_items(dataset: Path = typer.Option(..., "--dataset", exists=False, file_okay=True, dir_okay=False, readable=True)) -> None:
    result = validate_items_file(dataset)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        raise typer.Exit(code=1)


@validate_app.command("model")
def validate_model(input_path: Path = typer.Option(..., "--input", exists=False, file_okay=True, dir_okay=False)) -> None:
    result = validate_model_file(input_path)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        raise typer.Exit(code=1)


@validate_app.command("model-repo")
def validate_model_repo(path: Path = typer.Option(..., "--path", exists=False, file_okay=False, dir_okay=True)) -> None:
    result = validate_model_repository(path)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        raise typer.Exit(code=1)


@validate_app.command("results")
def validate_results(input_path: Path = typer.Option(..., "--input", exists=False, file_okay=True, dir_okay=False, readable=True)) -> None:
    result = validate_results_file(input_path)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        raise typer.Exit(code=1)


@validate_app.command("summary")
def validate_summary(input_path: Path = typer.Option(..., "--input", exists=False, file_okay=True, dir_okay=False)) -> None:
    result = validate_summary_file(input_path)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        raise typer.Exit(code=1)


@validate_app.command("manifest")
def validate_manifest(input_path: Path = typer.Option(..., "--input", exists=False, file_okay=True, dir_okay=False), package_dir: Path | None = typer.Option(None, "--package-dir", exists=False, file_okay=False, dir_okay=True), verify_files: bool = typer.Option(False, "--verify-files")) -> None:
    result = validate_manifest_file(input_path, package_dir=package_dir, verify_files=verify_files)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        raise typer.Exit(code=1)


@validate_app.command("submission")
def validate_submission(path: Path = typer.Option(..., "--path", exists=False, file_okay=False, dir_okay=True)) -> None:
    result = validate_submission_manifest(path)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        raise typer.Exit(code=1)


def _stderr_progress(event: dict[str, Any]) -> None:
    message = _format_progress_event(event)
    if not message:
        return
    print(message, file=sys.stderr, flush=True)


def _format_progress_event(event: dict[str, Any]) -> str:
    event_name = str(event.get("event", ""))
    if event_name == "run_started":
        return (
            f"[run] started run_id={event.get('run_id')} "
            f"model={event.get('model_id')} dataset={event.get('dataset_id')} "
            f"trials={event.get('total_trials')} retry_max={event.get('retry_max_attempts')}"
        )
    if event_name == "trial_started":
        return f"[run] trial {event.get('trial_id')}/{event.get('total_trials')} started item={event.get('item_id')}"
    if event_name == "trial_retry":
        return (
            f"[run] trial {event.get('trial_id')}/{event.get('total_trials')} retry "
            f"{event.get('next_attempt')}/{event.get('max_attempts')} after {event.get('error_type')}"
        )
    if event_name == "trial_passed":
        return (
            f"[run] trial {event.get('trial_id')}/{event.get('total_trials')} passed "
            f"attempts={event.get('attempts')} latency_ms={_format_number(event.get('latency_ms'))}"
        )
    if event_name == "trial_backend_error":
        return (
            f"[run] trial {event.get('trial_id')}/{event.get('total_trials')} backend_error "
            f"attempts={event.get('attempts')} error={event.get('error_type')} "
            f"latency_ms={_format_number(event.get('latency_ms'))}"
        )
    if event_name == "artifact_written":
        return f"[run] wrote {event.get('kind')} {event.get('path')}"
    if event_name == "run_completed":
        return (
            f"[run] completed run_id={event.get('run_id')} trials={event.get('total_trials')} "
            f"backend_errors={event.get('backend_error_count')} retried_trials={event.get('retried_trial_count')}"
        )
    return ""


def _format_number(value: object) -> str:
    if isinstance(value, int | float):
        return f"{value:.1f}"
    return str(value)
