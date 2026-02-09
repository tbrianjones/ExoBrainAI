"""HTMX fragment endpoints (all GET, read-only) and CLI read wrappers."""

from __future__ import annotations

import asyncio
import base64
import html as html_mod
import json
import mimetypes
from pathlib import Path

import yaml
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.api.routes.ui import _render_markdown
from src.config import settings
from src.core.db import db_session, get_db_path
from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo

MAX_LIMIT = 200

router = APIRouter()


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
    }
    return templates.TemplateResponse("dashboard/_stats.html", ctx)


# ---------------------------------------------------------------------------
# Object listing (HTMX partial)
# ---------------------------------------------------------------------------

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
):
    """Return object list as an HTML fragment."""
    templates = _templates(request)

    # Cap limit to prevent unbounded queries
    limit = min(max(1, limit), MAX_LIMIT)
    offset = max(0, offset)
    include_system = system == "1"

    db_path = get_db_path()
    if not db_path.exists():
        return HTMLResponse("<div class='text-red-600'>Database not found.</div>")

    with db_session(db_path) as conn:
        obj_repo = ObjectRepo(conn)
        tag_repo = TagRepo(conn)

        if q.strip():
            # Fetch enough results to cover the offset + page
            objects = obj_repo.search(q.strip(), limit=offset + limit, include_system=include_system)
            objects = objects[offset:]
        else:
            objects = obj_repo.list(
                type_name=type or None,
                space_name=space or None,
                tag=tag or None,
                limit=limit,
                offset=offset,
                include_system=include_system,
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
    }
    return templates.TemplateResponse("objects/_list.html", ctx)


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

    mime_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
    size = _human_size(target.stat().st_size)

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
