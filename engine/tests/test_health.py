"""Tests for the health endpoint."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.backup import BackupInfo


@pytest.fixture()
def client(bootstrapped_db, _patched_settings):
    """Create a test client with the app configured for testing."""
    from src.api.main import app
    return TestClient(app)


class TestHealthEndpoint:
    """Test /health endpoint backup information."""

    def test_health_includes_backup_info(self, client):
        """Health response should include a backup section."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "backup" in data
        assert "last_backup_at" in data["backup"]
        assert "backup_age_seconds" in data["backup"]
        assert "backup_healthy" in data["backup"]

    def test_health_no_backups_is_degraded(self, client):
        """When no backups exist, status should be degraded."""
        with patch("src.api.routes.health.list_backups", return_value=[]):
            resp = client.get("/health")
            data = resp.json()
            assert data["status"] == "degraded"
            assert data["backup"]["last_backup_at"] is None
            assert data["backup"]["backup_age_seconds"] is None
            assert data["backup"]["backup_healthy"] is False

    def test_health_recent_backup_is_ok(self, client):
        """When a recent backup exists, status should be ok and backup_healthy True."""
        recent = BackupInfo(
            path=_fake_path("exobrain-20260210-1200.db.gz"),
            size_bytes=1000,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        with patch("src.api.routes.health.list_backups", return_value=[recent]):
            resp = client.get("/health")
            data = resp.json()
            assert data["status"] == "ok"
            assert data["backup"]["backup_healthy"] is True
            assert data["backup"]["last_backup_at"] is not None
            assert data["backup"]["backup_age_seconds"] is not None
            assert data["backup"]["backup_age_seconds"] < 3600

    def test_health_stale_backup_is_degraded(self, client):
        """When the last backup is older than 2x interval, status should be degraded."""
        from src.config import settings

        # Create a backup that is 3x the interval age (well past the 2x threshold)
        stale_age = timedelta(minutes=settings.backup_interval_minutes * 3)
        stale = BackupInfo(
            path=_fake_path("exobrain-20260101-0000.db.gz"),
            size_bytes=500,
            created_at=datetime.now(timezone.utc) - stale_age,
        )
        with patch("src.api.routes.health.list_backups", return_value=[stale]):
            resp = client.get("/health")
            data = resp.json()
            assert data["status"] == "degraded"
            assert data["backup"]["backup_healthy"] is False
            assert data["backup"]["backup_age_seconds"] > 0


def _fake_path(name: str):
    """Return a Path-like for test BackupInfo objects."""
    from pathlib import Path
    return Path("/tmp") / name
