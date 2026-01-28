"""Tests for src.core.db: connection management, WAL mode, migrations."""

import sqlite3

import pytest

from src.core.db import check_integrity, get_connection, init_db, run_migrations


class TestGetConnection:
    """Test SQLite connection configuration."""

    def test_wal_mode_enabled(self, tmp_db_path, _patched_settings):
        conn = get_connection(tmp_db_path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode == "wal"

    def test_foreign_keys_enabled(self, tmp_db_path, _patched_settings):
        conn = get_connection(tmp_db_path)
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        conn.close()
        assert fk == 1

    def test_row_factory_is_row(self, tmp_db_path, _patched_settings):
        conn = get_connection(tmp_db_path)
        assert conn.row_factory is sqlite3.Row
        conn.close()


class TestRunMigrations:
    """Test the migration runner."""

    def test_applies_all_migrations(self, tmp_db_path, _patched_settings):
        conn = get_connection(tmp_db_path)
        applied = run_migrations(conn)
        assert len(applied) >= 2
        assert 1 in applied
        assert 2 in applied
        conn.close()

    def test_creates_schema_version_table(self, tmp_db_path, _patched_settings):
        conn = get_connection(tmp_db_path)
        run_migrations(conn)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        ).fetchall()
        assert len(rows) == 1
        conn.close()

    def test_records_applied_versions(self, tmp_db_path, _patched_settings):
        conn = get_connection(tmp_db_path)
        run_migrations(conn)
        versions = conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()
        assert len(versions) >= 1
        assert versions[0]["version"] == 1
        conn.close()

    def test_idempotent_running_twice(self, tmp_db_path, _patched_settings):
        conn = get_connection(tmp_db_path)
        first = run_migrations(conn)
        second = run_migrations(conn)
        assert len(first) >= 1
        assert len(second) == 0  # nothing new to apply
        conn.close()

    def test_idempotent_data_unchanged(self, tmp_db_path, _patched_settings):
        """Running migrations twice leaves the same schema_version rows."""
        conn = get_connection(tmp_db_path)
        run_migrations(conn)
        rows_after_first = conn.execute("SELECT * FROM schema_version").fetchall()
        run_migrations(conn)
        rows_after_second = conn.execute("SELECT * FROM schema_version").fetchall()
        assert len(rows_after_first) == len(rows_after_second)
        conn.close()


class TestInitDb:
    """Test the init_db helper."""

    def test_creates_db_file(self, tmp_db_path, _patched_settings):
        conn = init_db(tmp_db_path)
        assert tmp_db_path.exists()
        conn.close()

    def test_creates_parent_dirs(self, tmp_path, _patched_settings):
        deep_path = tmp_path / "a" / "b" / "c" / "exobrain.db"
        conn = init_db(deep_path)
        assert deep_path.exists()
        conn.close()

    def test_returned_connection_is_usable(self, tmp_db_path, _patched_settings):
        conn = init_db(tmp_db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [r["name"] for r in tables]
        assert "objects" in table_names
        conn.close()


class TestCheckIntegrity:
    """Test integrity checking."""

    def test_clean_db_passes(self, db_conn):
        result = check_integrity(db_conn)
        assert result["ok"] is True
        assert result["integrity"] == "ok"
        assert result["foreign_key_violations"] == 0
