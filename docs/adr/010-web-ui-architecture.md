# ADR-010: Web UI Architecture

- **Status:** Accepted
- **Date:** 2026-02-06
- **Impact:** Medium
- **Related ADRs:** ADR-002 (SQLite Core Memory Layer), ADR-003 (CLI as Sole Write Interface), ADR-004 (Claude Code First UI), ADR-005 (API Layer Deferred), ADR-006 (Information-Centric Vision), ADR-007 (Projection Layer)

## Context and Problem Statement

ExoBrain has no visual interface. Everything runs through CLI commands or Claude Code, making it difficult to understand what is in the system, verify operations work, and explore the data at a glance. A read-only web explorer would complement the existing CLI workflow without creating a competing write path.

## Decision Drivers

- Need to visualize object counts, types, tags, links, and file storage
- Must not introduce a competing write path; CLI remains the sole write interface (ADR-003)
- Must not increase deployment complexity; no new Docker services, no new ports, no JS build step
- Must integrate into existing infrastructure (FastAPI on port 8420)
- Should be lightweight and require zero client-side JavaScript authoring

## Decision

### Integrated Server-Rendered Web UI

Build a read-only explorer as server-rendered HTML within the existing FastAPI service, using:

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Templates | Jinja2 | Already a FastAPI ecosystem library; server-rendered HTML |
| Styling | Tailwind CSS (CDN) | Utility classes in HTML; no CSS files; no build step |
| Interactivity | HTMX (CDN) | HTML attributes trigger GET requests and swap page fragments; zero JS to write |
| Data access | Repository layer (read-only) | ObjectRepo, TagRepo, LinkRepo, FileRepo; safe, fast, no side effects |

### Key Constraints

1. **Read-only.** All UI endpoints are GET requests. No write operations to ExoBrain. All mutations continue through the CLI.
2. **Route isolation.** All UI routes under `/ui/` prefix. All HTMX fragment endpoints under `/ui-api/` prefix. Existing API routes (`/health`, `/status`, `/query/*`, `/doc/*`, `/admin/*`) are unchanged.
3. **No new Docker services.** Everything in the existing `exobrain` container on port 8420.
4. **No JS build step.** Tailwind and HTMX loaded from CDN. No npm, no node_modules, no webpack.
5. **Repository layer for data.** Read-only queries through ObjectRepo, TagRepo, LinkRepo, FileRepo. No direct SQL in route handlers.
6. **Path validation.** File explorer validates all paths stay within `$EXOBRAIN_DATA_DIR` to prevent path traversal.
7. **Markdown rendered server-side.** Content is rendered to HTML on the server via the `markdown` Python library.

### Pages (6 Views)

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `GET /ui/` | System overview: object counts, DB size, projection health |
| Object Browser | `GET /ui/objects` | Filterable list with live search, pagination |
| Object Detail | `GET /ui/objects/{id}` | Full metadata, rendered content, tags, links, files |
| File Explorer | `GET /ui/files` | Browse sharded file storage and projected directory |
| Projection Explorer | `GET /ui/projection` | Tier stats, top scores, override lists |
| CLI Console | `GET /ui/console` | Run whitelisted read-only CLI commands |

### Future Write Path

When write operations are needed in the UI, they should go through CLI subprocess calls (not direct repository writes) to prevent divergence between CLI and UI behavior. This is a future consideration; the initial implementation is strictly read-only.

## Alternatives Considered

### Separate React SPA

- **Pro:** Rich interactivity, large ecosystem
- **Con:** Requires Node.js, npm, build step, separate dev server, client-side state management, API contract. Massive increase in complexity for a read-only explorer.
- **Verdict:** Rejected. Overkill for server-rendered read-only views.

### Separate Service (e.g., Node.js or Streamlit)

- **Pro:** Complete separation of concerns
- **Con:** New Docker service, new port, deployment coordination, shared database access complexity
- **Verdict:** Rejected. Violates simplicity constraint; no benefit for read-only pages.

### htmy (Python HTMX Framework)

- **Pro:** Type-safe HTML generation in Python
- **Con:** Less established, smaller community, steeper learning curve
- **Verdict:** Rejected. Jinja2 templates with HTMX attributes are simpler and more widely understood.

### No UI (Status Quo)

- **Pro:** Zero effort
- **Con:** Cannot visually explore data, difficult to verify system state, poor developer experience
- **Verdict:** Rejected. Visual exploration provides significant value.

## Consequences

### Positive

- Visual exploration of all ExoBrain data without writing custom queries
- Auto-refreshing dashboard shows system health at a glance
- File explorer makes sharded storage and projected files browsable
- CLI console provides quick access to read-only commands from the browser
- Zero additional deployment complexity

### Negative

- CDN dependencies (Tailwind, HTMX) require internet for first load
- Server-rendered HTML is less interactive than a SPA
- Template files add to the codebase size

### Neutral

- Future write operations will require additional architectural decisions
- The UI is coupled to the repository layer API, which is stable

## Agent Rules

- MUST keep all UI endpoints as GET requests (read-only)
- MUST use repository layer for data access; no direct SQL in route handlers
- MUST validate file paths against `$EXOBRAIN_DATA_DIR` in the file explorer
- MUST render markdown server-side; no client-side rendering
- MUST keep all UI routes under `/ui/` prefix and HTMX endpoints under `/ui-api/`
- MUST NOT add write operations to the UI without a new ADR
- SHOULD use HTMX for dynamic updates instead of writing JavaScript
- SHOULD reuse existing repository methods rather than creating new queries
