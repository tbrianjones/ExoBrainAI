"""Query endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.graphrag import QueryError, QueryMode, query_global, query_local

router = APIRouter()


class QueryRequest(BaseModel):
    """Query request body."""

    query: str
    community_level: int | None = None  # For global queries


class QueryResponse(BaseModel):
    """Query response body."""

    status: str
    mode: str
    query: str
    response: str


@router.post("/global", response_model=QueryResponse)
async def global_query(request: QueryRequest):
    """Run a global/theme query.

    Global queries use community summaries to answer broad questions
    about themes and patterns across the corpus.
    """
    try:
        result = query_global(request.query, request.community_level)
        return QueryResponse(**result)
    except QueryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@router.post("/local", response_model=QueryResponse)
async def local_query(request: QueryRequest):
    """Run a local/neighborhood query.

    Local queries focus on specific entities and their relationships,
    retrieving relevant context from the knowledge graph.
    """
    try:
        result = query_local(request.query)
        return QueryResponse(**result)
    except QueryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")
