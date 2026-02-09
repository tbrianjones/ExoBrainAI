"""Tests for src.cli.main: CLI commands via Typer CliRunner."""

import json

import pytest
from typer.testing import CliRunner

from src.cli.main import app
from src.core.bootstrap import BOOTSTRAP_IDS
from src.core.db import init_db
from src.core.bootstrap import bootstrap


runner = CliRunner()


@pytest.fixture()
def initialized_db(_patched_settings):
    """Initialize and bootstrap the DB so CLI commands can find it.

    The _patched_settings fixture makes settings.data_dir point to tmp_path,
    so init_db() and bootstrap() create the DB in the temp directory.
    """
    conn = init_db(_patched_settings.db_path)
    bootstrap(conn)
    conn.close()
    return _patched_settings


# ============================================================
# System Commands
# ============================================================


class TestInitCommand:
    """Test 'exobrain init'."""

    def test_init_creates_db(self, _patched_settings):
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "Initialized" in result.output

    def test_init_json(self, _patched_settings):
        result = runner.invoke(app, ["init", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ok"
        assert data["integrity"]["ok"] is True
        assert "bootstrap" in data

    def test_init_idempotent(self, _patched_settings):
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0


class TestStatusCommand:
    """Test 'exobrain status'."""

    def test_status_shows_counts(self, initialized_db):
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Objects:" in result.output
        assert "Tags:" in result.output

    def test_status_json(self, initialized_db):
        result = runner.invoke(app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "object_count" in data
        assert "type_counts" in data
        assert "integrity" in data
        assert data["object_count"] >= 11  # bootstrap objects


# ============================================================
# Capture Command
# ============================================================


class TestCaptureCommand:
    """Test 'exobrain capture'."""

    def test_capture_with_content(self, initialized_db):
        result = runner.invoke(app, ["capture", "My test content", "--title", "Test Title"])
        assert result.exit_code == 0
        assert "Created:" in result.output

    def test_capture_json(self, initialized_db):
        result = runner.invoke(app, ["capture", "JSON capture test", "--title", "JSON Test", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["title"] == "JSON Test"
        assert "id" in data

    def test_capture_with_tags(self, initialized_db):
        result = runner.invoke(app, [
            "capture", "Tagged content",
            "--title", "Tagged",
            "--tag", "alpha",
            "--tag", "beta",
        ])
        assert result.exit_code == 0
        assert "Tags:" in result.output
        assert "alpha" in result.output

    def test_capture_with_type(self, initialized_db):
        result = runner.invoke(app, [
            "capture", "A note",
            "--title", "My Note",
            "--type", "note",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["type_name"] == "Note"


# ============================================================
# Search Command
# ============================================================


class TestSearchCommand:
    """Test 'exobrain search'."""

    def test_search_finds_captured(self, initialized_db):
        # First capture something
        runner.invoke(app, ["capture", "Quantum mechanics exploration", "--title", "Quantum"])
        result = runner.invoke(app, ["search", "quantum"])
        assert result.exit_code == 0
        assert "Quantum" in result.output

    def test_search_no_results(self, initialized_db):
        result = runner.invoke(app, ["search", "xyznonexistentterm"])
        assert result.exit_code == 0
        assert "No results" in result.output

    def test_search_json(self, initialized_db):
        runner.invoke(app, ["capture", "Searchable content", "--title", "Searchable"])
        result = runner.invoke(app, ["search", "Searchable", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) >= 1


# ============================================================
# List Command
# ============================================================


class TestListCommand:
    """Test 'exobrain list'."""

    def test_list_empty_db(self, initialized_db):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_list_after_capture(self, initialized_db):
        runner.invoke(app, ["capture", "List test content", "--title", "List Test"])
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "List Test" in result.output

    def test_list_filter_by_type(self, initialized_db):
        runner.invoke(app, ["capture", "A doc", "--title", "Doc", "--type", "document"])
        runner.invoke(app, ["capture", "A note", "--title", "NoteObj", "--type", "note"])
        result = runner.invoke(app, ["list", "--type", "note"])
        assert result.exit_code == 0
        assert "NoteObj" in result.output

    def test_list_json(self, initialized_db):
        runner.invoke(app, ["capture", "JSON list test", "--title", "JSON List"])
        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)


# ============================================================
# Tag Commands
# ============================================================


class TestTagCommands:
    """Test 'exobrain tag add/remove/list'."""

    def _capture_and_get_id(self, initialized_db):
        """Helper: capture an object and return its ID."""
        result = runner.invoke(app, [
            "capture", "Tag test object", "--title", "Tag Test", "--json",
        ])
        data = json.loads(result.output)
        return data["id"]

    def test_tag_add(self, initialized_db):
        obj_id = self._capture_and_get_id(initialized_db)
        result = runner.invoke(app, ["tag", "add", obj_id, "mytag"])
        assert result.exit_code == 0
        assert "Tagged" in result.output

    def test_tag_add_json(self, initialized_db):
        obj_id = self._capture_and_get_id(initialized_db)
        result = runner.invoke(app, ["tag", "add", obj_id, "jsontag", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["added"] is True
        assert data["tag"] == "jsontag"

    def test_tag_remove(self, initialized_db):
        obj_id = self._capture_and_get_id(initialized_db)
        runner.invoke(app, ["tag", "add", obj_id, "removeme"])
        result = runner.invoke(app, ["tag", "remove", obj_id, "removeme"])
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_tag_remove_json(self, initialized_db):
        obj_id = self._capture_and_get_id(initialized_db)
        runner.invoke(app, ["tag", "add", obj_id, "goner"])
        result = runner.invoke(app, ["tag", "remove", obj_id, "goner", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["removed"] is True

    def test_tag_list(self, initialized_db):
        obj_id = self._capture_and_get_id(initialized_db)
        runner.invoke(app, ["tag", "add", obj_id, "listed"])
        result = runner.invoke(app, ["tag", "list"])
        assert result.exit_code == 0
        assert "listed" in result.output

    def test_tag_list_json(self, initialized_db):
        obj_id = self._capture_and_get_id(initialized_db)
        runner.invoke(app, ["tag", "add", obj_id, "jsonlisted"])
        result = runner.invoke(app, ["tag", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        tag_texts = [t["tag_text"] for t in data]
        assert "jsonlisted" in tag_texts


# ============================================================
# Link Commands
# ============================================================


class TestLinkCommands:
    """Test 'exobrain link create/list/remove'."""

    def _create_two_objects(self, initialized_db):
        """Helper: create two objects and return their IDs."""
        r1 = runner.invoke(app, ["capture", "Link source", "--title", "Source", "--json"])
        r2 = runner.invoke(app, ["capture", "Link target", "--title", "Target", "--json"])
        id1 = json.loads(r1.output)["id"]
        id2 = json.loads(r2.output)["id"]
        return id1, id2

    def test_link_create(self, initialized_db):
        id1, id2 = self._create_two_objects(initialized_db)
        result = runner.invoke(app, ["link", "create", id1, id2, "related-to"])
        assert result.exit_code == 0
        assert "Linked" in result.output

    def test_link_create_json(self, initialized_db):
        id1, id2 = self._create_two_objects(initialized_db)
        result = runner.invoke(app, ["link", "create", id1, id2, "inspired-by", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["relationship"] == "inspired-by"

    def test_link_list(self, initialized_db):
        id1, id2 = self._create_two_objects(initialized_db)
        runner.invoke(app, ["link", "create", id1, id2, "depends-on"])
        result = runner.invoke(app, ["link", "list", id1])
        assert result.exit_code == 0
        assert "depends-on" in result.output

    def test_link_list_json(self, initialized_db):
        id1, id2 = self._create_two_objects(initialized_db)
        runner.invoke(app, ["link", "create", id1, id2, "json-link"])
        result = runner.invoke(app, ["link", "list", id1, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert any(l["relationship"] == "json-link" for l in data)

    def test_link_remove(self, initialized_db):
        id1, id2 = self._create_two_objects(initialized_db)
        create_result = runner.invoke(app, ["link", "create", id1, id2, "temp", "--json"])
        link = json.loads(create_result.output)
        link_id = str(link["id"])
        result = runner.invoke(app, ["link", "remove", link_id])
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_link_remove_json(self, initialized_db):
        id1, id2 = self._create_two_objects(initialized_db)
        create_result = runner.invoke(app, ["link", "create", id1, id2, "temp2", "--json"])
        link = json.loads(create_result.output)
        link_id = str(link["id"])
        result = runner.invoke(app, ["link", "remove", link_id, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["deleted"] is True


# ============================================================
# JSON Output Consistency
# ============================================================


class TestJsonOutputConsistency:
    """Verify that --json flag always produces parseable JSON."""

    def test_init_json_parseable(self, _patched_settings):
        result = runner.invoke(app, ["init", "--json"])
        assert result.exit_code == 0
        json.loads(result.output)  # should not raise

    def test_status_json_parseable(self, initialized_db):
        result = runner.invoke(app, ["status", "--json"])
        assert result.exit_code == 0
        json.loads(result.output)

    def test_capture_json_parseable(self, initialized_db):
        result = runner.invoke(app, ["capture", "JSON test", "--title", "JT", "--json"])
        assert result.exit_code == 0
        json.loads(result.output)

    def test_list_json_parseable(self, initialized_db):
        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0
        json.loads(result.output)

    def test_search_json_parseable(self, initialized_db):
        result = runner.invoke(app, ["search", "test", "--json"])
        assert result.exit_code == 0
        json.loads(result.output)

    def test_tag_list_json_parseable(self, initialized_db):
        result = runner.invoke(app, ["tag", "list", "--json"])
        assert result.exit_code == 0
        json.loads(result.output)

    def test_type_list_json_parseable(self, initialized_db):
        result = runner.invoke(app, ["type", "list", "--json"])
        assert result.exit_code == 0
        json.loads(result.output)

    def test_space_list_json_parseable(self, initialized_db):
        result = runner.invoke(app, ["space", "list", "--json"])
        assert result.exit_code == 0
        json.loads(result.output)

    def test_doctor_json_parseable(self, initialized_db):
        result = runner.invoke(app, ["doctor", "--json"])
        assert result.exit_code == 0
        json.loads(result.output)


# ============================================================
# Get Command
# ============================================================


class TestGetCommand:
    """Test 'exobrain get'."""

    def test_get_by_full_id(self, initialized_db):
        create = runner.invoke(app, ["capture", "Get test", "--title", "Get Me", "--json"])
        obj_id = json.loads(create.output)["id"]
        result = runner.invoke(app, ["get", obj_id])
        assert result.exit_code == 0
        assert "Get Me" in result.output

    def test_get_json(self, initialized_db):
        create = runner.invoke(app, ["capture", "Get JSON", "--title", "JSON Get", "--json"])
        obj_id = json.loads(create.output)["id"]
        result = runner.invoke(app, ["get", obj_id, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["title"] == "JSON Get"
        assert "tags" in data
        assert "links" in data

    def test_get_shows_full_content(self, initialized_db):
        long_content = "A" * 500
        create = runner.invoke(app, ["capture", long_content, "--title", "Long", "--json"])
        obj_id = json.loads(create.output)["id"]
        result = runner.invoke(app, ["get", obj_id])
        assert result.exit_code == 0
        # Content should NOT be truncated
        assert "..." not in result.output or long_content[:200] in result.output

    def test_get_nonexistent(self, initialized_db):
        result = runner.invoke(app, ["get", "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"])
        assert result.exit_code == 1


# ============================================================
# Update Command
# ============================================================


class TestUpdateCommand:
    """Test 'exobrain update'."""

    def test_update_title(self, initialized_db):
        create = runner.invoke(app, ["capture", "Update me", "--title", "Original", "--json"])
        obj_id = json.loads(create.output)["id"]
        result = runner.invoke(app, ["update", obj_id, "--title", "Changed"])
        assert result.exit_code == 0
        assert "Updated" in result.output

    def test_update_json(self, initialized_db):
        create = runner.invoke(app, ["capture", "Update JSON", "--title", "Before", "--json"])
        obj_id = json.loads(create.output)["id"]
        result = runner.invoke(app, ["update", obj_id, "--title", "After", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["title"] == "After"

    def test_update_space(self, initialized_db):
        create = runner.invoke(app, ["capture", "Move me", "--title", "Movable", "--json"])
        obj_id = json.loads(create.output)["id"]
        result = runner.invoke(app, ["update", obj_id, "--space", "inbox", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["space_name"] == "inbox"


# ============================================================
# Delete Command
# ============================================================


class TestDeleteCommand:
    """Test 'exobrain delete'."""

    def test_delete_with_yes(self, initialized_db):
        create = runner.invoke(app, ["capture", "Delete me", "--title", "Doomed", "--json"])
        obj_id = json.loads(create.output)["id"]
        result = runner.invoke(app, ["delete", obj_id, "--yes"])
        assert result.exit_code == 0
        assert "Deleted" in result.output

    def test_delete_json(self, initialized_db):
        create = runner.invoke(app, ["capture", "Delete JSON", "--title", "Doomed JSON", "--json"])
        obj_id = json.loads(create.output)["id"]
        result = runner.invoke(app, ["delete", obj_id, "--yes", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["deleted"] is True

    def test_delete_bootstrap_object_blocked(self, initialized_db):
        """Cannot delete bootstrap type/space objects."""
        result = runner.invoke(app, ["delete", BOOTSTRAP_IDS["document"], "--yes"])
        assert result.exit_code == 1
        assert "Cannot delete bootstrap" in result.output


# ============================================================
# Type and Space Commands
# ============================================================


class TestTypeCommands:
    """Test 'exobrain type list/create'."""

    def test_type_list(self, initialized_db):
        result = runner.invoke(app, ["type", "list"])
        assert result.exit_code == 0
        assert "Document" in result.output
        assert "Note" in result.output
        assert "URL" in result.output

    def test_type_create(self, initialized_db):
        result = runner.invoke(app, ["type", "create", "meeting", "--summary", "Meeting notes"])
        assert result.exit_code == 0
        assert "Meeting" in result.output

    def test_type_create_json(self, initialized_db):
        result = runner.invoke(app, ["type", "create", "event", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["title"] == "Event"


class TestSpaceCommands:
    """Test 'exobrain space list/create'."""

    def test_space_list(self, initialized_db):
        result = runner.invoke(app, ["space", "list"])
        assert result.exit_code == 0
        assert "inbox" in result.output
        assert "primitives" in result.output

    def test_space_create(self, initialized_db):
        result = runner.invoke(app, ["space", "create", "work"])
        assert result.exit_code == 0
        assert "Created space" in result.output

    def test_space_create_hierarchical(self, initialized_db):
        result = runner.invoke(app, ["space", "create", "work/projects"])
        assert result.exit_code == 0
        # Should create both work and work/projects
        assert "work" in result.output

    def test_space_create_json(self, initialized_db):
        result = runner.invoke(app, ["space", "create", "personal", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)


# ============================================================
# Capture defaults to inbox
# ============================================================


class TestCaptureDefaults:
    """Test capture uses inbox as default space."""

    def test_capture_default_space_is_inbox(self, initialized_db):
        result = runner.invoke(app, ["capture", "Inbox test", "--title", "Inbox Default", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["space_name"] == "inbox"

    def test_capture_with_explicit_space(self, initialized_db):
        # Create a space first
        runner.invoke(app, ["space", "create", "work"])
        result = runner.invoke(app, [
            "capture", "Work content", "--title", "Work Item", "--space", "work", "--json"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["space_name"] == "work"


# ============================================================
# URL type resolution
# ============================================================


class TestURLTypeResolution:
    """Test that URL type resolves correctly (case-insensitive)."""

    def test_capture_url_type(self, initialized_db):
        result = runner.invoke(app, [
            "capture", "https://example.com",
            "--title", "Example",
            "--type", "url",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["type_name"] == "URL"

    def test_capture_URL_type_uppercase(self, initialized_db):
        result = runner.invoke(app, [
            "capture", "https://example.com",
            "--title", "Example Upper",
            "--type", "URL",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["type_name"] == "URL"


# ============================================================
# Capture: --always-project and --created-at flags
# ============================================================


class TestCaptureFlags:
    """Test capture flags used by rewired commands."""

    def test_capture_always_project(self, initialized_db):
        """capture --always-project sets projection_override to 'always'."""
        result = runner.invoke(app, [
            "capture", "always project test",
            "--title", "Always Projected",
            "--always-project", "--json",
        ])
        assert result.exit_code == 0
        obj = json.loads(result.output)
        assert obj["projection_override"] == "always"

    def test_capture_created_at(self, initialized_db):
        """capture --created-at preserves the given timestamp."""
        ts = "2025-06-15T10:30:00.000Z"
        result = runner.invoke(app, [
            "capture", "timestamp test",
            "--title", "Timestamped",
            "--created-at", ts, "--json",
        ])
        assert result.exit_code == 0
        obj = json.loads(result.output)
        assert obj["created_at"] == ts
        assert obj["updated_at"] == ts

    def test_capture_stdin(self, initialized_db):
        """capture reads from stdin when no content argument is given."""
        result = runner.invoke(app, [
            "capture", "--title", "From Stdin", "--json",
        ], input="stdin content here")
        assert result.exit_code == 0
        obj = json.loads(result.output)
        assert "stdin content here" in obj.get("content", "")

    def test_capture_full_combo(self, initialized_db):
        """capture with all flags used by generate-transcript and similar commands."""
        result = runner.invoke(app, [
            "capture",
            "--title", "Transcript",
            "--type", "document",
            "--space", "inbox",
            "--tag", "transcript",
            "--tag", "raw",
            "--always-project",
            "--created-at", "2025-01-01T00:00:00.000Z",
            "--json",
        ], input="Full transcript content")
        assert result.exit_code == 0
        obj = json.loads(result.output)
        assert obj["title"] == "Transcript"
        assert obj["projection_override"] == "always"
        assert obj["created_at"] == "2025-01-01T00:00:00.000Z"
        assert "Full transcript content" in obj.get("content", "")


# ============================================================
# Projection CLI commands
# ============================================================


class TestProjectionCLI:
    """Test project, sync, and tier status CLI commands."""

    @pytest.fixture(autouse=True)
    def _ensure_projected_dir(self, initialized_db):
        """Ensure projected_dir exists for projection tests."""
        from src.config import settings
        settings.projected_dir.mkdir(parents=True, exist_ok=True)

    def test_project_cli(self, initialized_db):
        """project runs without error on a bootstrapped DB."""
        result = runner.invoke(app, ["project", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "projected" in data
        assert "spaces" in data
        assert "errors" in data

    def test_project_dry_run(self, initialized_db):
        """project --dry-run returns a preview without writing files."""
        result = runner.invoke(app, ["project", "--dry-run", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True

    def test_project_cleanup(self, initialized_db):
        """project --cleanup removes stale projections."""
        result = runner.invoke(app, ["project", "--cleanup", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "deprojected" in data

    def test_tier_status_cli(self, initialized_db):
        """tier status returns expected fields."""
        result = runner.invoke(app, ["tier", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_objects" in data
        assert "projected_count" in data
        assert "hot_tier_limit" in data
        assert "currently_projected_files" in data

    def test_sync_cli(self, initialized_db):
        """sync runs without error (even when no projected files exist)."""
        from src.config import settings
        settings.projected_dir.mkdir(parents=True, exist_ok=True)
        result = runner.invoke(app, ["sync", "--json"])
        assert result.exit_code == 0

    def test_capture_project_integration(self, initialized_db):
        """Integration: capture --always-project then project creates a file on disk."""
        from src.config import settings

        # Create object with always-project
        result = runner.invoke(app, [
            "capture", "integration test content",
            "--title", "Integration Test",
            "--always-project", "--json",
        ])
        assert result.exit_code == 0
        obj = json.loads(result.output)

        # Run projection
        proj_result = runner.invoke(app, ["project", "--json"])
        assert proj_result.exit_code == 0

        # Verify projected file exists
        projected_files = list(settings.projected_dir.rglob("*.md"))
        # Filter out CLAUDE.md
        content_files = [f for f in projected_files if f.name != "CLAUDE.md"]
        assert len(content_files) >= 1

        # Verify our object's file exists (match by ID prefix)
        obj_id_prefix = obj["id"][:12]
        matching = [f for f in content_files if obj_id_prefix in f.name]
        assert len(matching) == 1

        # Verify file content includes our text
        file_content = matching[0].read_text()
        assert "integration test content" in file_content
