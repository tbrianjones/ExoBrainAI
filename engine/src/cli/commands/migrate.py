"""Migration from ideas/ folder to ExoBrain."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from src.config import settings
from src.core import OverlayRecord, TagItem, append_overlay, generate_doc_id, write_raw_doc

app = typer.Typer()


def extract_metadata_from_readme(readme_path: Path) -> dict:
    """Extract metadata from an idea space README.md.

    Looks for:
    - Title (first # heading)
    - Origin section
    - Open Questions section
    """
    if not readme_path.exists():
        return {}

    content = readme_path.read_text(encoding="utf-8")
    metadata = {}

    # Extract title
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()

    # Extract idea number from path
    idea_dir = readme_path.parent.name
    if idea_dir.startswith("0"):
        num_match = re.match(r"(\d+)-(.+)", idea_dir)
        if num_match:
            metadata["idea_number"] = num_match.group(1)
            metadata["idea_slug"] = num_match.group(2)

    return metadata


def migrate_file(
    source_path: Path,
    dry_run: bool = True,
    idea_metadata: dict | None = None,
) -> dict:
    """Migrate a single file to ExoBrain.

    Args:
        source_path: Path to the source file
        dry_run: If True, don't write anything
        idea_metadata: Optional metadata from the idea space README

    Returns:
        Migration result with doc_id and status
    """
    if not source_path.exists():
        return {"status": "error", "error": f"File not found: {source_path}"}

    content = source_path.read_text(encoding="utf-8")

    # Generate document ID
    doc_id = generate_doc_id()

    # Determine file type and extract metadata
    file_type = "unknown"
    title = None
    tags = []

    if "transcripts" in str(source_path):
        file_type = "transcript"
        tags.append(TagItem(tag="transcript", confidence=1.0))

        # Try to extract date and topic from filename
        # Format: YYYY-MM-DD-topic-suffix.md
        stem = source_path.stem
        date_match = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)", stem)
        if date_match:
            date_str = date_match.group(1)
            topic = date_match.group(2).replace("-", " ")
            # Remove common suffixes
            for suffix in [" raw", " summary", " exact"]:
                topic = topic.replace(suffix, "")
            title = f"Transcript: {topic.title()} ({date_str})"

    elif "views" in str(source_path):
        file_type = "view"
        tags.append(TagItem(tag="view", confidence=1.0))
        title = f"View: {source_path.stem.replace('-', ' ').title()}"

    elif source_path.name == "README.md":
        file_type = "readme"
        tags.append(TagItem(tag="idea-readme", confidence=1.0))
        if idea_metadata and idea_metadata.get("title"):
            title = idea_metadata["title"]

    # Add idea space tag if available
    if idea_metadata:
        if idea_metadata.get("idea_slug"):
            tags.append(TagItem(tag=f"idea:{idea_metadata['idea_slug']}", confidence=1.0))
        if idea_metadata.get("idea_number"):
            tags.append(TagItem(tag=f"idea-{idea_metadata['idea_number']}", confidence=0.9))

    result = {
        "status": "success" if not dry_run else "dry-run",
        "source": str(source_path),
        "doc_id": doc_id,
        "file_type": file_type,
        "title": title,
        "tags": [t.tag for t in tags],
        "content_length": len(content),
    }

    if dry_run:
        return result

    # Write raw document
    doc = write_raw_doc(content, doc_id)

    # Create overlay record with extracted metadata
    overlay = OverlayRecord(
        doc_id=doc_id,
        source="import",
        title=title,
        tags=tags if tags else None,
        extra={
            "migrated_from": str(source_path),
            "migrated_at": datetime.now().isoformat(),
            "file_type": file_type,
        },
    )
    append_overlay(overlay)

    result["raw_path"] = str(doc.path)
    return result


def migrate_idea_space(
    idea_path: Path,
    dry_run: bool = True,
    transcripts_only: bool = False,
) -> list[dict]:
    """Migrate an entire idea space to ExoBrain.

    Args:
        idea_path: Path to the idea space folder
        dry_run: If True, don't write anything
        transcripts_only: If True, only migrate transcripts

    Returns:
        List of migration results
    """
    if not idea_path.is_dir():
        return [{"status": "error", "error": f"Not a directory: {idea_path}"}]

    results = []

    # Extract metadata from README
    readme_path = idea_path / "README.md"
    idea_metadata = extract_metadata_from_readme(readme_path)

    # Migrate README (unless transcripts_only)
    if not transcripts_only and readme_path.exists():
        results.append(migrate_file(readme_path, dry_run, idea_metadata))

    # Migrate transcripts
    transcripts_dir = idea_path / "transcripts"
    if transcripts_dir.exists():
        for f in sorted(transcripts_dir.glob("*.md")):
            results.append(migrate_file(f, dry_run, idea_metadata))

    # Migrate views (unless transcripts_only)
    if not transcripts_only:
        views_dir = idea_path / "views"
        if views_dir.exists():
            for f in sorted(views_dir.glob("*.md")):
                results.append(migrate_file(f, dry_run, idea_metadata))

    return results


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
        "./ideas",
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
    source_path = Path(source)

    if dry_run:
        typer.echo("DRY RUN MODE (use --execute to actually migrate)\n")
    else:
        # Ensure directories exist
        settings.ensure_dirs()

    results = []

    if source == "all":
        # Migrate all idea spaces
        ideas_path = Path(ideas_root)
        if not ideas_path.exists():
            typer.echo(f"Error: Ideas root not found: {ideas_path}", err=True)
            raise typer.Exit(1)

        for idea_dir in sorted(ideas_path.iterdir()):
            if idea_dir.is_dir() and idea_dir.name.startswith("0"):
                typer.echo(f"Processing: {idea_dir.name}")
                results.extend(migrate_idea_space(idea_dir, dry_run, transcripts_only))

    elif source_path.is_file():
        # Migrate a single file
        # Try to find parent idea space for metadata
        idea_metadata = None
        for parent in source_path.parents:
            readme = parent / "README.md"
            if readme.exists() and "ideas" in str(parent):
                idea_metadata = extract_metadata_from_readme(readme)
                break
        results.append(migrate_file(source_path, dry_run, idea_metadata))

    elif source_path.is_dir():
        # Migrate an idea space
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
