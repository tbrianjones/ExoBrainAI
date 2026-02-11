"""GraphRAG adapter: bridges SQLite objects to GraphRAG text input.

Reads objects from the SQLite database and produces text files in the
staged directory, which GraphRAG reads via its input symlink.
"""

import logging
import sqlite3
from pathlib import Path

from src.config import settings
from src.core.bootstrap import BOOTSTRAP_IDS

logger = logging.getLogger(__name__)

# System type IDs to exclude from staging
_SYSTEM_TYPE_IDS = frozenset([
    BOOTSTRAP_IDS["type"],
    BOOTSTRAP_IDS["space"],
    BOOTSTRAP_IDS["tag"],
])


def _build_document(obj: dict, tags: list[str]) -> str:
    """Build a GraphRAG input document from an object and its tags."""
    tag_str = ", ".join(tags) if tags else ""
    lines = [
        f"[DOC_ID: {obj['id']}]",
        "",
        "[METADATA]",
        f"TITLE: {obj['title']}",
        f"TYPE: {obj['type_name']}",
        f"SPACE: {obj['space_name']}",
        f"SUMMARY: {obj['summary'] or ''}",
        f"TAGS: {tag_str}",
        "",
        "[CONTENT]",
        obj["content"] or "(no content)",
    ]
    return "\n".join(lines)


def stage_for_graphrag(conn: sqlite3.Connection) -> dict:
    """Read all non-system objects from SQLite and write them as text files for GraphRAG.

    Args:
        conn: SQLite connection with row_factory = sqlite3.Row.

    Returns:
        Dict with count, staged_dir, and list of staged object summaries.
    """
    staged_dir = settings.staged_dir
    staged_dir.mkdir(parents=True, exist_ok=True)

    # Fetch all non-system objects (exclude type, space, tag objects)
    placeholders = ",".join("?" for _ in _SYSTEM_TYPE_IDS)
    rows = conn.execute(
        f"""SELECT o.id, o.title, o.summary, o.content,
                   t.title as type_name,
                   s.title as space_name
            FROM objects o
            JOIN objects t ON o.type_id = t.id
            JOIN objects s ON o.space_id = s.id
            WHERE o.type_id NOT IN ({placeholders})
              AND o.deleted_at IS NULL
              AND o.purged_at IS NULL
            ORDER BY o.created_at""",
        tuple(_SYSTEM_TYPE_IDS),
    ).fetchall()

    staged_objects = []
    for row in rows:
        obj = dict(row)

        # Fetch tags for this object
        tag_rows = conn.execute(
            "SELECT tag_text FROM object_tags WHERE object_id = ? ORDER BY tag_text",
            (obj["id"],),
        ).fetchall()
        tags = [r["tag_text"] for r in tag_rows]

        # Build and write the document
        doc_text = _build_document(obj, tags)
        doc_path = staged_dir / f"{obj['id']}.txt"
        doc_path.write_text(doc_text, encoding="utf-8")

        staged_objects.append({
            "id": obj["id"],
            "title": obj["title"],
            "type": obj["type_name"],
        })
        logger.debug(f"Staged: {obj['id']} ; {obj['title']}")

    # Ensure the graphrag/input symlink exists
    graphrag_input = settings.graphrag_dir / "input"
    settings.graphrag_dir.mkdir(parents=True, exist_ok=True)
    if not graphrag_input.exists():
        logger.info(f"Creating symlink: {graphrag_input} -> {staged_dir}")
        graphrag_input.symlink_to(staged_dir)

    logger.info(f"Staged {len(staged_objects)} objects to {staged_dir}")

    return {
        "count": len(staged_objects),
        "staged_dir": str(staged_dir),
        "objects": staged_objects,
    }
