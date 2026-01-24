"""Health and status endpoints."""

from fastapi import APIRouter

from src import __version__
from src.config import settings
from src.graphrag import get_index_status

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": __version__}


@router.get("/status")
async def status():
    """Get ExoBrain status."""
    raw_count = len(list(settings.raw_dir.glob("*.md"))) if settings.raw_dir.exists() else 0
    staged_count = (
        len(list(settings.staged_dir.glob("*.md"))) if settings.staged_dir.exists() else 0
    )
    idx_status = get_index_status()

    return {
        "version": __version__,
        "data_dir": str(settings.data_dir),
        "ollama_host": settings.ollama_host,
        "llm_model": settings.llm_model,
        "embed_model": settings.embed_model,
        "documents": {
            "raw": raw_count,
            "staged": staged_count,
        },
        "index": idx_status,
    }
