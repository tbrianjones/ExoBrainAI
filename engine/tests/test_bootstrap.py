"""Tests for src.core.bootstrap: type system initialization."""

import sqlite3

import pytest

from src.core.bootstrap import (
    BOOTSTRAP_IDS,
    BOOTSTRAP_SPACES,
    BOOTSTRAP_TYPES,
    bootstrap,
    get_space_id,
    get_type_id,
)
from src.core.db import check_integrity


class TestBootstrapCreation:
    """Test that bootstrap creates the expected types and spaces."""

    def test_creates_seven_types(self, db_conn):
        result = bootstrap(db_conn)
        assert result["types_created"] == 7
        assert len(BOOTSTRAP_TYPES) == 7

    def test_creates_five_spaces(self, db_conn):
        result = bootstrap(db_conn)
        assert result["spaces_created"] == 5
        assert len(BOOTSTRAP_SPACES) == 5

    def test_total_bootstrap_objects(self, db_conn):
        result = bootstrap(db_conn)
        assert result["total_bootstrap_objects"] == len(BOOTSTRAP_IDS)

    def test_all_types_in_database(self, bootstrapped_db):
        for key, title, summary in BOOTSTRAP_TYPES:
            obj_id = BOOTSTRAP_IDS[key]
            row = bootstrapped_db.execute(
                "SELECT * FROM objects WHERE id = ?", (obj_id,)
            ).fetchone()
            assert row is not None, f"Bootstrap type missing: {key}"
            assert row["title"] == title

    def test_all_spaces_in_database(self, bootstrapped_db):
        for key, title, summary in BOOTSTRAP_SPACES:
            obj_id = BOOTSTRAP_IDS[key]
            row = bootstrapped_db.execute(
                "SELECT * FROM objects WHERE id = ?", (obj_id,)
            ).fetchone()
            assert row is not None, f"Bootstrap space missing: {key}"
            assert row["title"] == title


class TestBootstrapIdempotency:
    """Test that running bootstrap twice produces no duplicates."""

    def test_idempotent_second_run_creates_nothing(self, db_conn):
        first = bootstrap(db_conn)
        second = bootstrap(db_conn)
        assert first["types_created"] == 7
        assert second["types_created"] == 0
        assert first["spaces_created"] == 5
        assert second["spaces_created"] == 0

    def test_idempotent_object_count_unchanged(self, db_conn):
        bootstrap(db_conn)
        count_1 = db_conn.execute("SELECT COUNT(*) as cnt FROM objects").fetchone()["cnt"]
        bootstrap(db_conn)
        count_2 = db_conn.execute("SELECT COUNT(*) as cnt FROM objects").fetchone()["cnt"]
        assert count_1 == count_2


class TestBootstrapIntegrity:
    """Test FK integrity after bootstrap."""

    def test_fk_integrity_passes(self, bootstrapped_db):
        result = check_integrity(bootstrapped_db)
        assert result["ok"] is True
        assert result["foreign_key_violations"] == 0

    def test_general_integrity_passes(self, bootstrapped_db):
        result = check_integrity(bootstrapped_db)
        assert result["integrity"] == "ok"


class TestBootstrapDeterminism:
    """Test that bootstrap IDs are deterministic."""

    def test_ids_are_deterministic(self):
        """The same keys always produce the same UUIDs."""
        assert BOOTSTRAP_IDS["type"] == "00000000-0000-7000-8000-000000000001"
        assert BOOTSTRAP_IDS["space"] == "00000000-0000-7000-8000-000000000002"
        assert BOOTSTRAP_IDS["document"] == "00000000-0000-7000-8000-000000000004"
        assert BOOTSTRAP_IDS["primitives"] == "00000000-0000-7000-8000-000000000101"
        assert BOOTSTRAP_IDS["inbox"] == "00000000-0000-7000-8000-000000000201"

    def test_get_type_id_returns_correct_id(self):
        assert get_type_id("document") == BOOTSTRAP_IDS["document"]
        assert get_type_id("note") == BOOTSTRAP_IDS["note"]
        assert get_type_id("type") == BOOTSTRAP_IDS["type"]

    def test_get_type_id_raises_for_unknown(self):
        with pytest.raises(KeyError):
            get_type_id("nonexistent_type")

    def test_get_space_id_returns_correct_id(self):
        assert get_space_id("primitives") == BOOTSTRAP_IDS["primitives"]
        assert get_space_id("primitives/type") == BOOTSTRAP_IDS["primitives/type"]

    def test_get_space_id_raises_for_unknown(self):
        with pytest.raises(KeyError):
            get_space_id("nonexistent_space")


class TestBootstrapForeignKeyEnforcement:
    """Test that FKs are properly re-enabled after bootstrap."""

    def test_fk_enforced_after_bootstrap(self, bootstrapped_db):
        """After bootstrap, foreign keys should be ON and enforced."""
        fk_status = bootstrapped_db.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk_status == 1, "Foreign keys should be enabled after bootstrap"

    def test_fk_violation_after_bootstrap(self, bootstrapped_db):
        """Inserting a bad FK reference should fail after bootstrap completes."""
        with pytest.raises(sqlite3.IntegrityError):
            bootstrapped_db.execute(
                "INSERT INTO objects (id, type_id, space_id, title) VALUES (?, ?, ?, ?)",
                ("test-bad-fk", "nonexistent-type", "nonexistent-space", "Bad FK"),
            )
