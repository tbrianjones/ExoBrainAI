"""Staging logic: merge raw documents with overlay annotations."""

from pathlib import Path

from src.config import settings
from src.core.models import AggregatedOverlay, RawDocument
from src.core.overlay import aggregate_overlays, get_all_doc_overlays
from src.core.raw import get_raw_doc, list_raw_docs


def format_staged_doc(raw: RawDocument, overlay: AggregatedOverlay) -> str:
    """Format a staged document by merging raw content with overlay.

    Args:
        raw: The raw document
        overlay: Aggregated overlay data

    Returns:
        Formatted staged document content
    """
    lines = []

    # Document ID header
    lines.append(f"[DOC_ID: {raw.id}]")
    lines.append("")

    # Overlay section (only if there's overlay data)
    if not overlay.is_empty():
        lines.append("[OVERLAY]")

        if overlay.titles:
            lines.append("TITLES:")
            for title in overlay.titles:
                lines.append(f"- {title}")
            lines.append("")

        if overlay.summaries:
            lines.append("SUMMARIES:")
            for summary in overlay.summaries:
                lines.append(f"- {summary}")
            lines.append("")

        if overlay.tags:
            lines.append("TAGS:")
            for tag in overlay.tags:
                conf = f" (confidence={tag.confidence})" if tag.confidence is not None else ""
                note = f" ; {tag.note}" if tag.note else ""
                lines.append(f"- {tag.tag}{conf}{note}")
            lines.append("")

        if overlay.entities:
            lines.append("ENTITIES:")
            for entity in overlay.entities:
                conf = (
                    f" (confidence={entity.confidence})"
                    if entity.confidence is not None
                    else ""
                )
                note = f" ; {entity.note}" if entity.note else ""
                lines.append(f"- {entity.name}{conf}{note}")
            lines.append("")

        if overlay.links:
            lines.append("LINKS:")
            for link in overlay.links:
                conf = f" (confidence={link.confidence})" if link.confidence is not None else ""
                note = f" ; {link.note}" if link.note else ""
                lines.append(f"- {link.doc_id}{conf}{note}")
            lines.append("")

    # Raw content section
    lines.append("[RAW]")
    lines.append(raw.content)

    return "\n".join(lines)


def stage_doc(doc_id: str, days: int | None = None) -> Path | None:
    """Stage a single document.

    Args:
        doc_id: Document ID to stage
        days: Overlay aggregation window in days

    Returns:
        Path to staged file, or None if raw doc not found
    """
    raw = get_raw_doc(doc_id)
    if raw is None:
        return None

    overlay = aggregate_overlays(doc_id, days)
    content = format_staged_doc(raw, overlay)

    settings.staged_dir.mkdir(parents=True, exist_ok=True)
    path = settings.staged_dir / f"{doc_id}.txt"
    path.write_text(content, encoding="utf-8")

    return path


def stage_all(days: int | None = None) -> list[Path]:
    """Stage all raw documents.

    Args:
        days: Overlay aggregation window in days

    Returns:
        List of paths to staged files
    """
    # Get all overlays upfront for efficiency
    all_overlays = get_all_doc_overlays(days)

    staged_paths = []
    for doc_id in list_raw_docs():
        raw = get_raw_doc(doc_id)
        if raw is None:
            continue

        overlay = all_overlays.get(doc_id, AggregatedOverlay(doc_id=doc_id))
        content = format_staged_doc(raw, overlay)

        settings.staged_dir.mkdir(parents=True, exist_ok=True)
        path = settings.staged_dir / f"{doc_id}.txt"
        path.write_text(content, encoding="utf-8")
        staged_paths.append(path)

    return staged_paths


def get_staged_doc(doc_id: str) -> str | None:
    """Read a staged document.

    Args:
        doc_id: Document ID

    Returns:
        Staged document content, or None if not found
    """
    path = settings.staged_dir / f"{doc_id}.txt"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def list_staged_docs() -> list[str]:
    """List all staged document IDs.

    Returns:
        List of document IDs
    """
    if not settings.staged_dir.exists():
        return []
    return [p.stem for p in settings.staged_dir.glob("*.txt")]


def delete_staged_doc(doc_id: str) -> bool:
    """Delete a staged document.

    Args:
        doc_id: Document ID

    Returns:
        True if deleted, False if not found
    """
    path = settings.staged_dir / f"{doc_id}.txt"
    if path.exists():
        path.unlink()
        return True
    return False


def clean_staged() -> int:
    """Remove all staged documents.

    Returns:
        Number of files deleted
    """
    if not settings.staged_dir.exists():
        return 0

    count = 0
    for path in settings.staged_dir.glob("*.txt"):
        path.unlink()
        count += 1
    return count
