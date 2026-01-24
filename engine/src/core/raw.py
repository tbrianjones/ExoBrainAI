"""Raw document operations."""

from pathlib import Path

from uuid7 import uuid7

from src.config import settings
from src.core.models import RawDocument


def generate_doc_id() -> str:
    """Generate a new UUIDv7 document ID."""
    return str(uuid7())


def list_raw_docs() -> list[str]:
    """List all raw document IDs.

    Returns:
        List of document IDs (filenames without .md extension)
    """
    if not settings.raw_dir.exists():
        return []
    return [p.stem for p in settings.raw_dir.glob("*.md")]


def get_raw_doc(doc_id: str) -> RawDocument | None:
    """Get a raw document by ID.

    Args:
        doc_id: Document ID (UUIDv7)

    Returns:
        RawDocument if found, None otherwise
    """
    path = settings.raw_dir / f"{doc_id}.md"
    if not path.exists():
        return None
    return RawDocument(
        id=doc_id,
        content=path.read_text(encoding="utf-8"),
        path=str(path),
    )


def write_raw_doc(content: str, doc_id: str | None = None) -> RawDocument:
    """Write a new raw document.

    Args:
        content: Document content (markdown)
        doc_id: Optional document ID; generated if not provided

    Returns:
        The created RawDocument
    """
    if doc_id is None:
        doc_id = generate_doc_id()

    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    path = settings.raw_dir / f"{doc_id}.md"
    path.write_text(content, encoding="utf-8")

    return RawDocument(
        id=doc_id,
        content=content,
        path=str(path),
    )


def delete_raw_doc(doc_id: str) -> bool:
    """Delete a raw document.

    Args:
        doc_id: Document ID to delete

    Returns:
        True if deleted, False if not found
    """
    path = settings.raw_dir / f"{doc_id}.md"
    if path.exists():
        path.unlink()
        return True
    return False


def raw_doc_exists(doc_id: str) -> bool:
    """Check if a raw document exists.

    Args:
        doc_id: Document ID to check

    Returns:
        True if exists
    """
    return (settings.raw_dir / f"{doc_id}.md").exists()


def get_raw_doc_path(doc_id: str) -> Path:
    """Get the path for a raw document.

    Args:
        doc_id: Document ID

    Returns:
        Path object (may not exist)
    """
    return settings.raw_dir / f"{doc_id}.md"
