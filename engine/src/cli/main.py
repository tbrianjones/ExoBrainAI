"""ExoBrain CLI entry point."""

import typer

from src import __version__

app = typer.Typer(
    name="exobrain",
    help="Local-first GraphRAG memory engine",
    no_args_is_help=True,
)


@app.command()
def version():
    """Show version information."""
    typer.echo(f"ExoBrain v{__version__}")


@app.command()
def init():
    """Initialize data directories and pull Ollama models."""
    from src.config import settings

    typer.echo(f"Initializing ExoBrain in {settings.data_dir}...")
    settings.ensure_dirs()
    typer.echo("Created directories:")
    typer.echo(f"  - {settings.raw_dir}")
    typer.echo(f"  - {settings.overlay_dir}")
    typer.echo(f"  - {settings.staged_dir}")
    typer.echo(f"  - {settings.graphrag_dir}")
    typer.echo(f"  - {settings.logs_dir}")
    typer.echo("Done. Add raw documents to the raw/ directory to get started.")


@app.command()
def status():
    """Show ExoBrain status."""
    from src.config import settings

    typer.echo(f"Data directory: {settings.data_dir}")
    typer.echo(f"Ollama host: {settings.ollama_host}")
    typer.echo(f"LLM model: {settings.llm_model}")
    typer.echo(f"Embed model: {settings.embed_model}")

    # Count files
    raw_count = len(list(settings.raw_dir.glob("*.md"))) if settings.raw_dir.exists() else 0
    staged_count = (
        len(list(settings.staged_dir.glob("*.md"))) if settings.staged_dir.exists() else 0
    )

    typer.echo(f"Raw documents: {raw_count}")
    typer.echo(f"Staged documents: {staged_count}")


@app.command()
def doctor():
    """Validate configuration and connectivity."""
    import httpx

    from src.config import settings

    typer.echo("Checking ExoBrain configuration...")
    errors = []

    # Check data directory
    if not settings.data_dir.exists():
        errors.append(f"Data directory does not exist: {settings.data_dir}")
    else:
        typer.echo(f"[OK] Data directory: {settings.data_dir}")

    # Check Ollama connectivity
    try:
        response = httpx.get(f"{settings.ollama_host}/api/tags", timeout=5.0)
        if response.status_code == 200:
            typer.echo(f"[OK] Ollama connection: {settings.ollama_host}")
        else:
            errors.append(f"Ollama returned status {response.status_code}")
    except Exception as e:
        errors.append(f"Cannot connect to Ollama: {e}")

    if errors:
        typer.echo("\nErrors found:")
        for err in errors:
            typer.echo(f"  - {err}")
        raise typer.Exit(1)
    else:
        typer.echo("\nAll checks passed.")


if __name__ == "__main__":
    app()
