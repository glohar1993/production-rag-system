"""Web search fallback tool — real results via duckduckgo-search library."""
from __future__ import annotations
import uuid
import asyncio
import structlog
from app.models import DocumentChunk

log = structlog.get_logger(__name__)


class WebSearchTool:
    """
    Real web search using the duckduckgo-search library (no API key required).
    Falls back to an older DDGS text interface if the primary method fails.
    Called when CRAG grades retrieval as INCORRECT (nothing useful in the index).
    """

    async def search(self, query: str, max_results: int = 3) -> list[DocumentChunk]:
        """Run a web search and return results as DocumentChunks."""
        try:
            results = await asyncio.to_thread(self._sync_search, query, max_results)
            log.info("web_search_results", query=query[:60], n=len(results))
            return results
        except Exception as exc:
            log.warning("web_search_failed", query=query[:60], error=str(exc))
            return []

    def _sync_search(self, query: str, max_results: int) -> list[DocumentChunk]:
        from duckduckgo_search import DDGS
        chunks: list[DocumentChunk] = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                # Each result: {'title': ..., 'href': ..., 'body': ...}
                body = r.get("body", "").strip()
                if not body:
                    continue
                chunks.append(DocumentChunk(
                    id=str(uuid.uuid4()),
                    content=f"{r.get('title', '')}\n{body}",
                    metadata={
                        "source_type": "web",
                        "url": r.get("href", ""),
                    },
                    score=0.6,
                    source=r.get("href", "web")[:60],
                ))
        return chunks
