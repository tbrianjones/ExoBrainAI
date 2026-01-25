"""ExoBrain CLI entry point."""

from typing import Optional

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
    import httpx

    from src.config import settings
    from src.graphrag import write_graphrag_settings

    typer.echo(f"Initializing ExoBrain in {settings.data_dir}...")
    settings.ensure_dirs()
    typer.echo("Created directories:")
    typer.echo(f"  - {settings.raw_dir}")
    typer.echo(f"  - {settings.overlay_dir}")
    typer.echo(f"  - {settings.staged_dir}")
    typer.echo(f"  - {settings.graphrag_dir}")
    typer.echo(f"  - {settings.logs_dir}")

    # Create symlink: graphrag/input -> staged/ (GraphRAG expects relative paths)
    input_link = settings.graphrag_dir / "input"
    if not input_link.exists():
        input_link.symlink_to(settings.staged_dir)
        typer.echo(f"  - {input_link} -> {settings.staged_dir}")
    else:
        typer.echo(f"  - {input_link} (symlink exists)")

    # Initialize GraphRAG settings
    settings_path = write_graphrag_settings()
    typer.echo(f"  - {settings_path}")

    # Try to pull Ollama models
    typer.echo(f"\nOllama mode: {settings.ollama_mode}")
    typer.echo(f"Ollama host: {settings.ollama_host}")

    # Check if Ollama is reachable
    try:
        httpx.get(f"{settings.ollama_host}/api/tags", timeout=5.0)
        ollama_available = True
    except Exception:
        ollama_available = False

    if not ollama_available:
        if settings.ollama_mode == "native":
            typer.echo("\n[WARN] Native Ollama is not running.")
            typer.echo("       Run: ./scripts/setup-native-ollama.sh")
            typer.echo("\n       Or start it manually:")
            typer.echo("         brew install ollama")
            typer.echo("         ollama serve")
        else:
            typer.echo("\n[WARN] Docker Ollama is not running.")
            typer.echo("       Start with: docker compose --profile docker up -d")
    else:
        typer.echo(f"\nPulling Ollama models...")
        for model in [settings.llm_model, settings.embed_model]:
            try:
                typer.echo(f"  Pulling {model}...")
                response = httpx.post(
                    f"{settings.ollama_host}/api/pull",
                    json={"name": model},
                    timeout=600.0,
                )
                if response.status_code == 200:
                    typer.echo(f"  [OK] {model}")
                else:
                    typer.echo(f"  [WARN] Could not pull {model}: {response.status_code}")
            except Exception as e:
                typer.echo(f"  [WARN] Could not pull {model}: {e}")

    typer.echo("\nDone. Add raw documents to the raw/ directory to get started.")


@app.command()
def status():
    """Show ExoBrain status."""
    from src.config import settings
    from src.graphrag import get_index_status

    typer.echo(f"Data directory: {settings.data_dir}")
    typer.echo(f"Ollama mode: {settings.ollama_mode}")
    typer.echo(f"Ollama host: {settings.ollama_host}")
    typer.echo(f"LLM model: {settings.llm_model}")
    typer.echo(f"Embed model: {settings.embed_model}")

    # Count files
    raw_count = len(list(settings.raw_dir.glob("*.md"))) if settings.raw_dir.exists() else 0
    staged_count = (
        len(list(settings.staged_dir.glob("*.txt"))) if settings.staged_dir.exists() else 0
    )

    typer.echo(f"\nDocuments:")
    typer.echo(f"  Raw: {raw_count}")
    typer.echo(f"  Staged: {staged_count}")

    # Index status
    idx_status = get_index_status()
    typer.echo(f"\nIndex:")
    typer.echo(f"  Indexed: {idx_status.get('indexed', False)}")
    if idx_status.get("timestamp"):
        typer.echo(f"  Last build: {idx_status['timestamp']}")


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

    # Check subdirectories
    for name, path in [
        ("raw", settings.raw_dir),
        ("overlay", settings.overlay_dir),
        ("staged", settings.staged_dir),
        ("graphrag", settings.graphrag_dir),
    ]:
        if path.exists():
            typer.echo(f"[OK] {name}: {path}")
        else:
            typer.echo(f"[WARN] {name} does not exist: {path}")

    # Check Ollama connectivity
    typer.echo(f"\nOllama mode: {settings.ollama_mode}")
    try:
        response = httpx.get(f"{settings.ollama_host}/api/tags", timeout=5.0)
        if response.status_code == 200:
            typer.echo(f"[OK] Ollama connection: {settings.ollama_host}")
            # Check for required models
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            for model in [settings.llm_model, settings.embed_model]:
                # Model names might include :latest suffix
                if any(model in m or m.startswith(model.split(":")[0]) for m in models):
                    typer.echo(f"[OK] Model available: {model}")
                else:
                    typer.echo(f"[WARN] Model not found: {model}")
        else:
            errors.append(f"Ollama returned status {response.status_code}")
    except Exception as e:
        if settings.ollama_mode == "native":
            errors.append(
                f"Cannot connect to native Ollama at {settings.ollama_host}.\n"
                "    Run: ./scripts/setup-native-ollama.sh"
            )
        else:
            errors.append(f"Cannot connect to Ollama: {e}")

    if errors:
        typer.echo("\nErrors found:")
        for err in errors:
            typer.echo(f"  - {err}")
        raise typer.Exit(1)
    else:
        typer.echo("\nAll checks passed.")


@app.command()
def stage(
    doc_id: Optional[str] = typer.Option(None, "--doc", "-d", help="Stage a specific document"),
    all_docs: bool = typer.Option(False, "--all", "-a", help="Stage all documents"),
):
    """Stage documents for indexing."""
    from src.core import list_raw_docs, stage_all, stage_doc

    if doc_id:
        typer.echo(f"Staging document: {doc_id}")
        result = stage_doc(doc_id)
        if result:
            typer.echo(f"Staged: {result}")
        else:
            typer.echo(f"Error: Document not found: {doc_id}", err=True)
            raise typer.Exit(1)
    elif all_docs:
        typer.echo("Staging all documents...")
        results = stage_all()
        typer.echo(f"Staged {len(results)} documents")
    else:
        typer.echo("Specify --doc <id> or --all")
        raise typer.Exit(1)


@app.command()
def index(
    incremental: bool = typer.Option(
        True, "--incremental/--full", help="Incremental or full indexing"
    ),
    fast: bool = typer.Option(
        False, "--fast", "-f", help="Use NLP-based extraction (faster, less accurate)"
    ),
):
    """Run GraphRAG indexing on staged documents.

    Use --fast for much faster indexing using NLP instead of LLM for entity extraction.
    Standard mode uses LLM for higher quality but is significantly slower.
    """
    from src.graphrag import run_index

    method = "fast" if fast else "standard"
    mode = "incremental" if incremental else "full"
    typer.echo(f"Running {method} {mode} index...")

    try:
        result = run_index(incremental=incremental, fast=fast)
        typer.echo(f"Status: {result['status']}")
        if result.get("documents"):
            typer.echo(f"Documents: {result['documents']}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def rebuild():
    """Full rebuild of the GraphRAG index."""
    from src.graphrag import rebuild_index

    typer.echo("Rebuilding index from scratch...")
    typer.echo("This may take a while for large document sets.")

    try:
        result = rebuild_index()
        typer.echo(f"Status: {result['status']}")
        if result.get("documents"):
            typer.echo(f"Documents: {result['documents']}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def query(
    q: str = typer.Argument(..., help="The query string"),
    mode: str = typer.Option("global", "--mode", "-m", help="Query mode: global or local"),
):
    """Query the GraphRAG index."""
    from src.graphrag import QueryMode, query as run_query

    try:
        query_mode = QueryMode(mode.lower())
    except ValueError:
        typer.echo(f"Invalid mode: {mode}. Use 'global' or 'local'.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Running {query_mode.value} query...")

    try:
        result = run_query(q, query_mode)
        typer.echo("\n" + "=" * 60)
        typer.echo(result["response"])
        typer.echo("=" * 60)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def capture(
    content: Optional[str] = typer.Argument(None, help="Content to capture (or use stdin)"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Optional title"),
):
    """Capture a new raw document."""
    import sys

    from src.core import OverlayRecord, append_overlay, write_raw_doc

    # Read from stdin if no content provided
    if content is None:
        if sys.stdin.isatty():
            typer.echo("Enter content (Ctrl+D to finish):")
        content = sys.stdin.read()

    if not content.strip():
        typer.echo("Error: No content provided", err=True)
        raise typer.Exit(1)

    # Write raw document
    doc = write_raw_doc(content)
    typer.echo(f"Created: {doc.id}")

    # Add title overlay if provided
    if title:
        record = OverlayRecord(
            doc_id=doc.id,
            source="human",
            title=title,
        )
        append_overlay(record)
        typer.echo(f"Added title: {title}")


@app.command()
def annotate(
    doc_id: str = typer.Argument(..., help="Document ID to annotate"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Set title"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="Set summary"),
    tag: Optional[list[str]] = typer.Option(None, "--tag", help="Add tag (repeatable)"),
    entity: Optional[list[str]] = typer.Option(None, "--entity", "-e", help="Add entity (repeatable)"),
    link: Optional[list[str]] = typer.Option(
        None, "--link", "-l", help="Link to another doc ID (repeatable)"
    ),
    link_note: Optional[str] = typer.Option(
        None, "--link-note", help="Note for the link (use with single --link)"
    ),
    source: str = typer.Option("human", "--source", help="Source: human, ai, system"),
):
    """Add annotations to an existing document.

    Examples:
        # Add a title
        exobrain annotate <doc-id> --title "My Document"

        # Add tags
        exobrain annotate <doc-id> --tag project-x --tag important

        # Link two documents
        exobrain annotate <doc-id> --link <other-doc-id> --link-note "Related discussion"

        # Add multiple annotations at once
        exobrain annotate <doc-id> --title "Notes" --tag meeting --entity "John Smith"
    """
    from src.core import (
        EntityItem,
        LinkItem,
        OverlayRecord,
        TagItem,
        append_overlay,
        raw_doc_exists,
    )

    # Verify document exists
    if not raw_doc_exists(doc_id):
        typer.echo(f"Error: Document not found: {doc_id}", err=True)
        raise typer.Exit(1)

    # Validate source
    if source not in ("human", "ai", "system", "import"):
        typer.echo(f"Error: Invalid source: {source}", err=True)
        raise typer.Exit(1)

    # Check if any annotations provided
    if not any([title, summary, tag, entity, link]):
        typer.echo("Error: No annotations provided. Use --title, --tag, --entity, --link, or --summary")
        raise typer.Exit(1)

    # Build overlay record
    tags = [TagItem(tag=t) for t in (tag or [])]
    entities = [EntityItem(name=e) for e in (entity or [])]
    links = []
    if link:
        for i, l in enumerate(link):
            note = link_note if (len(link) == 1 and link_note) else None
            links.append(LinkItem(doc_id=l, note=note))

    record = OverlayRecord(
        doc_id=doc_id,
        source=source,
        title=title,
        summary=summary,
        tags=tags if tags else None,
        entities=entities if entities else None,
        links=links if links else None,
    )

    append_overlay(record)

    # Report what was added
    typer.echo(f"Annotated: {doc_id}")
    if title:
        typer.echo(f"  Title: {title}")
    if summary:
        typer.echo(f"  Summary: {summary[:50]}..." if len(summary) > 50 else f"  Summary: {summary}")
    if tags:
        typer.echo(f"  Tags: {', '.join(t.tag for t in tags)}")
    if entities:
        typer.echo(f"  Entities: {', '.join(e.name for e in entities)}")
    if links:
        for lnk in links:
            if lnk.note:
                typer.echo(f"  Link: {lnk.doc_id} ; {lnk.note}")
            else:
                typer.echo(f"  Link: {lnk.doc_id}")


# Import and add migrate subcommand
from src.cli.commands.migrate import migrate as migrate_cmd


@app.command()
def migrate(
    source: str = typer.Argument(
        ...,
        help="Source path: file, idea folder, or 'all' for entire ideas/ directory",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Dry run shows what would be migrated without writing",
    ),
    transcripts_only: bool = typer.Option(
        False,
        "--transcripts-only",
        "-t",
        help="Only migrate transcript files",
    ),
    ideas_root: str = typer.Option(
        "/ideas",
        "--ideas-root",
        help="Root directory for ideas/ (for 'all' migration)",
    ),
):
    """Migrate content from ideas/ folder to ExoBrain.

    Examples:
        # Dry run on a single file
        exobrain migrate ideas/0001-foo/transcripts/2026-01-07-bar.md

        # Dry run on an idea space
        exobrain migrate ideas/0001-foo

        # Actually migrate (use --execute)
        exobrain migrate ideas/0001-foo/transcripts/2026-01-07-bar.md --execute

        # Migrate only transcripts from an idea space
        exobrain migrate ideas/0001-foo --transcripts-only --execute
    """
    # Call the actual migrate function
    from src.cli.commands.migrate import migrate as do_migrate

    # We need to invoke it with the same args
    # Since we're wrapping the typer command, just call the function directly
    from pathlib import Path

    from src.cli.commands.migrate import migrate_file, migrate_idea_space
    from src.config import settings

    source_path = Path(source)

    if dry_run:
        typer.echo("DRY RUN MODE (use --execute to actually migrate)\n")
    else:
        settings.ensure_dirs()

    results = []

    if source == "all":
        ideas_path = Path(ideas_root)
        if not ideas_path.exists():
            typer.echo(f"Error: Ideas root not found: {ideas_path}", err=True)
            raise typer.Exit(1)

        for idea_dir in sorted(ideas_path.iterdir()):
            if idea_dir.is_dir() and idea_dir.name.startswith("0"):
                typer.echo(f"Processing: {idea_dir.name}")
                results.extend(migrate_idea_space(idea_dir, dry_run, transcripts_only))

    elif source_path.is_file():
        from src.cli.commands.migrate import extract_metadata_from_readme

        idea_metadata = None
        for parent in source_path.parents:
            readme = parent / "README.md"
            if readme.exists() and "ideas" in str(parent):
                idea_metadata = extract_metadata_from_readme(readme)
                break
        results.append(migrate_file(source_path, dry_run, idea_metadata))

    elif source_path.is_dir():
        results.extend(migrate_idea_space(source_path, dry_run, transcripts_only))

    else:
        typer.echo(f"Error: Source not found: {source}", err=True)
        raise typer.Exit(1)

    # Print results
    typer.echo("\nMigration Results:")
    typer.echo("-" * 60)

    success_count = 0
    for r in results:
        status = r.get("status", "unknown")
        source_file = r.get("source", "unknown")

        if status in ("success", "dry-run"):
            success_count += 1
            typer.echo(f"[{status.upper()}] {Path(source_file).name}")
            typer.echo(f"  ID: {r.get('doc_id')}")
            typer.echo(f"  Type: {r.get('file_type')}")
            if r.get("title"):
                typer.echo(f"  Title: {r['title']}")
            if r.get("tags"):
                typer.echo(f"  Tags: {', '.join(r['tags'])}")
        else:
            typer.echo(f"[ERROR] {source_file}: {r.get('error')}")

    typer.echo("-" * 60)
    typer.echo(f"Total: {len(results)} files, {success_count} successful")

    if dry_run and success_count > 0:
        typer.echo("\nTo execute this migration, add --execute flag")


if __name__ == "__main__":
    app()
