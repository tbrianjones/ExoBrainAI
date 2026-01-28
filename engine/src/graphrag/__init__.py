"""GraphRAG integration for indexing and querying."""

from src.graphrag.config import (
    get_graphrag_root,
    get_graphrag_settings,
    write_graphrag_settings,
)
from src.graphrag.indexer import (
    IndexError,
    ensure_graphrag_initialized,
    get_index_status,
    rebuild_index,
    run_index,
)
from src.graphrag.querier import (
    QueryError,
    QueryMode,
    query,
    query_global,
    query_local,
)

try:
    from src.graphrag.adapter import stage_for_graphrag
except ImportError:
    pass

__all__ = [
    # Config
    "get_graphrag_root",
    "get_graphrag_settings",
    "write_graphrag_settings",
    # Adapter
    "stage_for_graphrag",
    # Indexer
    "IndexError",
    "ensure_graphrag_initialized",
    "get_index_status",
    "rebuild_index",
    "run_index",
    # Querier
    "QueryError",
    "QueryMode",
    "query",
    "query_global",
    "query_local",
]
