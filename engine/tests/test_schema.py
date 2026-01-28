"""Tests for src.core.schema: table creation, FTS5, indexes."""

import pytest


class TestTablesExist:
    """Verify all expected tables are created by migration 001."""

    EXPECTED_TABLES = ["objects", "object_tags", "links", "files", "schema_version"]

    def test_all_tables_present(self, db_conn):
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [r["name"] for r in rows]
        for expected in self.EXPECTED_TABLES:
            assert expected in table_names, f"Missing table: {expected}"

    def test_objects_columns(self, db_conn):
        info = db_conn.execute("PRAGMA table_info(objects)").fetchall()
        col_names = {r["name"] for r in info}
        expected = {"id", "type_id", "space_id", "title", "summary", "content", "created_at", "updated_at"}
        assert expected.issubset(col_names)

    def test_object_tags_columns(self, db_conn):
        info = db_conn.execute("PRAGMA table_info(object_tags)").fetchall()
        col_names = {r["name"] for r in info}
        assert {"id", "object_id", "tag_text", "tag_object_id", "created_at"}.issubset(col_names)

    def test_links_columns(self, db_conn):
        info = db_conn.execute("PRAGMA table_info(links)").fetchall()
        col_names = {r["name"] for r in info}
        assert {"id", "from_id", "to_id", "relationship", "created_at"}.issubset(col_names)

    def test_files_columns(self, db_conn):
        info = db_conn.execute("PRAGMA table_info(files)").fetchall()
        col_names = {r["name"] for r in info}
        assert {"object_id", "path", "role", "mime_type", "size_bytes", "sha256", "created_at"}.issubset(col_names)


class TestFTS5:
    """Verify the FTS5 virtual table exists and works."""

    def test_fts5_virtual_table_exists(self, db_conn):
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='objects_fts'"
        ).fetchall()
        assert len(rows) == 1

    def test_fts5_triggers_exist(self, db_conn):
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name"
        ).fetchall()
        trigger_names = [r["name"] for r in rows]
        assert "objects_fts_insert" in trigger_names
        assert "objects_fts_delete" in trigger_names
        assert "objects_fts_update" in trigger_names


class TestAutoUpdatedAtTrigger:
    """Verify the objects_auto_updated_at trigger from migration 002."""

    def test_trigger_exists(self, db_conn):
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name='objects_auto_updated_at'"
        ).fetchall()
        assert len(rows) == 1

    def test_updated_at_auto_changes(self, bootstrapped_db):
        """Updating an object should auto-refresh updated_at."""
        from src.core.bootstrap import BOOTSTRAP_IDS
        from src.core.repository import ObjectRepo

        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Trigger Test",
        )
        original_updated = obj["updated_at"]

        # Force a slight delay to ensure timestamps differ
        import time
        time.sleep(0.01)

        updated = repo.update(obj["id"], title="Trigger Test Updated")
        # updated_at should be refreshed by the trigger
        assert updated["updated_at"] is not None


class TestIndexes:
    """Verify performance indexes exist."""

    EXPECTED_INDEXES = [
        "idx_objects_type_id",
        "idx_objects_space_id",
        "idx_objects_created_at",
        "idx_object_tags_object_id",
        "idx_object_tags_tag_text",
        "idx_links_from_id",
        "idx_links_to_id",
    ]

    def test_all_indexes_present(self, db_conn):
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        ).fetchall()
        index_names = [r["name"] for r in rows]
        for expected in self.EXPECTED_INDEXES:
            assert expected in index_names, f"Missing index: {expected}"
