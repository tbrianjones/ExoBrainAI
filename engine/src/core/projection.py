"""Projection layer for ExoBrain.

Projects SQLite objects as markdown files with YAML frontmatter for AI-readable access.
"""

from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

import yaml

from src.config import settings
from src.core.bootstrap import BOOTSTRAP_IDS
from src.core.repository import ObjectRepo, TagRepo


class ProjectionResult(NamedTuple):
    """Result of a projection operation."""

    success: bool
    message: str
    path: Path | None = None


class SyncResult(NamedTuple):
    """Result of syncing a file back to the database."""

    success: bool
    message: str
    object_id: str | None = None


@dataclass
class ObjectScore:
    """An object with its computed projection score."""

    id: str
    title: str
    space_name: str
    score: float
    projection_override: str | None


def _slugify(text: str, max_length: int = 50) -> str:
    """Convert text to a URL-friendly slug."""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    # Remove special characters except hyphens and alphanumeric
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    # Replace multiple spaces/hyphens with single hyphen
    slug = re.sub(r"[-\s]+", "-", slug)
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    # Truncate to max length at word boundary
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]
    return slug or "untitled"


def _parse_iso_datetime(dt_str: str | None) -> datetime | None:
    """Parse an ISO datetime string to a datetime object."""
    if not dt_str:
        return None
    try:
        # Handle both formats: with and without microseconds
        if "." in dt_str:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        else:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def calculate_scores(conn: sqlite3.Connection) -> list[ObjectScore]:
    """Calculate projection scores for all non-bootstrap objects.

    Uses updated_at as proxy for access (Phase 1).
    Score = recency_weight * exp(-days_since_update / half_life)

    Returns list of ObjectScore sorted by score descending.
    """
    now = datetime.now(timezone.utc)

    # Get all non-bootstrap objects with their metadata
    bootstrap_type_ids = [
        BOOTSTRAP_IDS["type"],
        BOOTSTRAP_IDS["space"],
        BOOTSTRAP_IDS["tag"],
    ]
    placeholders = ",".join("?" for _ in bootstrap_type_ids)

    rows = conn.execute(
        f"""SELECT o.id, o.title, o.updated_at, o.projection_override,
                   s.title as space_name
            FROM objects o
            JOIN objects s ON o.space_id = s.id
            WHERE o.type_id NOT IN ({placeholders})
            ORDER BY o.updated_at DESC""",
        bootstrap_type_ids,
    ).fetchall()

    scores = []
    for row in rows:
        updated_at = _parse_iso_datetime(row["updated_at"])
        if updated_at:
            days_since = (now - updated_at).total_seconds() / 86400
        else:
            days_since = 365  # Default to old if no timestamp

        # Simple exponential decay based on recency
        # Phase 1: only recency matters (no access log yet)
        recency_score = math.exp(-days_since / settings.projection_halflife_days)
        score = settings.projection_recency_weight * recency_score

        scores.append(
            ObjectScore(
                id=row["id"],
                title=row["title"],
                space_name=row["space_name"],
                score=score,
                projection_override=row["projection_override"],
            )
        )

    # Sort by score descending
    scores.sort(key=lambda x: x.score, reverse=True)
    return scores


def get_projection_candidates(
    conn: sqlite3.Connection, limit: int | None = None
) -> list[ObjectScore]:
    """Get objects that should be projected, respecting overrides and limit.

    Returns:
        List of objects to project, with 'always' overrides first,
        then top-scoring objects up to limit, excluding 'never' overrides.
    """
    if limit is None:
        limit = settings.projection_hot_limit

    all_scores = calculate_scores(conn)

    # Separate by override status
    always_project = [s for s in all_scores if s.projection_override == "always"]
    never_project_ids = {s.id for s in all_scores if s.projection_override == "never"}
    auto_project = [
        s for s in all_scores if s.projection_override is None and s.id not in never_project_ids
    ]

    # Take always-project objects plus top auto-project up to limit
    remaining_slots = max(0, limit - len(always_project))
    candidates = always_project + auto_project[:remaining_slots]

    return candidates


def _get_space_path(conn: sqlite3.Connection, space_id: str) -> str:
    """Get the full path for a space (e.g., 'work/exobrain').

    Uses the space's summary field which contains the path.
    """
    row = conn.execute(
        "SELECT title, summary FROM objects WHERE id = ?", (space_id,)
    ).fetchone()
    if row:
        # Summary contains the path (e.g., "work/exobrain"), title is display name
        return row["summary"] or row["title"]
    return "inbox"


def project_object(conn: sqlite3.Connection, obj_id: str) -> ProjectionResult:
    """Project a single object to a markdown file.

    Creates file at: projected/{space-path}/{title-slug}-{id[:12]}.md
    """
    obj_repo = ObjectRepo(conn)
    tag_repo = TagRepo(conn)

    obj = obj_repo.get(obj_id)
    if not obj:
        return ProjectionResult(False, f"Object not found: {obj_id}")

    # Get space path
    space_path = _get_space_path(conn, obj["space_id"])

    # Get tags
    tags = tag_repo.list_for_object(obj_id)

    # Build frontmatter
    frontmatter = {
        "id": obj["id"],
        "type": obj["type_name"],
        "space": space_path,
        "title": obj["title"],
        "summary": obj["summary"],
        "tags": tags if tags else None,
        "created": obj["created_at"],
        "updated": obj["updated_at"],
        "projection_override": obj.get("projection_override"),
    }

    # Remove None values for cleaner output
    frontmatter = {k: v for k, v in frontmatter.items() if v is not None}

    # Build file content
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
    content_body = obj.get("content") or ""
    file_content = f"---\n{yaml_str}---\n\n{content_body}"

    # Compute file path
    slug = _slugify(obj["title"])
    id_suffix = obj["id"][:12]
    filename = f"{slug}-{id_suffix}.md"

    # Create directory structure
    dir_path = settings.projected_dir / space_path
    dir_path.mkdir(parents=True, exist_ok=True)

    file_path = dir_path / filename
    file_path.write_text(file_content, encoding="utf-8")

    return ProjectionResult(True, f"Projected to {file_path}", file_path)


def deproject_object(conn: sqlite3.Connection, obj_id: str) -> ProjectionResult:
    """Remove a projected file for an object.

    Searches for files matching the ID suffix pattern.
    """
    obj_repo = ObjectRepo(conn)
    obj = obj_repo.get(obj_id)
    if not obj:
        return ProjectionResult(False, f"Object not found: {obj_id}")

    space_path = _get_space_path(conn, obj["space_id"])
    id_suffix = obj_id[:12]

    # Find and delete the projected file
    dir_path = settings.projected_dir / space_path
    if dir_path.exists():
        for file_path in dir_path.glob(f"*-{id_suffix}.md"):
            file_path.unlink()
            return ProjectionResult(True, f"Deprojected {file_path}", file_path)

    return ProjectionResult(False, f"No projected file found for {obj_id}")


def generate_claude_md(conn: sqlite3.Connection, space_path: str) -> str:
    """Generate CLAUDE.md content for a space directory.

    Returns markdown string with object index and instructions.
    """
    # Find all objects in this space
    rows = conn.execute(
        """SELECT o.id, o.title, t.title as type_name,
                  GROUP_CONCAT(ot.tag_text, ', ') as tags
           FROM objects o
           JOIN objects t ON o.type_id = t.id
           JOIN objects s ON o.space_id = s.id
           LEFT JOIN object_tags ot ON o.id = ot.object_id
           WHERE s.summary = ? OR s.title = ?
           GROUP BY o.id
           ORDER BY o.updated_at DESC""",
        (space_path, space_path),
    ).fetchall()

    lines = [
        f"# {space_path}",
        "",
        "This directory contains projected ExoBrain objects.",
        "",
        "## Objects",
        "",
        "| ID (prefix) | Type | Title | Tags |",
        "|-------------|------|-------|------|",
    ]

    for row in rows:
        id_prefix = row["id"][:12]
        tags = row["tags"] or ""
        lines.append(f"| {id_prefix} | {row['type_name']} | {row['title']} | {tags} |")

    lines.extend([
        "",
        "## Usage",
        "",
        "- **Read**: Open any `.md` file to view object content",
        "- **Edit**: Modify the content body (below the `---` frontmatter)",
        "- **Sync**: Edits are automatically synced back to ExoBrain",
        "",
        "## Notes",
        "",
        "- `id` and `space` fields are immutable; edit via CLI",
        "- Files are regenerated on `exobrain project`",
        "",
    ])

    return "\n".join(lines)


def _write_claude_md_for_space(conn: sqlite3.Connection, space_path: str) -> None:
    """Write CLAUDE.md file for a space directory."""
    content = generate_claude_md(conn, space_path)
    dir_path = settings.projected_dir / space_path
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "CLAUDE.md").write_text(content, encoding="utf-8")


def _generate_root_claude_md(conn: sqlite3.Connection, projected_spaces: set[str]) -> str:
    """Generate root CLAUDE.md with space overview."""
    lines = [
        "# ExoBrain Projected Objects",
        "",
        "This directory contains AI-readable projections of ExoBrain objects.",
        "",
        "## Spaces",
        "",
    ]

    for space in sorted(projected_spaces):
        lines.append(f"- [{space}]({space}/)")

    lines.extend([
        "",
        "## Usage",
        "",
        "- Browse directories by space",
        "- Grep for content: `rg 'keyword' projected/`",
        "- Edit files directly; changes sync to ExoBrain",
        "",
        "## Commands",
        "",
        "- `exobrain project` ; Refresh projections",
        "- `exobrain project --cleanup` ; Remove stale projections",
        "- `exobrain tier status` ; View projection statistics",
        "",
    ])

    return "\n".join(lines)


def run_projection_cycle(
    conn: sqlite3.Connection, cleanup: bool = False, dry_run: bool = False
) -> dict:
    """Run a full projection cycle.

    Args:
        cleanup: If True, also deproject objects that no longer qualify
        dry_run: If True, only report what would be done

    Returns:
        Dict with projection statistics
    """
    candidates = get_projection_candidates(conn)
    candidate_ids = {c.id for c in candidates}

    # Track what we do
    projected_count = 0
    deprojected_count = 0
    projected_spaces: set[str] = set()
    errors: list[str] = []

    # Project candidates
    for candidate in candidates:
        if dry_run:
            projected_count += 1
            space_path = _get_space_path(conn,
                conn.execute("SELECT space_id FROM objects WHERE id = ?", (candidate.id,)).fetchone()["space_id"]
            )
            projected_spaces.add(space_path)
        else:
            result = project_object(conn, candidate.id)
            if result.success:
                projected_count += 1
                # Extract space from path
                if result.path:
                    rel_path = result.path.relative_to(settings.projected_dir)
                    space_path = str(rel_path.parent)
                    projected_spaces.add(space_path)
            else:
                errors.append(result.message)

    # Cleanup: find and remove projected files for non-candidates
    if cleanup and not dry_run:
        # Build set of candidate full IDs for reliable lookup
        candidate_ids = {c.id for c in candidates}

        # Find all currently projected files
        for md_file in settings.projected_dir.rglob("*.md"):
            if md_file.name == "CLAUDE.md":
                continue

            # Read the file and extract ID from frontmatter
            try:
                content = md_file.read_text(encoding="utf-8")
                if not content.startswith("---"):
                    continue
                parts = content.split("---", 2)
                if len(parts) < 2:
                    continue
                frontmatter = yaml.safe_load(parts[1])
                if not frontmatter or "id" not in frontmatter:
                    continue
                file_id = frontmatter["id"]
                if file_id not in candidate_ids:
                    md_file.unlink()
                    deprojected_count += 1
            except Exception as e:
                # Log error but continue processing other files
                errors.append(f"Failed to process {md_file.name}: {e}")

    # Generate CLAUDE.md files
    if not dry_run:
        for space_path in projected_spaces:
            _write_claude_md_for_space(conn, space_path)

        # Root CLAUDE.md
        root_content = _generate_root_claude_md(conn, projected_spaces)
        (settings.projected_dir / "CLAUDE.md").write_text(root_content, encoding="utf-8")

    return {
        "projected": projected_count,
        "deprojected": deprojected_count,
        "spaces": list(projected_spaces),
        "errors": errors,
        "dry_run": dry_run,
    }


def sync_from_file(conn: sqlite3.Connection, file_path: Path) -> SyncResult:
    """Sync changes from a projected file back to the database.

    Parses YAML frontmatter and body, validates, and updates SQLite.
    """
    if not file_path.exists():
        return SyncResult(False, f"File not found: {file_path}")

    if file_path.name == "CLAUDE.md":
        return SyncResult(False, "CLAUDE.md files are auto-generated, not synced")

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return SyncResult(False, f"Failed to read file: {e}")

    # Parse frontmatter
    if not content.startswith("---"):
        return SyncResult(False, "File does not have YAML frontmatter")

    parts = content.split("---", 2)
    if len(parts) < 3:
        return SyncResult(False, "Invalid frontmatter format")

    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return SyncResult(False, f"Invalid YAML: {e}")

    if not frontmatter or not isinstance(frontmatter, dict):
        return SyncResult(False, "Frontmatter is empty or not a dict")

    # Extract fields
    obj_id = frontmatter.get("id")
    if not obj_id:
        return SyncResult(False, "Missing required field: id")

    # Validate ID matches filename
    stem = file_path.stem
    if len(stem) > 12:
        expected_suffix = stem[-12:]
        if not obj_id.startswith(expected_suffix):
            return SyncResult(
                False,
                f"ID mismatch: frontmatter id {obj_id[:12]}... does not match filename suffix {expected_suffix}",
                obj_id,
            )

    # Get existing object to check immutable fields
    obj_repo = ObjectRepo(conn)
    existing = obj_repo.get(obj_id)
    if not existing:
        return SyncResult(False, f"Object not found in database: {obj_id}", obj_id)

    # Check space is not changed
    existing_space = _get_space_path(conn, existing["space_id"])
    file_space = frontmatter.get("space")
    if file_space and file_space != existing_space:
        return SyncResult(
            False,
            f"Space is immutable: cannot change from '{existing_space}' to '{file_space}'. Use CLI to move.",
            obj_id,
        )

    # Extract body content (everything after second ---)
    body = parts[2].strip() if len(parts) > 2 else ""

    # Prepare update fields
    title = frontmatter.get("title")
    summary = frontmatter.get("summary")
    projection_override = frontmatter.get("projection_override")

    # Update the object
    try:
        obj_repo.update(
            obj_id,
            title=title,
            summary=summary,
            content=body if body else None,
            projection_override=projection_override if projection_override is not None else ...,
        )
    except Exception as e:
        return SyncResult(False, f"Database update failed: {e}", obj_id)

    # Handle tags if present
    if "tags" in frontmatter:
        tag_repo = TagRepo(conn)
        new_tags = set(frontmatter.get("tags") or [])
        existing_tags = set(tag_repo.list_for_object(obj_id))

        # Add new tags
        for tag in new_tags - existing_tags:
            tag_repo.add(obj_id, tag)

        # Remove old tags
        for tag in existing_tags - new_tags:
            tag_repo.remove(obj_id, tag)

    return SyncResult(True, f"Synced {obj_id}", obj_id)


def get_tier_status(conn: sqlite3.Connection) -> dict:
    """Get projection tier statistics."""
    all_scores = calculate_scores(conn)
    candidates = get_projection_candidates(conn)

    always_override = [s for s in all_scores if s.projection_override == "always"]
    never_override = [s for s in all_scores if s.projection_override == "never"]

    # Count currently projected files
    projected_files = list(settings.projected_dir.rglob("*.md"))
    projected_files = [f for f in projected_files if f.name != "CLAUDE.md"]

    return {
        "total_objects": len(all_scores),
        "projected_count": len(candidates),
        "hot_tier_limit": settings.projection_hot_limit,
        "currently_projected_files": len(projected_files),
        "top_5_by_score": [
            {"id": s.id[:12], "title": s.title, "score": round(s.score, 4)}
            for s in all_scores[:5]
        ],
        "always_project": [{"id": s.id[:12], "title": s.title} for s in always_override],
        "never_project": [{"id": s.id[:12], "title": s.title} for s in never_override],
    }
