"""Core memory engine components."""

from src.core.models import (
    AggregatedOverlay,
    EntityItem,
    LinkItem,
    OverlayRecord,
    RawDocument,
    TagItem,
    generate_id,
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
    # Models
    "AggregatedOverlay",
    "EntityItem",
    "LinkItem",
    "OverlayRecord",
    "RawDocument",
    "TagItem",
    "generate_id",
    # Raw operations
    "delete_raw_doc",
    "generate_doc_id",
    "get_raw_doc",
    "list_raw_docs",
    "raw_doc_exists",
    "write_raw_doc",
    # Overlay operations
    "aggregate_overlays",
    "append_overlay",
    "get_all_doc_overlays",
    "get_overlays_for_doc",
    # Staging operations
    "clean_staged",
    "delete_staged_doc",
    "get_staged_doc",
    "list_staged_docs",
    "stage_all",
    "stage_doc",
]
