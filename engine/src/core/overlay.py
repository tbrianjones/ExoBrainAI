"""Overlay JSONL operations."""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from src.config import settings
from src.core.models import (
    AggregatedOverlay,
    EntityItem,
    LinkItem,
    OverlayRecord,
    TagItem,
)


def get_overlay_path(date: datetime | None = None) -> Path:
    """Get the overlay file path for a given date.

    Args:
        date: Date for the overlay file; defaults to today

    Returns:
        Path to the JSONL file
    """
    if date is None:
        date = datetime.now()
    filename = date.strftime("%Y-%m-%d") + ".jsonl"
    return settings.overlay_dir / filename


def append_overlay(record: OverlayRecord) -> None:
    """Append an overlay record to today's JSONL file.

    Args:
        record: The overlay record to append
    """
    settings.overlay_dir.mkdir(parents=True, exist_ok=True)
    path = get_overlay_path(record.ts)

    with open(path, "a", encoding="utf-8") as f:
        f.write(record.model_dump_json() + "\n")


def read_overlay_file(path: Path) -> list[OverlayRecord]:
    """Read all records from an overlay JSONL file.

    Args:
        path: Path to the JSONL file

    Returns:
        List of OverlayRecord objects
    """
    if not path.exists():
        return []

    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                records.append(OverlayRecord(**data))
    return records


def list_overlay_files(days: int | None = None) -> list[Path]:
    """List overlay files, optionally limited to recent days.

    Args:
        days: Number of days to look back; None for all files

    Returns:
        List of paths to overlay files, sorted by date descending
    """
    if not settings.overlay_dir.exists():
        return []

    files = list(settings.overlay_dir.glob("*.jsonl"))

    if days is not None:
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        files = [f for f in files if f.stem >= cutoff_str]

    return sorted(files, reverse=True)


def get_overlays_for_doc(
    doc_id: str,
    days: int | None = None,
) -> list[OverlayRecord]:
    """Get all overlay records for a specific document.

    Args:
        doc_id: Document ID to filter by
        days: Number of days to look back; None for all files

    Returns:
        List of OverlayRecord objects for the document
    """
    if days is None:
        days = settings.overlay_window_days

    records = []
    for path in list_overlay_files(days):
        for record in read_overlay_file(path):
            if record.doc_id == doc_id:
                records.append(record)
    return records


def aggregate_overlays(doc_id: str, days: int | None = None) -> AggregatedOverlay:
    """Aggregate all overlay data for a document.

    Collects all titles, summaries, tags, entities, and links
    from overlay records. Does not deduplicate.

    Args:
        doc_id: Document ID
        days: Number of days to look back

    Returns:
        AggregatedOverlay with all collected data
    """
    records = get_overlays_for_doc(doc_id, days)

    agg = AggregatedOverlay(doc_id=doc_id)

    for record in records:
        if record.title:
            agg.titles.append(record.title)
        if record.summary:
            agg.summaries.append(record.summary)
        if record.tags:
            agg.tags.extend(record.tags)
        if record.entities:
            agg.entities.extend(record.entities)
        if record.links:
            agg.links.extend(record.links)

    return agg


def get_all_doc_overlays(days: int | None = None) -> dict[str, AggregatedOverlay]:
    """Get aggregated overlays for all documents.

    Args:
        days: Number of days to look back

    Returns:
        Dictionary mapping doc_id to AggregatedOverlay
    """
    if days is None:
        days = settings.overlay_window_days

    # Collect all records by doc_id
    records_by_doc: dict[str, list[OverlayRecord]] = defaultdict(list)

    for path in list_overlay_files(days):
        for record in read_overlay_file(path):
            records_by_doc[record.doc_id].append(record)

    # Aggregate each document's records
    result = {}
    for doc_id, records in records_by_doc.items():
        agg = AggregatedOverlay(doc_id=doc_id)
        for record in records:
            if record.title:
                agg.titles.append(record.title)
            if record.summary:
                agg.summaries.append(record.summary)
            if record.tags:
                agg.tags.extend(record.tags)
            if record.entities:
                agg.entities.extend(record.entities)
            if record.links:
                agg.links.extend(record.links)
        result[doc_id] = agg

    return result
