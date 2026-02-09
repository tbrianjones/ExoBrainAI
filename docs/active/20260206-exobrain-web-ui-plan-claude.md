---
status: Planning
date: 2026-02-06
branch: feature/web-ui
related-adrs:
  - 002-sqlite-core-memory-layer
  - 003-exobrain-cli-architecture
  - 004-claude-code-first-ui
  - 005-api-layer
  - 006-information-centric-computing-vision
  - 007-projection-layer-architecture
future-adr: 010-web-ui-architecture
---

# ExoBrain Web UI: Admin Explorer

## Summary

ExoBrain's memory layer (SQLite, sharded file storage, projection layer) has no visual interface. Everything runs through CLI commands or Claude Code, making it hard to understand what's in the system, verify operations are working, and explore the data. This plan builds an MVP admin/explorer web UI integrated into the existing FastAPI service that lets the user see, explore, and interact with the entire memory layer from a browser.

## Agent Quick Start

**Load these files first:**
- `engine/src/api/main.py` ; FastAPI entry point (modify to add templates + new routers)
- `engine/src/core/repository.py` ; ObjectRepo, TagRepo, LinkRepo, FileRepo (all read queries use these)
- `engine/src/cli/main.py` ; CLI command interface (subprocess wrappers must match these flags/args)
- `engine/src/core/projection.py` ; Projection status functions for explorer page
- `engine/pyproject.toml` ; Add new dependencies here
- `engine/src/config.py` ; Settings and paths (EXOBRAIN_DATA_DIR, file_dir, projected_dir)

**Read these ADRs:**
- `docs/adr/002-sqlite-core-memory-layer.md` ; Schema, repository pattern, FTS5
- `docs/adr/003-exobrain-cli-architecture.md` ; CLI as sole write interface; --json output
- `docs/adr/006-information-centric-computing-vision.md` ; Interface flexibility vision
- `docs/adr/007-projection-layer-architecture.md` ; Projection scoring, sync, tier status

**Relevant skills:**
- `.claude/skills/exobrain.md` ; ExoBrain CLI interface patterns

**Explore:**
- `engine/src/api/routes/health.py` ; Example of existing API route using repos
- `engine/src/api/routes/` ; All existing routes (health, query, docs, admin)
- `engine/tests/conftest.py` ; Test fixtures pattern (tmp_data_dir, bootstrapped_db, sample_objects)
- `docker-compose.yml` ; Container setup (port 8420, volumes, env vars)

**Reference plans:**
- `docs/active/20260128-exobrain-projection-layer-plan-claude.md` ; Related projection layer plan

## Problem Statement

**User persona:** TBJ; system builder and primary user of ExoBrain

**Pain point:** The memory system stores objects in SQLite with files on disk and a projection layer that materializes markdown; all accessible only through CLI commands. Understanding what's in the system, verifying operations work correctly, and exploring relationships between objects requires remembering CLI syntax and reading raw JSON output. There's no way to visually browse, search, or interact with the knowledge base.

**Current state:** CLI (`exobrain` commands via Docker exec) and Claude Code commands are the only interfaces. The FastAPI service exists but serves only health/status endpoints and legacy GraphRAG queries. No CRUD endpoints for objects; no visual interface of any kind.

**Business impact:** Without visual feedback, it's difficult to verify the memory system is working correctly, understand what data exists, test projection/sync cycles, or build confidence in the system as it evolves. This blocks progression toward using ExoBrain as a real knowledge substrate.

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Time to understand system state | Minutes (run multiple CLI commands) | Seconds (open browser, see dashboard) | Manual observation |
| CLI commands needed for exploration | All exploration via CLI | Zero CLI needed for read operations | Can browse, search, filter entirely in browser |
| Operation verification | Run command, then run status/list to check | Trigger operation in UI, see result inline | Capture object via UI, see it appear in browser |
| Data discoverability | Must know ID or search term | Browse by type/space/tag, click through links | Navigate from dashboard to any object in 3 clicks |

## Feature Overview

A server-rendered web UI served from the existing FastAPI service on port 8420 that provides:

1. **Dashboard** ; system overview with object counts, type breakdown, projection stats, DB health
2. **Object Browser** ; filterable, searchable list of all objects with pagination
3. **Object Detail** ; full view of any object with tags, links, file attachment, edit/delete
4. **Projection Explorer** ; tier stats, scoring, override controls, trigger project/sync operations
5. **CLI Console** ; run any CLI command from the browser with formatted output history

### Core User Flow

1. Open `http://localhost:8420/` ; see dashboard with system stats
2. Click "Objects" in nav ; see all objects listed with type badges and tags
3. Filter by type (e.g., "Note") or search by keyword ; list updates instantly
4. Click an object ; see full detail: content, metadata, tags, links to other objects
5. Click a linked object ; navigate the knowledge graph
6. Click "Projection" ; see what's projected, scores, run projection cycle
7. Click "Console" ; run any CLI command and see structured output

## Scope

### In Scope (MVP)

- Dashboard with live system stats (object counts, DB size, projection health)
- Object browser with filtering (type, space, tag) and full-text search
- Object detail page with tags, links, file info, content display
- Inline tag add/remove on object detail
- Edit object title/summary/content via form
- Delete object with confirmation
- Projection explorer showing tier stats, scores, override lists
- Action buttons to trigger: project, project --cleanup, sync
- CLI console to run any exobrain command
- Render markdown content inline (objects and projected files)
- Render JSON prettily when displayed
- Show file metadata (path, MIME type, size, SHA256) for attachments
- Render common viewable file types inline (markdown, images, text)

### Out of Scope (Do Not Build)

- Conversational AI interface (stays in Claude Code; see ADR-004)
- User authentication or multi-user support (local-only system)
- Real-time WebSocket updates (HTMX polling or manual refresh is sufficient)
- GraphRAG query interface (existing /query endpoints remain separate)
- Mobile-responsive design (desktop browser is the target)
- Object creation wizard (use CLI console or direct capture endpoint)
- Link creation/management UI (use CLI console)
- Space hierarchy management UI (use CLI console)
- Custom CSS theme system
- Offline/PWA capabilities

### Dependencies

- Existing FastAPI service running in Docker (port 8420)
- Existing repository layer (ObjectRepo, TagRepo, LinkRepo, FileRepo)
- Existing CLI with --json support on all commands
- Existing projection layer (calculate_scores, get_tier_status, etc.)

## User Stories + Acceptance Criteria

### US-1: View System Dashboard

**As a** system operator, **I want to** see an overview of everything in ExoBrain when I open the browser, **so that** I can quickly understand system state.

**Given** the ExoBrain database is initialized
**When** I navigate to `http://localhost:8420/`
**Then** I see object counts by type, total tags, links, files, DB size, and projection stats

### US-2: Browse and Filter Objects

**As a** knowledge explorer, **I want to** browse all objects and filter by type, space, or tag, **so that** I can find specific objects without remembering CLI syntax.

**Given** objects exist in the database
**When** I navigate to `/objects` and select type "Note" from the filter dropdown
**Then** I see only Note objects listed with their titles, tags, and creation dates

### US-3: Search Objects

**As a** knowledge explorer, **I want to** search objects by keyword with instant results, **so that** I can find content quickly.

**Given** I am on the object browser page
**When** I type "quantum" in the search box and pause for 300ms
**Then** the object list updates to show only objects matching "quantum" (via FTS5)

### US-4: View Object Detail

**As a** knowledge explorer, **I want to** click an object and see everything about it, **so that** I understand its content, relationships, and metadata.

**Given** I am viewing the object browser
**When** I click on an object row
**Then** I see: title, type, space, content (rendered if markdown), summary, all tags, all links (clickable), file attachment info, created/updated timestamps

### US-5: Manage Object Tags

**As a** system operator, **I want to** add and remove tags from objects directly in the UI, **so that** I can organize without switching to the terminal.

**Given** I am viewing an object detail page
**When** I type a tag name and click "+"
**Then** the tag is added (via CLI subprocess) and the tag list refreshes inline

### US-6: Edit Object Content

**As a** system operator, **I want to** edit an object's title, summary, or content from the detail page, **so that** I can make quick corrections.

**Given** I am viewing an object detail page
**When** I modify the title field and submit the edit form
**Then** the object is updated (via CLI subprocess) and the page reflects the new title

### US-7: Explore Projection Layer

**As a** system operator, **I want to** see projection tier stats and trigger projection cycles, **so that** I can understand and control what gets projected.

**Given** I navigate to `/projection`
**When** the page loads
**Then** I see: total objects, projected count, hot tier limit, top 5 by score, always/never override lists, and action buttons

**When** I click "Run Projection"
**Then** the projection cycle runs (via CLI subprocess) and results appear inline on the page

### US-8: Run CLI Commands from Browser

**As a** system operator, **I want to** run any CLI command from the browser, **so that** I can test operations without switching to the terminal.

**Given** I navigate to `/console`
**When** I type "search quantum" and click Run
**Then** the command executes and formatted JSON output appears in the output area

## Key Decisions

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Frontend architecture | Integrated into existing FastAPI | Separate React SPA; Separate Svelte SPA | No new Docker service, no JS build step, no node_modules; simplest possible architecture |
| Template engine | Jinja2 | htmy (Python-native) | Battle-tested with FastAPI; familiar pattern; extensive documentation |
| Interactivity | HTMX (14KB CDN) | React; Vue; vanilla JS | HTML attributes trigger HTTP requests and swap fragments; no JS framework to maintain; no build step |
| Styling | Tailwind CSS via CDN | Custom CSS; Bootstrap; DaisyUI | Utility classes in HTML; no CSS files; no build step; rapid prototyping |
| Read path | API endpoints using repository layer directly | CLI subprocess for reads; Direct SQLite | Repository classes are thin, safe SQL wrappers; faster than subprocess; no side effects |
| Write path | API endpoints calling CLI via subprocess | API endpoints calling repository directly; WebSocket CLI | CLI remains sole write interface per ADR-003; prevents divergence as CLI evolves; --json output makes parsing easy |
| File rendering | Render markdown/images/text inline; metadata for other types | Metadata only; Render all types | GitHub-style approach; handles common cases without heavy infrastructure |

### Detail: Write Path via CLI Subprocess

The CLI is the canonical write interface (ADR-003). Rather than duplicating validation and business logic from CLI handlers into API endpoints, the web UI calls CLI commands via `asyncio.create_subprocess_exec`. This means:

- As the CLI evolves with new commands or validation, the web UI gets those changes for free
- No risk of the API doing things the CLI can't do (or vice versa)
- The `--json` flag on every CLI command provides structured output for parsing
- Subprocess overhead is negligible for local admin operations (in-container, no Docker exec)

### Detail: HTMX Instead of JS Framework

HTMX lets HTML elements make HTTP requests and swap page fragments. The server returns HTML (not JSON), which HTMX inserts into the DOM. Example: `<button hx-post="/ui-api/cli/project" hx-target="#result">Run</button>`. No JavaScript to write, no build process, no client-side state management. This matches the project's "keep simple" ethos and avoids introducing npm/webpack/vite infrastructure.

## Technical Approach

### Architecture

```
Browser (localhost:8420)
    |
    |  Full pages: GET /, /objects, /objects/{id}, /projection, /console
    |  HTMX fragments: GET/POST /ui-api/*
    v
FastAPI (existing service, same container)
    |
    |--- ui.py (page routes) ---> Jinja2 templates ---> HTML response
    |
    |--- ui_api.py (fragment routes)
    |       |
    |       |-- Reads ---> Repository layer ---> SQLite
    |       |
    |       |-- Writes --> asyncio.subprocess --> exobrain CLI --json
    |
    |--- health.py, query.py, docs.py, admin.py (existing, unchanged)
```

### File Structure

```
engine/src/api/
  main.py                                # MODIFY: add Jinja2, static mount, new routers
  routes/
    ui.py                                # NEW: full-page route handlers
    ui_api.py                            # NEW: HTMX fragments + CLI subprocess wrappers
  templates/
    base.html                            # NEW: shared layout (nav, Tailwind CDN, HTMX CDN)
    dashboard.html                       # NEW: system overview
    objects/
      browse.html                        # NEW: object list with filters
      detail.html                        # NEW: single object view
      _list.html                         # NEW: HTMX partial for object table rows
      _search_results.html               # NEW: HTMX partial for search results
    projection/
      status.html                        # NEW: projection explorer
      _status_fragment.html              # NEW: HTMX partial for refreshable stats
    cli/
      console.html                       # NEW: CLI command runner
      _output.html                       # NEW: HTMX partial for command output
    partials/
      _flash.html                        # NEW: notification banner
      _pagination.html                   # NEW: reusable pagination controls
  static/
    style.css                            # NEW: minimal custom CSS
engine/tests/test_ui_api.py              # NEW: UI endpoint tests
```

Files prefixed with `_` are HTMX partials: HTML fragments returned by `/ui-api/` endpoints, never rendered as full pages.

### Dependencies

Add to `engine/pyproject.toml` under `[project.optional-dependencies]` api group:
- `jinja2>=3.1.0` (template engine; optional FastAPI dependency made explicit)
- `python-multipart>=0.0.6` (form data parsing for POST endpoints)
- `markdown>=3.5.0` (server-side markdown rendering for content display)

No npm, no node_modules, no build step. Tailwind CSS and HTMX load from CDN in `base.html`.

### Key Code Patterns

**DB connection dependency:**
```python
from src.core.db import db_session, get_db_path

def get_db():
    with db_session(get_db_path()) as conn:
        yield conn
```

**Read endpoint (returns HTML fragment):**
```python
@router.get("/objects")
async def list_objects_fragment(request: Request, type: str = None, ...
                                conn = Depends(get_db)):
    objects = ObjectRepo(conn).list(type_name=type, ...)
    return templates.TemplateResponse("objects/_list.html", {"request": request, "objects": objects})
```

**Write endpoint (CLI subprocess):**
```python
async def run_cli(parts: list[str]) -> dict:
    cmd = ["exobrain"] + parts + ["--json"]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await proc.communicate()
    return {"success": proc.returncode == 0, "output": json.loads(stdout) if proc.returncode == 0 else stdout.decode(), "error": stderr.decode() or None}
```

**HTMX pattern (live search):**
```html
<input type="search" name="q"
    hx-get="/ui-api/search"
    hx-trigger="keyup changed delay:300ms"
    hx-target="#results-body">
```

**Content rendering:** Markdown rendered server-side via `markdown` library. JSON pretty-printed with `json.dumps(data, indent=2)`. Images served from file storage path. Other file types show metadata only.

## Implementation Phases

### Phase 1: Skeleton
Get a page rendering in the browser.
1. Add jinja2, python-multipart, markdown to pyproject.toml api extras
2. Create `templates/` and `static/` directories under `engine/src/api/`
3. Create `base.html` with Tailwind CDN, HTMX CDN, navigation sidebar
4. Create `dashboard.html` with placeholder content
5. Create `routes/ui.py` with `GET /` rendering dashboard
6. Update `main.py`: add Jinja2Templates, mount static files, include ui router
7. Rebuild Docker image; verify page loads at localhost:8420

**Verify:** Browser shows styled dashboard page with navigation links.

### Phase 2: Dashboard with Live Data
1. Create `routes/ui_api.py` with `GET /ui-api/stats` endpoint
2. Stats endpoint uses ObjectRepo, TagRepo, LinkRepo, FileRepo, get_tier_status()
3. Dashboard loads stats via HTMX: `hx-get="/ui-api/stats" hx-trigger="load"`
4. Display: object counts by type, tag/link/file counts, DB size, projection tier status

**Verify:** Dashboard shows real data from the ExoBrain database.

### Phase 3: Object Browser
1. Add `GET /objects` page route (loads types/spaces for filter dropdowns)
2. Add `GET /ui-api/objects` returning `_list.html` partial (supports ?type=&space=&tag=&q=&limit=&offset=)
3. Add `GET /ui-api/search` for live search with 300ms debounce
4. Object table: ID prefix, type badge, title, tags, created date
5. Filter dropdowns trigger HTMX swaps on table body
6. Pagination controls

**Verify:** Browse objects, filter by type, search by keyword, paginate through results.

### Phase 4: Object Detail + Write Operations
1. Add `GET /objects/{id}` page route
2. Detail template: all fields, tags (add/remove inline), links (clickable), file info, content (rendered markdown)
3. Implement `run_cli()` async subprocess helper
4. CLI wrapper endpoints: update, delete, tag add, tag remove
5. Edit form for title/summary/content
6. Delete with hx-confirm dialog

**Verify:** Click object from browser, see detail, add a tag, edit title, verify changes persist.

### Phase 5: Projection Explorer
1. Add `GET /projection` page route
2. Tier stats, top scores, always/never override lists
3. Action buttons: Run Projection, Cleanup, Sync All
4. CLI wrapper endpoints: project, project --cleanup, sync
5. Results appear inline after button clicks

**Verify:** View stats, click "Run Projection", see output. Check projected/ directory.

### Phase 6: CLI Console
1. Add `GET /console` page route
2. Text input + Run button; scrolling output history (newest first)
3. `POST /ui-api/cli/run` generic command runner with shlex parsing
4. Quick-action buttons: status, doctor, tier status, list, search
5. Output renders as styled terminal blocks; JSON pretty-printed

**Verify:** Type "status", see formatted output. Type "search quantum", see results.

## Open Questions

| Question | Impact | Notes |
|----------|--------|-------|
| Should the dashboard auto-refresh on an interval? | UX polish | Could add `hx-trigger="load, every 30s"` for live dashboard; defer to Phase 2 feedback |
| Should object detail support inline content editing with a markdown preview? | Complexity | Split-pane editor is significantly more work; text area is sufficient for MVP |
| Should the CLI console sanitize commands? | Security | Local-only system; basic safety (strip dangerous flags) may be sufficient; no auth |
| Should we add a file browser as a separate page? | Scope | File info is shown on object detail; a dedicated file tree view could come later |
| What port should the UI serve on if /health conflicts? | Routing | UI at `/`, existing API at `/health`, `/status`, `/query/*`, `/doc/*`, `/admin/*`; test for conflicts |

## Future Considerations

Items discussed but deferred:

- **Link graph visualization** ; network diagram showing relationships between objects; needs a JS graph library (e.g., D3, vis.js)
- **Batch operations** ; tag multiple objects at once, bulk delete, bulk projection override
- **Space hierarchy browser** ; tree view of space organization
- **Activity timeline** ; chronological view using access_log table
- **Mobile responsive design** ; not needed for local admin use
- **REST API formalization** ; proper CRUD API with OpenAPI docs (ADR-005 defers this)
- **Real-time updates via WebSocket** ; push projection changes to browser
- **Authentication** ; needed only if exposed beyond localhost

## Verification

### Build and Launch
```bash
cd /Users/tbj/projects/claude_writer
docker compose build exobrain
docker compose up -d
# Open http://localhost:8420/ in browser
```

### End-to-End Checks
1. Dashboard loads with real stats (object counts, DB size, projection info)
2. Object browser lists objects; filter by type returns filtered results
3. Search box returns matching objects within 300ms of typing
4. Object detail shows full content, tags, links, file metadata
5. Add a tag via detail page; tag appears without page reload
6. Edit object title; change persists (verify via `exobrain get <id> --json`)
7. Projection page shows tier stats; "Run Projection" shows cycle results
8. Console: run `status` and see formatted JSON output
9. Console: run `capture "test from UI" --title "Web Test" --type note --json`; verify object appears in browser

### Automated Tests
```bash
docker compose exec exobrain pytest tests/test_ui_api.py -v
```

## References

- [ADR-002: SQLite Core Memory Layer](../adr/002-sqlite-core-memory-layer.md)
- [ADR-003: ExoBrain CLI Architecture](../adr/003-exobrain-cli-architecture.md)
- [ADR-004: Claude Code as First UI](../adr/004-claude-code-first-ui.md)
- [ADR-005: API Layer Deferred](../adr/005-api-layer.md)
- [ADR-006: Information-Centric Computing Vision](../adr/006-information-centric-computing-vision.md)
- [ADR-007: Projection Layer Architecture](../adr/007-projection-layer-architecture.md)
- **Future ADR:** ADR-010 should document the web UI architecture decision (HTMX + Jinja2, CLI subprocess for writes, repository for reads)
