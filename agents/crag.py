"""CRAG Agent — self-correcting RAG loop with multi-source routing."""
from __future__ import annotations
import asyncio
import structlog
from app.config import get_settings
from app.models import DocumentChunk
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker
from tools.web_search import WebSearchTool

log = structlog.get_logger(__name__)
settings = get_settings()


class CRAGAgent:
    """
    Corrective RAG agent for the AMBIGUOUS grade path:
    1. Decomposes query into sub-queries (done upstream)
    2. For each sub-query: retrieves from vector store + web fallback
    3. Merges and deduplicates results
    """

    def __init__(self) -> None:
        self._retriever = HybridRetriever()
        self._reranker = Reranker()
        self._web = WebSearchTool()

    async def _retrieve_single(self, query: str, filters: dict) -> list[DocumentChunk]:
        chunks = await self._retriever.retrieve(query, top_k=10, filters=filters)
        chunks = await self._reranker.rerank(query, chunks, top_k=3)

        if not chunks or max(c.score for c in chunks) < settings.crag_relevance_threshold:
            # Fallback to web search
            log.info("crag_web_fallback", query=query[:60])
            web_chunks = await self._web.search(query, max_results=settings.crag_max_web_results)
            chunks = chunks + web_chunks

        return chunks

    async def retrieve_and_merge(
        self,
        sub_queries: list[str],
        filters: dict,
    ) -> list[DocumentChunk]:
        """Run sub-query retrieval in parallel and merge results."""
        results = await asyncio.gather(
            *[self._retrieve_single(q, filters) for q in sub_queries]
        )

        # Flatten and deduplicate by id
        seen: set[str] = set()
        merged: list[DocumentChunk] = []
        for chunk_list in results:
            for chunk in chunk_list:
                if chunk.id not in seen:
                    seen.add(chunk.id)
                    merged.append(chunk)

        merged.sort(key=lambda c: c.score, reverse=True)
        log.info("crag_merged", n_sub_queries=len(sub_queries), total_chunks=len(merged))
        return merged
