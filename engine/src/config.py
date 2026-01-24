"""ExoBrain configuration from environment variables."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ExoBrain settings loaded from environment."""

    # Data directory (required)
    data_dir: Path = Path(os.environ.get("EXOBRAIN_DATA_DIR", "/data"))

    # API settings
    api_port: int = 8420
    api_host: str = "0.0.0.0"

    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    llm_model: str = "llama3.1:8b"
    embed_model: str = "nomic-embed-text"

    # Overlay settings
    overlay_window_days: int = 30

    # Watcher settings
    watcher_debounce_seconds: float = 2.0

    class Config:
        env_prefix = "EXOBRAIN_"
        env_file = ".env"

    @property
    def raw_dir(self) -> Path:
        """Directory for raw documents."""
        return self.data_dir / "raw"

    @property
    def overlay_dir(self) -> Path:
        """Directory for overlay annotations."""
        return self.data_dir / "overlay" / "annotations"

    @property
    def staged_dir(self) -> Path:
        """Directory for staged documents."""
        return self.data_dir / "staged"

    @property
    def graphrag_dir(self) -> Path:
        """Directory for GraphRAG artifacts."""
        return self.data_dir / "graphrag"

    @property
    def logs_dir(self) -> Path:
        """Directory for logs."""
        return self.data_dir / "logs"

    def ensure_dirs(self) -> None:
        """Create all required directories if they don't exist."""
        for d in [
            self.raw_dir,
            self.overlay_dir,
            self.staged_dir,
            self.graphrag_dir / "output",
            self.logs_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
