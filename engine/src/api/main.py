"""ExoBrain HTTP API entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import __version__
from src.api.routes import admin, docs, health, query
from src.config import settings

app = FastAPI(
    title="ExoBrain API",
    description="Local-first GraphRAG memory engine",
    version=__version__,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(query.router, prefix="/query", tags=["query"])
app.include_router(docs.router, prefix="/doc", tags=["documents"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


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
