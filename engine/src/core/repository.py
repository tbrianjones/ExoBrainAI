"""Repository layer for ExoBrain SQLite operations.

Thin Python classes over raw sqlite3. Callers see clean methods; SQL stays internal.
"""

from __future__ import annotations

import hashlib
import mimetypes
import shutil
import sqlite3
from pathlib import Path

from src.config import settings
from src.core.models import generate_id


def _escape_like(value: str) -> str:
    """Escape LIKE wildcard characters for safe use in LIKE clauses."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def compute_content_hash(title: str, summary: str | None, content: str | None) -> str:
    """Compute SHA-256 hash of an object's content fields.

    Used for change detection: if the hash matches, no history entry is created.
    """
    raw = f"{title}\0{summary or ''}\0{content or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


_SORT_COLUMNS = {
    "id": "o.id",
    "type": "t.title",
    "title": "o.title",
    "created": "o.created_at",
}


class ObjectRepo:
    """CRUD operations for ExoBrain objects."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(
        self,
        type_id: str,
        space_id: str,
        title: str,
        summary: str | None = None,
        content: str | None = None,
        id: str | None = None,
        source: str = "human",
        created_at: str | None = None,
    ) -> dict:
        """Create a new object. Returns the created object as a dict.

        Args:
            created_at: Optional ISO 8601 timestamp. When provided, sets both
                created_at and updated_at to bypass the auto-trigger.

        Note: Does not commit; caller is responsible for transaction management.
        """
        obj_id = id or generate_id()
        content_hash = compute_content_hash(title, summary, content)
        if created_at:
            self.conn.execute(
                """INSERT INTO objects (id, type_id, space_id, title, summary, content, source, content_hash, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (obj_id, type_id, space_id, title, summary, content, source, content_hash, created_at, created_at),
            )
        else:
            self.conn.execute(
                """INSERT INTO objects (id, type_id, space_id, title, summary, content, source, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (obj_id, type_id, space_id, title, summary, content, source, content_hash),
            )
        return self.get(obj_id)

    def get(self, obj_id: str, include_deleted: bool = False) -> dict | None:
        """Get an object by ID. Returns None if not found, soft-deleted, or purged.

        Args:
            include_deleted: If True, return soft-deleted and purged objects too.
        """
        deleted_filter = "" if include_deleted else "AND o.deleted_at IS NULL AND o.purged_at IS NULL"
        row = self.conn.execute(
            f"""SELECT o.*,
                      t.title as type_name,
                      s.title as space_name
               FROM objects o
               JOIN objects t ON o.type_id = t.id
               JOIN objects s ON o.space_id = s.id
               WHERE o.id = ? {deleted_filter}""",
            (obj_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def get_by_prefix(self, prefix: str, include_deleted: bool = False) -> dict | None:
        """Get an object by ID prefix (minimum 8 characters).

        Returns None if no match or multiple matches.
        """
        if len(prefix) < 8:
            return None
        safe_prefix = _escape_like(prefix)
        deleted_filter = "" if include_deleted else "AND o.deleted_at IS NULL AND o.purged_at IS NULL"
        rows = self.conn.execute(
            f"""SELECT o.*,
                      t.title as type_name,
                      s.title as space_name
               FROM objects o
               JOIN objects t ON o.type_id = t.id
               JOIN objects s ON o.space_id = s.id
               WHERE o.id LIKE ? ESCAPE '\\' {deleted_filter}""",
            (safe_prefix + "%",),
        ).fetchall()
        if len(rows) == 1:
            return dict(rows[0])
        return None

    def resolve_id(self, id_or_prefix: str, include_deleted: bool = False) -> str | None:
        """Resolve a full ID or prefix to a full ID. Returns None if unresolvable."""
        deleted_filter = "" if include_deleted else "AND deleted_at IS NULL AND purged_at IS NULL"
        # Try exact match first
        row = self.conn.execute(
            f"SELECT id FROM objects WHERE id = ? {deleted_filter}", (id_or_prefix,)
        ).fetchone()
        if row:
            return row["id"]
        # Try prefix match
        if len(id_or_prefix) >= 8:
            safe_prefix = _escape_like(id_or_prefix)
            rows = self.conn.execute(
                f"SELECT id FROM objects WHERE id LIKE ? ESCAPE '\\' {deleted_filter}",
                (safe_prefix + "%",),
            ).fetchall()
            if len(rows) == 1:
                return rows[0]["id"]
        return None

    def list(
        self,
        type_name: str | None = None,
        space_name: str | None = None,
        tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
        include_system: bool = False,
        include_deleted: bool = False,
        sort_by: str = "created",
        sort_order: str = "desc",
    ) -> list[dict]:
        """List objects with optional filters."""
        query = """
            SELECT DISTINCT o.id, o.type_id, o.space_id, o.title, o.summary,
                   o.created_at, o.updated_at,
                   t.title as type_name,
                   s.title as space_name
            FROM objects o
            JOIN objects t ON o.type_id = t.id
            JOIN objects s ON o.space_id = s.id
        """
        conditions = []
        params = []

        if not include_deleted:
            conditions.append("o.deleted_at IS NULL")
            conditions.append("o.purged_at IS NULL")

        if type_name:
            # Type filter takes precedence: when explicitly filtering by type,
            # system objects are always included (user is making a specific query).
            # The include_system flag applies only to unfiltered listings.
            conditions.append("LOWER(t.title) = ?")
            params.append(type_name.lower())
        elif not include_system:
            # Exclude system objects (types, spaces, tags) from default listing
            conditions.append("o.is_system_object = 0")

        if space_name:
            # Match objects IN the space, objects in child spaces,
            # and the space/subspace objects themselves (type = 'Space')
            conditions.append(
                "(LOWER(s.title) = ? OR LOWER(s.title) LIKE ?"
                " OR (LOWER(t.title) = 'space'"
                "     AND (LOWER(o.title) = ? OR LOWER(o.title) LIKE ?)))"
            )
            params.append(space_name.lower())
            params.append(space_name.lower() + "/%")
            params.append(space_name.lower())
            params.append(space_name.lower() + "/%")

        if tag:
            query += " JOIN object_tags ot ON o.id = ot.object_id"
            conditions.append("ot.tag_text = ?")
            params.append(tag)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        sort_col = _SORT_COLUMNS.get(sort_by, "o.created_at")
        order = "ASC" if sort_order.lower() == "asc" else "DESC"
        query += f" ORDER BY {sort_col} {order} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def update(
        self,
        obj_id: str,
        title: str | None = None,
        summary: str | None = None,
        content: str | None = None,
        space_id: str | None = None,
        projection_override: str | None | type(...) = ...,
    ) -> dict | None:
        """Update an object's mutable fields. Returns updated object or None.

        Computes content_hash for change detection. If content fields change,
        the hash is updated and triggers record history automatically.

        Args:
            projection_override: 'always', 'never', None (score-based), or ... (not provided)
        """
        fields = []
        params = []
        content_fields_changed = False

        if title is not None:
            fields.append("title = ?")
            params.append(title)
            content_fields_changed = True
        if summary is not None:
            fields.append("summary = ?")
            params.append(summary)
            content_fields_changed = True
        if content is not None:
            fields.append("content = ?")
            params.append(content)
            content_fields_changed = True
        if space_id is not None:
            fields.append("space_id = ?")
            params.append(space_id)
        if projection_override is not ...:
            fields.append("projection_override = ?")
            params.append(projection_override)

        if not fields:
            return self.get(obj_id)

        # Compute new content_hash if content fields changed
        if content_fields_changed:
            current = self.get(obj_id, include_deleted=True)
            if current is None:
                return None
            new_title = title if title is not None else current["title"]
            new_summary = summary if summary is not None else current["summary"]
            new_content = content if content is not None else current["content"]
            new_hash = compute_content_hash(new_title, new_summary, new_content)

            # Skip no-op: if hash matches current, no actual content change
            if current.get("content_hash") == new_hash:
                # Still apply non-content field changes (space, projection_override)
                non_content_fields = []
                non_content_params = []
                if space_id is not None:
                    non_content_fields.append("space_id = ?")
                    non_content_params.append(space_id)
                if projection_override is not ...:
                    non_content_fields.append("projection_override = ?")
                    non_content_params.append(projection_override)
                if non_content_fields:
                    non_content_params.append(obj_id)
                    self.conn.execute(
                        f"UPDATE objects SET {', '.join(non_content_fields)} WHERE id = ?",
                        non_content_params,
                    )
                return self.get(obj_id)

            fields.append("content_hash = ?")
            params.append(new_hash)

        # updated_at is set automatically by the objects_auto_updated_at trigger
        params.append(obj_id)

        self.conn.execute(
            f"UPDATE objects SET {', '.join(fields)} WHERE id = ?", params
        )
        # Note: Does not commit; caller is responsible for transaction management.
        return self.get(obj_id)

    def delete(self, obj_id: str) -> bool:
        """Soft-delete an object by setting deleted_at timestamp.

        Tags, links, and files remain attached. The object becomes invisible
        to list/search/get by default but can be recovered with undelete().

        Note: Does not commit; caller is responsible for transaction management.
        Returns True if soft-deleted.
        """
        cursor = self.conn.execute(
            "UPDATE objects SET deleted_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ? AND deleted_at IS NULL",
            (obj_id,),
        )
        return cursor.rowcount > 0

    def purge(self, obj_id: str) -> bool:
        """Tombstone an object: clear content but preserve the row and links.

        Removes history entries, tags, and file attachment. Sets title to
        '[Purged]', clears summary/content/content_hash, sets purged_at
        and deleted_at timestamps. Links remain intact so other objects'
        link graphs are not broken.

        Note: Does not commit; caller is responsible for transaction management.
        Returns True if purged.
        """
        # Check object exists
        row = self.conn.execute("SELECT id FROM objects WHERE id = ?", (obj_id,)).fetchone()
        if not row:
            return False

        # Clean up disk file before removing file record
        file_repo = FileRepo(self.conn)
        file_info = file_repo.get(obj_id)
        if file_info:
            full_path = FileRepo._validate_path(settings.files_dir / file_info["path"])
            if full_path.exists():
                full_path.unlink()
            for parent in [full_path.parent, full_path.parent.parent]:
                try:
                    parent.rmdir()
                except OSError:
                    break

        # Remove tags
        self.conn.execute("DELETE FROM object_tags WHERE object_id = ?", (obj_id,))

        # Remove file record
        self.conn.execute("DELETE FROM files WHERE object_id = ?", (obj_id,))

        # Tombstone the object row: clear content, set purged_at.
        # This UPDATE fires the objects_history_update trigger (which records the
        # pre-tombstone state), so we delete history AFTER the UPDATE to ensure
        # the trigger-created entry is also cleaned up.
        self.conn.execute(
            """UPDATE objects SET
                title = '[Purged]',
                summary = NULL,
                content = NULL,
                content_hash = NULL,
                purged_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                deleted_at = COALESCE(deleted_at, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            WHERE id = ?""",
            (obj_id,),
        )

        # Remove history entries AFTER the tombstone UPDATE, because the UPDATE
        # fires the history trigger which would re-create an entry.
        self.conn.execute("DELETE FROM object_history WHERE object_id = ?", (obj_id,))

        return True

    def undelete(self, obj_id: str) -> bool:
        """Restore a soft-deleted object by clearing deleted_at.

        Note: Does not commit; caller is responsible for transaction management.
        Returns True if restored.
        """
        cursor = self.conn.execute(
            "UPDATE objects SET deleted_at = NULL WHERE id = ? AND deleted_at IS NOT NULL",
            (obj_id,),
        )
        return cursor.rowcount > 0

    def list_deleted(self, limit: int = 50) -> list[dict]:
        """List all soft-deleted objects (excludes tombstoned/purged)."""
        rows = self.conn.execute(
            """SELECT o.id, o.type_id, o.space_id, o.title, o.summary,
                      o.created_at, o.updated_at, o.deleted_at,
                      t.title as type_name,
                      s.title as space_name
               FROM objects o
               JOIN objects t ON o.type_id = t.id
               JOIN objects s ON o.space_id = s.id
               WHERE o.deleted_at IS NOT NULL AND o.purged_at IS NULL
               ORDER BY o.deleted_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_history(self, obj_id: str) -> list[dict]:
        """Return all history entries for an object, ordered by version."""
        rows = self.conn.execute(
            """SELECT * FROM object_history
               WHERE object_id = ?
               ORDER BY version ASC""",
            (obj_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_version(self, obj_id: str, version: int) -> dict | None:
        """Return a specific historical version of an object."""
        row = self.conn.execute(
            """SELECT * FROM object_history
               WHERE object_id = ? AND version = ?""",
            (obj_id, version),
        ).fetchone()
        return dict(row) if row else None

    def search(
        self,
        query: str,
        limit: int = 20,
        include_system: bool = False,
        include_deleted: bool = False,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[dict]:
        """Full-text search across title, summary, and content.

        User input is quoted to prevent FTS5 syntax injection (AND, OR, NOT,
        NEAR, column filters, etc.). Special characters like +, *, (, ) in
        raw queries would otherwise cause FTS5 parse errors.

        When sort_by is None, results are ordered by FTS rank (relevance).
        """
        # Quote the query to force literal matching; escape internal quotes
        safe_query = '"' + query.replace('"', '""') + '"'

        system_filter = "" if include_system else "AND o.is_system_object = 0"
        deleted_filter = "" if include_deleted else "AND o.deleted_at IS NULL AND o.purged_at IS NULL"

        if sort_by and sort_by in _SORT_COLUMNS:
            sort_col = _SORT_COLUMNS[sort_by]
            order = "ASC" if sort_order.lower() == "asc" else "DESC"
            order_clause = f"ORDER BY {sort_col} {order}"
        else:
            order_clause = "ORDER BY rank"

        rows = self.conn.execute(
            f"""SELECT o.id, o.type_id, o.space_id, o.title, o.summary,
                      o.created_at, o.updated_at,
                      t.title as type_name,
                      s.title as space_name,
                      rank
               FROM objects_fts fts
               JOIN objects o ON o.rowid = fts.rowid
               JOIN objects t ON o.type_id = t.id
               JOIN objects s ON o.space_id = s.id
               WHERE objects_fts MATCH ?
               {system_filter}
               {deleted_filter}
               {order_clause}
               LIMIT ?""",
            (safe_query, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self, type_name: str | None = None, include_deleted: bool = False) -> int:
        """Count objects, optionally filtered by type name."""
        deleted_filter = "" if include_deleted else "AND o.deleted_at IS NULL AND o.purged_at IS NULL"
        if type_name:
            if not type_name.strip():
                return 0
            row = self.conn.execute(
                f"""SELECT COUNT(*) as cnt FROM objects o
                   JOIN objects t ON o.type_id = t.id
                   WHERE LOWER(t.title) = ? {deleted_filter}""",
                (type_name.lower(),),
            ).fetchone()
        else:
            deleted_where = "" if include_deleted else "WHERE o.deleted_at IS NULL AND o.purged_at IS NULL"
            row = self.conn.execute(
                f"SELECT COUNT(*) as cnt FROM objects o {deleted_where}"
            ).fetchone()
        return row["cnt"]

    def count_by_type(self, include_deleted: bool = False) -> dict[str, int]:
        """Count objects grouped by type name."""
        deleted_filter = "" if include_deleted else "WHERE o.deleted_at IS NULL AND o.purged_at IS NULL"
        rows = self.conn.execute(
            f"""SELECT t.title as type_name, COUNT(*) as cnt
               FROM objects o
               JOIN objects t ON o.type_id = t.id
               {deleted_filter}
               GROUP BY t.title
               ORDER BY cnt DESC"""
        ).fetchall()
        return {r["type_name"]: r["cnt"] for r in rows}

    def list_types(self) -> list[dict]:
        """List all type objects."""
        from src.core.bootstrap import BOOTSTRAP_IDS

        rows = self.conn.execute(
            """SELECT id, title, summary FROM objects
               WHERE type_id = ? ORDER BY title""",
            (BOOTSTRAP_IDS["type"],),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_spaces(self) -> list[dict]:
        """List all space objects."""
        from src.core.bootstrap import BOOTSTRAP_IDS

        rows = self.conn.execute(
            """SELECT id, title, summary FROM objects
               WHERE type_id = ? ORDER BY title""",
            (BOOTSTRAP_IDS["space"],),
        ).fetchall()
        return [dict(r) for r in rows]

    def resolve_type_by_name(self, name: str) -> str | None:
        """Resolve a type name to its ID. Returns None if not found."""
        from src.core.bootstrap import BOOTSTRAP_IDS

        row = self.conn.execute(
            """SELECT id FROM objects WHERE type_id = ? AND LOWER(title) = ?""",
            (BOOTSTRAP_IDS["type"], name.lower()),
        ).fetchone()
        return row["id"] if row else None

    def resolve_space_by_name(self, name: str) -> str | None:
        """Resolve a space name (path) to its ID. Matches title."""
        from src.core.bootstrap import BOOTSTRAP_IDS

        row = self.conn.execute(
            """SELECT id FROM objects WHERE type_id = ?
               AND LOWER(title) = ?""",
            (BOOTSTRAP_IDS["space"], name.lower()),
        ).fetchone()
        return row["id"] if row else None

    def resolve_prefix_matches(self, prefix: str) -> list[dict]:
        """Return all objects matching a prefix (for ambiguity reporting)."""
        if len(prefix) < 8:
            return []
        safe_prefix = _escape_like(prefix)
        rows = self.conn.execute(
            "SELECT id, title FROM objects WHERE id LIKE ? ESCAPE '\\'",
            (safe_prefix + "%",),
        ).fetchall()
        return [dict(r) for r in rows]

    def verify_content_hashes(self) -> list[dict]:
        """Verify content hashes for all objects. Returns list of mismatches."""
        rows = self.conn.execute(
            "SELECT id, title, summary, content, content_hash FROM objects"
        ).fetchall()
        mismatches = []
        for row in rows:
            expected = compute_content_hash(row["title"], row["summary"], row["content"])
            actual = row["content_hash"]
            if actual is not None and actual != expected:
                mismatches.append({
                    "id": row["id"],
                    "title": row["title"],
                    "expected_hash": expected,
                    "actual_hash": actual,
                })
        return mismatches

    def backfill_content_hashes(self) -> int:
        """Compute and set content_hash for all objects that lack one.

        Returns the number of objects updated.
        """
        rows = self.conn.execute(
            "SELECT id, title, summary, content FROM objects WHERE content_hash IS NULL"
        ).fetchall()
        count = 0
        for row in rows:
            h = compute_content_hash(row["title"], row["summary"], row["content"])
            self.conn.execute(
                "UPDATE objects SET content_hash = ? WHERE id = ?",
                (h, row["id"]),
            )
            count += 1
        return count

    def count_deleted(self) -> int:
        """Count soft-deleted objects (excludes tombstoned/purged)."""
        row = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM objects WHERE deleted_at IS NOT NULL AND purged_at IS NULL"
        ).fetchone()
        return row["cnt"]

    def count_history_entries(self) -> int:
        """Count total rows in object_history table."""
        row = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM object_history"
        ).fetchone()
        return row["cnt"]


class TagRepo:
    """Operations for object tags."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, object_id: str, tag_text: str, tag_object_id: str | None = None) -> bool:
        """Add a tag to an object. Returns True if added, False if already exists.

        Tags are normalized to lowercase for consistent lookup.
        Note: Does not commit; caller is responsible for transaction management.
        """
        # Normalize tag: lowercase and strip whitespace
        normalized_tag = tag_text.lower().strip()
        if not normalized_tag:
            return False
        try:
            self.conn.execute(
                """INSERT INTO object_tags (object_id, tag_text, tag_object_id)
                   VALUES (?, ?, ?)""",
                (object_id, normalized_tag, tag_object_id),
            )
            return True
        except sqlite3.IntegrityError:
            return False

    def remove(self, object_id: str, tag_text: str) -> bool:
        """Remove a tag from an object. Returns True if removed.

        Note: Does not commit; caller is responsible for transaction management.
        """
        # Match normalized tag
        normalized_tag = tag_text.lower().strip()
        cursor = self.conn.execute(
            "DELETE FROM object_tags WHERE object_id = ? AND tag_text = ?",
            (object_id, normalized_tag),
        )
        return cursor.rowcount > 0

    def list_for_object(self, object_id: str) -> list[str]:
        """List all tags for an object."""
        rows = self.conn.execute(
            "SELECT tag_text FROM object_tags WHERE object_id = ? ORDER BY tag_text",
            (object_id,),
        ).fetchall()
        return [r["tag_text"] for r in rows]

    def list_all(self, limit: int = 100) -> list[dict]:
        """List all distinct tags with usage counts."""
        rows = self.conn.execute(
            """SELECT tag_text, COUNT(*) as count
               FROM object_tags
               GROUP BY tag_text
               ORDER BY count DESC, tag_text
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        """Count total distinct tags."""
        row = self.conn.execute(
            "SELECT COUNT(DISTINCT tag_text) as cnt FROM object_tags"
        ).fetchone()
        return row["cnt"]


class LinkRepo:
    """Operations for links between objects."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(
        self,
        from_id: str,
        to_id: str,
        relationship: str,
        source: str = "human",
        confidence: float = 1.0,
    ) -> dict | None:
        """Create a link between two objects. Returns the link or None on conflict.

        Args:
            from_id: Source object ID
            to_id: Target object ID
            relationship: Relationship type (e.g., 'references', 'derived-from')
            source: Link provenance ('human', 'ai', 'import', 'system')
            confidence: Confidence score 0.0 to 1.0 (default 1.0)

        Note: Does not commit; caller is responsible for transaction management.
        """
        try:
            cursor = self.conn.execute(
                """INSERT INTO links (from_id, to_id, relationship, source, confidence)
                   VALUES (?, ?, ?, ?, ?)""",
                (from_id, to_id, relationship, source, confidence),
            )
            return self.get(cursor.lastrowid)
        except sqlite3.IntegrityError:
            return None

    def get(self, link_id: int) -> dict | None:
        """Get a link by its integer ID."""
        row = self.conn.execute(
            "SELECT * FROM links WHERE id = ?", (link_id,)
        ).fetchone()
        return dict(row) if row else None

    def delete(self, link_id: int) -> bool:
        """Delete a link by ID. Returns True if deleted.

        Note: Does not commit; caller is responsible for transaction management.
        """
        cursor = self.conn.execute("DELETE FROM links WHERE id = ?", (link_id,))
        return cursor.rowcount > 0

    def list_from(self, object_id: str) -> list[dict]:
        """List all links originating from an object."""
        rows = self.conn.execute(
            """SELECT l.*, o.title as to_title, o.purged_at as to_purged_at
               FROM links l
               JOIN objects o ON l.to_id = o.id
               WHERE l.from_id = ?
               ORDER BY l.created_at""",
            (object_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_to(self, object_id: str) -> list[dict]:
        """List all links pointing to an object."""
        rows = self.conn.execute(
            """SELECT l.*, o.title as from_title, o.purged_at as from_purged_at
               FROM links l
               JOIN objects o ON l.from_id = o.id
               WHERE l.to_id = ?
               ORDER BY l.created_at""",
            (object_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_all_for(self, object_id: str) -> list[dict]:
        """List all links involving an object (both directions)."""
        outgoing = self.list_from(object_id)
        incoming = self.list_to(object_id)
        for link in outgoing:
            link["direction"] = "outgoing"
        for link in incoming:
            link["direction"] = "incoming"
        return outgoing + incoming

    def count(self) -> int:
        """Count total links."""
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM links").fetchone()
        return row["cnt"]


class FileRepo:
    """Operations for file attachments."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _validate_path(full_path: Path) -> Path:
        """Validate that a resolved path stays inside the files directory.

        Prevents path traversal attacks where a tampered DB path value
        like '../../important_file' could escape the storage directory.
        """
        resolved = full_path.resolve()
        files_root = settings.files_dir.resolve()
        if not str(resolved).startswith(str(files_root)):
            raise ValueError(f"Path traversal detected: {full_path}")
        return resolved

    def _sharded_path(self, object_id: str, extension: str) -> Path:
        """Compute the sharded storage path for a file.

        Layout: files/{id[0:2]}/{id[2:4]}/{id}.{ext}
        """
        clean_id = object_id.replace("-", "")
        shard1 = clean_id[:2]
        shard2 = clean_id[2:4]
        filename = f"{object_id}{extension}"
        return settings.files_dir / shard1 / shard2 / filename

    def _compute_sha256(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def attach(
        self,
        object_id: str,
        source_path: str | Path,
        role: str = "primary",
    ) -> dict:
        """Attach a file to an object by copying it to sharded storage.

        Computes SHA-256 and MIME type automatically. If a file is already
        attached, the old file is deleted before attaching the new one
        to prevent orphaned files on disk.

        Note: Does not commit; caller is responsible for transaction management.
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        # Delete existing file to prevent orphaning (fixes expert review issue)
        existing = self.get(object_id)
        if existing:
            old_path = self._validate_path(settings.files_dir / existing["path"])
            if old_path.exists():
                old_path.unlink()
            # Clean up empty shard directories
            for parent in [old_path.parent, old_path.parent.parent]:
                try:
                    parent.rmdir()
                except OSError:
                    break

        extension = source.suffix or ""
        dest = self._sharded_path(object_id, extension)
        dest.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(str(source), str(dest))

        sha256 = self._compute_sha256(dest)
        mime_type = mimetypes.guess_type(str(source))[0]
        size_bytes = dest.stat().st_size
        rel_path = str(dest.relative_to(settings.files_dir))

        self.conn.execute(
            """INSERT OR REPLACE INTO files (object_id, path, role, mime_type, size_bytes, sha256)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (object_id, rel_path, role, mime_type, size_bytes, sha256),
        )

        return {
            "object_id": object_id,
            "path": rel_path,
            "role": role,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "sha256": sha256,
        }

    def detach(self, object_id: str) -> bool:
        """Remove file attachment. Deletes DB record first, then file on disk.

        Note: Does not commit; caller is responsible for transaction management.
        """
        row = self.conn.execute(
            "SELECT path FROM files WHERE object_id = ?", (object_id,)
        ).fetchone()
        if not row:
            return False

        # Delete DB record first (ensures no orphan references if disk op fails)
        self.conn.execute("DELETE FROM files WHERE object_id = ?", (object_id,))

        # Then delete file from disk (with path traversal guard)
        full_path = self._validate_path(settings.files_dir / row["path"])
        if full_path.exists():
            full_path.unlink()

        # Clean up empty shard directories
        for parent in [full_path.parent, full_path.parent.parent]:
            try:
                parent.rmdir()  # Only removes if empty
            except OSError:
                break

        return True

    def get(self, object_id: str) -> dict | None:
        """Get file info for an object."""
        row = self.conn.execute(
            "SELECT * FROM files WHERE object_id = ?", (object_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_full_path(self, object_id: str) -> Path | None:
        """Get the full filesystem path for an attached file."""
        row = self.conn.execute(
            "SELECT path FROM files WHERE object_id = ?", (object_id,)
        ).fetchone()
        if not row:
            return None
        return self._validate_path(settings.files_dir / row["path"])

    def count(self) -> int:
        """Count total file attachments."""
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM files").fetchone()
        return row["cnt"]
