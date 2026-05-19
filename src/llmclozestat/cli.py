import typer

app = typer.Typer(help="Cloze-based statistical profiling for LLM outputs.")


@app.command()
def version() -> None:
    """Print package version."""
    from llmclozestat import __version__

    typer.echo(__version__)
