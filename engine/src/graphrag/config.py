"""GraphRAG configuration for local Ollama models."""

import os
from pathlib import Path

import yaml

from src.config import settings


def get_graphrag_settings() -> dict:
    """Generate GraphRAG settings for Ollama.

    Returns a dictionary that can be written to settings.yaml
    for GraphRAG configuration.
    """
    return {
        "llm": {
            "api_key": "NONE",
            "type": "openai_chat",
            "model": settings.llm_model,
            "api_base": f"{settings.ollama_host}/v1",
            "max_tokens": 4096,
            "request_timeout": 180.0,
        },
        "embeddings": {
            "async_mode": "threaded",
            "llm": {
                "api_key": "NONE",
                "type": "openai_embedding",
                "model": settings.embed_model,
                "api_base": f"{settings.ollama_host}/v1",
            },
        },
        "chunks": {
            "size": 300,  # Smaller chunks for local models
            "overlap": 50,
        },
        "input": {
            "type": "file",
            "file_type": "text",
            "base_dir": str(settings.staged_dir),
        },
        "storage": {
            "type": "file",
            "base_dir": str(settings.graphrag_dir / "output"),
        },
        "cache": {
            "type": "file",
            "base_dir": str(settings.graphrag_dir / "cache"),
        },
        "reporting": {
            "type": "file",
            "base_dir": str(settings.graphrag_dir / "logs"),
        },
    }


def write_graphrag_settings() -> Path:
    """Write GraphRAG settings.yaml to the graphrag directory.

    Returns:
        Path to the written settings file
    """
    settings_dict = get_graphrag_settings()
    settings_path = settings.graphrag_dir / "settings.yaml"

    settings.graphrag_dir.mkdir(parents=True, exist_ok=True)

    with open(settings_path, "w", encoding="utf-8") as f:
        yaml.dump(settings_dict, f, default_flow_style=False)

    return settings_path


def get_graphrag_root() -> Path:
    """Get the GraphRAG project root directory.

    Returns:
        Path to the graphrag directory
    """
    return settings.graphrag_dir
