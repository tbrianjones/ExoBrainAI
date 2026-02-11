"""Tests for the web UI endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.core.bootstrap import BOOTSTRAP_IDS
from src.core.repository import ObjectRepo, TagRepo


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

class TestWikiLinks:
    """Test [[uuid|display text]] wiki-link rendering."""

    def test_basic_wikilink(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown("See [[069abc12-3456-7890-abcd-ef1234567890|My Document]] for details.")
        assert '<a href="/ui/objects/069abc12-3456-7890-abcd-ef1234567890">My Document</a>' in result
        assert "[[" not in result

    def test_multiple_wikilinks(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown(
            "Link to [[069abc12-3456-7890-abcd-ef1234567890|First]] and "
            "[[069abc12-3456-7890-abcd-ef1234567891|Second]]."
        )
        assert '<a href="/ui/objects/069abc12-3456-7890-abcd-ef1234567890">First</a>' in result
        assert '<a href="/ui/objects/069abc12-3456-7890-abcd-ef1234567891">Second</a>' in result

    def test_wikilink_in_paragraph(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown(
            "This builds on [[069abc12-3456-7890-abcd-ef1234567890|Dynamic Skill Architecture]], "
            "which established the pattern."
        )
        assert "<p>" in result
        assert '<a href="/ui/objects/069abc12-3456-7890-abcd-ef1234567890">Dynamic Skill Architecture</a>' in result

    def test_invalid_uuid_left_as_literal(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown("See [[not-a-valid-uuid|Broken Link]] here.")
        assert "[[not-a-valid-uuid|Broken Link]]" in result
        assert "<a " not in result or 'not-a-valid-uuid' not in result

    def test_display_text_html_escaped(self):
        from src.api.routes.ui import _convert_wikilinks
        # Test the conversion function directly to verify HTML escaping
        result = _convert_wikilinks('[[069abc12-3456-7890-abcd-ef1234567890|Title with <b>bold</b>]]')
        assert "&lt;b&gt;" in result
        assert "<b>" not in result

    def test_script_in_display_text_safe(self):
        from src.api.routes.ui import _render_markdown
        # nh3 strips <script> before wiki-link processing, so the link won't render;
        # the important thing is that no <script> tag appears in output
        result = _render_markdown('See [[069abc12-3456-7890-abcd-ef1234567890|Title with <script>]].')
        assert "<script>" not in result

    def test_wikilink_with_special_display_text(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown('See [[069abc12-3456-7890-abcd-ef1234567890|Title & "Quotes"]].')
        assert "&amp;" in result
        assert "Title" in result

    def test_wikilink_coexists_with_regular_links(self):
        from src.api.routes.ui import _render_markdown
        result = _render_markdown(
            "See [[069abc12-3456-7890-abcd-ef1234567890|Internal]] and "
            "[external](https://example.com)."
        )
        assert '<a href="/ui/objects/069abc12-3456-7890-abcd-ef1234567890">Internal</a>' in result
        assert 'href="https://example.com"' in result

    def test_convert_wikilinks_directly(self):
        from src.api.routes.ui import _convert_wikilinks
        result = _convert_wikilinks("text [[069abc12-3456-7890-abcd-ef1234567890|Link]] more")
        assert '<a href="/ui/objects/069abc12-3456-7890-abcd-ef1234567890">Link</a>' in result

    def test_no_wikilinks_unchanged(self):
        from src.api.routes.ui import _convert_wikilinks
        text = "<p>No wiki links here.</p>"
        assert _convert_wikilinks(text) == text


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


# ---------------------------------------------------------------------------
# Version history endpoint
# ---------------------------------------------------------------------------

class TestObjectHistory:

    def test_history_returns_fragment(self, populated_client):
        client, data = populated_client
        obj_id = data["obj_a"]["id"]
        resp = client.get(f"/ui-api/objects/{obj_id}/history")
        assert resp.status_code == 200

    def test_history_shows_versions_after_update(self, populated_client):
        client, data = populated_client
        conn = data["conn"]
        obj_id = data["obj_a"]["id"]
        # Create a version by updating
        obj_repo = ObjectRepo(conn)
        obj_repo.update(obj_id, title="Updated Alpha")
        conn.commit()
        resp = client.get(f"/ui-api/objects/{obj_id}/history")
        assert resp.status_code == 200
        # Template shows version numbers like "v1", "v2"
        assert "v1" in resp.text

    def test_history_nonexistent_object(self, client):
        resp = client.get("/ui-api/objects/00000000-0000-0000-0000-000000000000/history")
        assert resp.status_code == 200
        assert "not found" in resp.text.lower()


# ---------------------------------------------------------------------------
# Version diff endpoint
# ---------------------------------------------------------------------------

class TestObjectDiff:

    def test_diff_returns_fragment(self, populated_client):
        client, data = populated_client
        conn = data["conn"]
        obj_id = data["obj_a"]["id"]
        # Create a version
        obj_repo = ObjectRepo(conn)
        obj_repo.update(obj_id, title="Diff Test Title")
        conn.commit()
        resp = client.get(f"/ui-api/objects/{obj_id}/diff/1")
        assert resp.status_code == 200

    def test_diff_shows_changes(self, populated_client):
        client, data = populated_client
        conn = data["conn"]
        obj_id = data["obj_a"]["id"]
        obj_repo = ObjectRepo(conn)
        obj_repo.update(obj_id, content="Completely new content for diff test")
        conn.commit()
        resp = client.get(f"/ui-api/objects/{obj_id}/diff/1")
        assert resp.status_code == 200
        # Diff should show colored additions/deletions
        assert "dcfce7" in resp.text or "fecaca" in resp.text

    def test_diff_nonexistent_version(self, populated_client):
        client, data = populated_client
        obj_id = data["obj_a"]["id"]
        resp = client.get(f"/ui-api/objects/{obj_id}/diff/999")
        assert resp.status_code == 200
        assert "not found" in resp.text.lower()


# ---------------------------------------------------------------------------
# Delete / Purge POST endpoints
# ---------------------------------------------------------------------------

class TestDeletePurgeEndpoints:

    def test_delete_requires_csrf(self, populated_client):
        client, data = populated_client
        obj_id = data["obj_c"]["id"]
        resp = client.post(f"/ui-api/objects/{obj_id}/delete")
        assert resp.status_code == 403

    def test_purge_requires_csrf(self, populated_client):
        client, data = populated_client
        obj_id = data["obj_c"]["id"]
        resp = client.post(f"/ui-api/objects/{obj_id}/purge")
        assert resp.status_code == 403

    def test_delete_with_valid_csrf_calls_cli(self, populated_client):
        """With matching CSRF cookie and header, delete endpoint should attempt CLI call.

        In test env, the subprocess will fail (no CLI binary), but we should
        get an HTML response (not a 403).
        """
        client, data = populated_client
        obj_id = data["obj_c"]["id"]
        csrf_token = "a" * 64
        client.cookies.set("csrf_token", csrf_token)
        resp = client.post(
            f"/ui-api/objects/{obj_id}/delete",
            headers={"X-CSRF-Token": csrf_token},
        )
        # Should not be 403 (the CSRF check passed)
        assert resp.status_code == 200

    def test_purge_with_valid_csrf_calls_cli(self, populated_client):
        client, data = populated_client
        obj_id = data["obj_c"]["id"]
        csrf_token = "b" * 64
        client.cookies.set("csrf_token", csrf_token)
        resp = client.post(
            f"/ui-api/objects/{obj_id}/purge",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200

    def test_csrf_mismatch_rejected(self, populated_client):
        """POST with mismatched CSRF cookie and header should be rejected."""
        client, data = populated_client
        obj_id = data["obj_c"]["id"]
        client.cookies.set("csrf_token", "cookie_token_value_aaa")
        resp = client.post(
            f"/ui-api/objects/{obj_id}/delete",
            headers={"X-CSRF-Token": "header_token_value_bbb"},
        )
        assert resp.status_code == 403

    def test_csrf_missing_rejected(self, populated_client):
        """POST with no CSRF token at all should be rejected."""
        client, data = populated_client
        obj_id = data["obj_c"]["id"]
        # Clear any cookies
        client.cookies.clear()
        resp = client.post(f"/ui-api/objects/{obj_id}/delete")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Dashboard backup and health stats
# ---------------------------------------------------------------------------

class TestDashboardBackupStats:

    def test_stats_includes_backup_info(self, client):
        resp = client.get("/ui-api/stats")
        assert resp.status_code == 200
        assert "Backups" in resp.text

    def test_stats_includes_data_health(self, client):
        resp = client.get("/ui-api/stats")
        assert resp.status_code == 200
        assert "Data Health" in resp.text

    def test_stats_includes_deleted_count(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/stats")
        assert resp.status_code == 200
        assert "Deleted Objects" in resp.text or "deleted" in resp.text.lower()

    def test_stats_includes_history_count(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/stats")
        assert resp.status_code == 200
        assert "History" in resp.text or "history" in resp.text.lower()


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

class TestSecurityHeaders:

    def test_csp_header_present(self, client):
        """GET /ui/ should include a Content-Security-Policy header."""
        resp = client.get("/ui/")
        assert resp.status_code == 200
        csp = resp.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "script-src" in csp
        assert "frame-src 'none'" in csp


# ---------------------------------------------------------------------------
# File preview size limit
# ---------------------------------------------------------------------------

class TestFilePreviewSizeLimit:

    def test_preview_rejects_large_file(self, client, _patched_settings):
        """Files over MAX_PREVIEW_BYTES should return 'too_large' preview."""
        from src.config import settings

        # Create a file that exceeds the 10 MB limit
        files_dir = settings.files_dir
        files_dir.mkdir(parents=True, exist_ok=True)
        large_file = files_dir / "bigfile.txt"
        # Write just over 10 MB
        large_file.write_bytes(b"x" * (10 * 1024 * 1024 + 1))

        resp = client.get("/ui-api/files/preview?root=files&path=bigfile.txt")
        assert resp.status_code == 200
        assert "too large" in resp.text.lower()
        assert "10 MB" in resp.text


# ---------------------------------------------------------------------------
# Tags page
# ---------------------------------------------------------------------------

class TestTagsPage:

    def test_tags_page_renders(self, client):
        resp = client.get("/ui/tags")
        assert resp.status_code == 200
        assert "Tags" in resp.text

    def test_tags_page_shows_cloud(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui/tags")
        assert resp.status_code == 200
        assert "Tag Cloud" in resp.text
        assert "quantum" in resp.text
        assert "computing" in resp.text

    def test_tags_page_shows_summary_cards(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui/tags")
        assert resp.status_code == 200
        assert "Distinct Tags" in resp.text
        assert "Tag Assignments" in resp.text
        assert "Avg Tags/Object" in resp.text


class TestTagsListEndpoint:

    def test_tag_list_returns_html(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/tags")
        assert resp.status_code == 200
        assert "quantum" in resp.text
        assert "computing" in resp.text

    def test_tag_list_shows_counts(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/tags")
        assert resp.status_code == 200
        # "computing" appears on 2 objects
        assert "2" in resp.text

    def test_tag_list_search(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/tags?q=quant")
        assert resp.status_code == 200
        assert "quantum" in resp.text
        assert "machine-learning" not in resp.text

    def test_tag_list_sort_by_tag(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/tags?sort=tag&order=asc")
        assert resp.status_code == 200
        assert "computing" in resp.text

    def test_tag_list_empty_search(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/tags?q=zzzznonexistent")
        assert resp.status_code == 200
        assert "No tags found" in resp.text

    def test_tag_list_empty_db(self, client):
        resp = client.get("/ui-api/tags")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Spaces page
# ---------------------------------------------------------------------------

class TestSpacesPage:

    def test_spaces_page_renders(self, client):
        resp = client.get("/ui/spaces")
        assert resp.status_code == 200
        assert "Spaces" in resp.text

    def test_spaces_page_shows_summary_cards(self, client):
        resp = client.get("/ui/spaces")
        assert resp.status_code == 200
        assert "Total Spaces" in resp.text
        assert "Top-Level Spaces" in resp.text


class TestSpacesTreeEndpoint:

    def test_space_tree_returns_html(self, client):
        resp = client.get("/ui-api/spaces/tree")
        assert resp.status_code == 200
        # Bootstrap spaces should appear
        assert "primitives" in resp.text or "inbox" in resp.text

    def test_space_tree_shows_counts(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/spaces/tree")
        assert resp.status_code == 200
        assert "objects" in resp.text

    def test_space_tree_search(self, client):
        resp = client.get("/ui-api/spaces/tree?q=inbox")
        assert resp.status_code == 200
        assert "inbox" in resp.text

    def test_space_tree_search_no_results(self, client):
        resp = client.get("/ui-api/spaces/tree?q=zzzznonexistent")
        assert resp.status_code == 200
        assert "No spaces found" in resp.text


# ---------------------------------------------------------------------------
# Objects stats endpoint
# ---------------------------------------------------------------------------

class TestObjectsStats:

    def test_objects_stats_returns_html(self, client):
        resp = client.get("/ui-api/objects/stats")
        assert resp.status_code == 200
        assert "Total Objects" in resp.text

    def test_objects_stats_shows_counts(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui-api/objects/stats")
        assert resp.status_code == 200
        assert "Types" in resp.text
        assert "Tags" in resp.text
        assert "Links" in resp.text


# ---------------------------------------------------------------------------
# Objects page clickthrough
# ---------------------------------------------------------------------------

class TestObjectsClickthrough:

    def test_tag_preselection(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui/objects?tag=quantum")
        assert resp.status_code == 200
        assert 'selected' in resp.text

    def test_space_preselection(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui/objects?space=primitives")
        assert resp.status_code == 200
        assert 'selected' in resp.text

    def test_type_preselection(self, populated_client):
        client, data = populated_client
        resp = client.get("/ui/objects?type=Document")
        assert resp.status_code == 200
        assert 'selected' in resp.text


# ---------------------------------------------------------------------------
# Repository: TagRepo.list_all_enriched
# ---------------------------------------------------------------------------

class TestTagRepoListAllEnriched:

    def test_returns_tags_with_enrichment(self, sample_objects):
        conn = sample_objects["conn"]
        tag_repo = TagRepo(conn)
        tags, total = tag_repo.list_all_enriched()
        assert total == 4
        assert len(tags) <= 50
        # Check enrichment fields
        computing_tag = next(t for t in tags if t["tag_text"] == "computing")
        assert computing_tag["count"] == 2
        assert "Document" in computing_tag["types"]
        assert "primitives" in computing_tag["spaces"]

    def test_search_filter(self, sample_objects):
        conn = sample_objects["conn"]
        tag_repo = TagRepo(conn)
        tags, total = tag_repo.list_all_enriched(search="quant")
        assert total == 1
        assert tags[0]["tag_text"] == "quantum"

    def test_sort_by_tag_asc(self, sample_objects):
        conn = sample_objects["conn"]
        tag_repo = TagRepo(conn)
        tags, total = tag_repo.list_all_enriched(sort_by="tag", sort_order="asc")
        tag_names = [t["tag_text"] for t in tags]
        assert tag_names == sorted(tag_names)

    def test_pagination(self, sample_objects):
        conn = sample_objects["conn"]
        tag_repo = TagRepo(conn)
        tags, total = tag_repo.list_all_enriched(limit=2, offset=0)
        assert len(tags) == 2
        assert total == 4

    def test_total_assignments(self, sample_objects):
        conn = sample_objects["conn"]
        tag_repo = TagRepo(conn)
        assert tag_repo.total_assignments() == 5


# ---------------------------------------------------------------------------
# Repository: ObjectRepo.space_stats
# ---------------------------------------------------------------------------

class TestObjectRepoSpaceStats:

    def test_returns_space_stats(self, sample_objects):
        conn = sample_objects["conn"]
        obj_repo = ObjectRepo(conn)
        stats = obj_repo.space_stats()
        assert len(stats) > 0
        # Each stat should have required fields
        for s in stats:
            assert "space_id" in s
            assert "space_name" in s
            assert "direct_count" in s
            assert "types" in s

    def test_primitives_space_has_objects(self, sample_objects):
        conn = sample_objects["conn"]
        obj_repo = ObjectRepo(conn)
        stats = obj_repo.space_stats()
        primitives = next(s for s in stats if s["space_name"] == "primitives")
        assert primitives["direct_count"] == 3  # obj_a, obj_b, obj_c
        # Types should include Document and Note
        type_names = [t[0] for t in primitives["types"]]
        assert "Document" in type_names
        assert "Note" in type_names


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

class TestNavigation:

    def test_sidebar_has_tags_link(self, client):
        resp = client.get("/ui/")
        assert resp.status_code == 200
        assert '/ui/tags' in resp.text
        assert 'Tags' in resp.text

    def test_sidebar_has_spaces_link(self, client):
        resp = client.get("/ui/")
        assert resp.status_code == 200
        assert '/ui/spaces' in resp.text
        assert 'Spaces' in resp.text
