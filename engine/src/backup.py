"""Automated backup engine for ExoBrain SQLite database.

Uses sqlite3.Connection.backup() for transactionally consistent snapshots.
Backups are gzip-compressed and stored at $EXOBRAIN_DATA_DIR/backups/.
"""

from __future__ import annotations

import asyncio
import gzip
import logging
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class BackupInfo:
    """Information about a backup file."""

    path: Path
    size_bytes: int
    created_at: datetime

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "filename": self.path.name,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at.isoformat(),
        }


def _backup_dir() -> Path:
    """Return the backup directory, creating it if needed."""
    d = settings.data_dir / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_backup(
    db_path: Path | None = None,
    backup_dir: Path | None = None,
    compress: bool = True,
) -> BackupInfo:
    """Create a transactionally consistent backup of the database.

    Uses sqlite3.Connection.backup() for a hot backup that does not
    require locking the source database.

    Args:
        db_path: Path to source database. Defaults to settings.db_path.
        backup_dir: Directory to store backup. Defaults to $EXOBRAIN_DATA_DIR/backups/.
        compress: Whether to gzip-compress the backup.

    Returns:
        BackupInfo with path, size, and timestamp.
    """
    src_path = db_path or settings.db_path
    dest_dir = backup_dir or _backup_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d-%H%M")
    raw_name = f"exobrain-{timestamp}.db"
    raw_path = dest_dir / raw_name

    # Use sqlite3 backup API for a consistent snapshot
    src_conn = sqlite3.connect(str(src_path))
    dst_conn = sqlite3.connect(str(raw_path))
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    if compress:
        gz_path = raw_path.with_suffix(".db.gz")
        with open(raw_path, "rb") as f_in:
            with gzip.open(gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        raw_path.unlink()
        final_path = gz_path
    else:
        final_path = raw_path

    size = final_path.stat().st_size
    logger.info("Backup created: %s (%d bytes)", final_path.name, size)

    return BackupInfo(path=final_path, size_bytes=size, created_at=now)


def list_backups(backup_dir: Path | None = None) -> list[BackupInfo]:
    """List all backup files sorted by creation time (newest first).

    Args:
        backup_dir: Directory to scan. Defaults to $EXOBRAIN_DATA_DIR/backups/.

    Returns:
        List of BackupInfo objects.
    """
    d = backup_dir or _backup_dir()
    if not d.exists():
        return []

    backups = []
    for p in sorted(d.glob("exobrain-*.db*"), reverse=True):
        stat = p.stat()
        # Parse timestamp from filename: exobrain-YYYYMMDD-HHMM.db[.gz]
        name = p.name.replace(".db.gz", "").replace(".db", "")
        parts = name.replace("exobrain-", "")
        try:
            ts = datetime.strptime(parts, "%Y%m%d-%H%M").replace(tzinfo=timezone.utc)
        except ValueError:
            ts = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        backups.append(BackupInfo(path=p, size_bytes=stat.st_size, created_at=ts))

    return backups


def prune_backups(
    backup_dir: Path | None = None,
    retention_days: int | None = None,
) -> list[Path]:
    """Delete backups older than retention period.

    Args:
        backup_dir: Directory to prune. Defaults to $EXOBRAIN_DATA_DIR/backups/.
        retention_days: Days to keep. Defaults to settings.backup_retention_days.

    Returns:
        List of deleted file paths.
    """
    days = retention_days if retention_days is not None else settings.backup_retention_days
    d = backup_dir or _backup_dir()
    now = datetime.now(timezone.utc)
    deleted = []

    for info in list_backups(d):
        age_days = (now - info.created_at).total_seconds() / 86400
        if age_days > days:
            info.path.unlink()
            deleted.append(info.path)
            logger.info("Pruned old backup: %s (%.1f days old)", info.path.name, age_days)

    return deleted


def restore_backup(backup_path: Path, db_path: Path | None = None) -> None:
    """Restore database from a backup file.

    Args:
        backup_path: Path to backup file (.db or .db.gz).
        db_path: Target database path. Defaults to settings.db_path.

    Raises:
        FileNotFoundError: If backup_path does not exist.
        ValueError: If backup file format is unrecognized.
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    target = db_path or settings.db_path

    if str(backup_path).endswith(".db.gz"):
        with gzip.open(backup_path, "rb") as f_in:
            with open(target, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    elif str(backup_path).endswith(".db"):
        shutil.copy2(str(backup_path), str(target))
    else:
        raise ValueError(f"Unrecognized backup format: {backup_path.name}")

    logger.info("Restored database from: %s", backup_path.name)


async def backup_daemon() -> None:
    """Background task that periodically creates backups and prunes old ones.

    Runs every 15 minutes, creates a backup if more than
    EXOBRAIN_BACKUP_INTERVAL_MINUTES have elapsed since the last backup.

    Sleep/wake handling: Since this is an asyncio loop, the timer doesn't
    advance while the computer sleeps. On wake, it immediately detects
    the elapsed time and creates a backup if needed.
    """
    check_interval = 15 * 60  # 15 minutes

    while True:
        try:
            # Check time since last backup
            backups = list_backups()
            should_backup = True

            if backups:
                last = backups[0]  # newest first
                elapsed_minutes = (
                    datetime.now(timezone.utc) - last.created_at
                ).total_seconds() / 60
                if elapsed_minutes < settings.backup_interval_minutes:
                    should_backup = False

            if should_backup and settings.db_path.exists():
                create_backup()
                prune_backups()

        except Exception:
            logger.exception("Backup daemon error")

        await asyncio.sleep(check_interval)
