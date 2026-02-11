"""Health and status endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

from src import __version__
from src.backup import list_backups
from src.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint.

    Returns basic health status for Docker health checks and monitoring.
    Includes backup staleness detection: if the most recent backup is older
    than 2x the configured backup interval, overall status is degraded.
    """
    from src.core.db import get_db_path

    db_exists = get_db_path().exists()
    projected_dir_exists = settings.projected_dir.exists()

    # Backup health
    now = datetime.now(timezone.utc)
    try:
        backups = list_backups()
    except Exception:
        backups = []
    if backups:
        last_backup = backups[0]  # newest first
        last_backup_at = last_backup.created_at.isoformat()
        backup_age_seconds = (now - last_backup.created_at).total_seconds()
        max_age_seconds = settings.backup_interval_minutes * 60 * 2
        backup_healthy = backup_age_seconds <= max_age_seconds
    else:
        last_backup_at = None
        backup_age_seconds = None
        backup_healthy = False

    status = "ok"
    if not db_exists:
        status = "degraded"
    elif not backup_healthy:
        status = "degraded"

    return {
        "status": status,
        "version": __version__,
        "db_exists": db_exists,
        "projected_dir_exists": projected_dir_exists,
        "backup": {
            "last_backup_at": last_backup_at,
            "backup_age_seconds": backup_age_seconds,
            "backup_healthy": backup_healthy,
        },
    }


@router.get("/status")
async def status():
    """Get comprehensive ExoBrain status."""
    from src.core.db import check_integrity, db_session, get_db_path
    from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo

    result = {
        "version": __version__,
        "data_dir": str(settings.data_dir),
    }

    # SQLite v2 data
    db_path = get_db_path()
    if db_path.exists():
        with db_session(db_path) as conn:
            obj_repo = ObjectRepo(conn)
            tag_repo = TagRepo(conn)
            link_repo = LinkRepo(conn)
            file_repo = FileRepo(conn)
            integrity = check_integrity(conn)

            result["db"] = {
                "size_bytes": db_path.stat().st_size,
                "objects": obj_repo.count(),
                "type_counts": obj_repo.count_by_type(),
                "tags": tag_repo.count(),
                "links": link_repo.count(),
                "files": file_repo.count(),
                "integrity": "ok" if integrity["ok"] else "failed",
            }

            # Projection status
            try:
                from src.core.projection import get_tier_status
                tier_status = get_tier_status(conn)
                result["projection"] = {
                    "total_objects": tier_status["total_objects"],
                    "projected_count": tier_status["projected_count"],
                    "hot_tier_limit": tier_status["hot_tier_limit"],
                    "files_on_disk": tier_status["currently_projected_files"],
                }
            except Exception:
                result["projection"] = {"status": "error"}

    # Legacy data
    raw_count = len(list(settings.raw_dir.glob("*.md"))) if settings.raw_dir.exists() else 0
    staged_count = (
        len(list(settings.staged_dir.glob("*.txt"))) if settings.staged_dir.exists() else 0
    )

    try:
        from src.graphrag import get_index_status
        idx_status = get_index_status()
    except ImportError:
        idx_status = {"status": "not_installed"}

    result["legacy"] = {
        "raw": raw_count,
        "staged": staged_count,
    }
    result["graphrag"] = idx_status

    return result
