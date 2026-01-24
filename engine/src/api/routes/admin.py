"""Admin endpoints for staging and indexing."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core import stage_all, stage_doc
from src.graphrag import IndexError, rebuild_index, run_index

router = APIRouter()


class StageRequest(BaseModel):
    """Stage request body."""

    doc_id: str | None = None  # If None, stage all


class StageResponse(BaseModel):
    """Stage response body."""

    status: str
    staged: int


class IndexResponse(BaseModel):
    """Index response body."""

    status: str
    incremental: bool
    documents: int | None = None


@router.post("/stage", response_model=StageResponse)
async def admin_stage(request: StageRequest):
    """Trigger staging of documents."""
    if request.doc_id:
        result = stage_doc(request.doc_id)
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"Document not found: {request.doc_id}"
            )
        return StageResponse(status="success", staged=1)
    else:
        results = stage_all()
        return StageResponse(status="success", staged=len(results))


@router.post("/index/incremental", response_model=IndexResponse)
async def admin_index_incremental():
    """Trigger incremental index update."""
    try:
        result = run_index(incremental=True)
        return IndexResponse(
            status=result["status"],
            incremental=True,
            documents=result.get("documents"),
        )
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")


@router.post("/index/rebuild", response_model=IndexResponse)
async def admin_index_rebuild():
    """Trigger full index rebuild."""
    try:
        result = rebuild_index()
        return IndexResponse(
            status=result["status"],
            incremental=False,
            documents=result.get("documents"),
        )
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {e}")
