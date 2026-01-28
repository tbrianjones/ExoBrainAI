"""Core memory engine components.

v2: SQLite-backed object system (db, schema, bootstrap, repository)
v1 (legacy): File-based raw/overlay/staging system
"""

# v2 core
from src.core.bootstrap import BOOTSTRAP_IDS, bootstrap, get_space_id, get_type_id
from src.core.db import check_integrity, get_connection, get_db_path, init_db, run_migrations
from src.core.models import (
    ExoFile,
    ExoLink,
    ExoObject,
    ExoTag,
    ObjectDetail,
    ObjectSummary,
    SearchResult,
    StatusInfo,
    generate_id,
)
from src.core.repository import FileRepo, LinkRepo, ObjectRepo, TagRepo

# v1 legacy (kept for migration and backward compatibility)
from src.core.models import (
    AggregatedOverlay,
    EntityItem,
    LinkItem,
    OverlayRecord,
    RawDocument,
    TagItem,
)
from src.core.overlay import (
    aggregate_overlays,
    append_overlay,
    get_all_doc_overlays,
    get_overlays_for_doc,
)
from src.core.raw import (
    delete_raw_doc,
    generate_doc_id,
    get_raw_doc,
    list_raw_docs,
    raw_doc_exists,
    write_raw_doc,
)
from src.core.stager import (
    clean_staged,
    delete_staged_doc,
    get_staged_doc,
    list_staged_docs,
    stage_all,
    stage_doc,
)

__all__ = [
    # v2 core
    "BOOTSTRAP_IDS",
    "ExoFile",
    "ExoLink",
    "ExoObject",
    "ExoTag",
    "FileRepo",
    "LinkRepo",
    "ObjectDetail",
    "ObjectRepo",
    "ObjectSummary",
    "SearchResult",
    "StatusInfo",
    "TagRepo",
    "bootstrap",
    "check_integrity",
    "generate_id",
    "get_connection",
    "get_db_path",
    "get_space_id",
    "get_type_id",
    "init_db",
    "run_migrations",
    # v1 legacy
    "AggregatedOverlay",
    "EntityItem",
    "LinkItem",
    "OverlayRecord",
    "RawDocument",
    "TagItem",
    "aggregate_overlays",
    "append_overlay",
    "clean_staged",
    "delete_raw_doc",
    "delete_staged_doc",
    "generate_doc_id",
    "get_all_doc_overlays",
    "get_overlays_for_doc",
    "get_raw_doc",
    "get_staged_doc",
    "list_raw_docs",
    "list_staged_docs",
    "raw_doc_exists",
    "stage_all",
    "stage_doc",
    "write_raw_doc",
]
