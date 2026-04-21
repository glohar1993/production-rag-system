"""Metadata + entity filters applied post-retrieval."""
from __future__ import annotations
import re
import structlog
from app.models import DocumentChunk

log = structlog.get_logger(__name__)


class MetadataFilter:
    """
    Post-retrieval filter layer:
    - Drops chunks below a score threshold
    - Filters by allowed metadata values
    - Entity-level deduplication (removes near-duplicate content)
    """

    def __init__(self, score_threshold: float = 0.0) -> None:
        self._score_threshold = score_threshold

    def by_score(self, chunks: list[DocumentChunk], threshold: float | None = None) -> list[DocumentChunk]:
        t = threshold if threshold is not None else self._score_threshold
        filtered = [c for c in chunks if c.score >= t]
        log.debug("score_filter", before=len(chunks), after=len(filtered), threshold=t)
        return filtered

    def by_metadata(self, chunks: list[DocumentChunk], allowed: dict[str, list]) -> list[DocumentChunk]:
        """Keep only chunks whose metadata values match the allowed sets."""
        if not allowed:
            return chunks
        result = []
        for chunk in chunks:
            if all(chunk.metadata.get(k) in vs for k, vs in allowed.items()):
                result.append(chunk)
        return result

    def deduplicate_near(self, chunks: list[DocumentChunk], overlap_threshold: float = 0.8) -> list[DocumentChunk]:
        """
        Simple near-duplicate removal: if two chunks share > overlap_threshold
        of their n-gram tokens, keep only the higher-scored one.
        """
        def ngrams(text: str, n: int = 3) -> set[str]:
            tokens = re.findall(r"\w+", text.lower())
            return set(zip(*[tokens[i:] for i in range(n)]))  # type: ignore

        kept: list[DocumentChunk] = []
        for chunk in chunks:
            chunk_ngrams = ngrams(chunk.content)
            duplicate = False
            for kept_chunk in kept:
                kept_ngrams = ngrams(kept_chunk.content)
                if not chunk_ngrams or not kept_ngrams:
                    continue
                overlap = len(chunk_ngrams & kept_ngrams) / min(len(chunk_ngrams), len(kept_ngrams))
                if overlap >= overlap_threshold:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(chunk)
        return kept
