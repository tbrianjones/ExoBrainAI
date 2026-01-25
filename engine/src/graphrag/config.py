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
        # Models configuration (v2 format with Ollama-specific settings)
        "models": {
            "default_chat_model": {
                "type": "chat",
                "model_provider": "openai",
                "auth_type": "api_key",
                "api_key": "ollama",
                "model": settings.llm_model,
                "api_base": f"{settings.ollama_host}/v1",
                # CRITICAL: Local models don't reliably produce valid JSON
                "model_supports_json": False,
                "concurrent_requests": 1,  # Conservative for local
                "async_mode": "threaded",
                "retry_strategy": "exponential_backoff",
                "max_retries": 2,  # Fewer retries; each retry wastes timeout budget
                "request_timeout": 1200.0,  # 20 min; community_reports needs 2-3 min each
                "max_tokens": 2048,  # Increased for community reports
                "temperature": 0.0,  # Deterministic output for extraction
            },
            "default_embedding_model": {
                "type": "embedding",
                "model_provider": "openai",
                "auth_type": "api_key",
                "api_key": "ollama",
                "model": settings.embed_model,
                "api_base": f"{settings.ollama_host}/v1",
                "concurrent_requests": 1,
                "async_mode": "threaded",
                "retry_strategy": "exponential_backoff",
                "max_retries": 2,
                "request_timeout": 180.0,  # 3 min for embedding batches
            },
        },
        # Input configuration (uses symlink: graphrag/input -> staged/)
        "input": {
            "storage": {
                "type": "file",
                "base_dir": "input",  # Relative to graphrag root; symlinked to staged/
            },
            "file_type": "text",
        },
        # Chunking: smaller chunks = better entity extraction across boundaries
        "chunks": {
            "size": 300,  # Smaller chunks prevent clustering failures
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
            # Entity types tuned for personal knowledge base
            "entity_types": ["person", "organization", "concept", "project", "technology", "idea", "book", "event"],
            "max_gleanings": 0,  # Reduce LLM calls for local models
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
            "max_length": 1500,  # Fits in 8K context window
            "max_input_length": 4000,  # Must fit in 8K context with output
        },
        "embed_graph": {
            "enabled": False,
        },
        "umap": {
            "enabled": False,
        },
        "snapshots": {
            "graphml": True,  # Enable for Gephi Lite visualization
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
