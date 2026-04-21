"""Search debug route — exposes raw retrieval results."""
import time
from fastapi import APIRouter
from app.models import SearchRequest, SearchResponse
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker

router = APIRouter(tags=["search"])
retriever = HybridRetriever()
reranker = Reranker()


@router.post("/search")
async def search(request: SearchRequest) -> SearchResponse:
    """Raw hybrid retrieval without generation — useful for debugging."""
    start = time.perf_counter()

    chunks = await retriever.retrieve(
        query=request.query,
        top_k=request.top_k * 4,
        filters=request.filters,
    )
    chunks = await reranker.rerank(query=request.query, chunks=chunks, top_k=request.top_k)

    return SearchResponse(
        chunks=chunks,
        latency_ms=(time.perf_counter() - start) * 1000,
    )
