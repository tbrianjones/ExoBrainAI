"""Health and status endpoints."""

from fastapi import APIRouter

from src import __version__
from src.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": __version__}


@router.get("/status")
async def status():
    """Get ExoBrain status."""
    from src.core.db import check_integrity, get_connection, get_db_path
    from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo

    result = {
        "version": __version__,
        "data_dir": str(settings.data_dir),
    }

    # SQLite v2 data
    db_path = get_db_path()
    if db_path.exists():
        conn = get_connection(db_path)
        obj_repo = ObjectRepo(conn)
        tag_repo = TagRepo(conn)
        link_repo = LinkRepo(conn)
        file_repo = FileRepo(conn)
        integrity = check_integrity(conn)

        result["db"] = {
            "path": str(db_path),
            "size_bytes": db_path.stat().st_size,
            "objects": obj_repo.count(),
            "type_counts": obj_repo.count_by_type(),
            "tags": tag_repo.count(),
            "links": link_repo.count(),
            "files": file_repo.count(),
            "integrity": "ok" if integrity["ok"] else "failed",
        }
        conn.close()

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
