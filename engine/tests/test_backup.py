"""Tests for the backup engine."""

import gzip
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.backup import BackupInfo, create_backup, list_backups, prune_backups, restore_backup


@pytest.fixture()
def backup_env(tmp_path, _patched_settings):
    """Set up a minimal database and backup directory for testing."""
    from src.core.db import init_db
    from src.core.bootstrap import bootstrap

    db_path = _patched_settings.db_path
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    conn = init_db(db_path)
    bootstrap(conn)
    conn.close()

    return {
        "db_path": db_path,
        "backup_dir": backup_dir,
        "settings": _patched_settings,
    }


class TestCreateBackup:
    """Test backup creation."""

    def test_create_compressed_backup(self, backup_env):
        info = create_backup(
            db_path=backup_env["db_path"],
            backup_dir=backup_env["backup_dir"],
        )
        assert info.path.exists()
        assert info.path.suffix == ".gz"
        assert info.size_bytes > 0
        assert isinstance(info.created_at, datetime)

    def test_create_uncompressed_backup(self, backup_env):
        info = create_backup(
            db_path=backup_env["db_path"],
            backup_dir=backup_env["backup_dir"],
            compress=False,
        )
        assert info.path.exists()
        assert info.path.suffix == ".db"
        assert info.size_bytes > 0

    def test_backup_is_valid_sqlite(self, backup_env):
        info = create_backup(
            db_path=backup_env["db_path"],
            backup_dir=backup_env["backup_dir"],
            compress=False,
        )
        # Verify the backup is a valid SQLite database
        conn = sqlite3.connect(str(info.path))
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        assert result == "ok"

    def test_compressed_backup_is_valid(self, backup_env):
        info = create_backup(
            db_path=backup_env["db_path"],
            backup_dir=backup_env["backup_dir"],
        )
        # Decompress and verify
        decompressed_path = backup_env["backup_dir"] / "test_verify.db"
        with gzip.open(info.path, "rb") as f_in:
            with open(decompressed_path, "wb") as f_out:
                f_out.write(f_in.read())
        conn = sqlite3.connect(str(decompressed_path))
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        assert result == "ok"


class TestListBackups:
    """Test backup listing."""

    def test_list_empty_directory(self, backup_env):
        backups = list_backups(backup_env["backup_dir"])
        assert len(backups) == 0

    def test_list_after_create(self, backup_env):
        create_backup(
            db_path=backup_env["db_path"],
            backup_dir=backup_env["backup_dir"],
        )
        backups = list_backups(backup_env["backup_dir"])
        assert len(backups) == 1

    def test_list_sorted_newest_first(self, backup_env):
        # Create two backups with different names
        info1 = create_backup(
            db_path=backup_env["db_path"],
            backup_dir=backup_env["backup_dir"],
        )
        # Create a second one with a slightly different name
        (backup_env["backup_dir"] / "exobrain-29991231-2359.db.gz").write_bytes(b"\x00")
        backups = list_backups(backup_env["backup_dir"])
        assert len(backups) >= 2


class TestPruneBackups:
    """Test backup pruning."""

    def test_prune_old_backups(self, backup_env):
        # Create a fake old backup
        old_path = backup_env["backup_dir"] / "exobrain-20200101-0000.db.gz"
        old_path.write_bytes(b"\x00")

        deleted = prune_backups(backup_env["backup_dir"], retention_days=1)
        assert len(deleted) == 1
        assert not old_path.exists()

    def test_prune_keeps_recent(self, backup_env):
        info = create_backup(
            db_path=backup_env["db_path"],
            backup_dir=backup_env["backup_dir"],
        )
        deleted = prune_backups(backup_env["backup_dir"], retention_days=7)
        assert len(deleted) == 0
        assert info.path.exists()


class TestRestoreBackup:
    """Test backup restoration."""

    def test_restore_uncompressed(self, backup_env):
        info = create_backup(
            db_path=backup_env["db_path"],
            backup_dir=backup_env["backup_dir"],
            compress=False,
        )
        # Create a different target path
        target = backup_env["backup_dir"] / "restored.db"
        restore_backup(info.path, target)
        assert target.exists()

        # Verify it's a valid database
        conn = sqlite3.connect(str(target))
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        assert result == "ok"

    def test_restore_compressed(self, backup_env):
        info = create_backup(
            db_path=backup_env["db_path"],
            backup_dir=backup_env["backup_dir"],
        )
        target = backup_env["backup_dir"] / "restored.db"
        restore_backup(info.path, target)
        assert target.exists()

        conn = sqlite3.connect(str(target))
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        assert result == "ok"

    def test_restore_nonexistent_raises(self, backup_env):
        with pytest.raises(FileNotFoundError):
            restore_backup(Path("/nonexistent/backup.db.gz"))

    def test_restore_bad_format_raises(self, backup_env):
        bad_file = backup_env["backup_dir"] / "backup.txt"
        bad_file.write_text("not a backup")
        with pytest.raises(ValueError):
            restore_backup(bad_file)


class TestBackupInfo:
    """Test BackupInfo dataclass."""

    def test_to_dict(self):
        now = datetime.now(timezone.utc)
        info = BackupInfo(
            path=Path("/backups/exobrain-20260210-1200.db.gz"),
            size_bytes=1234,
            created_at=now,
        )
        d = info.to_dict()
        assert d["filename"] == "exobrain-20260210-1200.db.gz"
        assert d["size_bytes"] == 1234
        assert "path" in d
        assert "created_at" in d
