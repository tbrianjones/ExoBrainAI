"""Full-page UI route handlers (all GET, read-only)."""

import html

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src import __version__
from src.core.db import db_session, get_db_path
from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo

router = APIRouter()

# HTML tags allowed in rendered markdown output
_SAFE_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr",
    "ul", "ol", "li", "dl", "dt", "dd",
    "strong", "em", "b", "i", "u", "s", "del", "ins", "mark", "sub", "sup",
    "a", "code", "pre", "blockquote", "kbd", "var", "samp",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",
    "img", "figure", "figcaption",
    "div", "span", "abbr", "details", "summary",
}
_SAFE_ATTRS = {"a": {"href", "title"}, "img": {"src", "alt", "title"}, "td": {"align"}, "th": {"align"}}

import re

_TAG_RE = re.compile(r"<(/?)(\w+)([^>]*)(/?)>", re.DOTALL)
_ATTR_RE = re.compile(r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\S+))')


def _sanitize_html(raw_html: str) -> str:
    """Strip dangerous HTML tags and attributes from rendered markdown.

    Allows safe formatting tags; removes script, iframe, event handlers, etc.
    """
    def _replace_tag(m: re.Match) -> str:
        slash = m.group(1)
        tag = m.group(2).lower()
        attrs_str = m.group(3)
        self_close = m.group(4)

        if tag not in _SAFE_TAGS:
            return ""

        # Filter attributes
        allowed = _SAFE_ATTRS.get(tag, set())
        safe_attrs = []
        for attr_m in _ATTR_RE.finditer(attrs_str):
            attr_name = attr_m.group(1).lower()
            attr_val = attr_m.group(2) or attr_m.group(3) or attr_m.group(4) or ""
            if attr_name in allowed:
                # Block javascript: URIs
                if attr_name in ("href", "src") and attr_val.strip().lower().startswith("javascript:"):
                    continue
                safe_attrs.append(f'{attr_name}="{html.escape(attr_val)}"')

        attr_str = (" " + " ".join(safe_attrs)) if safe_attrs else ""
        return f"<{slash}{tag}{attr_str}{self_close}>"

    return _TAG_RE.sub(_replace_tag, raw_html)


def _strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter (--- delimited block at start) from text."""
    if not text.startswith("---"):
        return text
    # Find closing ---
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4:].lstrip("\n")


def _render_markdown(content: str) -> str:
    """Render markdown to sanitized HTML, stripping any YAML frontmatter."""
    import markdown as md
    clean = _strip_frontmatter(content)
    raw_html = md.markdown(clean, extensions=["fenced_code", "tables"])
    return _sanitize_html(raw_html)


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
    templates = _templates(request)
    ctx = _base_context(request, "objects")

    db_path = get_db_path()
    if not db_path.exists():
        ctx["error"] = "Database not found"
        return templates.TemplateResponse("objects/detail_error.html", ctx, status_code=503)

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
            ctx["error"] = "Object not found"
            return templates.TemplateResponse("objects/detail_error.html", ctx, status_code=404)

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
                        ctx["file_content_html"] = _render_markdown(raw)
                    else:
                        ctx["file_content_html"] = f"<pre>{html.escape(raw)}</pre>"

        # Render summary and content as sanitized markdown
        summary = obj.get("summary") or ""
        if summary:
            ctx["summary_html"] = _render_markdown(summary)
        else:
            ctx["summary_html"] = None

        content = obj.get("content") or ""
        if content:
            ctx["content_html"] = _render_markdown(content)
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
