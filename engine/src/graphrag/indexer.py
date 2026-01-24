"""GraphRAG indexing operations."""

import asyncio
import logging
import subprocess
from pathlib import Path

from src.config import settings
from src.graphrag.config import get_graphrag_root, write_graphrag_settings

logger = logging.getLogger(__name__)


class IndexError(Exception):
    """Error during indexing."""

    pass


def ensure_graphrag_initialized() -> None:
    """Ensure GraphRAG is initialized with settings.

    Creates the settings.yaml file if it doesn't exist.
    """
    settings_path = settings.graphrag_dir / "settings.yaml"
    if not settings_path.exists():
        logger.info("Initializing GraphRAG settings...")
        write_graphrag_settings()


def run_index(incremental: bool = True) -> dict:
    """Run GraphRAG indexing.

    Args:
        incremental: If True, run incremental update; if False, full rebuild

    Returns:
        Dictionary with indexing results

    Raises:
        IndexError: If indexing fails
    """
    ensure_graphrag_initialized()
    root = get_graphrag_root()

    # Check if there are staged documents
    staged_count = len(list(settings.staged_dir.glob("*.md"))) if settings.staged_dir.exists() else 0
    if staged_count == 0:
        logger.warning("No staged documents to index")
        return {"status": "skipped", "reason": "no documents", "documents": 0}

    logger.info(f"Running {'incremental' if incremental else 'full'} index on {staged_count} documents")

    try:
        # GraphRAG CLI command (v2.x uses `graphrag index` or `graphrag update`)
        if incremental:
            cmd = ["graphrag", "update", "--root", str(root)]
        else:
            cmd = ["graphrag", "index", "--root", str(root)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
        )

        if result.returncode != 0:
            logger.error(f"GraphRAG indexing failed: {result.stderr}")
            raise IndexError(f"Indexing failed: {result.stderr}")

        logger.info("Indexing completed successfully")
        return {
            "status": "success",
            "incremental": incremental,
            "documents": staged_count,
            "output": result.stdout,
        }

    except subprocess.TimeoutExpired:
        raise IndexError("Indexing timed out after 1 hour")
    except Exception as e:
        raise IndexError(f"Indexing error: {e}")


def rebuild_index() -> dict:
    """Run a full GraphRAG rebuild.

    Clears existing index and rebuilds from scratch.

    Returns:
        Dictionary with indexing results
    """
    logger.info("Starting full index rebuild...")

    # Clear existing output
    output_dir = settings.graphrag_dir / "output"
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
        logger.info("Cleared existing index output")

    return run_index(incremental=False)


def get_index_status() -> dict:
    """Get the current index status.

    Returns:
        Dictionary with index status information
    """
    output_dir = settings.graphrag_dir / "output"

    if not output_dir.exists():
        return {
            "indexed": False,
            "output_dir": str(output_dir),
        }

    # Find the most recent output directory
    output_dirs = sorted(output_dir.iterdir()) if output_dir.is_dir() else []

    if not output_dirs:
        return {
            "indexed": False,
            "output_dir": str(output_dir),
        }

    latest = output_dirs[-1]

    # Check for key artifacts
    artifacts = {
        "entities": (latest / "create_final_entities.parquet").exists(),
        "relationships": (latest / "create_final_relationships.parquet").exists(),
        "communities": (latest / "create_final_communities.parquet").exists(),
        "documents": (latest / "create_final_documents.parquet").exists(),
    }

    return {
        "indexed": all(artifacts.values()),
        "output_dir": str(latest),
        "artifacts": artifacts,
        "timestamp": latest.name if latest.is_dir() else None,
    }
