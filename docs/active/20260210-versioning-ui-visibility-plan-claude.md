---
status: Complete
date: 2026-02-10
branch: feature/web-ui-explorer
related-adrs:
  - 010-web-ui-architecture
  - 012-object-versioning-and-backup
  - 013-web-ui-write-operations
  - 003-exobrain-cli-architecture
---

# Versioning Visibility, Delete/Purge, and Backup Health in Web UI

## Summary

Commit 67c3331 added object versioning, soft delete, and automated backups to ExoBrain's backend, but none of this was visible in the web UI. This feature surfaces version history with inline diffs, adds the first write operations (soft delete and tombstone purge) via HTMX POST endpoints, and extends the dashboard with backup and data health statistics. ADR-013 was created to document the write operations architecture.

## Agent Quick Start

**Files to load:**
- `docs/adr/013-web-ui-write-operations.md` ; Write operations architecture
- `docs/adr/012-object-versioning-and-backup.md` ; Versioning and backup backend
- `docs/adr/010-web-ui-architecture.md` ; Web UI architecture (Jinja2 + HTMX + Tailwind)
- `engine/src/api/routes/ui_api.py` ; HTMX fragment endpoints and CLI wrappers
- `engine/src/core/repository.py` ; ObjectRepo (tombstone purge, count helpers, LinkRepo purged_at)
- `engine/src/core/schema.py` ; Migration 008 (tombstone support)
- `engine/src/api/templates/objects/detail.html` ; Object detail page (version display, delete/purge buttons, tombstone links)
- `engine/src/api/templates/objects/_history.html` ; Version history fragment
- `engine/src/api/templates/objects/_diff.html` ; Inline diff fragment
- `engine/src/api/templates/dashboard/_stats.html` ; Dashboard stats (backup + health cards)

**ADRs to read:**
- [ADR-013](../adr/013-web-ui-write-operations.md) ; Write operations via CLI subprocess
- [ADR-012](../adr/012-object-versioning-and-backup.md) ; Versioning, soft delete, backup
- [ADR-010](../adr/010-web-ui-architecture.md) ; Web UI architecture
- [ADR-003](../adr/003-exobrain-cli-architecture.md) ; CLI as sole write interface

**Relevant skills:**
- `exobrain` ; ExoBrain CLI interface

**Areas to explore:**
- `engine/src/api/templates/objects/` ; All object-related templates
- `engine/src/api/templates/dashboard/` ; Dashboard templates
- `engine/tests/test_repository.py` ; Tombstone and count helper tests
- `engine/tests/test_ui_api.py` ; UI endpoint tests for history, diff, delete/purge

## Problem Statement

**User persona:** ExoBrain user managing a growing knowledge base through the web UI

**Pain point:** Backend versioning, soft delete, and backup capabilities (ADR-012) were invisible in the web UI. Users had no way to see version history, compare changes, delete objects, or monitor backup health without dropping to the CLI.

**Current state (before):** Web UI was strictly read-only (ADR-010). No version information displayed. No delete or purge actions. Dashboard showed object counts but no backup or data health stats.

**Business impact:** The web UI is the primary browsing interface. Without visibility into versioning and data safety, users cannot trust the system or perform basic management tasks.

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Version history visible on detail page | Not shown | Shown for objects with version > 1 | Manual check |
| Inline diff viewable | Not available | Expandable per-version diffs | Manual check |
| Delete/purge actions available | CLI only | Buttons on detail page with confirmation | Manual check |
| Tombstone preserves links | Hard delete broke link graphs | Purged objects show as `[Purged]` in link tables | Test suite |
| Backup stats on dashboard | Not shown | Backup count, size, last backup, interval, retention | Manual check |
| Data health on dashboard | Not shown | Soft-deleted count, history entry count | Manual check |
| Test coverage | 353 tests | 387 tests | `pytest tests/ -v` |

## Feature Overview

Surfaces ExoBrain's data safety features in the web UI across three areas:

**1. Version History and Diff Viewer**
- Object detail page shows version number in metadata grid
- "Version History" section (lazy-loaded via HTMX) appears when version > 1
- Each historical version is expandable to show colored inline diffs (green additions, red deletions)
- Diffs are computed server-side using `difflib.unified_diff` for title, summary, and content fields

**2. Delete and Purge Actions**
- Two buttons in the actions dropdown on the object detail page
- "Mark Deleted" (amber): soft delete via CLI subprocess; redirects to object list
- "Delete Permanently" (red): tombstone purge via CLI subprocess; redirects to object list
- Both require native browser confirmation dialogs (`hx-confirm`)
- Both verify `HX-Request: true` header for CSRF protection

**3. Backup and Health Dashboard**
- New "Backups" card: last backup time, count, total size, interval, retention
- New "Data Health" card: soft-deleted objects count, version history entries count

### Core User Flow

1. User navigates to an object detail page
2. If the object has been edited (version > 1), a "Version History" section appears
3. User clicks a version row to expand and see the diff against the next version
4. User clicks the actions dropdown and selects "Mark Deleted" or "Delete Permanently"
5. Browser shows confirmation dialog; on confirm, POST request fires via HTMX
6. CLI subprocess executes the operation; user is redirected to the objects list
7. User visits the dashboard to see backup health and data integrity stats

## Scope

**In scope:**
- Version history display and inline diff viewer on object detail page
- Soft delete and tombstone purge buttons with confirmation
- Tombstone purge implementation (preserves object row and links, clears content)
- Migration 008: `purged_at` column for tombstone support
- `purged_at IS NULL` filters across all repository query methods
- LinkRepo: include `purged_at` in SELECTs for tombstone styling
- Dashboard: backup and data health statistics
- ADR-013: documenting write operations architecture
- Count helper methods: `count_deleted()`, `count_history_entries()`
- Tests: 34 new tests for tombstone behavior, history/diff endpoints, delete/purge endpoints, dashboard stats

**Out of scope (do not build):**
- Undo/undelete from the web UI (CLI only for now)
- Bulk delete operations
- Version restore from the web UI
- Edit/update operations in the web UI
- Backup restore from the web UI
- Real-time backup status or progress indicators

**Dependencies:**
- ADR-012 backend (versioning, soft delete, backup) must be in place
- Migration 007 must have been applied before migration 008

## User Stories and Acceptance Criteria

### US-1: View version history

**As a** knowledge base user, **I want to** see the version history of an object, **so that** I can understand how it has changed over time.

- **Given** an object with version > 1, **When** I view its detail page, **Then** a "Version History" section appears showing all previous versions with timestamps
- **Given** an object with version = 1, **When** I view its detail page, **Then** no history section is shown

### US-2: Compare versions with inline diffs

**As a** knowledge base user, **I want to** see what changed between versions, **so that** I can identify specific edits.

- **Given** a version entry in the history list, **When** I click to expand it, **Then** an inline diff appears showing additions (green) and deletions (red) for each changed field
- **Given** a version where only the title changed, **When** I expand the diff, **Then** only the title field diff is shown (not summary or content)

### US-3: Soft delete an object

**As a** knowledge base user, **I want to** mark an object as deleted from the web UI, **so that** I can remove it from view without permanent loss.

- **Given** I am on an object detail page, **When** I click "Mark Deleted" and confirm, **Then** the object is soft-deleted and I am redirected to the objects list
- **Given** a request without the `HX-Request` header, **When** the delete endpoint is called, **Then** it returns 403 Forbidden

### US-4: Permanently purge an object

**As a** knowledge base user, **I want to** permanently destroy an object's content, **so that** I can remove sensitive or irrelevant data.

- **Given** I am on an object detail page, **When** I click "Delete Permanently" and confirm, **Then** the object becomes a tombstone: title is `[Purged]`, content is cleared, but links remain intact
- **Given** another object links to a purged object, **When** I view the linking object's detail page, **Then** the link shows `[Purged]` in gray italic instead of a clickable link

### US-5: Monitor backup and data health

**As a** knowledge base user, **I want to** see backup status and data health on the dashboard, **so that** I can verify my data is protected.

- **Given** I am on the dashboard, **When** the page loads, **Then** I see backup count, total size, last backup time, interval, and retention
- **Given** I am on the dashboard, **When** the page loads, **Then** I see counts of soft-deleted objects and version history entries

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Write mechanism | CLI subprocess (`asyncio.create_subprocess_exec`) | Preserves ADR-003: CLI as sole write interface |
| CSRF protection | `HX-Request: true` header check | HTMX sends this automatically; simple and effective |
| Purge strategy | Tombstone (UPDATE, not DELETE) | Preserves link integrity; other objects' link graphs don't break |
| History deletion order | Delete history AFTER tombstone UPDATE | The UPDATE triggers `objects_history_update` which would re-create an entry |
| Confirmation UX | `hx-confirm` (native browser dialog) | Simple, no custom modal needed; consistent with HTMX patterns |
| Diff rendering | Server-side `difflib.unified_diff` | No client-side JS dependency; colored HTML rendered by Jinja2 |
| History loading | HTMX lazy load on page load | Avoids slowing down the main detail page render |

### Tombstone Purge (Detail)

The original `purge()` did `DELETE FROM objects WHERE id = ?` with CASCADE, which destroyed all links pointing to or from the object. This broke other objects' link graphs silently.

The tombstone approach instead:
1. Removes tags, file records, and disk files
2. Updates the object row: sets `title='[Purged]'`, clears `summary`/`content`/`content_hash`, sets `purged_at` and `deleted_at`
3. Deletes history entries AFTER the UPDATE (because the UPDATE fires the history trigger)
4. Links remain intact; the object row persists with its ID

### Trigger Ordering (Detail)

The `objects_history_update` trigger fires on any UPDATE that changes title, summary, or content. The tombstone UPDATE changes all three, so the trigger fires and creates a history entry. To ensure clean purge, history deletion must happen AFTER the tombstone UPDATE.

## Technical Approach

### Architecture

```
Browser (HTMX)
  |
  v
FastAPI endpoints (/ui-api/)
  |
  +-- GET /objects/{id}/history -> ObjectRepo.list_history() -> _history.html
  +-- GET /objects/{id}/diff/{version} -> ObjectRepo.get_version() + difflib -> _diff.html
  +-- POST /objects/{id}/delete -> asyncio.create_subprocess_exec("exobrain", "delete", ...) -> HX-Redirect
  +-- POST /objects/{id}/purge -> asyncio.create_subprocess_exec("exobrain", "purge", ...) -> HX-Redirect
  +-- GET /stats -> ObjectRepo.count_deleted(), count_history_entries(), list_backups() -> _stats.html
```

### Files Changed

| File | Change |
|------|--------|
| `docs/adr/013-web-ui-write-operations.md` | Created |
| `engine/src/core/schema.py` | Migration 008: `purged_at` column |
| `engine/src/core/repository.py` | Tombstone purge, `purged_at` filters, count helpers, LinkRepo `purged_at` |
| `engine/src/api/routes/ui_api.py` | History, diff, delete, purge endpoints; dashboard backup stats |
| `engine/src/api/templates/objects/detail.html` | Version display, delete/purge buttons, history section, tombstone links |
| `engine/src/api/templates/objects/_history.html` | Created: version history HTMX fragment |
| `engine/src/api/templates/objects/_diff.html` | Created: inline diff HTMX fragment |
| `engine/src/api/templates/dashboard/_stats.html` | Backup and data health cards |
| `engine/src/api/templates/base.html` | Removed "Read-only" label from sidebar |
| `CLAUDE.md` | Added ADR-013 to table |
| `engine/tests/test_repository.py` | Updated purge tests for tombstone; added TestObjectRepoPurgeTombstone, TestObjectRepoCountHelpers |
| `engine/tests/test_ui_api.py` | Added TestObjectHistory, TestObjectDiff, TestDeletePurgeEndpoints, TestDashboardBackupStats |

### Code Patterns

- **HTMX fragments**: GET endpoints return HTML partials via `templates.TemplateResponse()`
- **CLI subprocess writes**: POST endpoints verify `HX-Request` header, then `asyncio.create_subprocess_exec("exobrain", ...)` with 30s timeout
- **Tombstone filtering**: `AND o.purged_at IS NULL` added alongside `deleted_at IS NULL` in all query methods
- **Diff rendering**: `_render_diff_html()` helper uses `difflib.unified_diff` and `html.escape` for safe colored output

## Implementation Phases

### Phase 0: ADR-013 (Complete)
- Created `docs/adr/013-web-ui-write-operations.md`
- Updated `CLAUDE.md` ADR table

### Phase 1: Tombstone Schema and Repository (Complete)
- Added Migration 008 (`purged_at` column + index)
- Rewrote `purge()` as tombstone UPDATE
- Added `purged_at IS NULL` filters to all query methods
- Added `count_deleted()` and `count_history_entries()` helpers
- Updated LinkRepo to include `purged_at` in SELECTs

### Phase 2: Version History and Diff Viewer (Complete)
- Added `GET /ui-api/objects/{id}/history` endpoint
- Added `GET /ui-api/objects/{id}/diff/{version}` endpoint with `_render_diff_html()`
- Created `_history.html` and `_diff.html` templates
- Updated `detail.html` with version display and lazy-loaded history section

### Phase 3: Delete and Purge Buttons (Complete)
- Added `POST /ui-api/objects/{id}/delete` and `POST /ui-api/objects/{id}/purge` endpoints
- Updated `detail.html` with action dropdown buttons and `hx-confirm` dialogs
- Added tombstone styling in links table (`[Purged]` in gray italic)

### Phase 4: Backup and Health Dashboard (Complete)
- Extended `dashboard_stats()` with backup info and count helpers
- Updated `_stats.html` with Backups and Data Health cards
- Removed "Read-only" label from `base.html` sidebar

### Phase 5: Tests (Complete)
- Updated existing purge tests for tombstone behavior
- Added `TestObjectRepoPurgeTombstone` (14 tests) and `TestObjectRepoCountHelpers` (5 tests)
- Added UI API tests: history, diff, delete/purge, dashboard backup stats (14 tests)
- Total: 387 tests passing (up from 353)

## Open Questions

| Question | Impact | Notes |
|----------|--------|-------|
| Should undelete be exposed in the web UI? | Medium | Currently CLI only; would need another POST endpoint |
| Should version restore be in the web UI? | Medium | Currently CLI only; more complex UX (version selection) |
| Should we add a "trash" view for soft-deleted objects? | Low | Users can use CLI `exobrain deleted` for now |
| Should bulk delete be supported? | Low | Single-object operations only for now |

## Future Considerations

- **Undelete button**: Add a restore action for soft-deleted objects viewed with `include_deleted=True`
- **Version restore**: Allow restoring to a previous version from the history viewer
- **Trash view**: Dedicated page showing soft-deleted objects with undelete/purge actions
- **Audit log**: Track who performed delete/purge operations and when
- **Edit operations**: Extend write surface beyond delete/purge to title/summary/content editing
- **Batch operations**: Multi-select and bulk delete for power users

## Verification

```bash
# Apply migration and run tests
docker compose exec exobrain exobrain init
docker compose exec exobrain python -m pytest tests/ -v

# Manual verification
# 1. Browse to http://localhost:8420/ui/objects/{id} ; see version, history, delete buttons
# 2. Edit an object via CLI, reload ; version history appears with expandable diffs
# 3. Soft delete via UI button ; object disappears from list
# 4. Purge via UI button ; tombstone created, links show [Purged]
# 5. Dashboard at http://localhost:8420/ui/ ; backup and health stats visible
```

**Test results:** 387 passed, 0 failed, 42 warnings

## References

- [ADR-013: Web UI Write Operations](../adr/013-web-ui-write-operations.md)
- [ADR-012: Object Versioning and Backup](../adr/012-object-versioning-and-backup.md)
- [ADR-010: Web UI Architecture](../adr/010-web-ui-architecture.md)
- [ADR-003: CLI as Sole Write Interface](../adr/003-exobrain-cli-architecture.md)
- [Object Versioning and Backup Plan](20260210-object-versioning-and-backup-plan-claude.md) ; Backend plan (predecessor)
