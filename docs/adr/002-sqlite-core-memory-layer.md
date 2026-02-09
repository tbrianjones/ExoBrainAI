# ADR 002: SQLite Core Memory Layer

- **Status:** Accepted
- **Date:** 2026-01-27
- **Tags:** architecture, storage, sqlite, local-first
- **Impact:** High

## Context

ExoBrain v1 uses file-based storage: raw markdown files plus date-partitioned JSONL overlay annotations. This approach has several problems. There is no structured way to query, filter by type, or traverse relationships between objects. Finding anything requires running the full GraphRAG pipeline, which depends on a running Ollama instance and completed indexing. Simple operations like "list my recent notes" or "search for X" are impossible without the heavyweight infrastructure.

The system needs a structured base layer that provides instant searchability, structured queries, and data integrity without requiring GraphRAG or any external service. This base layer becomes the single source of truth, replacing the raw+overlay file system.

The conceptual model is "everything is an object." Types, spaces, and tags are all objects in the same table. The type system is self-referential: the `type` type object references itself. This creates a unified, queryable knowledge store where every piece of information follows the same structure.

## Decision Drivers

1. **Instant searchability**: Captured content must be searchable immediately; no pipeline or indexing delay
2. **Structured queries**: Filter by type, space, tag, date range, or any combination
3. **Data integrity**: Foreign key constraints, unique constraints, and transactions protect consistency
4. **Zero external dependencies**: The storage engine must be part of the Python standard library
5. **Single-user personal system**: No need for client/server database architecture; one user, one machine

## Considered Options

### Option 1: Keep file-based storage (raw markdown + JSONL overlays)

The current v1 approach. Raw markdown files in `raw/{uuidv7}.md` with overlay annotations in `overlay/annotations/{date}.jsonl`.

Rejected. No structured queries are possible without scanning all files. Cross-document queries require reading every JSONL partition. There is no way to filter by type or space without building a secondary index. The system is entirely dependent on GraphRAG for any kind of retrieval.

### Option 2: PostgreSQL

A full relational database with all the query capabilities needed.

Rejected. PostgreSQL requires an external server process, adds deployment complexity, and is overkill for a single-user personal knowledge system. The Docker setup would need a persistent Postgres container with volume management, backups, and configuration. For one user on one machine, this is unnecessary overhead.

### Option 3: SQLite (chosen)

SQLite is part of the Python standard library. The entire database is a single file. WAL mode enables concurrent reads while a single writer operates. FTS5 provides full-text search. No external server, no configuration, no deployment complexity.

## Decision Outcome

Chosen option: **SQLite with WAL mode, repository pattern, forward-only migrations, FTS5 search, and self-referential type system.**

The database is the single source of truth for all ExoBrain data. Every piece of knowledge is a typed, tagged, space-organized object stored in the `objects` table. Files on disk hold raw evidence (PDFs, images); the `content` column holds searchable text. The CLI is the sole write interface.

### Schema (Migration v1)

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    description TEXT
);

CREATE TABLE objects (
    id TEXT PRIMARY KEY,                          -- UUIDv7
    type_id TEXT NOT NULL REFERENCES objects(id),  -- self-referential for types
    space_id TEXT NOT NULL REFERENCES objects(id), -- FK to space object
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,                                  -- inline text content
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE object_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    tag_text TEXT NOT NULL,
    tag_object_id TEXT REFERENCES objects(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(object_id, tag_text)
);

CREATE TABLE links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id TEXT NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    to_id TEXT NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    relationship TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(from_id, to_id, relationship)
);

CREATE TABLE files (
    object_id TEXT PRIMARY KEY REFERENCES objects(id) ON DELETE CASCADE,
    path TEXT NOT NULL,                  -- relative to files_dir
    role TEXT NOT NULL DEFAULT 'primary', -- primary, markdown_conversion, source
    mime_type TEXT,
    size_bytes INTEGER,
    sha256 TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE VIRTUAL TABLE objects_fts USING fts5(
    title, summary, content,
    content='objects', content_rowid='rowid'
);

-- INSERT/UPDATE/DELETE triggers keep FTS5 index in sync with objects table
```

Indexes on: `objects.type_id`, `objects.space_id`, `objects.created_at`, `objects.updated_at`, `objects(type_id, created_at DESC)`, `object_tags.object_id`, `object_tags.tag_text`, `links.from_id`, `links.to_id`.

### Schema Additions (Migrations v2-v4)

Subsequent migrations have added:

- **v2:** Auto-update `updated_at` trigger (fires on any object modification)
- **v3:** `access_log` table for future scoring; `projection_override` column on objects (ADR-007)
- **v4:** Performance indexes (`updated_at`, composite `type_id, created_at DESC`); `source` column (values: `human`, `ai`, `import`, `system`); `status` column (values: `active`, `draft`, `archived`, `deprecated`); `is_system_object` column (marks bootstrap objects); link metadata columns (`source`, `confidence`)

See ADR-009 for the migration strategy and data durability guarantees.

### Key Design Choices

**Repository pattern (no ORM):** Thin Python classes whose methods contain SQL internally. Callers see `repo.create(title="My note")` and never see SQL. Same clean API as an ORM without the dependency or magic. If SQLite were ever swapped for another database, only repository internals change.

**Forward-only integer migrations:** A `schema_version` table tracks applied migrations by number. The `init` command applies any unapplied migrations automatically. No Alembic, no down migrations. This is the pattern SQLite-native tools like Datasette and Litestream use.

**UUIDv7 for IDs:** Time-sortable, globally unique. Bootstrap objects use hardcoded deterministic UUIDs so they are stable across installations. All user-created objects receive generated UUIDv7 values.

**Self-referential bootstrap:** The `type` type object points to itself as its own type. Types, spaces, and tags are all objects in the `objects` table. Bootstrap creates 11 types (`type`, `space`, `tag`, `document`, `transcript`, `note`, `url`, `concept`, `event`, `person`, `project`) and 5 spaces (`primitives`, `primitives/type`, `primitives/space`, `primitives/tag`, `inbox`). The `inbox` space is the default capture destination. Bootstrap is idempotent via `INSERT OR IGNORE` and uses hardcoded UUIDs. Bootstrap objects are marked with `is_system_object = 1` (migration v4) and filtered from user-facing list/search results.

**Content column for searchable text:** Short content is stored inline in a TEXT column, indexed by FTS5. Files on disk hold binary evidence (PDFs, images, source documents). The `content` column is for text that should be queryable; the `files` table references raw evidence.

**Two-level sharded file storage:** Files are stored at `files/{id[0:2]}/{id[2:4]}/{id}.{ext}`. Since UUIDv7 values have a time-based prefix, files created around the same time share shard directories. The scheme provides moderate fan-out (256 top-level dirs, 65536 second-level) appropriate for the expected scale. Empty shard directories are cleaned up on file detach.

**One file per object:** The `files` table uses `PRIMARY KEY (object_id)`, enforcing at most one file per object. If multiple attachments are needed, the design is to create separate objects and link them, aligning with the "everything is an object" philosophy.

**DB-first detach ordering:** When removing file attachments, the DB record is deleted before the disk file. If the process crashes between operations, the result is an orphaned file on disk (detectable by `doctor`). The alternative (disk first, DB second) would leave a dangling DB reference to a missing file, which is harder to detect and recover from.

**FTS5 content-sync via triggers:** The FTS5 table uses `content='objects'` (external content) with insert/delete/update triggers. This is the pattern recommended by the SQLite documentation. A `WHEN` guard on the `updated_at` auto-trigger prevents double FTS5 sync.

**Bootstrap FK-disable/re-enable pattern:** Bootstrap code disables foreign keys to insert self-referential objects (the "type" type has `type_id` pointing to itself), then re-enables FKs and runs `PRAGMA foreign_key_check` to verify. A `finally` block guarantees re-enablement.

**BEGIN/END-aware SQL splitting:** The migration runner parses SQL blocks line by line, tracking `BEGIN`/`END` blocks to avoid splitting trigger bodies at internal semicolons. This is a common pitfall in SQLite migration runners.

## Consequences

### Positive

- **Instant search**: FTS5 makes content searchable at insert time; no pipeline or delay
- **Structured queries**: Filter by type, space, tag, date range, or any combination via SQL
- **Data integrity**: Foreign key constraints, unique constraints, and transactions prevent inconsistency
- **Zero external dependencies**: SQLite is in the Python standard library; no server to install or configure
- **Simple backup**: Copy one file to back up the entire knowledge base
- **Self-describing schema**: The type system, space hierarchy, and tag vocabulary are all queryable objects in the same table
- **Portable**: Single `.db` file plus a `files/` directory; move them anywhere

### Negative

- **Single writer**: SQLite supports only one concurrent writer (WAL mode mitigates this for concurrent reads, and single-user usage means this is rarely a problem)
- **No built-in replication**: No master/replica or multi-node capability (acceptable for a personal system)
- **Schema changes require migrations**: Adding columns or tables means writing new migration SQL and incrementing the version number
- **No native JSON column type**: SQLite stores JSON as TEXT; queries against JSON fields require `json_extract()` (not currently needed but relevant for future schema evolution)

## Agent Rules

1. **MUST** enable WAL mode on every database connection. Call `PRAGMA journal_mode=WAL` immediately after opening the connection. WAL mode enables concurrent reads during writes and prevents locking issues.

2. **MUST** use the repository pattern for all database access. CLI commands and API code call repository methods; they never execute raw SQL directly. Repository classes live in `engine/src/core/repository.py`.

3. **MUST** use forward-only integer migrations. Never create "down" migrations. Never modify an existing migration after it has been applied. New schema changes get the next integer version number in `engine/src/core/schema.py`.

4. **MUST** use UUIDv7 for all new object IDs. Bootstrap objects use hardcoded deterministic UUIDs that are stable across installations. See `engine/src/core/bootstrap.py` for the canonical bootstrap UUID values.

5. **MUST** keep FTS5 triggers in sync with the `objects` table. Any migration that modifies the `objects` table schema must also update the FTS5 virtual table and its INSERT/UPDATE/DELETE triggers. FTS5 indexes the `title`, `summary`, and `content` columns.

6. **NEVER** use an ORM (SQLAlchemy, Peewee, Django ORM, etc.). The repository pattern with raw `sqlite3` is the chosen approach. ORMs add complexity, hide SQL behavior, and make SQLite-specific features (FTS5, `INSERT OR IGNORE`, pragma configuration) harder to use.

7. **MUST** run `PRAGMA foreign_key_check` after bootstrap completes. Bootstrap temporarily disables foreign keys (`PRAGMA foreign_keys = OFF`) to handle self-referential inserts; the check afterward verifies all references are valid.

8. **SHOULD** use the `content` column for searchable text and the `files` table for binary evidence. Short text (notes, summaries, transcripts) goes in `content`. PDFs, images, and source documents are attached as files. Both can coexist on the same object.

9. **MUST** enable foreign keys on every connection with `PRAGMA foreign_keys = ON`. SQLite does not enforce foreign keys by default; this pragma is required for constraint enforcement.

10. **MUST** make bootstrap idempotent. Use `INSERT OR IGNORE` for all bootstrap objects so that running `exobrain init` multiple times never creates duplicates or raises errors.

11. **SHOULD** support `--json` output on all CLI commands. Claude Code (the first UI) parses JSON output via the exobrain skill. Human-readable text is the default; `--json` produces machine-parseable output.

12. **MUST** store the database file and `files/` directory under `$EXOBRAIN_DATA_DIR`. This directory is the canonical data location. Derived data (GraphRAG indexes, caches, logs) belongs in `$EXOBRAIN_CACHE_DIR`.

13. **MUST** escape LIKE wildcard characters (%, _, \) in user-provided values used in LIKE clauses. Use the `_escape_like()` function from `repository.py` and include `ESCAPE '\'` in the SQL. This prevents accidental wildcard injection in prefix-matching queries.

14. **MUST** validate file paths in FileRepo operations using `_validate_path()` to ensure paths resolve within `files_dir`. This prevents path traversal attacks where a crafted path could escape the file storage directory.

15. **SHOULD** exclude bootstrap objects (types, spaces, tags) from FTS5 search results. Users searching for content should not see system infrastructure objects. The `search()` method filters by `type_id NOT IN (...)` to skip bootstrap type definitions.

## Future Work

These items were identified during review but are not critical for the current single-user system. They should be addressed when the relevant area is next modified.

**Transaction model.** Every repository method calls `conn.commit()` independently. Multi-step operations like `capture` (create object + add tags + attach file) use a compensating delete on failure rather than a true transaction rollback. This works but is fragile. A future improvement would add a `unit_of_work` context manager that defers commit until all steps succeed, giving true atomicity. The current auto-commit model should be documented as an explicit design choice until then.

**FTS5 improvements.** Two enhancements would improve search quality: (1) Add `tokenize='porter unicode61'` for stemmed search (finding "computing" when searching "compute"); (2) Use `bm25(10.0, 5.0, 1.0)` weighted ranking so title matches rank higher than content matches. ~~(3) Composite index `(type_id, created_at DESC)`:~~ completed in migration v4. Note: Migration v3 was used for the projection layer (ADR-007), adding `access_log` table and `projection_override` column.

**FTS5 rowid fragility.** The FTS5 table uses `content_rowid='rowid'`, linking to SQLite's implicit rowid on the `objects` table. `VACUUM` can reassign rowids, breaking FTS5 sync. Mitigation: add `WITHOUT ROWID` to the objects table (requires making `id TEXT PRIMARY KEY` explicit, which it already is) or avoid `VACUUM` in favor of `PRAGMA incremental_vacuum`. This is low risk since the `id` column is already the primary key and SQLite uses it as the rowid alias.

**`_split_sql` limitations.** The migration SQL parser handles `BEGIN...END` blocks but cannot handle semicolons inside SQL string literals or `CASE...END` expressions. This has not caused problems because no current migrations use these patterns, but future migrations should avoid them or the parser should be extended.

**Space hierarchy convention.** Spaces use a flat table with hierarchy encoded in the `summary` field (e.g., `work/exobrain`). The `space create` command auto-creates parents. This convention works but is not enforced at the schema level; it should be documented as an explicit design choice. A future migration could add a `parent_id` column if true hierarchical queries become necessary.

**Tag normalization.** Tags are normalized to lowercase and trimmed on insert (implemented in `TagRepo.add()`). Duplicate detection is case-insensitive. This was implemented as part of the expert review fixes (commit a4edf85).

**Deletion semantics for types/spaces.** Deleting a type or space object that other objects reference is blocked by foreign key constraints. The system prevents deleting bootstrap objects, but user-created types or spaces with dependents would fail silently. A future improvement could add a `--cascade` flag or a check-before-delete that reports dependents.

**CORS and API authentication.** The API uses `allow_origins=["*"]` with no authentication. This is acceptable while the API is read-only and bound to localhost, but must be addressed before any write endpoints are added to the API or the system is exposed beyond localhost.

## References

- PRD: `docs/archive/sqlite-base-memory-layer/20260127-exobrain-v2-sqlite-base-memory-layer-prd-chatgpt.md`
- Implementation Plan: `docs/archive/sqlite-base-memory-layer/20260127-exobrain-v2-sqlite-base-memory-layer-dev-plan-claude.md`
- ADR-001 (GraphRAG, being superseded): `docs/adr/001-exobrain-v2-graphrag-memory-engine.md`
- SQLite WAL Mode: https://www.sqlite.org/wal.html
- SQLite FTS5: https://www.sqlite.org/fts5.html
- UUIDv7: https://www.rfc-editor.org/rfc/rfc9562.html
