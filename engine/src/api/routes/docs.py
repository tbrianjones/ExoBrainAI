"""Document endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core import (
    AggregatedOverlay,
    RawDocument,
    aggregate_overlays,
    get_raw_doc,
    get_staged_doc,
    list_raw_docs,
)

router = APIRouter()


class DocumentResponse(BaseModel):
    """Full document response."""

    id: str
    raw: str | None
    overlay: AggregatedOverlay | None
    staged: str | None


class DocumentListResponse(BaseModel):
    """List of document IDs."""

    documents: list[str]
    count: int


@router.get("/", response_model=DocumentListResponse)
async def list_documents():
    """List all raw document IDs."""
    docs = list_raw_docs()
    return DocumentListResponse(documents=docs, count=len(docs))


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get a document with raw, overlay, and staged content."""
    raw_doc = get_raw_doc(doc_id)
    if raw_doc is None:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    overlay = aggregate_overlays(doc_id)
    staged = get_staged_doc(doc_id)

    return DocumentResponse(
        id=doc_id,
        raw=raw_doc.content,
        overlay=overlay if not overlay.is_empty() else None,
        staged=staged,
    )


@router.get("/{doc_id}/raw")
async def get_raw(doc_id: str):
    """Get only the raw document content."""
    raw_doc = get_raw_doc(doc_id)
    if raw_doc is None:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
    return {"id": doc_id, "content": raw_doc.content}


@router.get("/{doc_id}/overlay", response_model=AggregatedOverlay)
async def get_overlay(doc_id: str):
    """Get aggregated overlay data for a document."""
    # Check if raw doc exists
    raw_doc = get_raw_doc(doc_id)
    if raw_doc is None:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    return aggregate_overlays(doc_id)


@router.get("/{doc_id}/staged")
async def get_staged(doc_id: str):
    """Get the staged document content."""
    staged = get_staged_doc(doc_id)
    if staged is None:
        raise HTTPException(status_code=404, detail=f"Staged document not found: {doc_id}")
    return {"id": doc_id, "content": staged}


@router.get("/{doc_id}/links")
async def get_links(doc_id: str):
    """Get linked documents for a document."""
    overlay = aggregate_overlays(doc_id)
    return {
        "id": doc_id,
        "links": [
            {
                "doc_id": link.doc_id,
                "confidence": link.confidence,
                "note": link.note,
            }
            for link in overlay.links
        ],
    }
