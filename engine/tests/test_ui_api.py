"""Tests for the web UI endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.core.bootstrap import BOOTSTRAP_IDS, bootstrap
from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo


@pytest.fixture()
def client(bootstrapped_db, _patched_settings):
    """Create a test client with the app configured for testing."""
    from src.api.main import app
    return TestClient(app)


@pytest.fixture()
def populated_client(sample_objects, _patched_settings):
    """Create a test client with sample objects in the DB."""
    from src.api.main import app
    return TestClient(app), sample_objects


# ---------------------------------------------------------------------------
# Full-page routes (smoke tests)
# ---------------------------------------------------------------------------

class TestUIPages:
    """Test that full-page UI routes return 200."""

    def test_dashboard(self, client):
        resp = client.get("/ui/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text

    def test_objects_browse(self, client):
        resp = client.get("/ui/objects")
        assert resp.status_code == 200
        assert "Objects" in resp.text

    def test_files_explorer(self, client):
        resp = client.get("/ui/files")
        assert resp.status_code == 200
        assert "File Explorer" in resp.text

    def test_projection(self, client):
        resp = client.get("/ui/projection")
        assert resp.status_code == 200
        assert "Projection" in resp.text

    def test_console(self, client):
        resp = client.get("/ui/console")
        assert resp.status_code == 200
        assert "Console" in resp.text


# ---------------------------------------------------------------------------
# Dashboard stats endpoint
# ---------------------------------------------------------------------------

class TestDashboardStats:

    def test_stats_returns_html(self, client):
        resp = client.get("/ui-api/stats")
        assert resp.status_code == 200
        assert "Total Objects" in resp.text

    def test_stats_shows_type_counts(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/stats")
        assert resp.status_code == 200
        assert "Document" in resp.text


# ---------------------------------------------------------------------------
# Object listing endpoint
# ---------------------------------------------------------------------------

class TestObjectListing:

    def test_list_returns_objects(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/objects")
        assert resp.status_code == 200
        assert "Alpha Document" in resp.text
        assert "Beta Document" in resp.text
        assert "Gamma Note" in resp.text

    def test_filter_by_type(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/objects?type=Note")
        assert resp.status_code == 200
        assert "Gamma Note" in resp.text
        # Documents should not appear when filtering by Note
        assert "Alpha Document" not in resp.text

    def test_search(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/objects?q=quantum")
        assert resp.status_code == 200
        assert "Alpha Document" in resp.text

    def test_pagination(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/objects?limit=1&offset=0")
        assert resp.status_code == 200
        # Should show pagination controls
        assert "Next" in resp.text

    def test_empty_results(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/objects?q=zzzznonexistent")
        assert resp.status_code == 200
        assert "No objects found" in resp.text


# ---------------------------------------------------------------------------
# Object detail page
# ---------------------------------------------------------------------------

class TestObjectDetail:

    def test_detail_page(self, populated_client):
        client, data = populated_client
        obj_id = data["obj_a"]["id"]
        resp = client.get(f"/ui/objects/{obj_id}")
        assert resp.status_code == 200
        assert "Alpha Document" in resp.text
        assert "quantum" in resp.text.lower()

    def test_detail_shows_tags(self, populated_client):
        client, data = populated_client
        obj_id = data["obj_a"]["id"]
        resp = client.get(f"/ui/objects/{obj_id}")
        assert "quantum" in resp.text
        assert "computing" in resp.text

    def test_detail_shows_links(self, populated_client):
        client, data = populated_client
        obj_id = data["obj_a"]["id"]
        resp = client.get(f"/ui/objects/{obj_id}")
        assert "related-to" in resp.text

    def test_detail_renders_markdown(self, populated_client):
        client, data = populated_client
        obj_id = data["obj_a"]["id"]
        resp = client.get(f"/ui/objects/{obj_id}")
        # Content should be rendered (not raw markdown)
        assert "Quantum computing" in resp.text

    def test_detail_not_found(self, client):
        resp = client.get("/ui/objects/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_detail_prefix_match(self, populated_client):
        client, data = populated_client
        obj_id = data["obj_a"]["id"]
        # Use enough characters for a unique prefix match
        prefix = obj_id[:20]
        resp = client.get(f"/ui/objects/{prefix}")
        assert resp.status_code == 200
        assert "Alpha Document" in resp.text


# ---------------------------------------------------------------------------
# File tree endpoint
# ---------------------------------------------------------------------------

class TestFileTree:

    def test_files_tree(self, client, _patched_settings):
        """File tree should return something even if directory is empty."""
        resp = client.get("/ui-api/files/tree?root=files")
        assert resp.status_code == 200

    def test_invalid_root(self, client):
        """Should reject unknown root paths."""
        resp = client.get("/ui-api/files/tree?root=../../etc")
        assert resp.status_code == 200
        assert "not found" in resp.text.lower()

    def test_path_traversal(self, client):
        """Should reject path traversal attempts."""
        resp = client.get("/ui-api/files/tree?root=files&path=../../etc")
        assert resp.status_code == 200
        assert "not found" in resp.text.lower()


# ---------------------------------------------------------------------------
# File preview endpoint
# ---------------------------------------------------------------------------

class TestFilePreview:

    def test_preview_nonexistent(self, client):
        resp = client.get("/ui-api/files/preview?root=files&path=nonexistent.md")
        assert resp.status_code == 200
        assert "not found" in resp.text.lower()

    def test_preview_path_traversal(self, client):
        resp = client.get("/ui-api/files/preview?root=files&path=../../etc/passwd")
        assert resp.status_code == 200
        assert "not found" in resp.text.lower()


# ---------------------------------------------------------------------------
# Projection status endpoint
# ---------------------------------------------------------------------------

class TestProjectionStatus:

    def test_projection_fragment(self, client):
        resp = client.get("/ui-api/projection/status")
        assert resp.status_code == 200
        assert "Eligible Objects" in resp.text


# ---------------------------------------------------------------------------
# CLI console endpoint
# ---------------------------------------------------------------------------

class TestCLIConsole:

    def test_empty_command(self, client):
        resp = client.get("/ui-api/cli/run?cmd=")
        assert resp.status_code == 200
        assert resp.text == ""

    def test_disallowed_command(self, client):
        resp = client.get("/ui-api/cli/run?cmd=capture+test")
        assert resp.status_code == 200
        assert "not allowed" in resp.text.lower()

    def test_disallowed_delete(self, client):
        resp = client.get("/ui-api/cli/run?cmd=delete+someid+--yes")
        assert resp.status_code == 200
        assert "not allowed" in resp.text.lower()

    def test_disallowed_update(self, client):
        resp = client.get("/ui-api/cli/run?cmd=update+someid+--title+hacked")
        assert resp.status_code == 200
        assert "not allowed" in resp.text.lower()

    def test_allowed_status(self, client):
        """status command should be allowed (may fail inside test env but should not be rejected)."""
        resp = client.get("/ui-api/cli/run?cmd=status")
        assert resp.status_code == 200
        # Should not contain "not allowed"
        assert "not allowed" not in resp.text.lower()

    def test_allowed_search(self, client):
        """search command with args should be allowed."""
        resp = client.get("/ui-api/cli/run?cmd=search+quantum")
        assert resp.status_code == 200
        assert "not allowed" not in resp.text.lower()

    def test_allowed_get(self, client):
        """get command with args should be allowed."""
        resp = client.get("/ui-api/cli/run?cmd=get+00000000")
        assert resp.status_code == 200
        assert "not allowed" not in resp.text.lower()

    def test_allowed_list(self, client):
        """list command should be allowed."""
        resp = client.get("/ui-api/cli/run?cmd=list")
        assert resp.status_code == 200
        assert "not allowed" not in resp.text.lower()

    def test_allowed_tier_status(self, client):
        """tier status command should be allowed."""
        resp = client.get("/ui-api/cli/run?cmd=tier+status")
        assert resp.status_code == 200
        assert "not allowed" not in resp.text.lower()
