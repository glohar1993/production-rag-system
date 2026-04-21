"""Web search fallback tool for CRAG agent."""
from __future__ import annotations
import uuid
import httpx
import structlog
from app.models import DocumentChunk

log = structlog.get_logger(__name__)

DUCKDUCKGO_URL = "https://api.duckduckgo.com/"


class WebSearchTool:
    """
    Lightweight web search using DuckDuckGo Instant Answer API.
    Used as a fallback when vector store retrieval yields low-confidence results.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout

    async def search(self, query: str, max_results: int = 3) -> list[DocumentChunk]:
        """Return web results as DocumentChunks."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    DUCKDUCKGO_URL,
                    params={"q": query, "format": "json", "no_redirect": "1", "no_html": "1"},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            log.warning("web_search_failed", query=query[:60], error=str(exc))
            return []

        chunks: list[DocumentChunk] = []

        # Abstract (top answer)
        if data.get("AbstractText"):
            chunks.append(DocumentChunk(
                id=str(uuid.uuid4()),
                content=data["AbstractText"],
                metadata={"source_type": "web", "url": data.get("AbstractURL", "")},
                score=0.7,
                source=data.get("AbstractSource", "web"),
            ))

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                chunks.append(DocumentChunk(
                    id=str(uuid.uuid4()),
                    content=topic["Text"],
                    metadata={
                        "source_type": "web",
                        "url": topic.get("FirstURL", ""),
                    },
                    score=0.5,
                    source="duckduckgo",
                ))
            if len(chunks) >= max_results:
                break

        log.info("web_search_results", query=query[:60], n=len(chunks))
        return chunks
