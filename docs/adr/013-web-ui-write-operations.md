# ADR-013: Web UI Write Operations

- **Status:** Accepted
- **Date:** 2026-02-10
- **Impact:** Medium
- **Related ADRs:** ADR-003 (CLI as Sole Write Interface), ADR-010 (Read-only Web UI), ADR-012 (Object Versioning and Backup)

## Context and Problem Statement

ADR-010 established a read-only web UI for ExoBrain, with an explicit note that write operations were a future consideration requiring a new ADR. ADR-012 introduced object versioning, soft delete, and automated backup, making destructive operations recoverable. With these safety nets in place, the most common write operations (delete and purge) can be exposed in the UI without the risk that previously justified a read-only constraint.

The central question: how should the web UI perform write operations while preserving the CLI as the sole write interface (ADR-003)?

## Decision Drivers

- ADR-010 originally specified a read-only UI, but versioning and backup (ADR-012) now make undo possible for most destructive actions
- Preserving link integrity after purge requires a tombstone approach instead of CASCADE DELETE, which destroys the relationship graph
- The CLI subprocess pattern introduces no new write path; the CLI remains the single source of truth for all mutations
- HX-Request header verification prevents non-HTMX POST requests, providing basic CSRF mitigation without token infrastructure
- Delete and purge are the most frequently needed write operations when browsing objects; forcing users to switch to the terminal for these actions breaks workflow

## Decision

### CLI Subprocess Writes via HTMX POST Endpoints

Write operations in the web UI route through CLI subprocess calls using `asyncio.create_subprocess_exec`, preserving the CLI as the sole write interface per ADR-003. The UI never writes to the database directly; it invokes the same CLI commands that Claude Code and terminal users invoke.

| Layer | Mechanism | Rationale |
|-------|-----------|-----------|
| Client | HTMX `hx-post` to `/ui-api/` endpoints | Consistent with existing HTMX fragment pattern from ADR-010 |
| Server | `asyncio.create_subprocess_exec("exobrain", ...)` | Reuses CLI validation, logging, and business logic |
| Safety | `hx-confirm` attribute on destructive actions | Native browser confirmation dialog; no custom modal needed |
| CSRF | Verify `HX-Request: true` header on all POST endpoints | Rejects non-HTMX requests; lightweight protection without token management |

### Initial Write Surface: Delete and Purge Only

The initial implementation exposes exactly two write operations:

| Operation | CLI Command | UI Trigger | Confirmation |
|-----------|-------------|------------|--------------|
| Soft delete | `exobrain delete <id> --yes` | Button on object detail page | `hx-confirm` dialog |
| Purge (tombstone) | `exobrain purge <id> --yes` | Button on object detail page | `hx-confirm` dialog |

No general editing UI is included. The write surface is intentionally minimal; only operations that are tedious to perform from the terminal while browsing objects in the UI.

### Tombstone Purge Instead of Hard Delete

The existing `purge` command performs a CASCADE DELETE, permanently removing the object row and all associated tags, links, and history. This destroys link integrity: other objects that reference the purged object lose their link targets silently.

The tombstone approach replaces hard delete with content clearing:

1. A new `purged_at` column on the `objects` table records when an object was tombstoned
2. Purge clears `title`, `summary`, and `content` but preserves the object row
3. All links, tags, and history remain intact
4. Tombstoned objects are excluded from normal queries but visible when explicitly requested
5. The object detail page shows a tombstone indicator for purged objects

This preserves the link graph. An object that was `derived-from` a purged source still has a valid link target; the target simply displays as "[purged]" rather than vanishing.

### Route Structure

All write endpoints live under the existing `/ui-api/` prefix established in ADR-010:

| Endpoint | Method | Action |
|----------|--------|--------|
| `/ui-api/objects/{id}/delete` | POST | Soft delete (sets `deleted_at`) |
| `/ui-api/objects/{id}/purge` | POST | Tombstone purge (clears content, sets `purged_at`) |

POST handlers verify the `HX-Request` header and return HTMX fragments that update the page state (e.g., replacing the action buttons with a "deleted" indicator, or redirecting to the object list).

## Alternatives Considered

### Keep UI Fully Read-Only (Current State)

- **Pro:** Zero risk of accidental data modification from the UI; simplest architecture
- **Con:** Delete and purge are common operations when reviewing objects in the browser; switching to the terminal interrupts the workflow
- **Verdict:** Rejected. The safety nets from ADR-012 (versioning, soft delete, automated backup) mitigate the risk that originally justified read-only.

### Direct Repository Writes from API Endpoints

- **Pro:** Lower latency; no subprocess overhead
- **Con:** Creates a second write path alongside the CLI, violating ADR-003. Business logic, validation, and audit logging would need to be duplicated or extracted into a shared layer.
- **Verdict:** Rejected. The CLI subprocess pattern preserves the single write path guarantee.

### REST API with JSON Endpoints

- **Pro:** Standard API design; reusable by other clients
- **Con:** HTMX fragment responses are simpler and consistent with the existing UI architecture (ADR-010). A JSON API would require client-side JavaScript to handle responses and update the DOM.
- **Verdict:** Rejected. HTMX fragments keep the zero-JS-authoring constraint from ADR-010 intact.

### Hard Delete (CASCADE) for Purge

- **Pro:** Complete removal; no residual data; simpler implementation
- **Con:** Destroys link integrity. Objects that reference the purged target lose their links via CASCADE DELETE. The relationship graph degrades silently over time.
- **Verdict:** Rejected. Tombstone purge preserves the link graph while still clearing sensitive or unwanted content.

## Consequences

### Positive

- Users can delete and purge objects directly from the UI while browsing
- Tombstone purge preserves the link graph; no silent loss of relationship integrity
- The CLI remains the single write authority; no new write path is introduced
- HX-Request header verification provides CSRF mitigation without additional infrastructure
- Soft delete is fully recoverable via `exobrain undelete`; tombstone purge clears content but keeps the structural record

### Negative

- Subprocess calls add latency (200-500ms per invocation, consistent with the overhead noted in ADR-003)
- Two concepts of "write" exist: direct CLI invocation and UI-via-CLI invocation (though they execute the same code path)
- The tombstone approach means purged objects consume a small amount of storage permanently (mitigated by the fact that content is cleared; only metadata remains)

### Neutral

- Future write operations (edit title, manage tags, create links) can follow the same subprocess pattern without architectural changes
- The `purged_at` column enables future UI features like "show purged objects" filters and purge audit trails

## Schema Changes (Migration 008)

| Change | Description |
|--------|-------------|
| `objects.purged_at` | ISO 8601 timestamp; NULL means active. Set when an object is tombstone-purged. |

The migration adds the column as nullable with no default, requiring no data backfill.

## Generated Skills

### `add-web-ui-write-operation`

Step-by-step checklist for adding a new write operation to the ExoBrain web UI. Use when user mentions add write operation, UI write, web delete, web edit, UI mutation, or POST endpoint.

**Workflow:**
1. Ensure the CLI command exists for the operation (CLI is sole write interface per ADR-003)
2. Add POST endpoint under `/ui-api/` prefix in route handlers
3. Implement via `asyncio.create_subprocess_exec("exobrain", ...)` to invoke CLI
4. Verify `HX-Request: true` header on the POST endpoint; reject requests without it
5. Add `hx-confirm` attribute on the UI trigger element for destructive operations
6. Return HTMX fragment that updates the relevant page section in place
7. Log subprocess invocations (command, exit code, stderr) for debugging

## Agent Rules

- MUST verify the `HX-Request` header on all POST endpoints; reject requests without it
- MUST use `hx-confirm` for all destructive operations (delete, purge)
- MUST route writes through CLI subprocess (`asyncio.create_subprocess_exec`); never write to the database directly from API handlers
- MUST NOT add write operations to the UI without updating this ADR or creating a new one
- SHOULD use tombstone purge instead of hard delete to preserve link integrity
- SHOULD return HTMX fragments from POST endpoints that update the relevant page section in place
- SHOULD log subprocess invocations (command, exit code, stderr) for debugging write failures
