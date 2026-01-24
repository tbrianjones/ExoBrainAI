"""ExoBrain HTTP API entry point."""

import uvicorn
from fastapi import FastAPI

from src import __version__
from src.config import settings

app = FastAPI(
    title="ExoBrain API",
    description="Local-first GraphRAG memory engine",
    version=__version__,
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": __version__}


@app.get("/status")
async def status():
    """Get ExoBrain status."""
    raw_count = len(list(settings.raw_dir.glob("*.md"))) if settings.raw_dir.exists() else 0
    staged_count = (
        len(list(settings.staged_dir.glob("*.md"))) if settings.staged_dir.exists() else 0
    )

    return {
        "version": __version__,
        "data_dir": str(settings.data_dir),
        "ollama_host": settings.ollama_host,
        "llm_model": settings.llm_model,
        "embed_model": settings.embed_model,
        "raw_documents": raw_count,
        "staged_documents": staged_count,
    }


def main():
    """Run the API server."""
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
