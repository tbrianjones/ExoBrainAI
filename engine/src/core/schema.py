"""Database schema migrations.

Each migration is a tuple of (version, description, sql).
Migrations are forward-only and applied in order.
"""

MIGRATION_001 = """
-- Core objects table: everything is an object
CREATE TABLE IF NOT EXISTS objects (
    id TEXT PRIMARY KEY,
    type_id TEXT NOT NULL REFERENCES objects(id),
    space_id TEXT NOT NULL REFERENCES objects(id),
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Tags: semantic labels attached to objects
CREATE TABLE IF NOT EXISTS object_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    tag_text TEXT NOT NULL,
    tag_object_id TEXT REFERENCES objects(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(object_id, tag_text)
);

-- Links: explicit relationships between objects
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id TEXT NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    to_id TEXT NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    relationship TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(from_id, to_id, relationship)
);

-- Files: at most one file attachment per object
CREATE TABLE IF NOT EXISTS files (
    object_id TEXT PRIMARY KEY REFERENCES objects(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'primary',
    mime_type TEXT,
    size_bytes INTEGER,
    sha256 TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_objects_type_id ON objects(type_id);
CREATE INDEX IF NOT EXISTS idx_objects_space_id ON objects(space_id);
CREATE INDEX IF NOT EXISTS idx_objects_created_at ON objects(created_at);
CREATE INDEX IF NOT EXISTS idx_object_tags_object_id ON object_tags(object_id);
CREATE INDEX IF NOT EXISTS idx_object_tags_tag_text ON object_tags(tag_text);
CREATE INDEX IF NOT EXISTS idx_links_from_id ON links(from_id);
CREATE INDEX IF NOT EXISTS idx_links_to_id ON links(to_id);

-- FTS5 virtual table for full-text search across title, summary, content.
-- IMPORTANT: This relies on the implicit integer rowid that SQLite provides for
-- all tables unless they use WITHOUT ROWID. The objects table has a TEXT PRIMARY
-- KEY (id) but still gets an implicit rowid. Do NOT add WITHOUT ROWID to the
-- objects table; it would silently break all FTS5 triggers below.
-- WARNING: Do NOT run VACUUM on this database. VACUUM reassigns rowids,
-- breaking external-content FTS5 tables. Use incremental_vacuum instead.
CREATE VIRTUAL TABLE IF NOT EXISTS objects_fts USING fts5(
    title, summary, content,
    content='objects', content_rowid='rowid'
);

-- Triggers to keep FTS index in sync with objects table
CREATE TRIGGER IF NOT EXISTS objects_fts_insert AFTER INSERT ON objects BEGIN
    INSERT INTO objects_fts(rowid, title, summary, content)
    VALUES (new.rowid, new.title, new.summary, new.content);
END;

CREATE TRIGGER IF NOT EXISTS objects_fts_delete AFTER DELETE ON objects BEGIN
    INSERT INTO objects_fts(objects_fts, rowid, title, summary, content)
    VALUES ('delete', old.rowid, old.title, old.summary, old.content);
END;

CREATE TRIGGER IF NOT EXISTS objects_fts_update AFTER UPDATE ON objects BEGIN
    INSERT INTO objects_fts(objects_fts, rowid, title, summary, content)
    VALUES ('delete', old.rowid, old.title, old.summary, old.content);
    INSERT INTO objects_fts(rowid, title, summary, content)
    VALUES (new.rowid, new.title, new.summary, new.content);
END;
"""

MIGRATION_002 = """
-- Auto-update the updated_at timestamp on any object modification.
-- The WHEN guard prevents infinite recursion: the trigger only fires when the
-- caller did NOT already change updated_at. Without this guard, the UPDATE
-- inside the trigger would re-fire the trigger (infinite loop), and even with
-- SQLite's default recursive_triggers=OFF it would double-fire the FTS5 sync.
CREATE TRIGGER IF NOT EXISTS objects_auto_updated_at AFTER UPDATE ON objects
WHEN old.updated_at = new.updated_at
BEGIN
    UPDATE objects SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = new.id;
END;
"""

MIGRATION_003 = """
-- Track access for scoring (Phase 4; create table now, populate later)
CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    action TEXT NOT NULL,  -- 'read', 'write', 'search_hit'
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_access_log_object_id ON access_log(object_id);
CREATE INDEX IF NOT EXISTS idx_access_log_timestamp ON access_log(timestamp);

-- Projection override flag: NULL (use score), 'always', 'never'
ALTER TABLE objects ADD COLUMN projection_override TEXT;
"""

MIGRATION_004 = """
-- Performance: Index for projection scoring ORDER BY updated_at DESC
CREATE INDEX IF NOT EXISTS idx_objects_updated_at ON objects(updated_at);

-- Composite index for common query pattern: filter by type, order by created
CREATE INDEX IF NOT EXISTS idx_objects_type_created ON objects(type_id, created_at DESC);

-- Provenance: Track where content came from
-- Values: 'human' (user created), 'ai' (LLM generated), 'import' (external), 'system' (bootstrap)
ALTER TABLE objects ADD COLUMN source TEXT DEFAULT 'human';

-- Lifecycle: Object status for draft/archive workflows
-- Values: 'active' (default), 'draft', 'archived', 'deprecated'
ALTER TABLE objects ADD COLUMN status TEXT DEFAULT 'active';

-- System marker: Replace hardcoded bootstrap ID checks with queryable column
-- Set to 1 for all bootstrap objects (types, spaces, tags in primitives/)
ALTER TABLE objects ADD COLUMN is_system_object INTEGER DEFAULT 0;

-- Link metadata: Track provenance and confidence of relationships
ALTER TABLE links ADD COLUMN source TEXT DEFAULT 'human';
ALTER TABLE links ADD COLUMN confidence REAL DEFAULT 1.0;
"""

MIGRATION_005 = """
-- Bootstrap spaces: set title to their canonical path
UPDATE objects SET title = 'primitives' WHERE id = '00000000-0000-7000-8000-000000000101';
UPDATE objects SET title = 'primitives/type' WHERE id = '00000000-0000-7000-8000-000000000102';
UPDATE objects SET title = 'primitives/space' WHERE id = '00000000-0000-7000-8000-000000000103';
UPDATE objects SET title = 'primitives/tag' WHERE id = '00000000-0000-7000-8000-000000000104';
UPDATE objects SET title = 'primitives/relationship' WHERE id = '00000000-0000-7000-8000-000000000105';
UPDATE objects SET title = 'inbox' WHERE id = '00000000-0000-7000-8000-000000000201';

-- User-created spaces: move path from summary to title, clear summary
UPDATE objects SET title = summary, summary = NULL
WHERE type_id = '00000000-0000-7000-8000-000000000002'
AND id NOT LIKE '00000000%'
AND summary IS NOT NULL;
"""

MIGRATION_006 = """
-- Retype all view-tagged objects from Document to View.
-- The View type object (00000000-0000-7000-8000-00000000000c) is created by
-- bootstrap, which runs after migrations. This migration only retypes existing
-- objects; the UPDATE is a no-op if no view-tagged Documents exist or if the
-- View type hasn't been bootstrapped yet (init runs bootstrap immediately after).
UPDATE objects SET type_id = '00000000-0000-7000-8000-00000000000c'
WHERE id IN (SELECT object_id FROM object_tags WHERE tag_text = 'view')
AND type_id = '00000000-0000-7000-8000-000000000004';
"""

MIGRATION_007 = """
-- Object versioning: track version number (starts at 1, incremented by trigger)
ALTER TABLE objects ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

-- Content hash: SHA-256 of title + summary + content for change detection
ALTER TABLE objects ADD COLUMN content_hash TEXT;

-- Soft delete: NULL means active, ISO 8601 timestamp means deleted
ALTER TABLE objects ADD COLUMN deleted_at TEXT;

-- Index for efficient soft-delete filtering
CREATE INDEX IF NOT EXISTS idx_objects_deleted_at ON objects(deleted_at);

-- History table: stores previous versions of objects.
-- No FK to objects(id) because history must survive hard deletes (purge).
CREATE TABLE IF NOT EXISTS object_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    title TEXT,
    summary TEXT,
    content TEXT,
    content_hash TEXT,
    changed_by TEXT DEFAULT 'system',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(object_id, version)
);
CREATE INDEX IF NOT EXISTS idx_object_history_object_id ON object_history(object_id);
CREATE INDEX IF NOT EXISTS idx_object_history_created_at ON object_history(created_at);

-- Trigger: record previous state into history when content changes.
-- The WHEN clause uses IS NOT to handle NULL comparisons correctly
-- (NULL != NULL is NULL in SQL, but NULL IS NOT NULL is true).
-- Only fires when title, summary, or content actually changes.
CREATE TRIGGER IF NOT EXISTS objects_history_update
AFTER UPDATE ON objects
FOR EACH ROW
WHEN OLD.title != NEW.title OR OLD.summary IS NOT NEW.summary OR OLD.content IS NOT NEW.content
BEGIN
    INSERT OR IGNORE INTO object_history (object_id, version, title, summary, content, content_hash, changed_by)
    VALUES (OLD.id, OLD.version, OLD.title, OLD.summary, OLD.content, OLD.content_hash, 'system');
END;

-- Trigger: auto-increment version when content changes.
-- Uses the same WHEN guard as the history trigger.
-- The UPDATE inside this trigger does NOT re-fire the history trigger because
-- it only changes `version`, not title/summary/content.
CREATE TRIGGER IF NOT EXISTS objects_version_bump
AFTER UPDATE ON objects
FOR EACH ROW
WHEN OLD.title != NEW.title OR OLD.summary IS NOT NEW.summary OR OLD.content IS NOT NEW.content
BEGIN
    UPDATE objects SET version = OLD.version + 1 WHERE id = NEW.id;
END;

-- Backup log: records backup events for write-count triggers
CREATE TABLE IF NOT EXISTS backup_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    size_bytes INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    write_count INTEGER DEFAULT 0
);
"""

MIGRATION_008 = """
-- Tombstone support: purged objects keep their row and links but lose content.
-- purged_at is NULL for active objects, ISO 8601 timestamp for tombstoned objects.
ALTER TABLE objects ADD COLUMN purged_at TEXT;
CREATE INDEX IF NOT EXISTS idx_objects_purged_at ON objects(purged_at);
"""

MIGRATIONS: list[tuple[int, str, str]] = [
    (1, "Initial schema: objects, tags, links, files, FTS5", MIGRATION_001),
    (2, "Auto-update updated_at trigger", MIGRATION_002),
    (3, "Access log and projection override", MIGRATION_003),
    (4, "Performance indexes, source, status, is_system_object, link metadata", MIGRATION_004),
    (5, "Move space paths from summary to title", MIGRATION_005),
    (6, "Create View type and retype view-tagged documents", MIGRATION_006),
    (7, "Object versioning, soft delete, history triggers, backup log", MIGRATION_007),
    (8, "Tombstone support: purged_at column for link-preserving purge", MIGRATION_008),
]
