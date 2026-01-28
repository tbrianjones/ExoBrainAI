"""ExoBrain CLI entry point.

The CLI is the sole write interface for ExoBrain. All commands support --json output.
"""

import json
import sys
from contextlib import contextmanager
from typing import Optional

import typer

from src import __version__

app = typer.Typer(
    name="exobrain",
    help="ExoBrain: local-first personal knowledge system",
    no_args_is_help=True,
)

# Subcommand groups
tag_app = typer.Typer(help="Manage tags on objects")
link_app = typer.Typer(help="Manage links between objects")
type_app = typer.Typer(help="Manage object types")
space_app = typer.Typer(help="Manage spaces")
file_app = typer.Typer(help="Manage file attachments")
tier_app = typer.Typer(help="Projection tier management")
graphrag_app = typer.Typer(help="GraphRAG operations (optional)")

app.add_typer(tag_app, name="tag")
app.add_typer(link_app, name="link")
app.add_typer(type_app, name="type")
app.add_typer(space_app, name="space")
app.add_typer(file_app, name="file")
app.add_typer(tier_app, name="tier")
app.add_typer(graphrag_app, name="graphrag")


def _output(data: dict | list, as_json: bool = False) -> None:
    """Output data as JSON or human-readable text."""
    if as_json:
        typer.echo(json.dumps(data, indent=2, default=str))
    else:
        if isinstance(data, list):
            for item in data:
                _print_object_summary(item)
        elif isinstance(data, dict):
            _print_object_detail(data)


def _print_object_summary(obj: dict) -> None:
    """Print a compact one-line object summary."""
    obj_id = obj.get("id", "?")[:12]
    type_name = obj.get("type_name", obj.get("type", "?"))
    title = obj.get("title", "untitled")
    typer.echo(f"  {obj_id}  [{type_name}]  {title}")


def _print_object_detail(obj: dict) -> None:
    """Print full object detail."""
    typer.echo(f"ID:      {obj.get('id', '?')}")
    typer.echo(f"Type:    {obj.get('type_name', obj.get('type', '?'))}")
    typer.echo(f"Space:   {obj.get('space_name', obj.get('space', '?'))}")
    typer.echo(f"Title:   {obj.get('title', '')}")
    if obj.get("summary"):
        typer.echo(f"Summary: {obj['summary']}")
    if obj.get("content"):
        typer.echo(f"Content: {obj['content']}")
    if obj.get("created_at"):
        typer.echo(f"Created: {obj['created_at']}")
    if obj.get("updated_at"):
        typer.echo(f"Updated: {obj['updated_at']}")


def _get_db():
    """Get a database connection, initializing if needed."""
    from src.core.db import get_connection, get_db_path

    db_path = get_db_path()
    if not db_path.exists():
        typer.echo("Database not found. Run 'exobrain init' first.", err=True)
        raise typer.Exit(1)
    return get_connection(db_path)


@contextmanager
def _db_session():
    """Context manager that opens and guarantees closing of a DB connection."""
    conn = _get_db()
    try:
        yield conn
    finally:
        conn.close()


def _resolve_id(conn, id_or_prefix: str) -> str:
    """Resolve an ID or prefix to a full object ID."""
    from src.core.repository import ObjectRepo

    repo = ObjectRepo(conn)
    resolved = repo.resolve_id(id_or_prefix)
    if not resolved:
        # Check if prefix is ambiguous (multiple matches)
        matches = repo.resolve_prefix_matches(id_or_prefix)
        if len(matches) > 1:
            typer.echo(f"Ambiguous prefix '{id_or_prefix}'; matches {len(matches)} objects:", err=True)
            for m in matches[:10]:
                typer.echo(f"  {m['id'][:12]}  {m['title']}", err=True)
            raise typer.Exit(1)
        typer.echo(f"Object not found: {id_or_prefix}", err=True)
        raise typer.Exit(1)
    return resolved


def _resolve_type_id(conn, type_name: str) -> str:
    """Resolve a type name to its object ID."""
    from src.core.bootstrap import BOOTSTRAP_IDS
    from src.core.repository import ObjectRepo

    # Check bootstrap types first (case-insensitive).
    # Keys containing "/" are spaces (e.g., "primitives/type"), not types.
    for key, obj_id in BOOTSTRAP_IDS.items():
        if key == type_name.lower() and "/" not in key:
            return obj_id

    # Try DB lookup via repository
    repo = ObjectRepo(conn)
    resolved = repo.resolve_type_by_name(type_name)
    if resolved:
        return resolved

    typer.echo(f"Unknown type: {type_name}", err=True)
    raise typer.Exit(1)


def _resolve_space_id(conn, space_name: str) -> str:
    """Resolve a space name to its object ID.

    Matches by: bootstrap key, exact title, or exact summary (hierarchical path).
    """
    from src.core.bootstrap import BOOTSTRAP_IDS
    from src.core.repository import ObjectRepo

    # Check bootstrap spaces first (exact key match)
    if space_name in BOOTSTRAP_IDS:
        return BOOTSTRAP_IDS[space_name]

    # Try DB lookup via repository
    repo = ObjectRepo(conn)
    resolved = repo.resolve_space_by_name(space_name)
    if resolved:
        return resolved

    typer.echo(f"Unknown space: {space_name}. Create it with 'exobrain space create {space_name}'", err=True)
    raise typer.Exit(1)


# === System Commands ===


@app.command()
def version():
    """Show version information."""
    typer.echo(f"ExoBrain v{__version__}")


@app.command()
def init(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Initialize the database, run migrations, and bootstrap types/spaces."""
    from src.config import settings
    from src.core.bootstrap import bootstrap
    from src.core.db import check_integrity, init_db

    settings.ensure_dirs()
    conn = init_db()
    result = bootstrap(conn)
    integrity = check_integrity(conn)
    conn.close()

    output = {
        "status": "ok",
        "db_path": str(settings.db_path),
        "migrations_applied": True,
        "bootstrap": result,
        "integrity": integrity,
    }

    if json_output:
        typer.echo(json.dumps(output, indent=2))
    else:
        typer.echo(f"Initialized ExoBrain at {settings.db_path}")
        typer.echo(f"  Types: {result['types_created']} created ({result['total_bootstrap_objects']} total bootstrap objects)")
        typer.echo(f"  Spaces: {result['spaces_created']} created")
        typer.echo(f"  Integrity: {'OK' if integrity['ok'] else 'FAILED'}")


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show ExoBrain status: object counts, DB size, integrity."""
    from src.config import settings
    from src.core.db import check_integrity
    from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo

    with _db_session() as conn:
        obj_repo = ObjectRepo(conn)
        tag_repo = TagRepo(conn)
        link_repo = LinkRepo(conn)
        file_repo = FileRepo(conn)

        type_counts = obj_repo.count_by_type()
        object_count = obj_repo.count()
        tag_count = tag_repo.count()
        link_count = link_repo.count()
        file_count = file_repo.count()
        db_size = settings.db_path.stat().st_size if settings.db_path.exists() else 0

        integrity = check_integrity(conn)

    output = {
        "version": __version__,
        "data_dir": str(settings.data_dir),
        "db_path": str(settings.db_path),
        "db_size_bytes": db_size,
        "object_count": object_count,
        "type_counts": type_counts,
        "tag_count": tag_count,
        "link_count": link_count,
        "file_count": file_count,
        "integrity": "ok" if integrity["ok"] else "failed",
    }

    if json_output:
        typer.echo(json.dumps(output, indent=2))
    else:
        typer.echo(f"ExoBrain v{__version__}")
        typer.echo(f"Data: {settings.data_dir}")
        typer.echo(f"DB:   {settings.db_path} ({db_size:,} bytes)")
        typer.echo(f"\nObjects: {output['object_count']}")
        for type_name, count in type_counts.items():
            typer.echo(f"  {type_name}: {count}")
        typer.echo(f"\nTags:  {output['tag_count']} distinct")
        typer.echo(f"Links: {output['link_count']}")
        typer.echo(f"Files: {output['file_count']}")
        typer.echo(f"\nIntegrity: {output['integrity']}")


@app.command()
def doctor(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Validate DB integrity, check for orphans, run FK check."""
    from src.config import settings
    from src.core.db import check_integrity

    with _db_session() as conn:
        integrity = check_integrity(conn)

        # FTS5 integrity check
        fts_ok = True
        try:
            conn.execute("INSERT INTO objects_fts(objects_fts) VALUES('integrity-check')")
            fts_status = "ok"
        except Exception as e:
            fts_ok = False
            fts_status = str(e)

        # Check for orphaned files on disk
        orphaned_files = []
        if settings.files_dir.exists():
            for file_path in settings.files_dir.rglob("*"):
                if file_path.is_file():
                    rel = str(file_path.relative_to(settings.files_dir))
                    row = conn.execute(
                        "SELECT object_id FROM files WHERE path = ?", (rel,)
                    ).fetchone()
                    if not row:
                        orphaned_files.append(str(file_path))

    all_ok = integrity["ok"] and fts_ok

    output = {
        "integrity": integrity["integrity"],
        "foreign_key_violations": integrity["foreign_key_violations"],
        "fts_status": fts_status,
        "ok": all_ok,
        "orphaned_files": orphaned_files,
    }

    if json_output:
        typer.echo(json.dumps(output, indent=2))
    else:
        if integrity["ok"]:
            typer.echo("[OK] Database integrity check passed")
        else:
            typer.echo(f"[FAIL] Integrity: {integrity['integrity']}")
            typer.echo(f"[FAIL] FK violations: {integrity['foreign_key_violations']}")
        if fts_ok:
            typer.echo("[OK] FTS5 index integrity passed")
        else:
            typer.echo(f"[FAIL] FTS5 integrity: {fts_status}")
        if orphaned_files:
            typer.echo(f"[WARN] {len(orphaned_files)} orphaned files on disk")
            for f in orphaned_files[:5]:
                typer.echo(f"  {f}")
        else:
            typer.echo("[OK] No orphaned files")

    if not all_ok:
        raise typer.Exit(1)


# === Object Commands ===


@app.command()
def capture(
    content: Optional[str] = typer.Argument(None, help="Content to capture (or use stdin)"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Title"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="Summary"),
    type_name: str = typer.Option("document", "--type", help="Object type"),
    space_name: Optional[str] = typer.Option(None, "--space", help="Space name"),
    tags: Optional[list[str]] = typer.Option(None, "--tag", help="Tag (repeatable)"),
    file_path: Optional[str] = typer.Option(None, "--file", "-f", help="File to attach"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Capture a new object. Content via argument or stdin."""
    from src.core.repository import FileRepo, ObjectRepo, TagRepo

    # Read from stdin if no content provided
    if content is None:
        if sys.stdin.isatty():
            typer.echo("Enter content (Ctrl+D to finish):")
        content = sys.stdin.read().strip()

    if not content and not title:
        typer.echo("Error: provide content or at least a title", err=True)
        raise typer.Exit(1)

    with _db_session() as conn:
        type_id = _resolve_type_id(conn, type_name)

        # Default space: inbox
        if space_name:
            space_id = _resolve_space_id(conn, space_name)
        else:
            from src.core.bootstrap import BOOTSTRAP_IDS

            space_id = BOOTSTRAP_IDS["inbox"]

        # Atomic: create object, add tags, attach file in one transaction.
        # Individual repo methods commit internally, but if file attach fails
        # we want the whole operation to be visible as partial. Wrap the
        # multi-step operation so failure is clear.
        obj_repo = ObjectRepo(conn)
        obj = obj_repo.create(
            type_id=type_id,
            space_id=space_id,
            title=title or (content[:80] if content else "Untitled"),
            summary=summary,
            content=content or None,
        )

        try:
            # Add tags
            if tags:
                tag_repo = TagRepo(conn)
                for tag_text in tags:
                    tag_repo.add(obj["id"], tag_text)

            # Attach file
            if file_path:
                file_repo = FileRepo(conn)
                file_repo.attach(obj["id"], file_path)
        except Exception:
            # Roll back the entire capture on failure
            obj_repo.delete(obj["id"])
            raise

        # Re-fetch with all data
        obj = obj_repo.get(obj["id"])

    if json_output:
        _output(obj, as_json=True)
    else:
        typer.echo(f"Created: {obj['id']}")
        typer.echo(f"  Type:  {obj['type_name']}")
        typer.echo(f"  Title: {obj['title']}")
        if tags:
            typer.echo(f"  Tags:  {', '.join(tags)}")
        if file_path:
            typer.echo(f"  File:  {file_path}")


@app.command()
def get(
    id_or_prefix: str = typer.Argument(..., help="Object ID or prefix (min 8 chars)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Get full detail for an object."""
    from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo

    with _db_session() as conn:
        obj_id = _resolve_id(conn, id_or_prefix)

        obj_repo = ObjectRepo(conn)
        tag_repo = TagRepo(conn)
        link_repo = LinkRepo(conn)
        file_repo = FileRepo(conn)

        obj = obj_repo.get(obj_id)
        obj["tags"] = tag_repo.list_for_object(obj_id)
        obj["links"] = link_repo.list_all_for(obj_id)
        obj["file"] = file_repo.get(obj_id)

    if json_output:
        _output(obj, as_json=True)
    else:
        _print_object_detail(obj)
        if obj["tags"]:
            typer.echo(f"Tags:    {', '.join(obj['tags'])}")
        if obj["links"]:
            typer.echo("Links:")
            for link in obj["links"]:
                direction = link.get("direction", "?")
                rel = link.get("relationship", "?")
                other = link.get("to_title") or link.get("from_title") or link.get("to_id") or link.get("from_id")
                typer.echo(f"  [{direction}] {rel} -> {other}")
        if obj["file"]:
            typer.echo(f"File:    {obj['file']['path']} ({obj['file'].get('mime_type', 'unknown')})")


@app.command(name="list")
def list_objects(
    type_name: Optional[str] = typer.Option(None, "--type", help="Filter by type"),
    space_name: Optional[str] = typer.Option(None, "--space", help="Filter by space"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
    limit: int = typer.Option(50, "--limit", "-n", help="Max results"),
    offset: int = typer.Option(0, "--offset", help="Skip first N results"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List objects with optional filters."""
    from src.core.repository import ObjectRepo

    with _db_session() as conn:
        obj_repo = ObjectRepo(conn)
        objects = obj_repo.list(
            type_name=type_name,
            space_name=space_name,
            tag=tag,
            limit=limit,
            offset=offset,
        )

    if json_output:
        _output(objects, as_json=True)
    else:
        if not objects:
            typer.echo("No objects found.")
        else:
            typer.echo(f"Objects ({len(objects)}):")
            for obj in objects:
                _print_object_summary(obj)


@app.command()
def update(
    id_or_prefix: str = typer.Argument(..., help="Object ID or prefix"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="New summary"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="New content"),
    space_name: Optional[str] = typer.Option(None, "--space", help="Move to space"),
    always_project: bool = typer.Option(False, "--always-project", help="Always include in projection"),
    never_project: bool = typer.Option(False, "--never-project", help="Never include in projection"),
    auto_project: bool = typer.Option(False, "--auto-project", help="Use score-based projection (default)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Update an object's title, summary, content, space, or projection override."""
    from src.core.repository import ObjectRepo

    # Validate projection flags are mutually exclusive
    proj_flags = [always_project, never_project, auto_project]
    if sum(proj_flags) > 1:
        typer.echo("Error: --always-project, --never-project, and --auto-project are mutually exclusive", err=True)
        raise typer.Exit(1)

    # Determine projection_override value (use sentinel to distinguish "not set" from "set to None")
    projection_override = ...  # Ellipsis as sentinel for "not provided"
    if always_project:
        projection_override = "always"
    elif never_project:
        projection_override = "never"
    elif auto_project:
        projection_override = None  # Explicit None means "use score-based"

    with _db_session() as conn:
        obj_id = _resolve_id(conn, id_or_prefix)

        space_id = None
        if space_name:
            space_id = _resolve_space_id(conn, space_name)

        obj_repo = ObjectRepo(conn)
        obj = obj_repo.update(
            obj_id,
            title=title,
            summary=summary,
            content=content,
            space_id=space_id,
            projection_override=projection_override,
        )

    if json_output:
        _output(obj, as_json=True)
    else:
        typer.echo(f"Updated: {obj_id}")
        _print_object_detail(obj)


@app.command()
def delete(
    id_or_prefix: str = typer.Argument(..., help="Object ID or prefix"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Delete an object and all its tags, links, and file."""
    from src.core.bootstrap import BOOTSTRAP_IDS
    from src.core.repository import ObjectRepo

    with _db_session() as conn:
        obj_id = _resolve_id(conn, id_or_prefix)

        # Guard against deleting bootstrap type/space objects
        bootstrap_ids = set(BOOTSTRAP_IDS.values())
        if obj_id in bootstrap_ids:
            typer.echo(f"Cannot delete bootstrap object: {obj_id}", err=True)
            raise typer.Exit(1)

        obj_repo = ObjectRepo(conn)
        obj = obj_repo.get(obj_id)

        if not yes:
            typer.confirm(f"Delete '{obj['title']}' ({obj_id})?", abort=True)

        # ObjectRepo.delete() handles CASCADE + disk cleanup
        deleted = obj_repo.delete(obj_id)

    result = {"id": obj_id, "deleted": deleted, "title": obj["title"]}

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        if deleted:
            typer.echo(f"Deleted: {obj['title']} ({obj_id})")
        else:
            typer.echo(f"Failed to delete: {obj_id}", err=True)
            raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Full-text search across title, summary, and content."""
    from src.core.repository import ObjectRepo

    with _db_session() as conn:
        obj_repo = ObjectRepo(conn)
        results = obj_repo.search(query, limit=limit)

    if json_output:
        _output(results, as_json=True)
    else:
        if not results:
            typer.echo("No results found.")
        else:
            typer.echo(f"Results ({len(results)}):")
            for obj in results:
                _print_object_summary(obj)
                # Show content snippet if available
                snippet = obj.get("summary") or obj.get("content") or ""
                if snippet:
                    if len(snippet) > 120:
                        snippet = snippet[:120] + "..."
                    typer.echo(f"           {snippet}")


# === Tag Commands ===


@tag_app.command("add")
def tag_add(
    id_or_prefix: str = typer.Argument(..., help="Object ID or prefix"),
    tag_text: str = typer.Argument(..., help="Tag to add"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Add a tag to an object."""
    from src.core.repository import TagRepo

    with _db_session() as conn:
        obj_id = _resolve_id(conn, id_or_prefix)
        tag_repo = TagRepo(conn)
        added = tag_repo.add(obj_id, tag_text)

    result = {"object_id": obj_id, "tag": tag_text, "added": added}

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        if added:
            typer.echo(f"Tagged {obj_id[:12]} with '{tag_text}'")
        else:
            typer.echo(f"Tag '{tag_text}' already exists on {obj_id[:12]}")


@tag_app.command("remove")
def tag_remove(
    id_or_prefix: str = typer.Argument(..., help="Object ID or prefix"),
    tag_text: str = typer.Argument(..., help="Tag to remove"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Remove a tag from an object."""
    from src.core.repository import TagRepo

    with _db_session() as conn:
        obj_id = _resolve_id(conn, id_or_prefix)
        tag_repo = TagRepo(conn)
        removed = tag_repo.remove(obj_id, tag_text)

    result = {"object_id": obj_id, "tag": tag_text, "removed": removed}

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        if removed:
            typer.echo(f"Removed tag '{tag_text}' from {obj_id[:12]}")
        else:
            typer.echo(f"Tag '{tag_text}' not found on {obj_id[:12]}")


@tag_app.command("list")
def tag_list(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all tags with usage counts."""
    from src.core.repository import TagRepo

    with _db_session() as conn:
        tag_repo = TagRepo(conn)
        tags = tag_repo.list_all()

    if json_output:
        typer.echo(json.dumps(tags, indent=2))
    else:
        if not tags:
            typer.echo("No tags found.")
        else:
            typer.echo("Tags:")
            for t in tags:
                typer.echo(f"  {t['tag_text']} ({t['count']})")


# === Link Commands ===


@link_app.command("create")
def link_create(
    from_prefix: str = typer.Argument(..., help="Source object ID or prefix"),
    to_prefix: str = typer.Argument(..., help="Target object ID or prefix"),
    relationship: str = typer.Argument(..., help="Relationship description"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Create a link between two objects."""
    from src.core.repository import LinkRepo

    with _db_session() as conn:
        from_id = _resolve_id(conn, from_prefix)
        to_id = _resolve_id(conn, to_prefix)

        link_repo = LinkRepo(conn)
        link = link_repo.create(from_id, to_id, relationship)

    if json_output:
        typer.echo(json.dumps(link, indent=2, default=str))
    else:
        if link:
            typer.echo(f"Linked: {from_id[:12]} --[{relationship}]--> {to_id[:12]}")
        else:
            typer.echo("Link already exists.", err=True)


@link_app.command("list")
def link_list(
    id_or_prefix: str = typer.Argument(..., help="Object ID or prefix"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all links for an object."""
    from src.core.repository import LinkRepo

    with _db_session() as conn:
        obj_id = _resolve_id(conn, id_or_prefix)
        link_repo = LinkRepo(conn)
        links = link_repo.list_all_for(obj_id)

    if json_output:
        typer.echo(json.dumps(links, indent=2, default=str))
    else:
        if not links:
            typer.echo("No links found.")
        else:
            typer.echo("Links:")
            for link in links:
                direction = link.get("direction", "?")
                rel = link.get("relationship", "?")
                other = link.get("to_title") or link.get("from_title") or "?"
                typer.echo(f"  [{direction}] {rel} -> {other} (link #{link['id']})")


@link_app.command("remove")
def link_remove(
    link_id: int = typer.Argument(..., help="Link ID to remove"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Remove a link by its ID."""
    from src.core.repository import LinkRepo

    with _db_session() as conn:
        link_repo = LinkRepo(conn)
        deleted = link_repo.delete(link_id)

    result = {"link_id": link_id, "deleted": deleted}

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        if deleted:
            typer.echo(f"Removed link #{link_id}")
        else:
            typer.echo(f"Link #{link_id} not found", err=True)


# === Type Commands ===


@type_app.command("list")
def type_list(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all object types."""
    from src.core.repository import ObjectRepo

    with _db_session() as conn:
        types = ObjectRepo(conn).list_types()

    if json_output:
        typer.echo(json.dumps(types, indent=2))
    else:
        typer.echo("Types:")
        for t in types:
            typer.echo(f"  {t['title']}: {t.get('summary', '')}")


@type_app.command("create")
def type_create(
    name: str = typer.Argument(..., help="Type name"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="Description"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Create a new object type."""
    from src.core.bootstrap import BOOTSTRAP_IDS
    from src.core.repository import ObjectRepo

    # Capitalize first letter but preserve rest of casing (e.g., "URL" stays "URL")
    display_name = name[0].upper() + name[1:] if name else name

    with _db_session() as conn:
        obj_repo = ObjectRepo(conn)
        obj = obj_repo.create(
            type_id=BOOTSTRAP_IDS["type"],
            space_id=BOOTSTRAP_IDS["primitives/type"],
            title=display_name,
            summary=summary,
        )

    if json_output:
        _output(obj, as_json=True)
    else:
        typer.echo(f"Created type: {display_name} ({obj['id']})")


# === Space Commands ===


@space_app.command("list")
def space_list(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all spaces (shows hierarchy)."""
    from src.core.repository import ObjectRepo

    with _db_session() as conn:
        spaces = ObjectRepo(conn).list_spaces()

    if json_output:
        typer.echo(json.dumps(spaces, indent=2))
    else:
        typer.echo("Spaces:")
        for s in spaces:
            typer.echo(f"  {s['title']}: {s.get('summary', '')}")


@space_app.command("create")
def space_create(
    name: str = typer.Argument(..., help="Space name (use / for hierarchy, e.g. 'work/exobrain')"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="Description"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Create a new space. Auto-creates parent spaces if needed."""
    from src.core.bootstrap import BOOTSTRAP_IDS
    from src.core.repository import ObjectRepo

    with _db_session() as conn:
        obj_repo = ObjectRepo(conn)

        # Create parent spaces if hierarchical
        parts = name.split("/")
        created = []
        for i in range(len(parts)):
            partial = "/".join(parts[: i + 1])
            # Check if exists via repository
            existing = obj_repo.resolve_space_by_name(partial)
            if not existing:
                display_title = parts[i].replace("-", " ").title()
                obj = obj_repo.create(
                    type_id=BOOTSTRAP_IDS["space"],
                    space_id=BOOTSTRAP_IDS["primitives/space"],
                    title=display_title,
                    summary=partial,
                )
                created.append({"name": partial, "id": obj["id"]})

    if json_output:
        typer.echo(json.dumps(created, indent=2))
    else:
        if created:
            for s in created:
                typer.echo(f"Created space: {s['name']} ({s['id']})")
        else:
            typer.echo(f"Space '{name}' already exists.")


# === File Commands ===


@file_app.command("attach")
def file_attach(
    id_or_prefix: str = typer.Argument(..., help="Object ID or prefix"),
    path: str = typer.Argument(..., help="Path to file"),
    role: str = typer.Option("primary", "--role", help="File role"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Attach a file to an object."""
    from src.core.repository import FileRepo

    with _db_session() as conn:
        obj_id = _resolve_id(conn, id_or_prefix)
        file_repo = FileRepo(conn)

        try:
            result = file_repo.attach(obj_id, path, role=role)
        except FileNotFoundError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(1)

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo(f"Attached: {path} -> {obj_id[:12]}")
        typer.echo(f"  SHA-256: {result['sha256']}")
        typer.echo(f"  Size:    {result['size_bytes']:,} bytes")


@file_app.command("detach")
def file_detach(
    id_or_prefix: str = typer.Argument(..., help="Object ID or prefix"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Remove file attachment from an object."""
    from src.core.repository import FileRepo

    with _db_session() as conn:
        obj_id = _resolve_id(conn, id_or_prefix)
        file_repo = FileRepo(conn)
        removed = file_repo.detach(obj_id)

    result = {"object_id": obj_id, "detached": removed}

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        if removed:
            typer.echo(f"Detached file from {obj_id[:12]}")
        else:
            typer.echo(f"No file attached to {obj_id[:12]}")


@file_app.command("path")
def file_path(
    id_or_prefix: str = typer.Argument(..., help="Object ID or prefix"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Print the full path to an attached file."""
    from src.core.repository import FileRepo

    with _db_session() as conn:
        obj_id = _resolve_id(conn, id_or_prefix)
        file_repo = FileRepo(conn)
        full_path = file_repo.get_full_path(obj_id)

    if json_output:
        typer.echo(json.dumps({"object_id": obj_id, "path": str(full_path) if full_path else None}, indent=2))
    else:
        if full_path:
            typer.echo(str(full_path))
        else:
            typer.echo(f"No file attached to {obj_id[:12]}", err=True)
            raise typer.Exit(1)


# === Projection Commands ===


@app.command()
def project(
    cleanup: bool = typer.Option(False, "--cleanup", help="Remove stale projections"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview what would be projected"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Project objects to markdown files for AI-readable access."""
    from src.core.projection import run_projection_cycle

    with _db_session() as conn:
        result = run_projection_cycle(conn, cleanup=cleanup, dry_run=dry_run)

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        action = "Would project" if dry_run else "Projected"
        typer.echo(f"{action} {result['projected']} objects to {len(result['spaces'])} spaces")
        if result['deprojected'] > 0:
            typer.echo(f"Deprojected {result['deprojected']} stale files")
        if result['errors']:
            typer.echo(f"Errors: {len(result['errors'])}", err=True)
            for err in result['errors'][:5]:
                typer.echo(f"  - {err}", err=True)


@tier_app.command("status")
def tier_status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show projection tier statistics."""
    from src.core.projection import get_tier_status

    with _db_session() as conn:
        status = get_tier_status(conn)

    if json_output:
        typer.echo(json.dumps(status, indent=2))
    else:
        typer.echo(f"Total objects:     {status['total_objects']}")
        typer.echo(f"Projected count:   {status['projected_count']}")
        typer.echo(f"Hot tier limit:    {status['hot_tier_limit']}")
        typer.echo(f"Files on disk:     {status['currently_projected_files']}")
        typer.echo()
        typer.echo("Top 5 by score:")
        for obj in status['top_5_by_score']:
            typer.echo(f"  {obj['id']}  {obj['score']:.4f}  {obj['title']}")
        if status['always_project']:
            typer.echo()
            typer.echo("Always project:")
            for obj in status['always_project']:
                typer.echo(f"  {obj['id']}  {obj['title']}")
        if status['never_project']:
            typer.echo()
            typer.echo("Never project:")
            for obj in status['never_project']:
                typer.echo(f"  {obj['id']}  {obj['title']}")


# === GraphRAG Commands (Phase 6; placeholder) ===


@graphrag_app.command("stage")
def graphrag_stage(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Stage SQLite objects as text files for GraphRAG indexing."""
    try:
        from src.graphrag.adapter import stage_for_graphrag
    except ImportError:
        typer.echo("GraphRAG not installed. Install with: pip install -e '.[graphrag]'", err=True)
        raise typer.Exit(1)

    with _db_session() as conn:
        result = stage_for_graphrag(conn)

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo(f"Staged {result['count']} documents for GraphRAG")


@graphrag_app.command("index")
def graphrag_index(
    incremental: bool = typer.Option(True, "--incremental/--full", help="Incremental or full"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Run GraphRAG indexing on staged documents."""
    try:
        from src.graphrag import run_index
    except ImportError:
        typer.echo("GraphRAG not installed. Install with: pip install -e '.[graphrag]'", err=True)
        raise typer.Exit(1)

    result = run_index(incremental=incremental)

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo(f"Index status: {result.get('status', 'unknown')}")


@graphrag_app.command("query")
def graphrag_query(
    query: str = typer.Argument(..., help="Query text"),
    mode: str = typer.Option("global", "--mode", "-m", help="Query mode: global or local"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Query the GraphRAG index."""
    try:
        from src.graphrag import QueryMode, query as run_query
    except ImportError:
        typer.echo("GraphRAG not installed. Install with: pip install -e '.[graphrag]'", err=True)
        raise typer.Exit(1)

    try:
        query_mode = QueryMode(mode.lower())
    except ValueError:
        typer.echo(f"Invalid mode: {mode}. Use 'global' or 'local'.", err=True)
        raise typer.Exit(1)

    result = run_query(query, query_mode)

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo(result.get("response", "No response"))


if __name__ == "__main__":
    app()
