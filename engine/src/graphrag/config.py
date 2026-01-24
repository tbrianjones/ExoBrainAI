"""GraphRAG configuration for local Ollama models."""

import os
from pathlib import Path

import yaml

from src.config import settings


def get_graphrag_settings() -> dict:
    """Generate GraphRAG settings for Ollama.

    Returns a dictionary that can be written to settings.yaml
    for GraphRAG v2.x configuration.
    """
    return {
        # Models configuration (v2 format)
        "models": {
            "default_chat_model": {
                "type": "chat",
                "model_provider": "openai",
                "auth_type": "api_key",
                "api_key": "NONE",
                "model": settings.llm_model,
                "api_base": f"{settings.ollama_host}/v1",
                "model_supports_json": False,  # Llama doesn't guarantee JSON
                "concurrent_requests": 1,  # Conservative for local
                "async_mode": "threaded",
                "retry_strategy": "exponential_backoff",
                "max_retries": 3,
            },
            "default_embedding_model": {
                "type": "embedding",
                "model_provider": "openai",
                "auth_type": "api_key",
                "api_key": "NONE",
                "model": settings.embed_model,
                "api_base": f"{settings.ollama_host}/v1",
                "concurrent_requests": 1,
                "async_mode": "threaded",
                "retry_strategy": "exponential_backoff",
                "max_retries": 3,
            },
        },
        # Input configuration
        "input": {
            "storage": {
                "type": "file",
                "base_dir": str(settings.staged_dir),
            },
            "file_type": "text",
        },
        # Chunking
        "chunks": {
            "size": 300,  # Smaller chunks for local models
            "overlap": 50,
            "group_by_columns": ["id"],
        },
        # Output/storage
        "output": {
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
        # Vector store
        "vector_store": {
            "default_vector_store": {
                "type": "lancedb",
                "db_uri": str(settings.graphrag_dir / "output" / "lancedb"),
                "container_name": "default",
            },
        },
        # Workflow settings
        "embed_text": {
            "model_id": "default_embedding_model",
            "vector_store_id": "default_vector_store",
        },
        "extract_graph": {
            "model_id": "default_chat_model",
            "entity_types": ["person", "organization", "concept", "technology", "event"],
            "max_gleanings": 1,
        },
        "summarize_descriptions": {
            "model_id": "default_chat_model",
            "max_length": 500,
        },
        "cluster_graph": {
            "max_cluster_size": 10,
        },
        "extract_claims": {
            "enabled": False,
        },
        "community_reports": {
            "model_id": "default_chat_model",
            "max_length": 2000,
            "max_input_length": 8000,
        },
        "embed_graph": {
            "enabled": False,
        },
        "umap": {
            "enabled": False,
        },
        "snapshots": {
            "graphml": False,
            "embeddings": False,
        },
        # Query settings
        "local_search": {
            "chat_model_id": "default_chat_model",
            "embedding_model_id": "default_embedding_model",
        },
        "global_search": {
            "chat_model_id": "default_chat_model",
        },
        "drift_search": {
            "chat_model_id": "default_chat_model",
            "embedding_model_id": "default_embedding_model",
        },
        "basic_search": {
            "chat_model_id": "default_chat_model",
            "embedding_model_id": "default_embedding_model",
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
