"""SQLite connection management, WAL mode, and migration runner."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.config import settings


def _split_sql(sql_block: str) -> list[str]:
    """Split a SQL block into individual statements, respecting BEGIN...END blocks.

    Handles CREATE TRIGGER statements that contain semicolons within their
    BEGIN...END bodies. A naive split on ';' would break these.
    """
    statements = []
    current = []
    in_block = False

    for line in sql_block.splitlines():
        stripped = line.strip()

        # Skip blank lines and comment-only lines
        if not stripped or stripped.startswith("--"):
            # Still accumulate comments inside a block for completeness
            if in_block:
                current.append(line)
            continue

        current.append(line)

        # Detect BEGIN (e.g., in CREATE TRIGGER)
        upper = stripped.upper()
        if upper.endswith("BEGIN") or upper == "BEGIN":
            in_block = True
            continue

        # Detect END; which closes a BEGIN block
        if in_block and (upper == "END;" or upper == "END"):
            in_block = False
            stmt = "\n".join(current).strip().rstrip(";")
            if stmt:
                statements.append(stmt)
            current = []
            continue

        # Outside a block, semicolons terminate statements
        if not in_block and stripped.endswith(";"):
            stmt = "\n".join(current).strip().rstrip(";")
            if stmt:
                statements.append(stmt)
            current = []

    # Handle any trailing statement without semicolon
    remaining = "\n".join(current).strip().rstrip(";")
    if remaining:
        # Filter out comment-only remnants
        lines = [l for l in remaining.splitlines() if l.strip() and not l.strip().startswith("--")]
        if lines:
            statements.append(remaining)

    return statements


def get_db_path() -> Path:
    """Return the path to the SQLite database file."""
    return settings.db_path


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Create a SQLite connection with WAL mode and foreign keys enabled.

    Args:
        db_path: Optional override for database path. Uses default if None.

    Returns:
        Configured sqlite3.Connection with row_factory set to sqlite3.Row.
    """
    path = db_path or get_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def run_migrations(conn: sqlite3.Connection) -> list[int]:
    """Apply all unapplied migrations in order.

    Returns:
        List of migration version numbers that were applied.
    """
    from src.core.schema import MIGRATIONS

    # Ensure schema_version table exists
    conn.execute(
        """CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            description TEXT
        )"""
    )
    conn.commit()

    # Get already-applied versions
    applied = {
        row["version"]
        for row in conn.execute("SELECT version FROM schema_version").fetchall()
    }

    # Apply pending migrations in order.
    # NOTE: We use execute() per statement rather than executescript() because
    # executescript() implicitly commits pending transactions and disables
    # PRAGMA foreign_keys for the duration. This preserves FK enforcement
    # and keeps the migration + version record in the same transaction.
    newly_applied = []
    for version, description, sql_block in MIGRATIONS:
        if version in applied:
            continue
        # Split the SQL block into individual statements and execute each one.
        # Temporarily disable FKs for DDL (CREATE TABLE with self-referential FKs).
        conn.execute("PRAGMA foreign_keys=OFF")
        try:
            for statement in _split_sql(sql_block):
                conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (version, description),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.execute("PRAGMA foreign_keys=ON")
        newly_applied.append(version)

    return newly_applied


def init_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Initialize the database: create file, run migrations, return connection.

    Args:
        db_path: Optional override for database path.

    Returns:
        Fully initialized sqlite3.Connection.
    """
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(path)
    run_migrations(conn)
    return conn


def check_integrity(conn: sqlite3.Connection) -> dict:
    """Run integrity and foreign key checks.

    Returns:
        Dict with 'integrity' and 'foreign_keys' results.
    """
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    return {
        "integrity": integrity,
        "foreign_key_violations": len(fk_violations),
        "ok": integrity == "ok" and len(fk_violations) == 0,
    }
