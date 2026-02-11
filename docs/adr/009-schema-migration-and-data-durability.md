# ADR-009: Schema Migration and Data Durability

- **Status:** Accepted
- **Date:** 2026-02-06
- **Impact:** High
- **Related ADRs:** ADR-002 (SQLite Core Memory Layer), ADR-006 (Information-Centric Vision)

## Context and Problem Statement

ExoBrain is designed to hold personal knowledge for years. The SQLite database will accumulate irreplaceable content: ideas, transcripts, connections, and the emergent structure of a person's thinking. Unlike a web application where data can be reconstructed from external sources, ExoBrain's value is in the unique, personal nature of its contents.

During integration testing (2026-02-06), we discovered that a database created before the migration tracking system existed had no `schema_version` table. This caused the `list` command to crash with `OperationalError: no such column: o.is_system_object`. Running `exobrain init` fixed it by applying all four migrations, but this revealed a critical requirement: the migration system must handle databases from any era of the project's history, including databases that predate the migration system itself.

## Decision Drivers

- Personal knowledge is irreplaceable; data loss is unacceptable
- The schema will continue to evolve as features are added
- Databases may sit untouched for months between development sessions
- `exobrain init` is the user's first command after `docker compose up`; it must always succeed
- Forward-only migrations are simpler and safer than reversible ones
- The user syncs `$EXOBRAIN_DATA_DIR` via Dropbox; the DB file must survive sync conflicts

## Decision

### Migration System Guarantees

1. **`exobrain init` is safe on any database state.** Whether the database is brand new, was created before migrations existed, or has partial migrations applied, `init` must succeed and bring the schema to current state.

2. **Migrations are forward-only.** No down migrations. Each migration has an integer version and a SQL block. Migrations use `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, and `ALTER TABLE ADD COLUMN` which are idempotent or safely fail on duplicates.

3. **Migration tracking via `schema_version` table.** Created automatically by `run_migrations()` if it doesn't exist. Each applied migration records its version number and timestamp.

4. **Foreign keys disabled during DDL.** Migrations temporarily disable foreign key enforcement (`PRAGMA foreign_keys=OFF`) to handle self-referential schemas, then re-enable after.

5. **Each migration is atomic.** Applied in a single transaction; on failure, the transaction is rolled back and the migration is not recorded.

### Data Durability Guarantees

1. **Canonical data lives at `$EXOBRAIN_DATA_DIR`.** This is the only directory that matters for backup. Contains `exobrain.db`, `files/`, and `projected/`.

2. **WAL mode is always enabled.** Every connection sets `PRAGMA journal_mode=WAL`, which provides crash safety and allows concurrent reads during writes.

3. **Derived data is regenerable.** The cache directory (`/cache` in container) holds staged files, GraphRAG indexes, and logs. All can be rebuilt from the canonical database.

4. **Projected files are a cache, not a source.** If projected files are deleted, `exobrain project` regenerates them. If they diverge from the database, `exobrain sync` reconciles them.

5. **Bootstrap is idempotent.** `INSERT OR IGNORE` ensures bootstrap objects (types, spaces) are created once and never duplicated, regardless of how many times `init` runs.

### Breaking Changes Policy

If a future migration cannot be expressed as additive DDL (`ADD COLUMN`, `CREATE TABLE`, `CREATE INDEX`), the migration must:
1. Create the new structure alongside the old
2. Copy data from old to new
3. Drop the old structure (if safe) or leave it as dead weight
4. Never delete or rename columns that contain user data without an explicit backup step

### Backup Strategy

The primary backup mechanism is Dropbox sync of `$EXOBRAIN_DATA_DIR`. Additionally:
- SQLite's WAL mode ensures the database is always in a consistent state for file-level copy
- `exobrain doctor` validates integrity, FTS5 index, and orphaned files at any time
- The database is a single file; any file-level backup tool works
- **See [ADR-012](012-object-versioning-and-backup.md)** for the automated backup engine, which provides periodic gzip-compressed snapshots and pre-migration backup guarantees

## Alternatives Considered

### Alembic or Other Migration Framework
- **Pro:** Mature tooling, auto-generation, dependency tracking
- **Con:** Heavy dependency for a single-file SQLite database; Alembic's model assumes server databases with rollback capability
- **Verdict:** Custom forward-only migrations are simpler and sufficient for this use case

### Versioned Database Files (v1.db, v2.db)
- **Pro:** Simple; never modify an existing database
- **Con:** Requires export/import tooling, breaks Dropbox sync continuity, loses edit history
- **Verdict:** In-place migration is better for a personal knowledge store that grows continuously

### Schema-Less Storage (JSON Blobs)
- **Pro:** No migrations needed; store everything as JSON in a single column
- **Con:** Loses FTS5, loses relational queries, loses type safety
- **Verdict:** Structured schema with FTS5 is core to ExoBrain's value proposition

## Consequences

### Positive
- Databases from any era of development can be upgraded by running `init`
- No data loss during schema evolution
- User can trust that running `init` after a long hiatus will bring everything up to date
- Dropbox sync provides automatic backup without configuration
- `doctor` command provides on-demand integrity verification

### Negative
- Forward-only migrations mean mistakes accumulate (dead columns cannot be cleanly removed)
- No automated backup verification (user must trust Dropbox or set up their own)
- SQLite's `ALTER TABLE` is limited (no `DROP COLUMN` before SQLite 3.35, no `RENAME COLUMN` before 3.25)
- Large migrations on databases with thousands of objects could be slow

### Neutral
- A future `exobrain export` / `exobrain import` command pair would complement this strategy for explicit backups and cross-machine transfer

## Schema Evolution History

| Migration | Version | Description |
|-----------|---------|-------------|
| 001 | 1 | Core schema: objects, tags, links, files, FTS5, triggers |
| 002 | 2 | Auto-update `updated_at` trigger |
| 003 | 3 | Access log table, `projection_override` column |
| 004 | 4 | Performance indexes, `source`, `status`, `is_system_object` columns, link metadata |
| 005 | 5 | Move space paths from `summary` to `title`; space `title` is now the hierarchical path |
| 006 | 6 | Create View type and retype view-tagged Document objects to View |
| 007 | 7 | Object versioning (`version`, `content_hash`, `deleted_at`), `object_history` table, history/version triggers, `backup_log` table |

## Generated Skills

### `add-database-migration`

Step-by-step checklist for adding a new schema migration to ExoBrain. Use when user mentions add migration, new migration, schema change, add column, alter table, or database migration.

**Workflow:**
1. Run `exobrain backup` to create a pre-migration backup
2. Add new migration entry to `MIGRATIONS` list in `engine/src/core/schema.py`
3. Use additive DDL only: `ADD COLUMN`, `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`
4. Test against both fresh databases (`exobrain init` on empty DB) and databases with existing data
5. Run `exobrain init` to apply the migration
6. Run `exobrain doctor` to verify integrity after migration
7. Update the Schema Evolution History table in this ADR

## Agent Rules

- MUST run `exobrain init` after any container rebuild; it is always safe and idempotent
- MUST write new migrations as additive DDL (`ADD COLUMN`, `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`)
- MUST NEVER write migrations that delete or rename columns containing user data
- MUST test migrations against both fresh databases and databases with existing data
- MUST include migration version, description, and SQL in the `MIGRATIONS` list in `schema.py`
- SHOULD run `exobrain doctor` after applying migrations to verify integrity
- MUST ensure `$EXOBRAIN_DATA_DIR` is the only directory required for full data recovery
- SHOULD document each migration's purpose in the Schema Evolution History table above
- MUST NEVER require the user to manually edit the database or run raw SQL to recover from a migration
