"""Pydantic models for ExoBrain v2 data structures.

These models represent the SQLite-backed object system where everything is an object.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from uuid_extensions import uuid7  # pip package: uuid7


def generate_id() -> str:
    """Generate a UUIDv7 string."""
    return str(uuid7())


# === Core object models ===


class ExoObject(BaseModel):
    """An object in the ExoBrain knowledge system.

    Everything is an object: documents, notes, transcripts, URLs, types, spaces, and tags.
    """

    id: str = Field(default_factory=generate_id)
    type_id: str
    space_id: str
    title: str
    summary: str | None = None
    content: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ExoTag(BaseModel):
    """A tag attached to an object."""

    id: int | None = None
    object_id: str
    tag_text: str
    tag_object_id: str | None = None
    created_at: str | None = None


class ExoLink(BaseModel):
    """A directed relationship between two objects."""

    id: int | None = None
    from_id: str
    to_id: str
    relationship: str
    created_at: str | None = None


class ExoFile(BaseModel):
    """A file attachment for an object. At most one per object."""

    object_id: str
    path: str
    role: str = "primary"
    mime_type: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    created_at: str | None = None


# === JSON output models (for --json CLI flag) ===


class ObjectSummary(BaseModel):
    """Compact object representation for list views."""

    id: str
    type: str  # type title, not type_id
    space: str  # space title, not space_id
    title: str
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: str | None = None


class ObjectDetail(BaseModel):
    """Full object detail with tags, links, and file info."""

    id: str
    type_id: str
    type: str
    space_id: str
    space: str
    title: str
    summary: str | None = None
    content: str | None = None
    tags: list[str] = Field(default_factory=list)
    links: list[dict] = Field(default_factory=list)
    file: dict | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SearchResult(BaseModel):
    """A search result from FTS5."""

    id: str
    type: str
    space: str
    title: str
    summary: str | None = None
    rank: float | None = None


class ObjectHistoryEntry(BaseModel):
    """A single version in an object's history."""

    id: int
    object_id: str
    version: int
    title: str | None = None
    summary: str | None = None
    content: str | None = None
    content_hash: str | None = None
    changed_by: str = "system"
    created_at: str | None = None


class StatusInfo(BaseModel):
    """System status information."""

    version: str
    data_dir: str
    db_path: str
    db_size_bytes: int
    object_count: int
    type_counts: dict[str, int] = Field(default_factory=dict)
    space_count: int = 0
    tag_count: int = 0
    link_count: int = 0
    file_count: int = 0
    integrity: str = "unknown"


# === Legacy models (kept for backward compatibility during migration) ===


class TagItem(BaseModel):
    """A tag with optional confidence and note (legacy overlay format)."""

    tag: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str | None = None


class EntityItem(BaseModel):
    """An entity mention with optional confidence and note (legacy overlay format)."""

    name: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str | None = None


class LinkItem(BaseModel):
    """A link to another document with optional confidence and note (legacy overlay format)."""

    doc_id: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str | None = None


class OverlayRecord(BaseModel):
    """An annotation record for a raw document (legacy overlay format)."""

    v: int = 1
    id: str = Field(default_factory=generate_id)
    ts: datetime = Field(default_factory=datetime.now)
    doc_id: str
    source: Literal["human", "ai", "system", "import"]
    title: str | None = None
    summary: str | None = None
    tags: list[TagItem] | None = None
    entities: list[EntityItem] | None = None
    links: list[LinkItem] | None = None
    extra: dict | None = None


class AggregatedOverlay(BaseModel):
    """Aggregated overlay data for a single document (legacy overlay format)."""

    doc_id: str
    titles: list[str] = Field(default_factory=list)
    summaries: list[str] = Field(default_factory=list)
    tags: list[TagItem] = Field(default_factory=list)
    entities: list[EntityItem] = Field(default_factory=list)
    links: list[LinkItem] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return not any([self.titles, self.summaries, self.tags, self.entities, self.links])


class RawDocument(BaseModel):
    """A raw document with its content and metadata (legacy format)."""

    id: str
    content: str
    path: str
