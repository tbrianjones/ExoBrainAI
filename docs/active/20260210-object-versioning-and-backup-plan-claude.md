---
status: Complete
date: 2026-02-10
branch: feature/web-ui-explorer
related-adrs:
  - 002-sqlite-core-memory-layer
  - 009-schema-migration-and-data-durability
  - 012-object-versioning-and-backup
---

# Object Versioning, Soft Delete, and Automated Backup

## Summary

ExoBrain lacked any recovery path for accidental edits or deletes. This feature adds three layers of protection: automated SQLite backups (using the built-in `.backup` API), trigger-based object version history, and soft delete with optional hard delete (purge). All 353 tests pass; migration 007 is applied.

## Agent Quick Start

**Files to load:**
- `docs/adr/012-object-versioning-and-backup.md` ; Architecture decisions
- `engine/src/backup.py` ; Backup engine (create, list, prune, restore, daemon)
- `engine/src/core/schema.py` ; Migration 007 (lines 169-240)
- `engine/src/core/repository.py` ; ObjectRepo changes (soft delete, purge, history, content hash)
- `engine/src/cli/main.py` ; New CLI commands (history, restore, undelete, purge, deleted, backup)
- `engine/src/core/models.py` ; ObjectHistoryEntry model
- `engine/src/config.py` ; Backup config settings
- `engine/src/api/main.py` ; Backup daemon lifespan registration

**ADRs to read:**
- [ADR-009](../adr/009-schema-migration-and-data-durability.md) ; Migration system, data durability guarantees
- [ADR-012](../adr/012-object-versioning-and-backup.md) ; Versioning architecture decisions

**Test files:**
- `engine/tests/test_history.py` ; 22 tests: content hash, versioning, history recording, backfill, verification
- `engine/tests/test_backup.py` ; 14 tests: create, list, prune, restore
- `engine/tests/test_repository.py` ; Updated: soft delete, purge, undelete, list_deleted tests

**Relevant skills:** `exobrain`

## Problem Statement

**User persona:** ExoBrain power user (the author) and Claude Code agents that modify objects programmatically.

**Pain point:** Updates overwrite in place with no undo. Deletes cascade permanently. The only backup is Dropbox syncing raw SQLite files (30-day window). An agent making a bad edit or accidental delete has zero recovery path within ExoBrain.

**Current state (before):** No version history, no soft delete, no automated backups. One bad `UPDATE` or `DELETE` and the content is gone.

**Business impact:** Personal knowledge is irreplaceable. A system designed for decades of use must protect against accidental data loss at every layer.

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Recovery from accidental delete | Impossible | `undelete` restores in seconds | `exobrain delete` + `exobrain undelete` |
| Recovery from bad edit | Impossible | `restore --version N` | `exobrain history` + `exobrain restore` |
| Backup coverage | Dropbox only | Automated hourly snapshots | `exobrain backup list` shows regular entries |
| Content integrity verification | None | Doctor verifies all hashes | `exobrain doctor --json` reports 0 mismatches |
| Test coverage | 308 tests | 353 tests (45 new) | `pytest tests/ -v` |

## Feature Overview

Three layers of protection, built in dependency order:

1. **Automated backup engine** (no schema dependency; built first)
   - `sqlite3.Connection.backup()` for transactionally consistent snapshots
   - Gzip compression; stored at `$EXOBRAIN_DATA_DIR/backups/`
   - Background daemon: checks every 15 min, backs up if >1 hour elapsed
   - Prunes backups older than 7 days
   - CLI: `backup`, `backup list`, `backup restore`

2. **Object version history** (trigger-based)
   - `version` column on objects (starts at 1, auto-incremented)
   - `content_hash` column (SHA-256 of title + summary + content)
   - `object_history` table stores previous versions (no FK; survives purge)
   - AFTER UPDATE triggers fire only when title/summary/content changes
   - No-op detection: same content_hash skips history recording

3. **Soft delete / hard delete**
   - `deleted_at` column: NULL = active, timestamp = soft-deleted
   - `delete()` sets timestamp; `purge()` does CASCADE + history removal
   - `undelete()` clears timestamp
   - All queries filter `WHERE deleted_at IS NULL` by default
   - `include_deleted` parameter on get/list/search/count for bypass

### Core User Flow

1. User creates/updates objects normally
2. On update, triggers record previous content into `object_history`
3. `exobrain history <ID>` shows all previous versions
4. `exobrain restore <ID> --version N` restores old content (creates new version)
5. `exobrain delete <ID>` soft-deletes (recoverable)
6. `exobrain undelete <ID>` restores soft-deleted object
7. `exobrain purge <ID> --yes` permanently removes object + history
8. Background daemon creates hourly backups automatically
9. `exobrain doctor` verifies content hashes for integrity

## Scope

**In scope (all complete):**
- ADR-012 documenting architecture decisions
- Backup engine with create/list/prune/restore/daemon
- Migration 007: version, content_hash, deleted_at, object_history, triggers, backup_log
- Repository: soft delete, purge, undelete, history, content hash, no-op detection, backfill, verification
- CLI: history, restore, undelete, purge, deleted, backup subcommands
- Updated doctor command with content hash verification
- 45 new tests; all 353 pass

**Out of scope (do not build):**
- Web UI diff view (deferred to follow-up PR; architecture scoped in ADR-012)
- Litestream to S3 (deferred to future phase)
- Write-count-based backup triggers (backup_log table created but daemon uses time-based only)
- `changed_columns` bitmask in history entries (column exists but always 0)
- Automatic backup before migration in code (documented as agent rule; manual `exobrain backup` required)

**Dependencies:**
- SQLite 3.27+ (for `backup()` API; already available)
- No new Python dependencies

## Key Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| History mechanism | Trigger-based | Event sourcing, CRDTs, git | Transparent to app code; impossible to bypass; minimal complexity |
| Delete default | Soft delete | Hard delete only | Personal knowledge is irreplaceable; default should be recoverable |
| Backup method | `sqlite3.Connection.backup()` | File copy, WAL checkpoint | Transactionally consistent hot backup; no locking |
| Content hash | SHA-256 of title+summary+content | Per-field hashing, no hashing | Single hash enables no-op detection and integrity verification |
| History FK | No FK to objects | FK with ON DELETE CASCADE | History must survive hard deletes (purge) for audit trail |
| Backup storage | `$EXOBRAIN_DATA_DIR/backups/` | Separate volume, S3 | Syncs via Dropbox automatically; S3 deferred |

## Technical Approach

### Schema Changes (Migration 007)

```sql
ALTER TABLE objects ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE objects ADD COLUMN content_hash TEXT;
ALTER TABLE objects ADD COLUMN deleted_at TEXT;

CREATE TABLE object_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    title TEXT, summary TEXT, content TEXT,
    content_hash TEXT, changed_by TEXT DEFAULT 'system',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(object_id, version)
);

-- Two AFTER UPDATE triggers with WHEN guards on title/summary/content changes:
-- objects_history_update: captures OLD values into object_history
-- objects_version_bump: increments version on the NEW row

CREATE TABLE backup_log (...);  -- For future write-count triggers
```

### Repository Layer

- `compute_content_hash()`: Module-level helper for SHA-256
- `create()`: Computes and stores content_hash
- `update()`: Computes new hash; skips if unchanged (no-op detection)
- `delete()`: `SET deleted_at = now()` (soft delete)
- `purge()`: `DELETE FROM objects` + `DELETE FROM object_history` + disk cleanup
- `undelete()`: `SET deleted_at = NULL`
- `list_history()`, `get_version()`, `list_deleted()`: New query methods
- `verify_content_hashes()`, `backfill_content_hashes()`: Integrity helpers
- All query methods: `WHERE deleted_at IS NULL` by default, `include_deleted` parameter

### Backup Engine (`engine/src/backup.py`)

- `create_backup()`: Uses `sqlite3.Connection.backup()`, gzip compresses
- `list_backups()`: Scans backup dir, parses timestamps from filenames
- `prune_backups()`: Deletes backups older than retention period
- `restore_backup()`: Decompresses and overwrites target database
- `backup_daemon()`: asyncio background task; checks every 15 min, backs up if >1h elapsed

### API Integration

- `engine/src/api/main.py`: Backup daemon registered via FastAPI `lifespan` context manager

### Configuration

- `EXOBRAIN_BACKUP_INTERVAL_MINUTES=60`
- `EXOBRAIN_BACKUP_RETENTION_DAYS=7`

## Implementation Phases

### Phase 1: ADR and Documentation [COMPLETE]
- [x] Write ADR-012
- [x] Update CLAUDE.md (ADR table, behavior rules, CLI commands)
- [x] Update ADR-009 (reference ADR-012, add migration 007 to history)

### Phase 2: Backup Engine [COMPLETE]
- [x] Create `engine/src/backup.py` (create, list, prune, restore, daemon)
- [x] Add backup config to `engine/src/config.py`
- [x] Add backup CLI commands (backup, backup list, backup restore)
- [x] Register backup daemon in `engine/src/api/main.py`

### Phase 3: Schema Migration [COMPLETE]
- [x] Add MIGRATION_007 to `engine/src/core/schema.py`
- [x] version, content_hash, deleted_at columns
- [x] object_history table with indexes
- [x] History and version bump triggers
- [x] backup_log table

### Phase 4: Repository Layer [COMPLETE]
- [x] Add `compute_content_hash()` helper
- [x] Update `create()` with content hash
- [x] Update `update()` with hash comparison and no-op detection
- [x] Change `delete()` to soft delete
- [x] Add `purge()`, `undelete()`, `list_deleted()`
- [x] Add `list_history()`, `get_version()`
- [x] Add `verify_content_hashes()`, `backfill_content_hashes()`
- [x] Add `deleted_at IS NULL` filter to get/list/search/count
- [x] Add `ObjectHistoryEntry` model

### Phase 5: CLI Commands [COMPLETE]
- [x] Update `delete` command (soft delete default, `--hard` flag)
- [x] Add `undelete` command
- [x] Add `purge` command
- [x] Add `deleted` command
- [x] Add `history` command
- [x] Add `restore` command
- [x] Update `doctor` with content hash verification
- [x] Update `init` with content hash backfill

### Phase 6: Tests [COMPLETE]
- [x] Create `test_history.py` (22 tests)
- [x] Create `test_backup.py` (14 tests)
- [x] Update `test_repository.py` (soft delete, purge, cascade tests)
- [x] All 353 tests pass

### Phase 7: Web UI Diff View [DEFERRED]
- [ ] `GET /ui/objects/{id}/history` ; version timeline page
- [ ] `GET /ui/objects/{id}/diff?v1=N&v2=M` ; side-by-side diff
- [ ] Server-side: `difflib.unified_diff`; client-side: `diff2html` via CDN

## Open Questions

| Question | Impact | Notes |
|----------|--------|-------|
| Should backup daemon log to backup_log table? | Low | Table exists; daemon currently uses filesystem timestamps only |
| Should `changed_columns` bitmask be populated? | Low | Column exists in history table; always 0 for now |
| Litestream to S3 timeline? | Medium | Mentioned in ADR-012 as future phase; no urgency with Dropbox |
| Web UI diff view priority? | Medium | Architecture scoped; ~110 lines estimated; deferred to follow-up PR |

## Future Considerations

- **Litestream to S3**: Continuous replication for disaster recovery beyond Dropbox
- **Web UI diff view**: Side-by-side version comparison using diff2html
- **Write-count triggers**: backup_log table supports tracking write counts between backups
- **History pruning**: Eventually may need to prune very old history entries (no immediate concern)
- **Dropbox Extended Version History**: Recommend 1-year add-on for additional safety net

## Verification

All verification steps have been completed:

```bash
# Unit tests: 353 pass (45 new)
docker compose exec exobrain python -m pytest tests/ -v

# Backup creation
docker compose exec exobrain exobrain backup --json

# Backup listing
docker compose exec exobrain exobrain backup list

# Migration applied
docker compose exec exobrain exobrain init --json

# Doctor with content hash verification
docker compose exec exobrain exobrain doctor --json
# Reports: integrity ok, fts ok, 0 hash mismatches, 0 orphaned files
```

## References

- [ADR-012: Object Versioning and Backup](../adr/012-object-versioning-and-backup.md)
- [ADR-009: Schema Migration and Data Durability](../adr/009-schema-migration-and-data-durability.md)
- [ADR-002: SQLite Core Memory Layer](../adr/002-sqlite-core-memory-layer.md)
