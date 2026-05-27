from __future__ import annotations

import json
from pathlib import Path

import typer

from llmclozestat.item_validation import validate_items_file

app = typer.Typer(help="Cloze-based statistical profiling for LLM outputs.")
validate_app = typer.Typer(help="Validate datasets, results, summaries, manifests, and submissions.")
app.add_typer(validate_app, name="validate")


@app.command()
def version() -> None:
    """Print package version."""
    from llmclozestat import __version__

    typer.echo(__version__)


@validate_app.command("items")
def validate_items(
    dataset: Path = typer.Option(
        ...,
        "--dataset",
        exists=False,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to a JSONL item dataset, such as datasets/smoke_v0/items.jsonl.",
    ),
) -> None:
    """Validate item JSONL structure and item-level cross-field rules."""
    result = validate_items_file(dataset)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.failed:
        raise typer.Exit(code=1)
