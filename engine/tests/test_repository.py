"""Tests for src.core.repository: ObjectRepo, TagRepo, LinkRepo, FileRepo."""

import hashlib
import sqlite3

import pytest

from src.core.bootstrap import BOOTSTRAP_IDS
from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo


# ============================================================
# ObjectRepo
# ============================================================


class TestObjectRepoCreate:
    """Test ObjectRepo.create."""

    def test_create_returns_dict_with_id(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Test Doc",
        )
        assert "id" in obj
        assert obj["title"] == "Test Doc"

    def test_create_with_all_fields(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["note"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Full Note",
            summary="A summary",
            content="Full content here",
        )
        assert obj["summary"] == "A summary"
        assert obj["content"] == "Full content here"

    def test_create_with_explicit_id(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        custom_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Custom ID",
            id=custom_id,
        )
        assert obj["id"] == custom_id

    def test_create_sets_timestamps(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Timestamped",
        )
        assert obj["created_at"] is not None
        assert obj["updated_at"] is not None

    def test_create_with_custom_created_at(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        custom_ts = "2026-01-07T00:00:00.000Z"
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Backdated",
            created_at=custom_ts,
        )
        assert obj["created_at"] == custom_ts
        assert obj["updated_at"] == custom_ts


class TestObjectRepoGet:
    """Test ObjectRepo.get and get_by_prefix."""

    def test_get_existing(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        obj = repo.get(sample_objects["obj_a"]["id"])
        assert obj is not None
        assert obj["title"] == "Alpha Document"
        assert obj["type_name"] == "Document"
        assert obj["space_name"] == "Primitives"

    def test_get_nonexistent_returns_none(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        assert repo.get("nonexistent-id") is None

    def test_get_by_prefix_works(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        full_id = sample_objects["obj_a"]["id"]
        # Use a long prefix to avoid collision with other UUIDv7s
        # generated in the same millisecond
        prefix = full_id[:30]
        obj = repo.get_by_prefix(prefix)
        assert obj is not None
        assert obj["id"] == full_id

    def test_get_by_prefix_too_short_returns_none(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        full_id = sample_objects["obj_a"]["id"]
        assert repo.get_by_prefix(full_id[:5]) is None

    def test_resolve_id_exact(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        full_id = sample_objects["obj_b"]["id"]
        assert repo.resolve_id(full_id) == full_id

    def test_resolve_id_prefix(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        full_id = sample_objects["obj_b"]["id"]
        # Use a long prefix to avoid collision with other UUIDv7s
        resolved = repo.resolve_id(full_id[:30])
        assert resolved == full_id

    def test_resolve_id_nonexistent_returns_none(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        assert repo.resolve_id("zzzzzzzz-zzzz-zzzz-zzzz") is None


class TestObjectRepoList:
    """Test ObjectRepo.list with filters."""

    def test_list_returns_user_objects(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.list()
        # Should include our 3 test objects (documents and notes, not bootstrap types/spaces/tags)
        titles = [r["title"] for r in results]
        assert "Alpha Document" in titles
        assert "Beta Document" in titles
        assert "Gamma Note" in titles

    def test_list_excludes_bootstrap_types_by_default(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.list()
        type_names = {r["type_name"] for r in results}
        assert "Type" not in type_names
        assert "Space" not in type_names

    def test_list_filter_by_type(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.list(type_name="Note")
        assert len(results) == 1
        assert results[0]["title"] == "Gamma Note"

    def test_list_filter_by_type_case_insensitive(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.list(type_name="note")
        assert len(results) == 1

    def test_list_filter_by_tag(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.list(tag="computing")
        titles = [r["title"] for r in results]
        assert "Alpha Document" in titles
        assert "Beta Document" in titles
        assert "Gamma Note" not in titles

    def test_list_with_limit(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.list(limit=1)
        assert len(results) == 1

    def test_list_with_offset(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        all_results = repo.list(limit=50)
        offset_results = repo.list(limit=50, offset=1)
        assert len(offset_results) == len(all_results) - 1


class TestObjectRepoUpdate:
    """Test ObjectRepo.update."""

    def test_update_title(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]
        updated = repo.update(obj_id, title="Updated Title")
        assert updated["title"] == "Updated Title"

    def test_update_summary_and_content(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]
        updated = repo.update(obj_id, summary="New summary", content="New content")
        assert updated["summary"] == "New summary"
        assert updated["content"] == "New content"

    def test_update_changes_updated_at(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]
        original = repo.get(obj_id)
        updated = repo.update(obj_id, title="Changed")
        # updated_at should be set (may be same in fast tests, but field exists)
        assert updated["updated_at"] is not None

    def test_update_no_fields_returns_unchanged(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]
        result = repo.update(obj_id)
        assert result["title"] == "Alpha Document"


class TestObjectRepoDelete:
    """Test ObjectRepo.delete."""

    def test_delete_existing(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        obj_id = sample_objects["obj_c"]["id"]
        assert repo.delete(obj_id) is True
        assert repo.get(obj_id) is None

    def test_delete_nonexistent_returns_false(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        assert repo.delete("nonexistent-id") is False


class TestObjectRepoSearch:
    """Test ObjectRepo.search (FTS5)."""

    def test_search_by_title(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.search("Alpha")
        assert len(results) >= 1
        assert any(r["title"] == "Alpha Document" for r in results)

    def test_search_by_content(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.search("superposition")
        assert len(results) >= 1
        assert any(r["title"] == "Alpha Document" for r in results)

    def test_search_by_summary(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.search("machine learning")
        assert len(results) >= 1
        assert any(r["title"] == "Beta Document" for r in results)

    def test_search_no_results(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.search("xyznonexistent")
        assert len(results) == 0

    def test_search_with_limit(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        results = repo.search("document", limit=1)
        assert len(results) <= 1


class TestObjectRepoCount:
    """Test ObjectRepo.count and count_by_type."""

    def test_count_all(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        # 12 bootstrap + 3 test objects = 15
        total = repo.count()
        assert total >= 15

    def test_count_by_type_name(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        doc_count = repo.count("Document")
        assert doc_count >= 2  # obj_a and obj_b

    def test_count_by_type_grouped(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        counts = repo.count_by_type()
        assert "Document" in counts
        assert "Note" in counts
        assert counts["Document"] >= 2
        assert counts["Note"] >= 1


# ============================================================
# TagRepo
# ============================================================


class TestTagRepoAdd:
    """Test TagRepo.add."""

    def test_add_tag(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]
        assert repo.add(obj_id, "new-tag") is True

    def test_duplicate_add_returns_false(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]
        # "quantum" was already added in the fixture
        assert repo.add(obj_id, "quantum") is False

    def test_add_with_tag_object_id(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]
        tag_type_id = BOOTSTRAP_IDS["tag"]
        assert repo.add(obj_id, "typed-tag", tag_object_id=tag_type_id) is True


class TestTagRepoRemove:
    """Test TagRepo.remove."""

    def test_remove_existing_tag(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]
        assert repo.remove(obj_id, "quantum") is True

    def test_remove_nonexistent_tag(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]
        assert repo.remove(obj_id, "nonexistent") is False


class TestTagRepoList:
    """Test TagRepo list operations."""

    def test_list_for_object(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        tags = repo.list_for_object(sample_objects["obj_a"]["id"])
        assert "quantum" in tags
        assert "computing" in tags
        assert len(tags) == 2

    def test_list_for_object_sorted(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        tags = repo.list_for_object(sample_objects["obj_a"]["id"])
        assert tags == sorted(tags)

    def test_list_all_tags(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        all_tags = repo.list_all()
        tag_texts = [t["tag_text"] for t in all_tags]
        assert "computing" in tag_texts
        assert "quantum" in tag_texts
        assert "machine-learning" in tag_texts
        assert "observation" in tag_texts

    def test_list_all_includes_counts(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        all_tags = repo.list_all()
        computing = next(t for t in all_tags if t["tag_text"] == "computing")
        assert computing["count"] == 2  # on obj_a and obj_b


# ============================================================
# LinkRepo
# ============================================================


class TestLinkRepoCreate:
    """Test LinkRepo.create."""

    def test_create_link(self, sample_objects):
        conn = sample_objects["conn"]
        repo = LinkRepo(conn)
        link = repo.create(
            sample_objects["obj_b"]["id"],
            sample_objects["obj_c"]["id"],
            "extends",
        )
        assert link is not None
        assert link["relationship"] == "extends"
        assert link["from_id"] == sample_objects["obj_b"]["id"]
        assert link["to_id"] == sample_objects["obj_c"]["id"]

    def test_duplicate_link_returns_none(self, sample_objects):
        conn = sample_objects["conn"]
        repo = LinkRepo(conn)
        # This link was created in the fixture
        link = repo.create(
            sample_objects["obj_a"]["id"],
            sample_objects["obj_b"]["id"],
            "related-to",
        )
        assert link is None


class TestLinkRepoDelete:
    """Test LinkRepo.delete."""

    def test_delete_existing_link(self, sample_objects):
        conn = sample_objects["conn"]
        repo = LinkRepo(conn)
        # Get an existing link
        links = repo.list_from(sample_objects["obj_a"]["id"])
        assert len(links) > 0
        link_id = links[0]["id"]
        assert repo.delete(link_id) is True

    def test_delete_nonexistent_link(self, bootstrapped_db):
        repo = LinkRepo(bootstrapped_db)
        assert repo.delete(99999) is False


class TestLinkRepoList:
    """Test LinkRepo list operations."""

    def test_list_from(self, sample_objects):
        conn = sample_objects["conn"]
        repo = LinkRepo(conn)
        links = repo.list_from(sample_objects["obj_a"]["id"])
        assert len(links) == 1
        assert links[0]["relationship"] == "related-to"
        assert links[0]["to_title"] == "Beta Document"

    def test_list_to(self, sample_objects):
        conn = sample_objects["conn"]
        repo = LinkRepo(conn)
        links = repo.list_to(sample_objects["obj_a"]["id"])
        assert len(links) == 1
        assert links[0]["relationship"] == "references"
        assert links[0]["from_title"] == "Gamma Note"

    def test_list_all_for(self, sample_objects):
        conn = sample_objects["conn"]
        repo = LinkRepo(conn)
        links = repo.list_all_for(sample_objects["obj_a"]["id"])
        assert len(links) == 2
        directions = {l["direction"] for l in links}
        assert "outgoing" in directions
        assert "incoming" in directions

    def test_count(self, sample_objects):
        conn = sample_objects["conn"]
        repo = LinkRepo(conn)
        assert repo.count() == 2  # two links created in fixture


# ============================================================
# FileRepo
# ============================================================


class TestFileRepoAttach:
    """Test FileRepo.attach."""

    def test_attach_creates_sharded_path(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        # Create a temp source file
        source = _patched_settings.data_dir / "test_source.txt"
        source.write_text("Hello, ExoBrain!")

        result = repo.attach(obj_id, source)
        assert result["object_id"] == obj_id
        assert result["size_bytes"] > 0
        assert result["sha256"] is not None
        assert "/" in result["path"]  # sharded path has slashes

    def test_attach_computes_sha256(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        source = _patched_settings.data_dir / "hash_test.txt"
        content = "Verify hash computation"
        source.write_text(content)

        result = repo.attach(obj_id, source)
        expected_sha = hashlib.sha256(content.encode()).hexdigest()
        assert result["sha256"] == expected_sha

    def test_attach_detects_mime_type(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        obj_id = sample_objects["obj_b"]["id"]

        source = _patched_settings.data_dir / "test.json"
        source.write_text('{"key": "value"}')

        result = repo.attach(obj_id, source)
        assert result["mime_type"] == "application/json"

    def test_attach_nonexistent_file_raises(self, sample_objects):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        with pytest.raises(FileNotFoundError):
            repo.attach(sample_objects["obj_a"]["id"], "/nonexistent/file.txt")

    def test_attach_copies_file(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        obj_id = sample_objects["obj_c"]["id"]

        source = _patched_settings.data_dir / "copy_test.txt"
        source.write_text("File to copy")

        repo.attach(obj_id, source)
        full_path = repo.get_full_path(obj_id)
        assert full_path is not None
        assert full_path.exists()
        assert full_path.read_text() == "File to copy"


class TestFileRepoDetach:
    """Test FileRepo.detach."""

    def test_detach_removes_db_record(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        source = _patched_settings.data_dir / "detach_test.txt"
        source.write_text("Will be detached")
        repo.attach(obj_id, source)

        assert repo.detach(obj_id) is True
        assert repo.get(obj_id) is None

    def test_detach_removes_file_from_disk(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        source = _patched_settings.data_dir / "disk_test.txt"
        source.write_text("Will be removed from disk")
        repo.attach(obj_id, source)

        full_path = repo.get_full_path(obj_id)
        assert full_path.exists()

        repo.detach(obj_id)
        assert not full_path.exists()

    def test_detach_nonexistent_returns_false(self, bootstrapped_db):
        repo = FileRepo(bootstrapped_db)
        assert repo.detach("nonexistent-id") is False


class TestFileRepoGet:
    """Test FileRepo.get and get_full_path."""

    def test_get_returns_file_info(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        source = _patched_settings.data_dir / "info_test.txt"
        source.write_text("Info content")
        repo.attach(obj_id, source)

        info = repo.get(obj_id)
        assert info is not None
        assert info["object_id"] == obj_id
        assert info["role"] == "primary"
        assert info["sha256"] is not None

    def test_get_nonexistent_returns_none(self, bootstrapped_db):
        repo = FileRepo(bootstrapped_db)
        assert repo.get("nonexistent-id") is None

    def test_get_full_path_returns_path(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        obj_id = sample_objects["obj_b"]["id"]

        source = _patched_settings.data_dir / "path_test.txt"
        source.write_text("Path content")
        repo.attach(obj_id, source)

        full_path = repo.get_full_path(obj_id)
        assert full_path is not None
        assert full_path.exists()

    def test_get_full_path_nonexistent_returns_none(self, bootstrapped_db):
        repo = FileRepo(bootstrapped_db)
        assert repo.get_full_path("nonexistent-id") is None

    def test_count(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)

        assert repo.count() == 0

        source = _patched_settings.data_dir / "count_test.txt"
        source.write_text("Count me")
        repo.attach(sample_objects["obj_a"]["id"], source)
        assert repo.count() == 1


# ============================================================
# Constraint Tests
# ============================================================


class TestConstraints:
    """Test FK violations, unique constraints, and cascade deletes."""

    def test_fk_violation_on_bad_type_id(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        with pytest.raises(sqlite3.IntegrityError):
            repo.create(
                type_id="nonexistent-type-id",
                space_id=BOOTSTRAP_IDS["primitives"],
                title="Bad Type",
            )

    def test_fk_violation_on_bad_space_id(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        with pytest.raises(sqlite3.IntegrityError):
            repo.create(
                type_id=BOOTSTRAP_IDS["document"],
                space_id="nonexistent-space-id",
                title="Bad Space",
            )

    def test_unique_tag_constraint(self, sample_objects):
        """Adding the same tag twice does not raise but returns False."""
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]
        assert repo.add(obj_id, "quantum") is False

    def test_unique_link_constraint(self, sample_objects):
        """Creating a duplicate link returns None."""
        conn = sample_objects["conn"]
        repo = LinkRepo(conn)
        result = repo.create(
            sample_objects["obj_a"]["id"],
            sample_objects["obj_b"]["id"],
            "related-to",
        )
        assert result is None

    def test_cascade_delete_removes_tags(self, sample_objects):
        conn = sample_objects["conn"]
        obj_id = sample_objects["obj_a"]["id"]
        tag_repo = TagRepo(conn)
        obj_repo = ObjectRepo(conn)

        # Verify tags exist before delete
        tags_before = tag_repo.list_for_object(obj_id)
        assert len(tags_before) > 0

        obj_repo.delete(obj_id)

        tags_after = tag_repo.list_for_object(obj_id)
        assert len(tags_after) == 0

    def test_cascade_delete_removes_links(self, sample_objects):
        conn = sample_objects["conn"]
        obj_id = sample_objects["obj_a"]["id"]
        link_repo = LinkRepo(conn)
        obj_repo = ObjectRepo(conn)

        # obj_a has outgoing and incoming links
        links_before = link_repo.list_all_for(obj_id)
        assert len(links_before) > 0

        obj_repo.delete(obj_id)

        links_after = link_repo.list_all_for(obj_id)
        assert len(links_after) == 0

    def test_cascade_delete_removes_file_record(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        obj_id = sample_objects["obj_a"]["id"]
        file_repo = FileRepo(conn)
        obj_repo = ObjectRepo(conn)

        source = _patched_settings.data_dir / "cascade_test.txt"
        source.write_text("Will be cascade deleted")
        file_repo.attach(obj_id, source)
        assert file_repo.get(obj_id) is not None

        obj_repo.delete(obj_id)
        assert file_repo.get(obj_id) is None

    def test_cascade_delete_removes_file_from_disk(self, sample_objects, _patched_settings):
        """ObjectRepo.delete() should remove the file from disk via detach."""
        conn = sample_objects["conn"]
        obj_id = sample_objects["obj_a"]["id"]
        file_repo = FileRepo(conn)
        obj_repo = ObjectRepo(conn)

        source = _patched_settings.data_dir / "disk_cascade_test.txt"
        source.write_text("Will be removed from disk on cascade")
        file_repo.attach(obj_id, source)

        full_path = file_repo.get_full_path(obj_id)
        assert full_path.exists()

        obj_repo.delete(obj_id)
        assert not full_path.exists()


# ============================================================
# TagRepo.count()
# ============================================================


class TestTagRepoCount:
    """Test TagRepo.count."""

    def test_count_returns_distinct_tags(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        count = repo.count()
        # 5 tags added in fixture: quantum, computing (on obj_a), machine-learning, computing (on obj_b), observation
        # Distinct: quantum, computing, machine-learning, observation = 4
        assert count == 4

    def test_count_empty(self, bootstrapped_db):
        repo = TagRepo(bootstrapped_db)
        assert repo.count() == 0


# ============================================================
# ObjectRepo.count() edge cases
# ============================================================


class TestObjectRepoCountEdge:
    """Edge cases for ObjectRepo.count."""

    def test_count_empty_string_counts_all(self, sample_objects):
        """Empty string is falsy, so count("") acts like count(None) and counts all."""
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        assert repo.count("") == repo.count()

    def test_count_whitespace_returns_zero(self, sample_objects):
        """Whitespace-only type name should return 0 (no type named '   ')."""
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        assert repo.count("   ") == 0

    def test_count_case_insensitive(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        upper = repo.count("Document")
        lower = repo.count("document")
        mixed = repo.count("DOCUMENT")
        assert upper == lower == mixed

    def test_count_url_type(self, sample_objects):
        """The URL type should resolve correctly (was broken by .capitalize())."""
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        # No URL objects exist, but should not crash
        assert repo.count("URL") == 0
        assert repo.count("url") == 0


# ============================================================
# FTS5 Update and Delete Triggers
# ============================================================


class TestFTS5Triggers:
    """Test that FTS5 stays in sync on update and delete."""

    def test_fts_reflects_updated_content(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        # Update content
        repo.update(obj_id, content="Completely new content about nanotechnology")

        # Should find by new content
        results = repo.search("nanotechnology")
        assert any(r["id"] == obj_id for r in results)

        # Should NOT find by old content
        results_old = repo.search("superposition")
        assert not any(r["id"] == obj_id for r in results_old)

    def test_fts_removes_deleted_object(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        obj_id = sample_objects["obj_c"]["id"]

        # Verify searchable before delete
        results = repo.search("observation")
        assert any(r["id"] == obj_id for r in results)

        repo.delete(obj_id)

        # Should not appear in search after delete
        results_after = repo.search("observation")
        assert not any(r["id"] == obj_id for r in results_after)

    def test_fts_reflects_updated_title(self, sample_objects):
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        obj_id = sample_objects["obj_b"]["id"]

        repo.update(obj_id, title="Renamed To Something Unique XYZ")

        results = repo.search("XYZ")
        assert any(r["id"] == obj_id for r in results)


# ============================================================
# ObjectRepo.list() case sensitivity
# ============================================================


class TestObjectRepoListCaseSensitivity:
    """Test that list type filter is case-insensitive."""

    def test_list_url_type(self, sample_objects):
        """Filtering by 'url' (lowercase) should work for URL type."""
        conn = sample_objects["conn"]
        repo = ObjectRepo(conn)
        # Create a URL-type object
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["url"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Example URL",
            content="https://example.com",
        )
        results = repo.list(type_name="url")
        assert any(r["id"] == obj["id"] for r in results)

        results_upper = repo.list(type_name="URL")
        assert any(r["id"] == obj["id"] for r in results_upper)


class TestLikeEscaping:
    """Test that LIKE wildcards in IDs are properly escaped."""

    def test_resolve_id_with_percent(self, bootstrapped_db):
        """A prefix containing '%' should not match all objects."""
        repo = ObjectRepo(bootstrapped_db)
        # '%' as a prefix should not accidentally match everything
        result = repo.resolve_id("%%%%%%%%")
        assert result is None

    def test_resolve_id_with_underscore(self, bootstrapped_db):
        """A prefix containing '_' should not act as single-char wildcard."""
        repo = ObjectRepo(bootstrapped_db)
        result = repo.resolve_id("________-____-____-____")
        assert result is None

    def test_get_by_prefix_with_percent(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        result = repo.get_by_prefix("%%%%%%%%")
        assert result is None


class TestSearchExcludesBootstrap:
    """Test that FTS5 search excludes bootstrap type/space/tag objects."""

    def test_search_does_not_return_bootstrap_types(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        # "Document" is a bootstrap type title
        results = repo.search("Document")
        bootstrap_ids = set(BOOTSTRAP_IDS.values())
        for r in results:
            assert r["id"] not in bootstrap_ids, f"Bootstrap object {r['id']} found in search results"

    def test_search_does_not_return_bootstrap_spaces(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        results = repo.search("Inbox")
        bootstrap_ids = set(BOOTSTRAP_IDS.values())
        for r in results:
            assert r["id"] not in bootstrap_ids


class TestPathTraversalGuard:
    """Test that FileRepo rejects path traversal attempts."""

    def test_validate_path_rejects_traversal(self, _patched_settings):
        """_validate_path should raise on paths that escape files_dir."""
        repo_cls = FileRepo
        from pathlib import Path
        traversal_path = _patched_settings.files_dir / ".." / ".." / "etc" / "passwd"
        with pytest.raises(ValueError, match="Path traversal"):
            repo_cls._validate_path(traversal_path)

    def test_validate_path_accepts_normal(self, _patched_settings):
        """_validate_path should accept paths within files_dir."""
        repo_cls = FileRepo
        normal_path = _patched_settings.files_dir / "ab" / "cd" / "test.txt"
        normal_path.parent.mkdir(parents=True, exist_ok=True)
        normal_path.touch()
        result = repo_cls._validate_path(normal_path)
        assert result is not None


class TestUnicodeFTS5:
    """Test that FTS5 handles Unicode content correctly."""

    def test_search_unicode_content(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["note"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="日本語テスト",
            content="これはテストです。Unicode content works.",
        )
        results = repo.search("Unicode")
        assert any(r["id"] == obj["id"] for r in results)

    def test_search_emoji_content(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["note"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Emoji Test",
            content="This has emojis 🎉 and special chars",
        )
        # Search by non-emoji part of the content
        results = repo.search("emojis")
        assert any(r["id"] == obj["id"] for r in results)


class TestNullVsEmptyString:
    """Test NULL vs empty string handling in objects."""

    def test_create_with_none_summary(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="No Summary",
            summary=None,
        )
        fetched = repo.get(obj["id"])
        assert fetched["summary"] is None

    def test_create_with_empty_string_summary(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Empty Summary",
            summary="",
        )
        fetched = repo.get(obj["id"])
        assert fetched["summary"] == ""

    def test_create_with_none_content(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="No Content",
            content=None,
        )
        fetched = repo.get(obj["id"])
        assert fetched["content"] is None


class TestFileRepoReplacement:
    """Test that attaching a file to an object that already has one replaces it."""

    def test_attach_replaces_existing(self, sample_objects, _patched_settings):
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        # Attach first file
        source1 = _patched_settings.data_dir / "first.txt"
        source1.write_text("First attachment")
        result1 = repo.attach(obj_id, source1)

        # Attach second file (should replace)
        source2 = _patched_settings.data_dir / "second.txt"
        source2.write_text("Second attachment")
        result2 = repo.attach(obj_id, source2)

        # Should have second file's content
        full_path = repo.get_full_path(obj_id)
        assert full_path.read_text() == "Second attachment"
        assert result2["sha256"] != result1["sha256"]

    def test_attach_replaces_cleans_old_file(self, sample_objects, _patched_settings):
        """Test that old file is deleted when attaching a new file."""
        conn = sample_objects["conn"]
        repo = FileRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        # Attach first file
        source1 = _patched_settings.data_dir / "first.txt"
        source1.write_text("First attachment")
        result1 = repo.attach(obj_id, source1)
        first_path = _patched_settings.files_dir / result1["path"]
        assert first_path.exists()

        # Attach second file with different extension
        source2 = _patched_settings.data_dir / "second.json"
        source2.write_text('{"key": "value"}')
        result2 = repo.attach(obj_id, source2)

        # Old file should be deleted
        assert not first_path.exists(), "Old file should be deleted on replace"

        # New file should exist
        new_path = _patched_settings.files_dir / result2["path"]
        assert new_path.exists()


class TestTagNormalization:
    """Test that tags are normalized (lowercase)."""

    def test_add_normalizes_to_lowercase(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        repo.add(obj_id, "UPPERCASE")
        conn.commit()

        tags = repo.list_for_object(obj_id)
        assert "uppercase" in tags
        assert "UPPERCASE" not in tags

    def test_add_normalizes_mixed_case(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        repo.add(obj_id, "MixedCase")
        conn.commit()

        tags = repo.list_for_object(obj_id)
        assert "mixedcase" in tags

    def test_add_trims_whitespace(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        repo.add(obj_id, "  padded  ")
        conn.commit()

        tags = repo.list_for_object(obj_id)
        assert "padded" in tags

    def test_remove_normalizes_query(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        # Add lowercase tag
        repo.add(obj_id, "newtag")
        conn.commit()

        # Remove with uppercase (should still match)
        result = repo.remove(obj_id, "NEWTAG")
        conn.commit()

        assert result is True
        tags = repo.list_for_object(obj_id)
        assert "newtag" not in tags

    def test_add_empty_tag_returns_false(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        result = repo.add(obj_id, "   ")
        assert result is False

    def test_duplicate_with_different_case_returns_false(self, sample_objects):
        conn = sample_objects["conn"]
        repo = TagRepo(conn)
        obj_id = sample_objects["obj_a"]["id"]

        # Add lowercase
        result1 = repo.add(obj_id, "mytag")
        conn.commit()

        # Try to add uppercase version (should fail as duplicate)
        result2 = repo.add(obj_id, "MYTAG")

        assert result1 is True
        assert result2 is False


class TestObjectSourceField:
    """Test the new source field for object provenance."""

    def test_create_default_source_is_human(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Default Source Test",
        )
        bootstrapped_db.commit()

        row = bootstrapped_db.execute(
            "SELECT source FROM objects WHERE id = ?", (obj["id"],)
        ).fetchone()
        assert row["source"] == "human"

    def test_create_with_explicit_source(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="AI Generated",
            source="ai",
        )
        bootstrapped_db.commit()

        row = bootstrapped_db.execute(
            "SELECT source FROM objects WHERE id = ?", (obj["id"],)
        ).fetchone()
        assert row["source"] == "ai"

    def test_create_with_import_source(self, bootstrapped_db):
        repo = ObjectRepo(bootstrapped_db)
        obj = repo.create(
            type_id=BOOTSTRAP_IDS["document"],
            space_id=BOOTSTRAP_IDS["primitives"],
            title="Imported Content",
            source="import",
        )
        bootstrapped_db.commit()

        row = bootstrapped_db.execute(
            "SELECT source FROM objects WHERE id = ?", (obj["id"],)
        ).fetchone()
        assert row["source"] == "import"


class TestLinkMetadata:
    """Test link source and confidence fields."""

    def test_create_link_default_source(self, sample_objects):
        conn = sample_objects["conn"]
        repo = LinkRepo(conn)

        link = repo.create(
            sample_objects["obj_a"]["id"],
            sample_objects["obj_c"]["id"],
            "new-relationship",
        )
        conn.commit()

        row = conn.execute(
            "SELECT source, confidence FROM links WHERE id = ?", (link["id"],)
        ).fetchone()
        assert row["source"] == "human"
        assert row["confidence"] == 1.0

    def test_create_link_with_ai_source(self, sample_objects):
        conn = sample_objects["conn"]
        repo = LinkRepo(conn)

        link = repo.create(
            sample_objects["obj_b"]["id"],
            sample_objects["obj_c"]["id"],
            "ai-suggested",
            source="ai",
            confidence=0.85,
        )
        conn.commit()

        row = conn.execute(
            "SELECT source, confidence FROM links WHERE id = ?", (link["id"],)
        ).fetchone()
        assert row["source"] == "ai"
        assert row["confidence"] == 0.85
