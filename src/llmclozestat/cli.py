from __future__ import annotations

import json
from pathlib import Path

import typer

from llmclozestat.aggregation import write_summary_file
from llmclozestat.environment_validation import validate_environment_file
from llmclozestat.item_validation import validate_items_file
from llmclozestat.manifest_validation import validate_manifest_file, validate_submission_manifest
from llmclozestat.model_validation import validate_model_file
from llmclozestat.result_validation import validate_results_file
from llmclozestat.submission import PrepareSubmissionError, prepare_submission_package
from llmclozestat.summary_validation import validate_summary_file

app = typer.Typer(help="Cloze-based statistical profiling for LLM outputs.")
validate_app = typer.Typer(help="Validate llmclozestat artifacts.")
app.add_typer(validate_app, name="validate")


@app.command()
def version() -> None:
    from llmclozestat import __version__

    typer.echo(__version__)


@app.command("aggregate")
def aggregate(
    input_path: Path = typer.Option(..., "--input", exists=False, file_okay=True, dir_okay=False),
    out: Path = typer.Option(..., "--out", file_okay=True, dir_okay=False),
) -> None:
    summary = write_summary_file(input_path, out)
    typer.echo(json.dumps({"status": "passed", "summary_path": str(out), "n_trials": summary["n_trials"]}, ensure_ascii=False))


@app.command("prepare-submission")
def prepare_submission(
    submitter_id: str = typer.Option(..., "--submitter-id"),
    run_id: str = typer.Option(..., "--run-id"),
    environment_json: Path = typer.Option(..., "--environment-json", exists=False, file_okay=True, dir_okay=False),
    run_jsonl: Path = typer.Option(..., "--run-jsonl", exists=False, file_okay=True, dir_okay=False),
    summary_json: Path = typer.Option(..., "--summary-json", exists=False, file_okay=True, dir_okay=False),
    out_dir: Path = typer.Option(..., "--out-dir", exists=False, file_okay=False, dir_okay=True),
    summary_md: Path | None = typer.Option(None, "--summary-md", exists=False, file_okay=True, dir_okay=False),
    write_manifest: bool = typer.Option(True, "--write-manifest/--no-write-manifest"),
    overwrite: bool = typer.Option(False, "--overwrite"),
    validate_sources: bool = typer.Option(True, "--validate-sources/--no-validate-sources"),
) -> None:
    try:
        result = prepare_submission_package(
            submitter_id=submitter_id,
            run_id=run_id,
            environment_json=environment_json,
            run_jsonl=run_jsonl,
            summary_json=summary_json,
            summary_md=summary_md,
            out_dir=out_dir,
            write_manifest=write_manifest,
            overwrite=overwrite,
            validate_sources=validate_sources,
        )
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
def validate_manifest(
    input_path: Path = typer.Option(..., "--input", exists=False, file_okay=True, dir_okay=False),
    package_dir: Path | None = typer.Option(None, "--package-dir", exists=False, file_okay=False, dir_okay=True),
    verify_files: bool = typer.Option(False, "--verify-files"),
) -> None:
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
