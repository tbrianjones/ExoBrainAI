---
status: Planning
date: 2026-02-10
branch: feature/web-ui-explorer
related-adrs: [ADR-010, ADR-011, ADR-012, ADR-013, ADR-014]
---

# Web UI Explorer Pages: Future Roadmap

## Summary

The ExoBrain web UI currently has 8 pages (Dashboard, Objects, Object Detail, Tags, Spaces, Files, Projection, Console) that cover core browsing and system monitoring. This plan captures 9 proposed future pages that would deepen the UI into a comprehensive knowledge exploration surface; each page targets a distinct user need (trust, exploration, temporal awareness, provenance tracking) and introduces unique browsing patterns not yet present in the UI.

## Agent Quick Start

**Files to load:**
- `engine/src/core/repository.py` ; all repo classes and methods
- `engine/src/api/routes/ui.py` ; full-page route handlers
- `engine/src/api/routes/ui_api.py` ; HTMX fragment endpoints
- `engine/src/api/templates/base.html` ; navigation sidebar
- `engine/src/api/static/style.css` ; custom CSS rules

**ADRs to read:**
- [ADR-010](../adr/010-web-ui-architecture.md) ; Web UI architecture, constraints, page table
- [ADR-011](../adr/011-primitive-semantics-and-knowledge-gardening.md) ; Primitive semantic roles (spaces, types, tags, links)
- [ADR-012](../adr/012-object-versioning-and-backup.md) ; Object versioning, soft delete, backup
- [ADR-013](../adr/013-web-ui-write-operations.md) ; Write operations via CLI subprocess
- [ADR-014](../adr/014-inline-content-references.md) ; Inline content references

**Relevant skills:** `exobrain` (CLI interface for data queries)

**Areas to explore:**
- `engine/src/core/schema.py` ; database schema for new query patterns
- `engine/src/core/bootstrap.py` ; RELATIONSHIP_VOCABULARY for link types
- `engine/tests/test_ui_api.py` ; existing test patterns for UI endpoints

## Problem Statement

**User persona:** Knowledge worker who captures thoughts, documents, and connections in ExoBrain through CLI and Claude Code, then uses the web UI to explore, verify, and understand their growing knowledge base.

**Pain point:** The current UI lets users browse objects, tags, and spaces, but lacks deeper surfaces for understanding *relationships between objects* (links/graph), *temporal patterns* (when things were created/modified), *system integrity* (is the data healthy?), *provenance* (what did AI agents create vs. humans?), and *full-text search* (with snippets and facets). Users cannot yet build trust in the system's health, see how their knowledge is growing over time, or trace how content flows from capture to publication.

**Current state:** 8 pages covering core CRUD browsing. Links appear only on object detail pages. Timeline is implicit in creation dates. Health checks require the CLI `doctor` command. Search exists as a filter on the Objects page but lacks snippet highlighting and faceted results.

**Business impact:** Deeper exploration surfaces increase user confidence in the system, surface hidden connections, and make the knowledge base feel alive rather than a static archive.

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Pages covering core primitives | 4/4 (objects, tags, spaces, types in filters) | 4/4 with dedicated surfaces | Type and Link pages exist |
| System health visibility | CLI only (`doctor` command) | Browser-based health dashboard | Health page exists and runs checks |
| Temporal awareness | None (creation date column only) | Activity heatmap + timeline | Timeline page exists |
| Search quality | Basic FTS filter on Objects page | Dedicated search with snippets + facets | Search page exists |

## Feature Overview

Nine proposed pages, each with a unique browsing pattern and data source:

### Core User Flow

1. User navigates to a new page via the sidebar
2. Page loads with summary cards providing at-a-glance context
3. Primary content area renders the page's unique visualization (graph, timeline, tree, grid, etc.)
4. User interacts via search, filters, or direct manipulation
5. Clickthrough links connect back to the Object Detail page or other explorer pages

## Scope

### In Scope (9 Proposed Pages)

| Priority | Page | URL | Unique Browsing Pattern |
|----------|------|-----|------------------------|
| Must-have | Links / Graph | `/ui/links` | Relationship-first browsing; orphan detection; link type filtering |
| Must-have | Timeline / Activity | `/ui/timeline` | Chronological event stream; activity heatmap; temporal filtering |
| Must-have | Health / Integrity | `/ui/health` | Diagnostic checks run in browser; hash verification; FTS sync status |
| Nice-to-have | Provenance / Agent Activity | `/ui/provenance` | Source-based filtering (human/ai/import/system); agent audit trail |
| Nice-to-have | Dedicated Search | `/ui/search` | FTS5 with relevance ranking; snippet highlighting; faceted results |
| Nice-to-have | Types | `/ui/types` | Type catalog; usage counts; distribution visualization |
| Nice-to-have | Deleted / Trash | `/ui/trash` | Soft-deleted object browser; recovery actions; tombstone visibility |
| Nice-to-have | Idea Spaces | `/ui/ideas` | Creative workspace grouping transcripts/concepts/views; provenance chains |
| Future | Analytics / Growth | `/ui/analytics` | Growth trends; tag proliferation; link density over time |

### Out of Scope (Do Not Build)

- Real-time WebSocket push updates (polling or manual refresh is sufficient)
- Graph visualization libraries (D3, vis.js, etc.); start with table/list views for links
- Mobile-specific responsive design beyond Tailwind's default breakpoints
- User authentication or multi-user access control
- Write operations beyond what ADR-013 already covers (delete, purge)
- External integrations (webhooks, API imports; separate plan exists)

### Dependencies

- All pages follow ADR-010 constraints (read-only GET, HTMX fragments, repository layer)
- Write operations (if any) follow ADR-013 pattern (CLI subprocess with CSRF)
- Navigation sidebar may need grouping when it exceeds 7-8 items

## Proposed Pages: Detailed Design

### 1. Links / Graph (`/ui/links`)

**Unique value:** Browse relationships as first-class entities. Currently links only appear contextually on object detail pages; this page makes them the primary browsing dimension.

**Layout:**
- Summary cards: Total Links, Relationship Types, Orphan Objects (unlinked), Avg Links/Object
- Filter bar: relationship type dropdown, source filter (human/ai), direction toggle
- Link table: From Object, Relationship, To Object, Source, Confidence, Created
- Orphan sidebar: list of objects with zero incoming/outgoing links

**New repository methods needed:**
- `LinkRepo.list_all(limit, offset, relationship, source, sort_by, sort_order)` ; paginated link listing
- `ObjectRepo.count_orphans()` ; objects with no links in either direction
- `LinkRepo.count_by_relationship()` ; grouped counts for filter badges

**Routes:**
- `GET /ui/links` ; full page
- `GET /ui-api/links` ; HTMX fragment with link table
- `GET /ui-api/links/orphans` ; orphan object list fragment

### 2. Timeline / Activity (`/ui/timeline`)

**Unique value:** Chronological view showing when objects were created, updated, and linked. Reveals temporal rhythms of knowledge capture.

**Layout:**
- Summary cards: Objects Today, This Week, This Month, Total History Entries
- Activity heatmap: GitHub-style contribution grid (365 days, colored by activity count)
- Event stream: chronological list of create/update/delete events with object links

**Data sources:**
- `objects.created_at` for creation events
- `object_history.changed_at` for update events
- `objects.deleted_at` for deletion events

**New repository methods needed:**
- `ObjectRepo.activity_by_date(days)` ; daily counts for heatmap
- `ObjectRepo.recent_activity(limit, offset)` ; merged event stream from objects + history

**Routes:**
- `GET /ui/timeline` ; full page with heatmap
- `GET /ui-api/timeline/events` ; paginated event stream fragment

### 3. Health / Integrity (`/ui/health`)

**Unique value:** Run `doctor`-style checks in the browser. Directly builds trust that the knowledge system is healthy.

**Layout:**
- Summary cards: Total Checks, Passed, Warnings, Errors
- Check results table: Check Name, Status (pass/warn/fail), Details, Duration
- Action buttons: "Run All Checks", "Run Selected"

**Checks to expose:**
- Content hash verification (`ObjectRepo.verify_content_hashes()`)
- FTS5 index sync (compare FTS rowcount with objects rowcount)
- Foreign key integrity (`PRAGMA foreign_key_check`)
- Orphaned files on disk (files in storage with no DB record)
- Orphaned file records (DB records with no file on disk)

**New repository methods needed:**
- `ObjectRepo.fts_sync_status()` ; compare FTS and objects row counts
- `FileRepo.find_orphaned()` ; files on disk with no DB record

**Routes:**
- `GET /ui/health` ; full page
- `GET /ui-api/health/run` ; run checks and return results fragment

### 4. Provenance / Agent Activity (`/ui/provenance`)

**Unique value:** Filter objects by source (human, ai, import, system). See what AI agents created and verify their work.

**Layout:**
- Summary cards: Human Objects, AI Objects, Import Objects, System Objects
- Source distribution bar chart (horizontal stacked bar)
- Filterable object list with source column prominent

**Data source:** `objects.source` column (already exists: human, ai, import, system)

**New repository methods needed:**
- `ObjectRepo.count_by_source()` ; grouped counts

**Routes:**
- `GET /ui/provenance` ; full page
- `GET /ui-api/provenance/objects` ; filtered object list fragment

### 5. Dedicated Search (`/ui/search`)

**Unique value:** Full FTS5 search with relevance ranking, snippet highlighting, and faceted results by type/space/tag.

**Layout:**
- Large search input (prominent, Google-style)
- Result count and timing
- Facet sidebar: type filter, space filter, tag filter (with counts)
- Results list: title, snippet with highlighted terms, type badge, space, date

**New repository methods needed:**
- `ObjectRepo.search_with_snippets(query, limit, offset)` ; uses FTS5 `snippet()` function
- `ObjectRepo.search_facets(query)` ; type/space/tag counts for the current query

**Routes:**
- `GET /ui/search` ; full page
- `GET /ui-api/search` ; results fragment with facets

### 6. Types (`/ui/types`)

**Unique value:** Makes the ontology visible. See all types with descriptions, counts, and which spaces use them.

**Layout:**
- Summary cards: Total Types, Custom Types, Most Used Type
- Type grid: Type Name, Description, Object Count, Top Spaces, Created Date
- Similar to the Tags page pattern but for types

**New repository methods needed:**
- `ObjectRepo.list_types_enriched()` ; types with counts, top spaces, creation dates

**Routes:**
- `GET /ui/types` ; full page
- `GET /ui-api/types` ; type list fragment

### 7. Deleted / Trash (`/ui/trash`)

**Unique value:** Browse and recover soft-deleted objects. See tombstones with preserved links.

**Layout:**
- Summary cards: Soft-Deleted, Tombstoned, Recoverable
- Object table: Title, Type, Deleted At, with Restore/Purge action buttons
- Tombstone section: purged objects showing preserved link graph

**Existing methods:** `ObjectRepo.list_deleted()`, `ObjectRepo.count_deleted()`, `ObjectRepo.undelete()`
**Write operations:** Restore via `POST /ui-api/objects/{id}/undelete` (ADR-013 pattern)

**Routes:**
- `GET /ui/trash` ; full page
- `GET /ui-api/trash/objects` ; deleted objects fragment

### 8. Idea Spaces (`/ui/ideas`)

**Unique value:** Creative workspace view grouping transcripts, concepts, and views within idea spaces. Shows provenance chains (transcript -> concept -> view).

**Layout:**
- Idea space cards: each showing transcript count, concept count, view count, last activity
- Expandable space detail: provenance chain visualization
- "Generate View" and "Generate Transcript" action links (to Claude Code)

**Data source:** Objects in `ideas/*` spaces, linked via `derived-from` and `references` relationships

**New repository methods needed:**
- `ObjectRepo.idea_space_summary()` ; per idea-space counts by type, link chains

**Routes:**
- `GET /ui/ideas` ; full page
- `GET /ui-api/ideas/spaces` ; idea space cards fragment

### 9. Analytics / Growth (`/ui/analytics`)

**Unique value:** Longitudinal trends showing whether the knowledge base is growing, stagnating, or being pruned. "Is the system alive?"

**Layout:**
- Growth chart: objects created per week/month over time
- Tag proliferation: new tags per period
- Link density: links per object over time
- Space activity: heatmap of space usage over time

**New repository methods needed:**
- `ObjectRepo.growth_by_period(period, start, end)` ; counts by week/month
- `TagRepo.growth_by_period(period, start, end)` ; new tag counts
- `LinkRepo.growth_by_period(period, start, end)` ; new link counts

**Routes:**
- `GET /ui/analytics` ; full page
- `GET /ui-api/analytics/data` ; chart data as JSON or HTML fragment

## Key Decisions

| Decision | Alternatives Considered | Rationale |
|----------|------------------------|-----------|
| Table/list views before graph visualization | D3.js force graph, vis.js network | Simpler, fits HTMX pattern, no JS build step required; graph viz can be added later |
| Server-side heatmap rendering | Client-side JS charting library | Consistent with ADR-010 constraint of zero client-side JS authoring |
| Read-only pages first | Inline editing for all new pages | Follows progressive enhancement; ADR-013 covers write patterns when needed |
| Navigation grouping at 10+ items | Flat sidebar forever | Sidebar becomes unwieldy; group into "Explore" (Objects/Tags/Spaces/Links/Types) and "System" (Dashboard/Health/Projection/Console) sections |

## Implementation Phases

### Phase 1: Must-Have Pages
- Links / Graph page
- Timeline / Activity page
- Health / Integrity page
- Navigation grouping (if sidebar exceeds 10 items)

### Phase 2: Nice-to-Have Pages
- Dedicated Search page
- Types page
- Provenance / Agent Activity page
- Deleted / Trash page

### Phase 3: Specialized Pages
- Idea Spaces page
- Analytics / Growth page

## Open Questions

| Question | Impact | Notes |
|----------|--------|-------|
| Should the activity heatmap use a JS library or be pure server-rendered HTML? | Timeline page complexity | SVG generation in Python is possible but verbose; a small charting library (Chart.js CDN) may be acceptable |
| When should navigation grouping happen? | All pages | Current sidebar has 7 items; at 10+ it needs sections. Decide before adding Phase 1 pages |
| Should the Health page run checks asynchronously? | Health page UX | Some checks (content hash verification) could be slow on large databases; consider background execution with polling |
| Should Search replace the Objects page search bar? | Search page scope | Could unify search experience or keep both (Objects page search for filtered context, Search page for global exploration) |

## Future Considerations

- **Graph visualization**: Once the Links page proves useful in table form, consider adding a force-directed graph view using a CDN-loaded library
- **Real-time updates**: WebSocket or SSE for live activity feed on Timeline page
- **Export/print**: PDF export for Analytics charts and Health reports
- **Keyboard navigation**: Vim-style shortcuts for power users navigating between pages
- **Sidebar sections**: When the sidebar grows beyond 10 items, group into "Explore" (Objects, Tags, Spaces, Links, Types, Ideas) and "System" (Dashboard, Health, Projection, Console, Trash) sections

## Verification

For each new page implemented:
1. Add smoke test: `GET /ui/{page}` returns 200 with expected heading
2. Add HTMX fragment test: `GET /ui-api/{endpoint}` returns HTML with expected content
3. Add repository method unit tests with `sample_objects` fixture
4. Verify navigation sidebar highlights the active page
5. Verify clickthrough links navigate correctly to Objects page with pre-selected filters
6. Run full test suite: `docker compose exec exobrain python -m pytest tests/ -v`

## References

- [Web UI Architecture Plan](20260206-exobrain-web-ui-plan-claude.md) ; original MVP plan
- [Versioning UI Visibility Plan](20260210-versioning-ui-visibility-plan-claude.md) ; version history UI
- [ADR-010: Web UI Architecture](../adr/010-web-ui-architecture.md) ; architectural constraints
- [ADR-011: Primitive Semantics](../adr/011-primitive-semantics-and-knowledge-gardening.md) ; knowledge gardening vision
- Consider generating **ADR-015** if graph visualization or charting libraries are introduced (violates "zero JS authoring" constraint)
