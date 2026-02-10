"""Tests for object versioning, history recording, and content hashing."""

import sqlite3

import pytest

from src.core.bootstrap import BOOTSTRAP_IDS
from src.core.repository import ObjectRepo, compute_content_hash


class TestContentHash:
    """Test content hash computation."""

    def test_compute_content_hash(self):
        h = compute_content_hash("Title", "Summary", "Content")
        assert len(h) == 64  # SHA-256 hex digest
        assert h == compute_content_hash("Title", "Summary", "Content")

    def test_hash_changes_with_title(self):
        h1 = compute_content_hash("Title A", "Summary", "Content")
        h2 = compute_content_hash("Title B", "Summary", "Content")
        assert h1 != h2

    def test_hash_changes_with_summary(self):
        h1 = compute_content_hash("Title", "Summary A", "Content")
        h2 = compute_content_hash("Title", "Summary B", "Content")
        assert h1 != h2

    def test_hash_changes_with_content(self):
        h1 = compute_content_hash("Title", "Summary", "Content A")
        h2 = compute_content_hash("Title", "Summary", "Content B")
        assert h1 != h2

    def test_hash_handles_none_summary(self):
        h = compute_content_hash("Title", None, "Content")
        assert len(h) == 64

    def test_hash_handles_none_content(self):
        h = compute_content_hash("Title", "Summary", None)
        assert len(h) == 64


class TestContentHashOnCreate:
    """Test that content_hash is set on object creation."""

    def test_create_sets_content_hash(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Hash Test",
            summary="A summary",
            content="Some content",
        )
        expected = compute_content_hash("Hash Test", "A summary", "Some content")
        assert obj["content_hash"] == expected

    def test_create_hash_with_none_fields(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["note"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="No Content",
        )
        expected = compute_content_hash("No Content", None, None)
        assert obj["content_hash"] == expected


class TestVersioning:
    """Test object version tracking."""

    def test_initial_version_is_1(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Version Test",
        )
        assert obj["version"] == 1

    def test_version_increments_on_title_change(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Original Title",
            content="Some content",
        )
        bootstrapped_db.commit()
        assert obj["version"] == 1

        updated = repo.update(obj["id"], title="Changed Title")
        assert updated["version"] == 2

    def test_version_increments_on_content_change(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Content Version",
            content="Original content",
        )
        bootstrapped_db.commit()

        updated = repo.update(obj["id"], content="Changed content")
        assert updated["version"] == 2

    def test_version_increments_on_summary_change(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Summary Version",
            summary="Original",
        )
        bootstrapped_db.commit()

        updated = repo.update(obj["id"], summary="Changed")
        assert updated["version"] == 2

    def test_no_version_bump_on_metadata_only_change(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Metadata Test",
        )
        bootstrapped_db.commit()

        updated = repo.update(obj["id"], projection_override="always")
        assert updated["version"] == 1


class TestHistoryRecording:
    """Test that update triggers record history entries."""

    def test_update_creates_history_entry(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="History Test",
            content="Original content",
        )
        bootstrapped_db.commit()

        repo.update(obj["id"], title="Updated Title")
        bootstrapped_db.commit()

        history = repo.list_history(obj["id"])
        assert len(history) == 1
        assert history[0]["version"] == 1
        assert history[0]["title"] == "History Test"
        assert history[0]["content"] == "Original content"

    def test_multiple_updates_create_multiple_entries(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Multi Update",
            content="v1 content",
        )
        bootstrapped_db.commit()

        repo.update(obj["id"], content="v2 content")
        bootstrapped_db.commit()
        repo.update(obj["id"], content="v3 content")
        bootstrapped_db.commit()

        history = repo.list_history(obj["id"])
        assert len(history) == 2
        assert history[0]["version"] == 1
        assert history[0]["content"] == "v1 content"
        assert history[1]["version"] == 2
        assert history[1]["content"] == "v2 content"

    def test_no_history_on_noop_update(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="No-Op Test",
            content="Same content",
        )
        bootstrapped_db.commit()

        # Update with identical content
        repo.update(obj["id"], title="No-Op Test", content="Same content")
        bootstrapped_db.commit()

        history = repo.list_history(obj["id"])
        assert len(history) == 0

    def test_no_history_on_metadata_only_update(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Metadata Only",
        )
        bootstrapped_db.commit()

        repo.update(obj["id"], projection_override="always")
        bootstrapped_db.commit()

        history = repo.list_history(obj["id"])
        assert len(history) == 0


class TestGetVersion:
    """Test retrieving a specific historical version."""

    def test_get_version(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Get Version Test",
            content="v1",
        )
        bootstrapped_db.commit()

        repo.update(obj["id"], content="v2")
        bootstrapped_db.commit()

        v1 = repo.get_version(obj["id"], 1)
        assert v1 is not None
        assert v1["content"] == "v1"
        assert v1["title"] == "Get Version Test"

    def test_get_nonexistent_version_returns_none(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="No Such Version",
        )
        bootstrapped_db.commit()

        assert repo.get_version(obj["id"], 99) is None


class TestBackfillContentHashes:
    """Test content hash backfill for existing objects."""

    def test_backfill_sets_hashes(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Backfill Test",
            content="Content",
        )
        bootstrapped_db.commit()

        # Manually clear the hash to simulate a pre-migration object
        bootstrapped_db.execute(
            "UPDATE objects SET content_hash = NULL WHERE id = ?", (obj["id"],)
        )
        bootstrapped_db.commit()

        count = repo.backfill_content_hashes()
        bootstrapped_db.commit()
        assert count >= 1

        updated = repo.get(obj["id"])
        expected = compute_content_hash("Backfill Test", None, "Content")
        assert updated["content_hash"] == expected


class TestVerifyContentHashes:
    """Test content hash verification."""

    def test_verify_all_ok(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="OK Hash",
            content="Content",
        )
        bootstrapped_db.commit()
        mismatches = repo.verify_content_hashes()
        assert len(mismatches) == 0

    def test_verify_detects_mismatch(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Bad Hash",
            content="Content",
        )
        bootstrapped_db.commit()

        # Tamper with the hash
        bootstrapped_db.execute(
            "UPDATE objects SET content_hash = 'bad_hash' WHERE id = ?", (obj["id"],)
        )
        bootstrapped_db.commit()

        mismatches = repo.verify_content_hashes()
        assert any(m["id"] == obj["id"] for m in mismatches)
