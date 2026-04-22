"""Web search fallback tool — real results via duckduckgo-search library."""
from __future__ import annotations
import re
import uuid
import asyncio
import structlog
from urllib.parse import urlparse
from app.models import DocumentChunk

log = structlog.get_logger(__name__)

# Matches language-prefixed Wikipedia/wiki subdomains (hi., fr., de., zh., ja., etc.)
# but NOT en. or www.
_NON_ENGLISH_WIKI_RE = re.compile(
    r'^(?!en\.|www\.)([a-z]{2,3})\.(?:wikipedia|wikibooks|wikivoyage|wiktionary)\.org$'
)


def _is_english_url(url: str) -> bool:
    """Return False for clearly non-English Wikipedia/wiki domains."""
    try:
        host = urlparse(url).hostname or ""
        return not _NON_ENGLISH_WIKI_RE.match(host)
    except Exception:
        return True


def _display_source(url: str) -> str:
    """Return clean domain label (e.g. 'en.wikipedia.org') instead of raw URL."""
    try:
        return urlparse(url).hostname or url[:60]
    except Exception:
        return url[:60]


class WebSearchTool:
    """
    Real web search using the duckduckgo-search library (no API key required).
    Called when CRAG grades retrieval as INCORRECT (nothing useful in the index).
    """

    async def search(self, query: str, max_results: int = 5) -> list[DocumentChunk]:
        """Run a web search and return deduplicated, scored DocumentChunks."""
        try:
            results = await asyncio.to_thread(self._sync_search, query, max_results)
            log.info("web_search_results", query=query[:60], n=len(results))
            return results
        except Exception as exc:
            log.warning("web_search_failed", query=query[:60], error=str(exc))
            return []

    def _sync_search(self, query: str, max_results: int) -> list[DocumentChunk]:
        from ddgs import DDGS

        chunks: list[DocumentChunk] = []
        seen_urls: set[str] = set()
        domain_count: dict[str, int] = {}

        # Fetch extra candidates to account for filtered-out results
        fetch_n = max_results * 3

        with DDGS() as ddgs:
            for position, r in enumerate(ddgs.text(query, max_results=fetch_n)):
                if len(chunks) >= max_results:
                    break

                url = r.get("href", "")
                body = r.get("body", "").strip()

                if not body:
                    continue
                if url in seen_urls:
                    continue
                if not _is_english_url(url):
                    continue

                domain = urlparse(url).hostname or ""
                if domain_count.get(domain, 0) >= 2:
                    # At most 2 results from the same domain
                    continue

                seen_urls.add(url)
                domain_count[domain] = domain_count.get(domain, 0) + 1

                # Position-based score: rank 0 → 0.95, rank 4 → 0.55, floor at 0.50
                score = round(max(0.50, 0.95 - 0.10 * len(chunks)), 2)

                chunks.append(DocumentChunk(
                    id=str(uuid.uuid4()),
                    content=f"{r.get('title', '')}\n{body}",
                    metadata={
                        "source_type": "web",
                        "url": url,
                    },
                    score=score,
                    source=_display_source(url),
                ))

        return chunks
