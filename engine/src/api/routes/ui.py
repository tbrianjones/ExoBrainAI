"""Full-page UI route handlers (all GET, read-only)."""

import html
import re
import secrets

import nh3
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from src import __version__
from src.core.db import db_session, get_db_path
from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo

router = APIRouter()

_ALLOWED_TAGS = {
    "p", "br", "strong", "em", "b", "i", "u", "s",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "a", "img",
    "pre", "code", "blockquote",
    "table", "thead", "tbody", "tr", "th", "td",
    "hr", "div", "span",
    "dl", "dt", "dd",
    "sup", "sub",
    "details", "summary",
}

_ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title"},
    "td": {"align"},
    "th": {"align"},
    "code": {"class"},
    "pre": {"class"},
    "span": {"class"},
    "div": {"class"},
}

def _sanitize_html(raw_html: str) -> str:
    """Sanitize HTML using nh3 (safe by default)."""
    return nh3.clean(
        raw_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        url_schemes={"http", "https", "mailto"},
    )


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
    raw_html = md.markdown(clean, extensions=["fenced_code", "tables"], tab_length=2)
    return _sanitize_html(raw_html)


def _generate_csrf_token() -> str:
    """Generate a random CSRF token."""
    return secrets.token_hex(32)


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
    csrf_token = _generate_csrf_token()
    ctx["csrf_token"] = csrf_token
    response = templates.TemplateResponse("dashboard.html", ctx)
    response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="strict", path="/")
    return response


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

    csrf_token = _generate_csrf_token()
    ctx["csrf_token"] = csrf_token
    response = templates.TemplateResponse("objects/browse.html", ctx)
    response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="strict", path="/")
    return response


@router.get("/objects/{obj_id}", response_class=HTMLResponse)
async def object_detail(request: Request, obj_id: str):
    """Single object detail page."""
    templates = _templates(request)
    ctx = _base_context(request, "objects")

    csrf_token = _generate_csrf_token()
    ctx["csrf_token"] = csrf_token

    db_path = get_db_path()
    if not db_path.exists():
        ctx["error"] = "Database not found"
        response = templates.TemplateResponse("objects/detail_error.html", ctx, status_code=503)
        response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="strict", path="/")
        return response

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
            # Check if it's a tombstone or soft-deleted object
            obj = obj_repo.get(obj_id, include_deleted=True)
            if obj is None:
                obj = obj_repo.get_by_prefix(obj_id, include_deleted=True)
            if obj is not None and obj.get("purged_at"):
                # Tombstone: show dedicated page with preserved links
                ctx["obj"] = obj
                ctx["links"] = link_repo.list_all_for(obj["id"])
                response = templates.TemplateResponse("objects/detail_tombstone.html", ctx, status_code=410)
                response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="strict", path="/")
                return response
            if obj is not None and obj.get("deleted_at"):
                # Soft-deleted: show the normal detail page with a notice
                ctx["obj"] = obj
                ctx["is_deleted"] = True
            else:
                ctx["error"] = "Object not found"
                response = templates.TemplateResponse("objects/detail_error.html", ctx, status_code=404)
                response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="strict", path="/")
                return response

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

    response = templates.TemplateResponse("objects/detail.html", ctx)
    response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="strict", path="/")
    return response


@router.get("/objects/{obj_id}/download")
async def object_download_markdown(request: Request, obj_id: str):
    """Download an object as a Markdown file with YAML frontmatter."""
    db_path = get_db_path()
    if not db_path.exists():
        return PlainTextResponse("Database not found", status_code=503)

    with db_session(db_path) as conn:
        obj_repo = ObjectRepo(conn)
        tag_repo = TagRepo(conn)

        obj = obj_repo.get(obj_id)
        if obj is None:
            obj = obj_repo.get_by_prefix(obj_id)
        if obj is None:
            return PlainTextResponse("Object not found", status_code=404)

        tags = tag_repo.list_for_object(obj["id"])

        # Build YAML frontmatter
        lines = ["---"]
        lines.append(f"id: {obj['id']}")
        title = obj.get("title", "").replace('"', '\\"')
        lines.append(f'title: "{title}"')
        lines.append(f"type: {obj.get('type_name', '')}")
        lines.append(f"space: {obj.get('space_name', '')}")
        if tags:
            lines.append(f"tags: [{', '.join(tags)}]")
        lines.append(f"created: {obj.get('created_at', '')}")
        lines.append(f"updated: {obj.get('updated_at', '')}")
        lines.append("---")
        lines.append("")

        if obj.get("summary"):
            lines.append(f"**Summary:** {obj['summary']}")
            lines.append("")

        if obj.get("content"):
            lines.append(obj["content"])

        md_content = "\n".join(lines)

        # Slugify title for filename
        slug = re.sub(r"[^\w\s-]", "", obj.get("title", "object").lower())
        slug = re.sub(r"[\s]+", "-", slug).strip("-") or "object"
        filename = f"{slug}.md"

        return PlainTextResponse(
            content=md_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@router.get("/objects/{obj_id}/pdf")
async def object_download_pdf(request: Request, obj_id: str):
    """Download an object as a PDF rendered from its markdown content."""
    from weasyprint import HTML

    db_path = get_db_path()
    if not db_path.exists():
        return PlainTextResponse("Database not found", status_code=503)

    with db_session(db_path) as conn:
        obj_repo = ObjectRepo(conn)
        tag_repo = TagRepo(conn)

        obj = obj_repo.get(obj_id)
        if obj is None:
            obj = obj_repo.get_by_prefix(obj_id)
        if obj is None:
            return PlainTextResponse("Object not found", status_code=404)

        tags = tag_repo.list_for_object(obj["id"])

        # Build the content HTML from markdown
        content_html = ""
        if obj.get("summary"):
            content_html += _render_markdown(f"**Summary:** {obj['summary']}")
        if obj.get("content"):
            content_html += _render_markdown(obj["content"])

        # Build tag badges
        tag_html = ""
        if tags:
            tag_html = " ".join(
                f'<span class="tag">{html.escape(t)}</span>' for t in tags
            )

        # Standalone HTML document with inline styles
        pdf_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: sans-serif; color: #1a1a1a; line-height: 1.6; margin: 0; padding: 0; }}
  .meta {{ background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 6px;
           padding: 16px 20px; margin-bottom: 24px; font-size: 11px; color: #64748b; }}
  .meta h1 {{ font-size: 20px; color: #111827; margin: 0 0 8px 0; }}
  .meta .type {{ display: inline-block; background: #dbeafe; color: #1d4ed8;
                 padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600; }}
  .meta .space {{ color: #6b7280; margin-left: 8px; }}
  .meta-grid {{ display: flex; gap: 24px; margin-top: 8px; font-family: monospace; font-size: 10px; }}
  .tag {{ display: inline-block; background: #f1f5f9; color: #475569;
          padding: 2px 8px; border-radius: 10px; font-size: 10px; margin-right: 4px; }}
  .tags {{ margin-top: 8px; }}
  .content {{ font-size: 14px; }}
  .content h1 {{ font-size: 22px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }}
  .content h2 {{ font-size: 18px; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; }}
  .content h3 {{ font-size: 16px; }}
  .content pre {{ background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px;
                  padding: 12px; overflow-x: auto; font-size: 12px; }}
  .content code {{ background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 0.9em; }}
  .content pre code {{ background: none; padding: 0; }}
  .content blockquote {{ border-left: 3px solid #d1d5db; margin-left: 0; padding-left: 16px; color: #6b7280; }}
  .content table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  .content th, .content td {{ border: 1px solid #d1d5db; padding: 6px 10px; text-align: left; font-size: 13px; }}
  .content th {{ background: #f8f9fa; font-weight: 600; }}
  .content a {{ color: #2563eb; }}
  .content img {{ max-width: 100%; }}
</style></head><body>
<div class="meta">
  <h1>{html.escape(obj.get('title', ''))}</h1>
  <span class="type">{html.escape(obj.get('type_name', ''))}</span>
  <span class="space">{html.escape(obj.get('space_name', ''))}</span>
  <div class="meta-grid">
    <span>ID: {obj['id']}</span>
    <span>Created: {obj.get('created_at', '')}</span>
    <span>Updated: {obj.get('updated_at', '')}</span>
  </div>
  {"<div class='tags'>" + tag_html + "</div>" if tag_html else ""}
</div>
<div class="content">
  {content_html}
</div>
</body></html>"""

        pdf_bytes = HTML(string=pdf_html).write_pdf()

        # Slugify title for filename
        slug = re.sub(r"[^\w\s-]", "", obj.get("title", "object").lower())
        slug = re.sub(r"[\s]+", "-", slug).strip("-") or "object"
        filename = f"{slug}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@router.get("/files", response_class=HTMLResponse)
async def files_explorer(request: Request):
    """File explorer page."""
    templates = _templates(request)
    ctx = _base_context(request, "files")
    csrf_token = _generate_csrf_token()
    ctx["csrf_token"] = csrf_token
    response = templates.TemplateResponse("files/explorer.html", ctx)
    response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="strict", path="/")
    return response


@router.get("/projection", response_class=HTMLResponse)
async def projection_status(request: Request):
    """Projection explorer page."""
    templates = _templates(request)
    ctx = _base_context(request, "projection")
    csrf_token = _generate_csrf_token()
    ctx["csrf_token"] = csrf_token
    response = templates.TemplateResponse("projection/status.html", ctx)
    response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="strict", path="/")
    return response


@router.get("/console", response_class=HTMLResponse)
async def cli_console(request: Request):
    """CLI console page."""
    templates = _templates(request)
    ctx = _base_context(request, "console")
    csrf_token = _generate_csrf_token()
    ctx["csrf_token"] = csrf_token
    response = templates.TemplateResponse("cli/console.html", ctx)
    response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="strict", path="/")
    return response
