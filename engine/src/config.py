"""ExoBrain configuration from environment variables."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


def _get_ollama_host() -> str:
    """Determine Ollama host based on mode and environment."""
    # Explicit override takes priority
    explicit_host = os.environ.get("EXOBRAIN_OLLAMA_HOST", "").strip()
    if explicit_host:
        return explicit_host

    # Otherwise, select based on mode
    mode = os.environ.get("EXOBRAIN_OLLAMA_MODE", "native").lower()
    if mode == "docker":
        return "http://ollama:11434"
    else:  # native (default)
        return "http://host.docker.internal:11434"


class Settings(BaseSettings):
    """ExoBrain settings loaded from environment."""

    # User info
    user: str = "Unknown"
    user_email: str = ""

    # Data directory (canonical data: raw docs, overlays) - syncs via Dropbox
    data_dir: Path = Path(os.environ.get("EXOBRAIN_DATA_DIR", "/data"))

    # Cache directory (derived data: staged, graphrag, logs) - container-local
    cache_dir: Path = Path(os.environ.get("EXOBRAIN_CACHE_DIR", "/cache"))

    # API settings
    api_port: int = 8420
    api_host: str = "0.0.0.0"

    # Ollama settings
    ollama_mode: str = os.environ.get("EXOBRAIN_OLLAMA_MODE", "native")
    ollama_host: str = _get_ollama_host()
    llm_model: str = "llama3.1:8b"  # 8B recommended; use 3B only for testing
    embed_model: str = "nomic-embed-text"

    # Overlay settings
    overlay_window_days: int = 30

    # Watcher settings
    watcher_debounce_seconds: float = 2.0

    class Config:
        env_prefix = "EXOBRAIN_"
        env_file = ".env"

    # === Canonical data (Dropbox-synced) ===

    @property
    def raw_dir(self) -> Path:
        """Directory for raw documents (canonical)."""
        return self.data_dir / "raw"

    @property
    def overlay_dir(self) -> Path:
        """Directory for overlay annotations (canonical)."""
        return self.data_dir / "overlay" / "annotations"

    # === Derived data (container-local) ===

    @property
    def staged_dir(self) -> Path:
        """Directory for staged documents (derived, regenerable)."""
        return self.cache_dir / "staged"

    @property
    def graphrag_dir(self) -> Path:
        """Directory for GraphRAG artifacts (derived, regenerable)."""
        return self.cache_dir / "graphrag"

    @property
    def logs_dir(self) -> Path:
        """Directory for logs (ephemeral)."""
        return self.cache_dir / "logs"

    def ensure_dirs(self) -> None:
        """Create all required directories if they don't exist."""
        # Canonical directories
        for d in [self.raw_dir, self.overlay_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Cache directories
        for d in [
            self.staged_dir,
            self.graphrag_dir / "output",
            self.graphrag_dir / "cache",
            self.logs_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
