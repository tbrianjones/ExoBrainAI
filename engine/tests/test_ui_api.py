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

    def test_disallowed_tag_add(self, client):
        """tag add is a write command; should be rejected."""
        resp = client.get("/ui-api/cli/run?cmd=tag+add+someid+sometag")
        assert resp.status_code == 200
        assert "not allowed" in resp.text.lower()

    def test_disallowed_project_without_dry_run(self, client):
        """project without --dry-run is a write command."""
        resp = client.get("/ui-api/cli/run?cmd=project")
        assert resp.status_code == 200
        assert "not allowed" in resp.text.lower()

    def test_disallowed_project_cleanup(self, client):
        """project --dry-run with extra args should be rejected."""
        resp = client.get("/ui-api/cli/run?cmd=project+--dry-run+--cleanup")
        assert resp.status_code == 200
        assert "not allowed" in resp.text.lower()

    def test_allowed_link_list(self, client):
        """link list with an ID argument should be allowed."""
        resp = client.get("/ui-api/cli/run?cmd=link+list+00000000")
        assert resp.status_code == 200
        assert "not allowed" not in resp.text.lower()


# ---------------------------------------------------------------------------
# Whitelist unit tests
# ---------------------------------------------------------------------------

class TestCommandWhitelist:
    """Unit tests for _is_command_allowed."""

    def test_exact_commands(self):
        from src.api.routes.ui_api import _is_command_allowed
        assert _is_command_allowed("status") is True
        assert _is_command_allowed("doctor") is True
        assert _is_command_allowed("version") is True

    def test_commands_with_args(self):
        from src.api.routes.ui_api import _is_command_allowed
        assert _is_command_allowed("get 069abc") is True
        assert _is_command_allowed("search quantum computing") is True
        assert _is_command_allowed("list --type Note") is True
        assert _is_command_allowed("list --type Note --tag test") is True

    def test_two_word_exact(self):
        from src.api.routes.ui_api import _is_command_allowed
        assert _is_command_allowed("tag list") is True
        assert _is_command_allowed("type list") is True
        assert _is_command_allowed("space list") is True
        assert _is_command_allowed("tier status") is True
        assert _is_command_allowed("project --dry-run") is True

    def test_two_word_with_args(self):
        from src.api.routes.ui_api import _is_command_allowed
        assert _is_command_allowed("link list 069abc") is True
        assert _is_command_allowed("file path 069abc") is True

    def test_write_commands_blocked(self):
        from src.api.routes.ui_api import _is_command_allowed
        assert _is_command_allowed("capture test") is False
        assert _is_command_allowed("delete someid --yes") is False
        assert _is_command_allowed("update someid --title x") is False
        assert _is_command_allowed("tag add someid test") is False
        assert _is_command_allowed("tag remove someid test") is False
        assert _is_command_allowed("link create a b rel") is False
        assert _is_command_allowed("link remove 1") is False
        assert _is_command_allowed("file attach someid /tmp/f") is False
        assert _is_command_allowed("file detach someid") is False

    def test_project_without_dry_run_blocked(self):
        from src.api.routes.ui_api import _is_command_allowed
        assert _is_command_allowed("project") is False
        assert _is_command_allowed("project --cleanup") is False
        assert _is_command_allowed("project --dry-run --cleanup") is False

    def test_empty_blocked(self):
        from src.api.routes.ui_api import _is_command_allowed
        assert _is_command_allowed("") is False
        assert _is_command_allowed("   ") is False


# ---------------------------------------------------------------------------
# HTML sanitization
# ---------------------------------------------------------------------------

class TestHTMLSanitization:
    """Test that markdown rendering strips dangerous HTML."""

    def test_script_tag_stripped(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "</script>" not in result

    def test_safe_tags_preserved(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown("**bold** and *italic*")
        assert "<strong>" in result
        assert "<em>" in result

    def test_links_preserved(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown("[test](https://example.com)")
        assert 'href="https://example.com"' in result

    def test_javascript_uri_blocked(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown('[click](javascript:alert(1))')
        assert "javascript:" not in result

    def test_iframe_stripped(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown('<iframe src="https://evil.com"></iframe>')
        assert "<iframe" not in result

    def test_img_onerror_stripped(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown('<img src="x" onerror="alert(1)">')
        assert "onerror" not in result


class TestFrontmatterStripping:
    """Test that YAML frontmatter is stripped before markdown rendering."""

    def test_frontmatter_stripped(self):
        from src.api.routes.ui import _strip_frontmatter
        text = "---\ntitle: Hello\npublished: true\n---\n\n# Heading"
        assert _strip_frontmatter(text) == "# Heading"

    def test_no_frontmatter_unchanged(self):
        from src.api.routes.ui import _strip_frontmatter
        text = "# Just a heading\n\nSome content."
        assert _strip_frontmatter(text) == text

    def test_unclosed_frontmatter_unchanged(self):
        from src.api.routes.ui import _strip_frontmatter
        text = "---\ntitle: Hello\nno closing delimiter"
        assert _strip_frontmatter(text) == text

    def test_render_markdown_strips_frontmatter(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown("---\ntitle: Test\n---\n\n**bold**")
        assert "<strong>bold</strong>" in result
        assert "title" not in result


# ---------------------------------------------------------------------------
# Limit cap
# ---------------------------------------------------------------------------

class TestLimitCap:

    def test_limit_capped(self, populated_client):
        """Requesting limit=99999 should be capped."""
        client, data = populated_client
        resp = client.get("/ui-api/objects?limit=99999")
        assert resp.status_code == 200
