"""Pydantic models for ExoBrain data structures."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from uuid7 import uuid7


def generate_id() -> str:
    """Generate a UUIDv7 string."""
    return str(uuid7())


class TagItem(BaseModel):
    """A tag with optional confidence and note."""

    tag: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str | None = None


class EntityItem(BaseModel):
    """An entity mention with optional confidence and note."""

    name: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str | None = None


class LinkItem(BaseModel):
    """A link to another document with optional confidence and note."""

    doc_id: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str | None = None  # Can be a paragraph describing the relationship


class OverlayRecord(BaseModel):
    """An annotation record for a raw document.

    Stored as JSONL, partitioned by date.
    Multiple records can reference the same doc_id.
    """

    v: int = 1  # Schema version
    id: str = Field(default_factory=generate_id)  # Record ID (UUIDv7)
    ts: datetime = Field(default_factory=datetime.now)  # Timestamp
    doc_id: str  # UUIDv7 of the raw document
    source: Literal["human", "ai", "system", "import"]

    # Optional annotation fields
    title: str | None = None
    summary: str | None = None
    tags: list[TagItem] | None = None
    entities: list[EntityItem] | None = None
    links: list[LinkItem] | None = None
    extra: dict | None = None  # Arbitrary additional data


class AggregatedOverlay(BaseModel):
    """Aggregated overlay data for a single document.

    Used when staging documents.
    """

    doc_id: str
    titles: list[str] = Field(default_factory=list)
    summaries: list[str] = Field(default_factory=list)
    tags: list[TagItem] = Field(default_factory=list)
    entities: list[EntityItem] = Field(default_factory=list)
    links: list[LinkItem] = Field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if overlay has any content."""
        return not any([self.titles, self.summaries, self.tags, self.entities, self.links])


class RawDocument(BaseModel):
    """A raw document with its content and metadata."""

    id: str  # UUIDv7 (filename without .md)
    content: str
    path: str  # Full path to the file
