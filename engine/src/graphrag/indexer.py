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

    Creates the settings.yaml file and input symlink if they don't exist.
    """
    # Ensure directories exist
    settings.graphrag_dir.mkdir(parents=True, exist_ok=True)
    settings.staged_dir.mkdir(parents=True, exist_ok=True)

    # Create settings.yaml if needed
    settings_path = settings.graphrag_dir / "settings.yaml"
    if not settings_path.exists():
        logger.info("Initializing GraphRAG settings...")
        write_graphrag_settings()

    # Create symlink: graphrag/input -> staged/ (GraphRAG expects relative paths)
    input_link = settings.graphrag_dir / "input"
    if not input_link.exists():
        logger.info(f"Creating symlink: {input_link} -> {settings.staged_dir}")
        input_link.symlink_to(settings.staged_dir)


def run_index(incremental: bool = True, fast: bool = False) -> dict:
    """Run GraphRAG indexing.

    Args:
        incremental: If True, run incremental update; if False, full rebuild
        fast: If True, use NLP-based extraction instead of LLM (much faster)

    Returns:
        Dictionary with indexing results

    Raises:
        IndexError: If indexing fails
    """
    ensure_graphrag_initialized()
    root = get_graphrag_root()

    # Check if there are staged documents
    staged_count = len(list(settings.staged_dir.glob("*.txt"))) if settings.staged_dir.exists() else 0
    if staged_count == 0:
        logger.warning("No staged documents to index")
        return {"status": "skipped", "reason": "no documents", "documents": 0}

    method = "fast" if fast else "standard"
    logger.info(f"Running {method} {'incremental' if incremental else 'full'} index on {staged_count} documents")

    try:
        # GraphRAG CLI command (v2.x uses `graphrag index` or `graphrag update`)
        if incremental:
            cmd = ["graphrag", "update", "--root", str(root), "--method", method]
        else:
            cmd = ["graphrag", "index", "--root", str(root), "--method", method]

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

    # GraphRAG v2 puts files directly in output/ (not subdirectories)
    # Check for key artifacts
    artifacts = {
        "entities": (output_dir / "entities.parquet").exists(),
        "relationships": (output_dir / "relationships.parquet").exists(),
        "communities": (output_dir / "communities.parquet").exists(),
        "community_reports": (output_dir / "community_reports.parquet").exists(),
        "documents": (output_dir / "documents.parquet").exists(),
        "text_units": (output_dir / "text_units.parquet").exists(),
    }

    # Index is considered complete if we have community_reports (final step)
    # Without community_reports, global queries will fail
    indexed = artifacts["community_reports"]

    return {
        "indexed": indexed,
        "output_dir": str(output_dir),
        "artifacts": artifacts,
    }
