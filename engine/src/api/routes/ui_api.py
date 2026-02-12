"""HTMX fragment endpoints and CLI wrappers for the web UI."""

from __future__ import annotations

import asyncio
import base64
import difflib
import html as html_mod
import json
import mimetypes
import secrets
from pathlib import Path

import yaml
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.api.routes.ui import _render_markdown
from src.config import settings
from src.core.db import db_session, get_db_path
from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo

MAX_LIMIT = 200
MAX_PREVIEW_BYTES = 10 * 1024 * 1024  # 10 MB

router = APIRouter()


def _verify_csrf(request: Request) -> bool:
    """Verify CSRF token: cookie must match X-CSRF-Token header."""
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token:
        return False
    return secrets.compare_digest(cookie_token, header_token)


def _templates(request: Request):
    """Get the Jinja2 templates instance from app state."""
    return request.app.state.templates


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

@router.get("/stats", response_class=HTMLResponse)
async def dashboard_stats(request: Request):
    """Return dashboard stats as an HTML fragment."""
    templates = _templates(request)

    db_path = get_db_path()
    if not db_path.exists():
        return HTMLResponse("<div class='text-red-600'>Database not found.</div>")

    with db_session(db_path) as conn:
        obj_repo = ObjectRepo(conn)
        tag_repo = TagRepo(conn)
        link_repo = LinkRepo(conn)
        file_repo = FileRepo(conn)

        type_counts = obj_repo.count_by_type()
        total_objects = obj_repo.count()
        tag_count = tag_repo.count()
        link_count = link_repo.count()
        file_count = file_repo.count()

        # Projection
        try:
            from src.core.projection import get_tier_status
            projection = get_tier_status(conn)
        except Exception:
            projection = {
                "total_objects": 0,
                "projected_count": 0,
                "hot_tier_limit": 0,
                "currently_projected_files": 0,
            }

        # Data health
        deleted_count = obj_repo.count_deleted()
        history_count = obj_repo.count_history_entries()

    # Backup info
    from src.backup import list_backups
    backups = list_backups()
    backup_count = len(backups)
    total_backup_size = sum(b.size_bytes for b in backups)
    total_backup_size_mb = f"{total_backup_size / (1024 * 1024):.2f}" if total_backup_size > 0 else "0.00"
    last_backup_at = backups[0].created_at.strftime("%Y-%m-%d %H:%M UTC") if backups else "Never"

    # DB size
    db_size_bytes = db_path.stat().st_size if db_path.exists() else 0
    db_size_mb = f"{db_size_bytes / (1024 * 1024):.2f}"

    ctx = {
        "request": request,
        "total_objects": total_objects,
        "type_counts": type_counts,
        "tag_count": tag_count,
        "link_count": link_count,
        "file_count": file_count,
        "projection": projection,
        "db_size_mb": db_size_mb,
        "db_path": str(db_path),
        "backup_count": backup_count,
        "total_backup_size_mb": total_backup_size_mb,
        "last_backup_at": last_backup_at,
        "backup_interval": settings.backup_interval_minutes,
        "backup_retention_days": settings.backup_retention_days,
        "deleted_count": deleted_count,
        "history_count": history_count,
    }
    return templates.TemplateResponse("dashboard/_stats.html", ctx)


# ---------------------------------------------------------------------------
# Object summary stats (HTMX partial)
# ---------------------------------------------------------------------------

@router.get("/objects/stats", response_class=HTMLResponse)
async def objects_stats(request: Request):
    """Return object summary stats as an HTML fragment."""
    templates = _templates(request)

    db_path = get_db_path()
    if not db_path.exists():
        return HTMLResponse("")

    with db_session(db_path) as conn:
        obj_repo = ObjectRepo(conn)
        tag_repo = TagRepo(conn)
        link_repo = LinkRepo(conn)

        ctx = {
            "request": request,
            "total_objects": obj_repo.count(),
            "type_count": len(obj_repo.count_by_type()),
            "tag_count": tag_repo.count(),
            "link_count": link_repo.count(),
        }
    return templates.TemplateResponse("objects/_stats.html", ctx)


# ---------------------------------------------------------------------------
# Tag listing (HTMX partial)
# ---------------------------------------------------------------------------

_VALID_TAG_SORT_COLS = {"tag", "count", "first_used", "last_used"}


@router.get("/tags", response_class=HTMLResponse)
async def list_tags(
    request: Request,
    q: str = "",
    limit: int = 50,
    offset: int = 0,
    sort: str = "count",
    order: str = "desc",
):
    """Return tag list as an HTML fragment."""
    templates = _templates(request)

    limit = min(max(1, limit), MAX_LIMIT)
    offset = max(0, offset)

    if sort not in _VALID_TAG_SORT_COLS:
        sort = "count"
    if order not in ("asc", "desc"):
        order = "desc"

    db_path = get_db_path()
    if not db_path.exists():
        return HTMLResponse("<div class='text-red-600'>Database not found.</div>")

    with db_session(db_path) as conn:
        tag_repo = TagRepo(conn)
        tags, total = tag_repo.list_all_enriched(
            search=q.strip(),
            limit=limit,
            offset=offset,
            sort_by=sort,
            sort_order=order,
        )

    ctx = {
        "request": request,
        "tags": tags,
        "total": total,
        "limit": limit,
        "offset": offset,
        "sort": sort,
        "order": order,
    }
    return templates.TemplateResponse("tags/_list.html", ctx)


# ---------------------------------------------------------------------------
# Space tree (HTMX partial)
# ---------------------------------------------------------------------------

def _build_space_tree(space_stats: list[dict], search: str = "") -> list[dict]:
    """Build a nested tree from space stats for recursive template rendering.

    Returns a list of root nodes. Each node has: name, leaf_name, depth,
    direct_count, total_count, types, last_activity, children (list of child nodes).
    """
    # Filter by search if provided
    if search:
        search_lower = search.lower()
        matching = {s["space_name"] for s in space_stats if search_lower in s["space_name"].lower()}
        # Include ancestors of matching spaces
        ancestors: set[str] = set()
        for name in matching:
            parts = name.split("/")
            for i in range(1, len(parts)):
                ancestors.add("/".join(parts[:i]))
        included = matching | ancestors
        space_stats = [s for s in space_stats if s["space_name"] in included]

    if not space_stats:
        return []

    # Sort by name for consistent tree order
    space_stats.sort(key=lambda s: s["space_name"])

    # Build nested tree
    nodes_by_name: dict[str, dict] = {}
    root_nodes: list[dict] = []

    for s in space_stats:
        name = s["space_name"]
        node = {
            "name": name,
            "leaf_name": name.rsplit("/", 1)[-1] if "/" in name else name,
            "depth": name.count("/"),
            "direct_count": s["direct_count"],
            "total_count": s["direct_count"],  # computed below
            "types": s.get("types", []),
            "last_activity": s.get("last_activity"),
            "children": [],
        }
        nodes_by_name[name] = node

        # Find parent
        if "/" in name:
            parent_name = name.rsplit("/", 1)[0]
            if parent_name in nodes_by_name:
                nodes_by_name[parent_name]["children"].append(node)
            else:
                root_nodes.append(node)
        else:
            root_nodes.append(node)

    # Compute total_count recursively (direct + all descendants)
    def _compute_total(node: dict) -> int:
        total = node["direct_count"]
        for child in node["children"]:
            total += _compute_total(child)
        node["total_count"] = total
        return total

    for root in root_nodes:
        _compute_total(root)

    return root_nodes


@router.get("/spaces/tree", response_class=HTMLResponse)
async def space_tree(request: Request, q: str = ""):
    """Return space tree as an HTML fragment."""
    templates = _templates(request)

    db_path = get_db_path()
    if not db_path.exists():
        return HTMLResponse("<div class='text-red-600'>Database not found.</div>")

    with db_session(db_path) as conn:
        obj_repo = ObjectRepo(conn)
        stats = obj_repo.space_stats()

    tree = _build_space_tree(stats, search=q.strip())

    ctx = {
        "request": request,
        "tree": tree,
    }
    return templates.TemplateResponse("spaces/_tree.html", ctx)


# ---------------------------------------------------------------------------
# Object listing (HTMX partial)
# ---------------------------------------------------------------------------

_VALID_SORT_COLS = {"id", "type", "title", "created", "updated"}

# Hex chars + dashes that appear in UUIDs
_UUID_CHARS = set("0123456789abcdef-")


def _looks_like_uuid_prefix(q: str) -> bool:
    """Check if query could be the start of a UUID."""
    return len(q) >= 3 and all(c in _UUID_CHARS for c in q.lower())


@router.get("/objects", response_class=HTMLResponse)
async def list_objects(
    request: Request,
    q: str = "",
    type: str = "",
    space: str = "",
    tag: str = "",
    system: str = "",
    limit: int = 50,
    offset: int = 0,
    sort: str = "created",
    order: str = "desc",
    date_from: str = "",
    date_to: str = "",
):
    """Return object list as an HTML fragment."""
    templates = _templates(request)

    # Cap limit to prevent unbounded queries
    limit = min(max(1, limit), MAX_LIMIT)
    offset = max(0, offset)
    include_system = system == "1"

    # Validate sort params
    if sort not in _VALID_SORT_COLS:
        sort = "created"
    if order not in ("asc", "desc"):
        order = "desc"

    db_path = get_db_path()
    if not db_path.exists():
        return HTMLResponse("<div class='text-red-600'>Database not found.</div>")

    with db_session(db_path) as conn:
        obj_repo = ObjectRepo(conn)
        tag_repo = TagRepo(conn)

        if q.strip():
            query_text = q.strip()

            # Search by ID prefix alongside FTS
            search_sort = sort if sort != "created" or order != "desc" else None
            objects = obj_repo.search(
                query_text,
                limit=offset + limit,
                include_system=include_system,
                sort_by=search_sort,
                sort_order=order,
            )

            # Also search by ID prefix if query looks like a UUID
            if _looks_like_uuid_prefix(query_text):
                from src.core.repository import _escape_like

                system_filter = "" if include_system else "AND o.is_system_object = 0"
                safe_prefix = _escape_like(query_text.lower())
                id_rows = conn.execute(
                    f"""SELECT o.id, o.type_id, o.space_id, o.title, o.summary,
                               o.created_at, o.updated_at,
                               t.title as type_name,
                               s.title as space_name
                        FROM objects o
                        JOIN objects t ON o.type_id = t.id
                        JOIN objects s ON o.space_id = s.id
                        WHERE o.id LIKE ? ESCAPE '\\'
                        AND o.deleted_at IS NULL AND o.purged_at IS NULL
                        {system_filter}
                        LIMIT ?""",
                    (safe_prefix + "%", limit),
                ).fetchall()
                # Merge ID matches (deduplicate by id)
                seen_ids = {obj["id"] for obj in objects}
                for row in id_rows:
                    if row["id"] not in seen_ids:
                        objects.insert(0, dict(row))
                        seen_ids.add(row["id"])

            objects = objects[offset:offset + limit]
        else:
            objects = obj_repo.list(
                type_name=type or None,
                space_name=space or None,
                tag=tag or None,
                limit=limit,
                offset=offset,
                include_system=include_system,
                sort_by=sort,
                sort_order=order,
                date_from=date_from or None,
                date_to=date_to or None,
            )

        # Batch fetch tags (avoids N+1 query)
        if objects:
            obj_ids = [obj["id"] for obj in objects]
            placeholders = ",".join("?" for _ in obj_ids)
            tag_rows = conn.execute(
                f"SELECT object_id, tag_text FROM object_tags WHERE object_id IN ({placeholders}) ORDER BY tag_text",
                obj_ids,
            ).fetchall()
            tags_by_obj: dict[str, list[str]] = {}
            for row in tag_rows:
                tags_by_obj.setdefault(row["object_id"], []).append(row["tag_text"])
            for obj in objects:
                obj["tags"] = tags_by_obj.get(obj["id"], [])

    ctx = {
        "request": request,
        "objects": objects,
        "limit": limit,
        "offset": offset,
        "sort": sort,
        "order": order,
    }
    return templates.TemplateResponse("objects/_list.html", ctx)


# ---------------------------------------------------------------------------
# Object version history and diff (HTMX partials)
# ---------------------------------------------------------------------------

@router.get("/objects/{obj_id}/history", response_class=HTMLResponse)
async def object_history(request: Request, obj_id: str):
    """Return version history list as an HTML fragment."""
    templates = _templates(request)

    db_path = get_db_path()
    if not db_path.exists():
        return HTMLResponse("<div class='text-red-600'>Database not found.</div>")

    with db_session(db_path) as conn:
        obj_repo = ObjectRepo(conn)
        versions = obj_repo.list_history(obj_id)
        obj = obj_repo.get(obj_id, include_deleted=True)

    if obj is None:
        return HTMLResponse("<div class='text-gray-500 text-sm'>Object not found.</div>")

    ctx = {
        "request": request,
        "versions": versions,
        "obj": obj,
    }
    return templates.TemplateResponse("objects/_history.html", ctx)


def _render_diff_html(old_text: str, new_text: str) -> str:
    """Generate HTML from a unified diff, with colored lines."""
    old_lines = (old_text or "").splitlines(keepends=True)
    new_lines = (new_text or "").splitlines(keepends=True)
    diff_lines = difflib.unified_diff(old_lines, new_lines, lineterm="")

    parts: list[str] = []
    for line in diff_lines:
        escaped = html_mod.escape(line.rstrip("\n"))
        if line.startswith("@@"):
            parts.append(f'<span class="text-blue-600">{escaped}</span>')
        elif line.startswith("+"):
            parts.append(f'<span style="background:#dcfce7;display:block">{escaped}</span>')
        elif line.startswith("-"):
            parts.append(f'<span style="background:#fecaca;display:block">{escaped}</span>')
        else:
            parts.append(f'<span style="display:block">{escaped}</span>')
    return "\n".join(parts)


@router.get("/objects/{obj_id}/diff/{version}", response_class=HTMLResponse)
async def object_diff(request: Request, obj_id: str, version: int):
    """Return diff between a historical version and the next version."""
    templates = _templates(request)

    db_path = get_db_path()
    if not db_path.exists():
        return HTMLResponse("<div class='text-red-600'>Database not found.</div>")

    with db_session(db_path) as conn:
        obj_repo = ObjectRepo(conn)
        old_ver = obj_repo.get_version(obj_id, version)
        if old_ver is None:
            return HTMLResponse("<div class='text-gray-500 text-sm'>Version not found.</div>")

        # The "next" version: check if version+1 exists in history; otherwise use the live object
        next_ver = obj_repo.get_version(obj_id, version + 1)
        if next_ver is None:
            next_ver = obj_repo.get(obj_id, include_deleted=True)

        if next_ver is None:
            return HTMLResponse("<div class='text-gray-500 text-sm'>Object not found.</div>")

        to_version = next_ver.get("version", version + 1)

    # Build diffs for each field that changed
    diffs = []
    for field in ("title", "summary", "content"):
        old_val = old_ver.get(field) or ""
        new_val = next_ver.get(field) or ""
        if old_val != new_val:
            diff_html = _render_diff_html(old_val, new_val)
            diffs.append({"field": field, "diff_html": diff_html})

    ctx = {
        "request": request,
        "diffs": diffs,
        "from_version": version,
        "to_version": to_version,
    }
    return templates.TemplateResponse("objects/_diff.html", ctx)


# ---------------------------------------------------------------------------
# File tree (HTMX partial)
# ---------------------------------------------------------------------------

def _validate_data_path(root: str, rel_path: str) -> Path | None:
    """Resolve a path within allowed data directories; return None if invalid."""
    if root == "files":
        base = settings.files_dir
    elif root == "projected":
        base = settings.projected_dir
    else:
        return None

    if rel_path:
        target = (base / rel_path).resolve()
    else:
        target = base.resolve()

    # Path traversal check
    base_resolved = base.resolve()
    if not (str(target) == str(base_resolved) or str(target).startswith(str(base_resolved) + "/")):
        return None

    return target


def _human_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.0f} {unit}" if unit == "B" else f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


@router.get("/files/tree", response_class=HTMLResponse)
async def file_tree(request: Request, root: str = "files", path: str = ""):
    """Return directory listing as an HTML fragment."""
    templates = _templates(request)

    target = _validate_data_path(root, path)
    if target is None or not target.exists() or not target.is_dir():
        return HTMLResponse("<div class='text-gray-500 text-sm'>Directory not found.</div>")

    entries = []
    try:
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name)):
            # Skip hidden files
            if item.name.startswith("."):
                continue

            rel = str(item.relative_to(_validate_data_path(root, "")))
            entry = {
                "name": item.name,
                "rel_path": rel,
                "is_dir": item.is_dir(),
                "size": _human_size(item.stat().st_size) if item.is_file() else "",
            }
            entries.append(entry)
    except PermissionError:
        return HTMLResponse("<div class='text-red-600 text-sm'>Permission denied.</div>")

    ctx = {
        "request": request,
        "entries": entries,
        "root": root,
    }
    return templates.TemplateResponse("files/_tree.html", ctx)


@router.get("/files/preview", response_class=HTMLResponse)
async def file_preview(request: Request, root: str = "files", path: str = ""):
    """Return file preview as an HTML fragment."""
    templates = _templates(request)

    target = _validate_data_path(root, path)
    if target is None or not target.exists() or not target.is_file():
        return HTMLResponse("<div class='text-gray-500 text-sm'>File not found.</div>")

    file_size = target.stat().st_size
    if file_size > MAX_PREVIEW_BYTES:
        ctx = {
            "request": request,
            "file_path": path,
            "mime_type": mimetypes.guess_type(str(target))[0] or "application/octet-stream",
            "size": _human_size(file_size),
            "preview_type": "too_large",
            "content": None,
            "frontmatter": None,
        }
        return templates.TemplateResponse("files/_preview.html", ctx)

    mime_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
    size = _human_size(file_size)

    ctx = {
        "request": request,
        "file_path": path,
        "mime_type": mime_type,
        "size": size,
        "frontmatter": None,
        "preview_type": None,
        "content": None,
    }

    # Parse frontmatter for projected markdown files
    if root == "projected" and target.suffix == ".md":
        try:
            raw = target.read_text(encoding="utf-8", errors="replace")
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    ctx["frontmatter"] = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                    ctx["content"] = _render_markdown(body)
                    ctx["preview_type"] = "html"
                    return templates.TemplateResponse("files/_preview.html", ctx)
        except Exception:
            pass

    # Markdown
    if mime_type and ("markdown" in mime_type or target.suffix == ".md"):
        try:
            raw = target.read_text(encoding="utf-8", errors="replace")
            ctx["content"] = _render_markdown(raw)
            ctx["preview_type"] = "html"
        except Exception:
            ctx["preview_type"] = None
    # Images
    elif mime_type and mime_type.startswith("image/"):
        try:
            data = target.read_bytes()
            ctx["content"] = base64.b64encode(data).decode("ascii")
            ctx["preview_type"] = "image"
        except Exception:
            ctx["preview_type"] = None
    # Text / JSON
    elif mime_type and ("text" in mime_type or "json" in mime_type):
        try:
            raw = target.read_text(encoding="utf-8", errors="replace")
            if "json" in mime_type:
                try:
                    parsed = json.loads(raw)
                    raw = json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    pass
            # Truncate very large files
            if len(raw) > 50000:
                raw = raw[:50000] + "\n\n... (truncated)"
            ctx["content"] = raw
            ctx["preview_type"] = "text"
        except Exception:
            ctx["preview_type"] = None

    return templates.TemplateResponse("files/_preview.html", ctx)


# ---------------------------------------------------------------------------
# Projection status (HTMX partial)
# ---------------------------------------------------------------------------

@router.get("/projection/status", response_class=HTMLResponse)
async def projection_status_fragment(request: Request):
    """Return projection status as an HTML fragment."""
    templates = _templates(request)

    db_path = get_db_path()
    if not db_path.exists():
        return HTMLResponse("<div class='text-red-600'>Database not found.</div>")

    with db_session(db_path) as conn:
        try:
            from src.core.projection import get_tier_status
            status = get_tier_status(conn)
        except Exception as e:
            return HTMLResponse(f"<div class='text-red-600'>Error: {html_mod.escape(str(e))}</div>")

    # List projected files on disk
    projected_files = []
    if settings.projected_dir.exists():
        for f in sorted(settings.projected_dir.rglob("*.md")):
            if f.name != "CLAUDE.md":
                projected_files.append(str(f.relative_to(settings.projected_dir)))

    ctx = {
        "request": request,
        "status": status,
        "projected_files": projected_files,
    }
    return templates.TemplateResponse("projection/_status_fragment.html", ctx)


# ---------------------------------------------------------------------------
# CLI console (read-only commands only)
# ---------------------------------------------------------------------------

# Commands allowed with arbitrary trailing arguments (read-only)
_COMMANDS_WITH_ARGS = {"get", "search", "list"}

# Commands allowed as exact matches only (no trailing args)
_EXACT_COMMANDS = {"status", "doctor", "version"}

# Two-word commands allowed as exact matches only
_EXACT_TWO_WORD = {"tag list", "type list", "space list", "tier status", "project --dry-run",
                   "link list", "file path"}

# Two-word commands that allow a trailing argument
_TWO_WORD_WITH_ARGS = {"link list", "file path"}


def _is_command_allowed(cmd: str) -> bool:
    """Check if a CLI command is in the read-only whitelist."""
    parts = cmd.strip().split()
    if not parts:
        return False

    # Exact single-word commands
    if len(parts) == 1 and parts[0] in (_EXACT_COMMANDS | _COMMANDS_WITH_ARGS):
        return True

    # Single-word commands with arguments: "get <id>", "search <query>", "list ..."
    if parts[0] in _COMMANDS_WITH_ARGS:
        return True

    # Two-word commands
    if len(parts) >= 2:
        two_word = f"{parts[0]} {parts[1]}"
        # Exact two-word (no extra args)
        if len(parts) == 2 and two_word in _EXACT_TWO_WORD:
            return True
        # Two-word with trailing argument
        if two_word in _TWO_WORD_WITH_ARGS:
            return True

    return False


@router.get("/cli/run", response_class=HTMLResponse)
async def cli_run(request: Request, cmd: str = ""):
    """Run a read-only CLI command and return formatted output."""
    templates = _templates(request)

    cmd = cmd.strip()
    if not cmd:
        return HTMLResponse("")

    if not _is_command_allowed(cmd):
        ctx = {
            "request": request,
            "command": cmd,
            "success": False,
            "output": f"Command not allowed: '{cmd}'. Only read-only commands are permitted.",
        }
        return templates.TemplateResponse("cli/_output.html", ctx)

    try:
        # Split command into args for subprocess
        args = ["exobrain"] + cmd.split()

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            error_output = stderr.decode("utf-8", errors="replace")
            output = error_output or output or "Command failed with no output."
            ctx = {
                "request": request,
                "command": cmd,
                "success": False,
                "output": output,
            }
        else:
            # Try to pretty-print JSON
            try:
                parsed = json.loads(output)
                output = json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, ValueError):
                pass
            ctx = {
                "request": request,
                "command": cmd,
                "success": True,
                "output": output,
            }
    except asyncio.TimeoutError:
        ctx = {
            "request": request,
            "command": cmd,
            "success": False,
            "output": "Command timed out after 30 seconds.",
        }
    except Exception as e:
        ctx = {
            "request": request,
            "command": cmd,
            "success": False,
            "output": str(e),
        }

    return templates.TemplateResponse("cli/_output.html", ctx)


# ---------------------------------------------------------------------------
# Object mutations (delete, purge) via CLI subprocess
# ---------------------------------------------------------------------------

@router.post("/objects/{obj_id}/delete", response_class=HTMLResponse)
async def delete_object(obj_id: str, request: Request):
    """Soft-delete an object via the CLI."""
    if not _verify_csrf(request):
        return HTMLResponse("Forbidden", status_code=403)

    try:
        proc = await asyncio.create_subprocess_exec(
            "exobrain", "delete", obj_id, "--yes", "--json",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode == 0:
            response = HTMLResponse('<div class="text-green-600 text-sm">Object deleted.</div>')
            response.headers["HX-Redirect"] = "/ui/objects"
            return response
        else:
            error = stderr.decode("utf-8", errors="replace") or stdout.decode("utf-8", errors="replace") or "Delete failed."
            return HTMLResponse(f'<div class="text-red-600 text-sm">{html_mod.escape(error)}</div>')
    except asyncio.TimeoutError:
        return HTMLResponse('<div class="text-red-600 text-sm">Delete timed out after 30 seconds.</div>')
    except Exception as e:
        return HTMLResponse(f'<div class="text-red-600 text-sm">{html_mod.escape(str(e))}</div>')


@router.post("/objects/{obj_id}/purge", response_class=HTMLResponse)
async def purge_object(obj_id: str, request: Request):
    """Permanently purge an object via the CLI."""
    if not _verify_csrf(request):
        return HTMLResponse("Forbidden", status_code=403)

    try:
        proc = await asyncio.create_subprocess_exec(
            "exobrain", "purge", obj_id, "--yes", "--json",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode == 0:
            response = HTMLResponse('<div class="text-green-600 text-sm">Object purged.</div>')
            response.headers["HX-Redirect"] = "/ui/objects"
            return response
        else:
            error = stderr.decode("utf-8", errors="replace") or stdout.decode("utf-8", errors="replace") or "Purge failed."
            return HTMLResponse(f'<div class="text-red-600 text-sm">{html_mod.escape(error)}</div>')
    except asyncio.TimeoutError:
        return HTMLResponse('<div class="text-red-600 text-sm">Purge timed out after 30 seconds.</div>')
    except Exception as e:
        return HTMLResponse(f'<div class="text-red-600 text-sm">{html_mod.escape(str(e))}</div>')