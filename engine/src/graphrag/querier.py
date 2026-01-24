"""GraphRAG query operations."""

import logging
import subprocess
from enum import Enum

from src.config import settings
from src.graphrag.config import get_graphrag_root
from src.graphrag.indexer import ensure_graphrag_initialized, get_index_status

logger = logging.getLogger(__name__)


class QueryMode(str, Enum):
    """Query mode for GraphRAG."""

    GLOBAL = "global"  # Theme-level, community summaries
    LOCAL = "local"  # Entity neighborhood, specific context


class QueryError(Exception):
    """Error during querying."""

    pass


def query(
    query_text: str,
    mode: QueryMode = QueryMode.GLOBAL,
    community_level: int | None = None,
) -> dict:
    """Run a GraphRAG query.

    Args:
        query_text: The query string
        mode: Query mode (global or local)
        community_level: For global queries, the community level to use

    Returns:
        Dictionary with query results

    Raises:
        QueryError: If query fails
    """
    ensure_graphrag_initialized()

    # Check if index exists
    status = get_index_status()
    if not status.get("indexed"):
        raise QueryError("No index available. Run 'exobrain index' first.")

    root = get_graphrag_root()

    logger.info(f"Running {mode.value} query: {query_text[:50]}...")

    try:
        cmd = [
            "python", "-m", "graphrag.query",
            "--root", str(root),
            "--method", mode.value,
            query_text,
        ]

        if community_level is not None and mode == QueryMode.GLOBAL:
            cmd.extend(["--community-level", str(community_level)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"GraphRAG query failed: {result.stderr}")
            raise QueryError(f"Query failed: {result.stderr}")

        response = result.stdout.strip()
        logger.info(f"Query completed, response length: {len(response)}")

        return {
            "status": "success",
            "mode": mode.value,
            "query": query_text,
            "response": response,
        }

    except subprocess.TimeoutExpired:
        raise QueryError("Query timed out after 5 minutes")
    except QueryError:
        raise
    except Exception as e:
        raise QueryError(f"Query error: {e}")


def query_global(query_text: str, community_level: int | None = None) -> dict:
    """Run a global/theme query.

    Global queries use community summaries to answer broad questions
    about themes and patterns across the corpus.

    Args:
        query_text: The query string
        community_level: Community hierarchy level (higher = broader)

    Returns:
        Query results dictionary
    """
    return query(query_text, QueryMode.GLOBAL, community_level)


def query_local(query_text: str) -> dict:
    """Run a local/neighborhood query.

    Local queries focus on specific entities and their relationships,
    retrieving relevant context from the knowledge graph.

    Args:
        query_text: The query string

    Returns:
        Query results dictionary
    """
    return query(query_text, QueryMode.LOCAL)
