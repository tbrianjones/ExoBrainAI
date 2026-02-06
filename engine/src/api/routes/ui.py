"""Full-page UI route handlers (all GET, read-only)."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src import __version__
from src.core.db import db_session, get_db_path
from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo

router = APIRouter()


def _templates(request: Request):
    """Get the Jinja2 templates instance from app state."""
    return request.app.state.templates


def _base_context(request: Request, active_page: str) -> dict:
    """Common template context for all pages."""
    return {
        "request": request,
        "active_page": active_page,
        "version": __version__,
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page; stats loaded via HTMX."""
    templates = _templates(request)
    ctx = _base_context(request, "dashboard")
    return templates.TemplateResponse("dashboard.html", ctx)


@router.get("/objects", response_class=HTMLResponse)
async def objects_browse(request: Request):
    """Object browser page."""
    templates = _templates(request)
    ctx = _base_context(request, "objects")

    db_path = get_db_path()
    if db_path.exists():
        with db_session(db_path) as conn:
            obj_repo = ObjectRepo(conn)
            tag_repo = TagRepo(conn)
            ctx["types"] = obj_repo.list_types()
            ctx["spaces"] = obj_repo.list_spaces()
            ctx["tags"] = tag_repo.list_all(limit=200)
    else:
        ctx["types"] = []
        ctx["spaces"] = []
        ctx["tags"] = []

    return templates.TemplateResponse("objects/browse.html", ctx)


@router.get("/objects/{obj_id}", response_class=HTMLResponse)
async def object_detail(request: Request, obj_id: str):
    """Single object detail page."""
    import markdown as md

    templates = _templates(request)
    ctx = _base_context(request, "objects")

    db_path = get_db_path()
    if not db_path.exists():
        return HTMLResponse("<h1>Database not found</h1>", status_code=503)

    with db_session(db_path) as conn:
        obj_repo = ObjectRepo(conn)
        tag_repo = TagRepo(conn)
        link_repo = LinkRepo(conn)
        file_repo = FileRepo(conn)

        obj = obj_repo.get(obj_id)
        if obj is None:
            # Try prefix match
            obj = obj_repo.get_by_prefix(obj_id)
        if obj is None:
            return HTMLResponse("<h1>Object not found</h1>", status_code=404)

        ctx["obj"] = obj
        ctx["tags"] = tag_repo.list_for_object(obj["id"])
        ctx["links"] = link_repo.list_all_for(obj["id"])

        # File info
        file_info = file_repo.get(obj["id"])
        ctx["file_info"] = file_info
        ctx["file_content_html"] = None

        if file_info:
            mime = file_info.get("mime_type", "")
            if mime and ("text" in mime or "markdown" in mime):
                full_path = file_repo.get_full_path(obj["id"])
                if full_path and full_path.exists():
                    raw = full_path.read_text(encoding="utf-8", errors="replace")
                    if "markdown" in mime:
                        ctx["file_content_html"] = md.markdown(
                            raw, extensions=["fenced_code", "tables"]
                        )
                    else:
                        ctx["file_content_html"] = f"<pre>{raw}</pre>"

        # Render content as markdown
        content = obj.get("content") or ""
        if content:
            ctx["content_html"] = md.markdown(
                content, extensions=["fenced_code", "tables"]
            )
        else:
            ctx["content_html"] = None

    return templates.TemplateResponse("objects/detail.html", ctx)


@router.get("/files", response_class=HTMLResponse)
async def files_explorer(request: Request):
    """File explorer page."""
    templates = _templates(request)
    ctx = _base_context(request, "files")
    return templates.TemplateResponse("files/explorer.html", ctx)


@router.get("/projection", response_class=HTMLResponse)
async def projection_status(request: Request):
    """Projection explorer page."""
    templates = _templates(request)
    ctx = _base_context(request, "projection")
    return templates.TemplateResponse("projection/status.html", ctx)


@router.get("/console", response_class=HTMLResponse)
async def cli_console(request: Request):
    """CLI console page."""
    templates = _templates(request)
    ctx = _base_context(request, "console")
    return templates.TemplateResponse("cli/console.html", ctx)
