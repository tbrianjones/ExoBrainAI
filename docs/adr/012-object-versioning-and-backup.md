# ADR-012: Object Versioning, Soft Delete, and Automated Backup

- **Status:** Accepted
- **Date:** 2026-02-10
- **Impact:** High
- **Related ADRs:** ADR-002 (SQLite Core Memory Layer), ADR-009 (Schema Migration and Data Durability)

## Context and Problem Statement

ExoBrain currently has no version history for objects. Updates overwrite in place, deletes cascade permanently, and the only backup is Dropbox syncing the raw SQLite files (with a 30-day version window). An agent or user making a bad edit or accidental delete has no recovery path within ExoBrain itself.

Three layers of protection are needed:
1. **Automated database backups**: Pre-migration snapshots and periodic `.backup` snapshots
2. **Object-level version history**: Track changes to title, summary, and content over time
3. **Soft delete with hard delete (purge)**: Recoverable deletion as default; permanent removal as explicit action

## Decision Drivers

- Personal knowledge is irreplaceable; every destructive operation should be recoverable by default
- Agents (Claude Code commands) modify objects programmatically; mistakes should be undoable
- SQLite's built-in `.backup` API provides transactionally consistent snapshots with no dependencies
- Trigger-based history is transparent to application code and impossible to bypass
- The system must remain simple; no external services or complex infrastructure

## Decision

### 1. Trigger-Based History Tables

Object history is recorded via SQLite `AFTER UPDATE` triggers on the `objects` table. When `title`, `summary`, or `content` changes, the trigger captures the **previous** values into an `object_history` table before the overwrite.

Each object tracks a `version` integer (starts at 1, increments on content changes). The `object_history` table has no foreign key to `objects` so that history survives hard deletes.

A `content_hash` column (SHA-256 of `title + summary + content`) enables change detection: if the hash matches, the update is a no-op and no history entry is created.

### 2. Soft Delete as Default

`ObjectRepo.delete()` sets `deleted_at` to the current timestamp instead of `DELETE FROM`. Tags, links, and files remain attached. All query methods (`list`, `search`, `get`, `count`) filter `WHERE deleted_at IS NULL` by default, with an `include_deleted` parameter to bypass.

Hard delete (`ObjectRepo.purge()`) performs the original `DELETE FROM` with CASCADE, plus removes history entries. This is for permanent expungement only.

`ObjectRepo.undelete()` clears `deleted_at` to restore a soft-deleted object.

### 3. Automated SQLite Backup

A backup engine uses `sqlite3.Connection.backup()` for transactionally consistent snapshots, gzip-compressed and stored at `$EXOBRAIN_DATA_DIR/backups/`. The backup daemon runs as an asyncio background task in FastAPI's lifespan, checking every 15 minutes and creating a backup if >1 hour has elapsed since the last one. Backups older than 7 days are pruned automatically.

Configuration via environment variables:
- `EXOBRAIN_BACKUP_INTERVAL_MINUTES=60` (time between backups)
- `EXOBRAIN_BACKUP_RETENTION_DAYS=7` (prune threshold)

### 4. Dropbox as Sync Layer, Not Backup Layer

Dropbox syncs `$EXOBRAIN_DATA_DIR` (including the `backups/` subdirectory), but is not the backup strategy itself. The automated backup engine provides the actual backup guarantees. For additional durability, Dropbox's Extended Version History add-on (1 year) is recommended. Litestream to S3 is deferred to a future phase.

## Alternatives Considered

### Event Sourcing
- **Pro:** Complete audit trail; can replay to any point
- **Con:** Massive complexity for a personal knowledge system; requires separate read models; overkill for undo/restore
- **Verdict:** Trigger-based history provides undo/restore without architectural upheaval

### CRDTs (Conflict-Free Replicated Data Types)
- **Pro:** Multi-device merge without conflicts
- **Con:** ExoBrain is single-writer by design (one SQLite file); CRDTs add complexity with no benefit
- **Verdict:** Not applicable to the current architecture

### Git-Based Version Control
- **Pro:** Mature diffing and merge tooling
- **Con:** Objects are stored in SQLite, not files; would require export/import on every change; git history on binary DB files is useless
- **Verdict:** The projection layer already provides file-level access; in-database history is more appropriate

### Hard Delete Only (Current Behavior)
- **Pro:** Simple; no extra tables or columns
- **Con:** No recovery path; agents can permanently destroy content
- **Verdict:** Unacceptable for a personal knowledge system designed for decades of use

## Consequences

### Positive
- Every content change is recorded and recoverable
- Accidental deletes are recoverable via `undelete`
- Automated backups provide pre-migration snapshots and regular protection
- Content hash prevents duplicate history entries from no-op updates
- Triggers are transparent; no application code changes needed for history recording

### Negative
- `object_history` table will grow over time (mitigated by only tracking content changes, not metadata)
- Soft delete requires `WHERE deleted_at IS NULL` in all queries (systematic but pervasive change)
- Backup files consume disk space (mitigated by gzip compression and 7-day retention)
- Two delete concepts (soft and hard) add cognitive load to the CLI

### Neutral
- A future web UI diff view can leverage the history table for side-by-side comparison
- The `backup_log` table enables write-count-based backup triggers in a future iteration

## Schema Changes (Migration 007)

| Change | Description |
|--------|-------------|
| `objects.version` | Integer, starts at 1, auto-incremented by trigger |
| `objects.content_hash` | SHA-256 of title + summary + content |
| `objects.deleted_at` | ISO 8601 timestamp; NULL means active |
| `object_history` table | Stores previous versions (object_id, version, title, summary, content, content_hash, changed_by, created_at) |
| `objects_history_update` trigger | Captures old values on content changes |
| `objects_version_bump` trigger | Increments version on content changes |
| `backup_log` table | Records backup timestamps and paths |

## Agent Rules

- MUST run `exobrain backup` before applying schema migrations or making architectural database changes
- MUST use `exobrain delete` (soft delete) as the default; only use `exobrain purge` when permanent removal is explicitly requested
- MUST NOT bypass soft delete by running raw `DELETE FROM objects` SQL
- SHOULD check `exobrain history <ID>` before restoring to verify the correct version
- SHOULD run `exobrain doctor` after restore operations to verify content hash integrity
