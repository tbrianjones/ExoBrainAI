"""ExoBrain HTTP API entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from src import __version__
from src.api.routes import admin, docs, health, query
from src.api.routes import ui, ui_api
from src.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown tasks including the backup daemon."""
    from src.backup import backup_daemon

    task = asyncio.create_task(backup_daemon())
    logger.info("Backup daemon started")
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Backup daemon stopped")


app = FastAPI(
    title="ExoBrain API",
    description="Local-first GraphRAG memory engine",
    version=__version__,
    lifespan=lifespan,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8420", "http://127.0.0.1:8420"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["HX-Request", "HX-Target", "HX-Trigger", "Content-Type", "X-CSRF-Token"],
)


class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-src 'none'; "
            "object-src 'none'"
        )
        return response

app.add_middleware(CSPMiddleware)

# Jinja2 templates and static files for the web UI
_templates_dir = Path(__file__).parent / "templates"
_static_dir = Path(__file__).parent / "static"

app.state.templates = Jinja2Templates(directory=str(_templates_dir))
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(query.router, prefix="/query", tags=["query"])
app.include_router(docs.router, prefix="/doc", tags=["documents"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

# Web UI routers
app.include_router(ui.router, prefix="/ui", tags=["ui"])
app.include_router(ui_api.router, prefix="/ui-api", tags=["ui-api"])


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
