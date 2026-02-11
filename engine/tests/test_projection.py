"""Tests for the projection layer.

Tests cover scoring, candidate selection, file projection, sync, and CLAUDE.md generation.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from src.config import settings
from src.core.bootstrap import BOOTSTRAP_IDS
from src.core.projection import (
    ProjectionResult,
    SyncResult,
    calculate_scores,
    deproject_object,
    generate_claude_md,
    get_projection_candidates,
    get_tier_status,
    project_object,
    run_projection_cycle,
    sync_from_file,
)
from src.core.repository import ObjectRepo, TagRepo


class TestCalculateScores:
    """Tests for calculate_scores function."""

    def test_empty_db_returns_empty_list(self, bootstrapped_db):
        """Empty DB (only bootstrap) returns empty list."""
        scores = calculate_scores(bootstrapped_db)
        assert scores == []

    def test_scores_sorted_by_recency(self, sample_objects):
        """More recently updated objects have higher scores."""
        conn = sample_objects["conn"]

        scores = calculate_scores(conn)
        assert len(scores) == 3

        # Scores should be sorted descending
        assert scores[0].score >= scores[1].score >= scores[2].score

    def test_older_objects_have_lower_scores(self, sample_objects):
        """Objects with older updated_at have lower scores."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        # Manually age obj_a
        old_time = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        conn.execute(
            "UPDATE objects SET updated_at = ? WHERE id = ?", (old_time, obj_a["id"])
        )
        conn.commit()

        scores = calculate_scores(conn)
        obj_a_score = next(s for s in scores if s.id == obj_a["id"])

        # obj_a should now have the lowest score
        assert obj_a_score.score < min(s.score for s in scores if s.id != obj_a["id"])

    def test_projection_override_included(self, sample_objects):
        """Projection override is included in scores."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        # Set override
        conn.execute(
            "UPDATE objects SET projection_override = 'always' WHERE id = ?",
            (obj_a["id"],),
        )
        conn.commit()

        scores = calculate_scores(conn)
        obj_a_score = next(s for s in scores if s.id == obj_a["id"])
        assert obj_a_score.projection_override == "always"


class TestGetProjectionCandidates:
    """Tests for get_projection_candidates function."""

    def test_respects_limit(self, sample_objects, _patched_settings):
        """Candidates are limited to hot tier limit."""
        conn = sample_objects["conn"]
        _patched_settings.projection_hot_limit = 2

        candidates = get_projection_candidates(conn, limit=2)
        assert len(candidates) == 2

    def test_always_override_included_regardless_of_score(self, sample_objects):
        """Objects with always override are included even with low score."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        # Age obj_a and set always override
        old_time = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        conn.execute(
            "UPDATE objects SET updated_at = ?, projection_override = 'always' WHERE id = ?",
            (old_time, obj_a["id"]),
        )
        conn.commit()

        candidates = get_projection_candidates(conn, limit=1)

        # obj_a should be included due to always override
        candidate_ids = {c.id for c in candidates}
        assert obj_a["id"] in candidate_ids

    def test_never_override_excluded(self, sample_objects):
        """Objects with never override are excluded."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        # Set never override on obj_a
        conn.execute(
            "UPDATE objects SET projection_override = 'never' WHERE id = ?",
            (obj_a["id"],),
        )
        conn.commit()

        candidates = get_projection_candidates(conn, limit=100)

        candidate_ids = {c.id for c in candidates}
        assert obj_a["id"] not in candidate_ids


class TestProjectObject:
    """Tests for project_object function."""

    def test_creates_file_with_correct_format(self, sample_objects, _patched_settings):
        """Projected file has correct YAML frontmatter and body."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        result = project_object(conn, obj_a["id"])
        assert result.success
        assert result.path is not None
        assert result.path.exists()

        content = result.path.read_text()
        assert content.startswith("---\n")

        # Parse frontmatter
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])

        assert frontmatter["id"] == obj_a["id"]
        assert frontmatter["title"] == "Alpha Document"
        assert frontmatter["type"] == "Document"
        assert "quantum" in frontmatter.get("tags", [])

        # Body content
        body = parts[2].strip()
        assert body == "Quantum computing leverages superposition and entanglement."

    def test_file_named_correctly(self, sample_objects, _patched_settings):
        """Filename follows {slug}-{id[:12]}.md pattern."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        result = project_object(conn, obj_a["id"])

        filename = result.path.name
        assert filename.endswith(".md")
        assert obj_a["id"][:12] in filename
        assert "alpha-document" in filename.lower()

    def test_creates_directory_structure(self, sample_objects, _patched_settings):
        """Projected files are organized by space."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        result = project_object(conn, obj_a["id"])

        # Should be in projected directory with space-based path
        assert str(_patched_settings.projected_dir) in str(result.path)
        # File should be in a subdirectory (space path)
        assert result.path.parent != _patched_settings.projected_dir

    def test_nonexistent_object_returns_failure(self, bootstrapped_db, _patched_settings):
        """Projecting nonexistent object returns failure result."""
        result = project_object(bootstrapped_db, "nonexistent-id")
        assert not result.success
        assert "not found" in result.message.lower()


class TestDeprojectObject:
    """Tests for deproject_object function."""

    def test_removes_projected_file(self, sample_objects, _patched_settings):
        """Deprojecting removes the file."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        # First project
        result = project_object(conn, obj_a["id"])
        assert result.path.exists()

        # Then deproject
        deproject_result = deproject_object(conn, obj_a["id"])
        assert deproject_result.success
        assert not result.path.exists()

    def test_nonexistent_projection_returns_failure(self, sample_objects, _patched_settings):
        """Deprojecting non-projected object returns failure."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        result = deproject_object(conn, obj_a["id"])
        assert not result.success
        assert "no projected file" in result.message.lower()


class TestSyncFromFile:
    """Tests for sync_from_file function."""

    def test_syncs_content_changes(self, sample_objects, _patched_settings):
        """Editing content body syncs back to DB."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        # Project first
        result = project_object(conn, obj_a["id"])
        file_path = result.path

        # Modify the body
        content = file_path.read_text()
        new_content = content.replace(
            "Quantum computing leverages superposition and entanglement.",
            "Updated content about quantum computing.",
        )
        file_path.write_text(new_content)

        # Sync
        sync_result = sync_from_file(conn, file_path)
        assert sync_result.success
        assert sync_result.object_id == obj_a["id"]

        # Verify DB updated
        obj_repo = ObjectRepo(conn)
        updated = obj_repo.get(obj_a["id"])
        assert "Updated content about quantum computing" in updated["content"]

    def test_syncs_title_changes(self, sample_objects, _patched_settings):
        """Editing title in frontmatter syncs back to DB."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        result = project_object(conn, obj_a["id"])
        file_path = result.path

        # Modify the title
        content = file_path.read_text()
        new_content = content.replace(
            'title: Alpha Document', 'title: "New Alpha Title"'
        )
        file_path.write_text(new_content)

        sync_result = sync_from_file(conn, file_path)
        assert sync_result.success

        obj_repo = ObjectRepo(conn)
        updated = obj_repo.get(obj_a["id"])
        assert updated["title"] == "New Alpha Title"

    def test_rejects_id_change(self, sample_objects, _patched_settings):
        """Changing ID in frontmatter is rejected."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        result = project_object(conn, obj_a["id"])
        file_path = result.path

        # Try to change the ID
        content = file_path.read_text()
        new_content = content.replace(obj_a["id"], "fake-id-12345678")
        file_path.write_text(new_content)

        sync_result = sync_from_file(conn, file_path)
        assert not sync_result.success
        assert "mismatch" in sync_result.message.lower() or "not found" in sync_result.message.lower()

    def test_rejects_space_change(self, sample_objects, _patched_settings):
        """Changing space in frontmatter is rejected."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        result = project_object(conn, obj_a["id"])
        file_path = result.path

        # Read and parse to find actual space value
        content = file_path.read_text()
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        actual_space = frontmatter["space"]

        # Try to change the space
        new_content = content.replace(f"space: {actual_space}", "space: different/space")
        file_path.write_text(new_content)

        sync_result = sync_from_file(conn, file_path)
        assert not sync_result.success
        assert "immutable" in sync_result.message.lower()

    def test_syncs_tag_changes(self, sample_objects, _patched_settings):
        """Modifying tags syncs back to DB."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        result = project_object(conn, obj_a["id"])
        file_path = result.path

        # Parse the file and modify tags programmatically
        content = file_path.read_text()
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])

        # Add a new tag
        frontmatter["tags"] = frontmatter.get("tags", []) + ["new-tag"]

        # Reconstruct the file
        yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
        body = parts[2] if len(parts) > 2 else ""
        new_content = f"---\n{yaml_str}---{body}"
        file_path.write_text(new_content)

        sync_result = sync_from_file(conn, file_path)
        assert sync_result.success

        tag_repo = TagRepo(conn)
        tags = tag_repo.list_for_object(obj_a["id"])
        assert "new-tag" in tags

    def test_ignores_claude_md(self, bootstrapped_db, _patched_settings):
        """CLAUDE.md files are not synced."""
        claude_md = _patched_settings.projected_dir / "CLAUDE.md"
        claude_md.parent.mkdir(parents=True, exist_ok=True)
        claude_md.write_text("# Test")

        result = sync_from_file(bootstrapped_db, claude_md)
        assert not result.success
        assert "auto-generated" in result.message.lower()


class TestGenerateClaudeMd:
    """Tests for generate_claude_md function."""

    def test_generates_space_index(self, sample_objects, _patched_settings):
        """CLAUDE.md lists objects in the space."""
        conn = sample_objects["conn"]

        # The primitives space title is "primitives" (path as title)
        content = generate_claude_md(conn, "primitives")

        assert "# primitives" in content
        assert "Alpha Document" in content
        assert "Beta Document" in content
        assert "Gamma Note" in content


class TestRunProjectionCycle:
    """Tests for run_projection_cycle function."""

    def test_projects_all_candidates(self, sample_objects, _patched_settings):
        """Full cycle projects all candidates."""
        conn = sample_objects["conn"]
        # Reset limit to allow all objects
        _patched_settings.projection_hot_limit = 200

        result = run_projection_cycle(conn, cleanup=False, dry_run=False)

        assert result["projected"] == 3
        assert len(result["errors"]) == 0

        # Check files exist
        projected_files = list(_patched_settings.projected_dir.rglob("*.md"))
        # 3 objects + CLAUDE.md files
        assert len([f for f in projected_files if f.name != "CLAUDE.md"]) == 3

    def test_dry_run_does_not_create_files(self, sample_objects, _patched_settings):
        """Dry run reports but doesn't create files."""
        conn = sample_objects["conn"]
        # Reset limit to allow all objects
        _patched_settings.projection_hot_limit = 200

        result = run_projection_cycle(conn, cleanup=False, dry_run=True)

        assert result["projected"] == 3
        assert result["dry_run"] is True

        # No actual files created
        projected_files = list(_patched_settings.projected_dir.rglob("*.md"))
        assert len(projected_files) == 0

    def test_cleanup_removes_stale_files(self, sample_objects, _patched_settings):
        """Cleanup removes files for objects no longer in candidates."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]
        # Reset limit to allow all objects initially
        _patched_settings.projection_hot_limit = 200

        # First run to project all
        first_result = run_projection_cycle(conn, cleanup=False, dry_run=False)
        assert first_result["projected"] == 3, f"Expected 3 projected, got {first_result}"

        # Verify files exist
        projected_files = list(_patched_settings.projected_dir.rglob("*.md"))
        object_files = [f for f in projected_files if f.name != "CLAUDE.md"]
        assert len(object_files) == 3, f"Expected 3 object files, got {len(object_files)}"

        # Set obj_a to never project
        conn.execute(
            "UPDATE objects SET projection_override = 'never' WHERE id = ?",
            (obj_a["id"],),
        )
        conn.commit()

        # Verify the update took effect
        row = conn.execute(
            "SELECT projection_override FROM objects WHERE id = ?", (obj_a["id"],)
        ).fetchone()
        assert row["projection_override"] == "never"

        # Verify obj_a is no longer a candidate
        candidates = get_projection_candidates(conn)
        candidate_ids = [c.id for c in candidates]
        assert obj_a["id"] not in candidate_ids, "obj_a should not be a candidate"

        # Debug: show candidate prefixes
        candidate_prefixes = {c.id[:12] for c in candidates}
        print(f"Candidate prefixes: {candidate_prefixes}")
        print(f"obj_a prefix: {obj_a['id'][:12]}")

        # Debug: show file IDs before cleanup
        for f in object_files:
            content = f.read_text()
            parts = content.split("---", 2)
            if len(parts) >= 2:
                fm = yaml.safe_load(parts[1])
                print(f"File {f.name}: id={fm.get('id', 'NO ID')[:12] if fm else 'NO FM'}")

        # Run with cleanup
        result = run_projection_cycle(conn, cleanup=True, dry_run=False)

        # Check files after cleanup
        remaining_files = list(_patched_settings.projected_dir.rglob("*.md"))
        remaining_object_files = [f for f in remaining_files if f.name != "CLAUDE.md"]

        # Print errors for debugging
        if result["errors"]:
            print(f"Errors during cleanup: {result['errors']}")

        assert result["deprojected"] >= 1, (
            f"Expected at least 1 deprojected, got {result['deprojected']}. "
            f"Candidates: {len(candidates)}, Files before: {len(object_files)}, "
            f"Files after: {len(remaining_object_files)}, "
            f"Errors: {result['errors']}, "
            f"Candidate prefixes: {candidate_prefixes}, obj_a prefix: {obj_a['id'][:12]}"
        )

    def test_creates_root_claude_md(self, sample_objects, _patched_settings):
        """Root CLAUDE.md is created with space overview."""
        conn = sample_objects["conn"]
        # Reset limit to allow all objects
        _patched_settings.projection_hot_limit = 200

        run_projection_cycle(conn, cleanup=False, dry_run=False)

        root_claude = _patched_settings.projected_dir / "CLAUDE.md"
        assert root_claude.exists()
        content = root_claude.read_text()
        assert "ExoBrain Projected Objects" in content


class TestGetTierStatus:
    """Tests for get_tier_status function."""

    def test_returns_correct_counts(self, sample_objects, _patched_settings):
        """Status returns correct object counts."""
        conn = sample_objects["conn"]
        # Reset limit to allow all objects
        _patched_settings.projection_hot_limit = 200

        status = get_tier_status(conn)

        assert status["total_objects"] == 3
        assert status["projected_count"] == 3
        assert status["hot_tier_limit"] == 200
        assert len(status["top_5_by_score"]) == 3

    def test_shows_overrides(self, sample_objects, _patched_settings):
        """Status shows override objects."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]
        obj_b = sample_objects["obj_b"]

        conn.execute(
            "UPDATE objects SET projection_override = 'always' WHERE id = ?",
            (obj_a["id"],),
        )
        conn.execute(
            "UPDATE objects SET projection_override = 'never' WHERE id = ?",
            (obj_b["id"],),
        )
        conn.commit()

        status = get_tier_status(conn)

        assert len(status["always_project"]) == 1
        assert status["always_project"][0]["id"] == obj_a["id"][:12]
        assert len(status["never_project"]) == 1
        assert status["never_project"][0]["id"] == obj_b["id"][:12]


class TestDeletedPurgedExclusion:
    """Tests that deleted and purged objects are excluded from projection scoring and CLAUDE.md."""

    def test_deleted_objects_excluded_from_projection_scores(self, sample_objects):
        """Soft-deleted objects should not appear in calculate_scores results."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        # Verify obj_a is included before deletion
        scores_before = calculate_scores(conn)
        score_ids_before = {s.id for s in scores_before}
        assert obj_a["id"] in score_ids_before

        # Soft-delete obj_a
        conn.execute(
            "UPDATE objects SET deleted_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?",
            (obj_a["id"],),
        )
        conn.commit()

        # Verify obj_a is excluded after deletion
        scores_after = calculate_scores(conn)
        score_ids_after = {s.id for s in scores_after}
        assert obj_a["id"] not in score_ids_after
        assert len(scores_after) == len(scores_before) - 1

    def test_purged_objects_excluded_from_projection_scores(self, sample_objects):
        """Purged (tombstoned) objects should not appear in calculate_scores results."""
        conn = sample_objects["conn"]
        obj_b = sample_objects["obj_b"]

        # Verify obj_b is included before purge
        scores_before = calculate_scores(conn)
        score_ids_before = {s.id for s in scores_before}
        assert obj_b["id"] in score_ids_before

        # Purge obj_b (set both purged_at and deleted_at as the real purge does)
        conn.execute(
            """UPDATE objects SET
                purged_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
                deleted_at = COALESCE(deleted_at, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
               WHERE id = ?""",
            (obj_b["id"],),
        )
        conn.commit()

        # Verify obj_b is excluded after purge
        scores_after = calculate_scores(conn)
        score_ids_after = {s.id for s in scores_after}
        assert obj_b["id"] not in score_ids_after
        assert len(scores_after) == len(scores_before) - 1

    def test_deleted_objects_excluded_from_claude_md(self, sample_objects, _patched_settings):
        """Soft-deleted objects should not appear in generate_claude_md output."""
        conn = sample_objects["conn"]
        obj_a = sample_objects["obj_a"]

        # Verify obj_a appears before deletion
        content_before = generate_claude_md(conn, "primitives")
        assert "Alpha Document" in content_before

        # Soft-delete obj_a
        conn.execute(
            "UPDATE objects SET deleted_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?",
            (obj_a["id"],),
        )
        conn.commit()

        # Verify obj_a no longer appears
        content_after = generate_claude_md(conn, "primitives")
        assert "Alpha Document" not in content_after
        # Other objects should still be present
        assert "Beta Document" in content_after
        assert "Gamma Note" in content_after
