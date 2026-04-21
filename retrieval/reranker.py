"""Cross-encoder reranker — rescores retrieved chunks for precision."""
from __future__ import annotations
import asyncio
import structlog
from sentence_transformers import CrossEncoder
from app.config import get_settings
from app.models import DocumentChunk

log = structlog.get_logger(__name__)
settings = get_settings()


class Reranker:
    """
    Uses a cross-encoder (ms-marco-MiniLM) to produce query-aware relevance
    scores, replacing the bi-encoder retrieval scores with higher-precision ones.
    """

    def __init__(self) -> None:
        self._model = CrossEncoder(settings.reranker_model)

    def _score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        scores = self._model.predict(pairs)
        return scores.tolist()

    async def rerank(
        self,
        query: str,
        chunks: list[DocumentChunk],
        top_k: int,
    ) -> list[DocumentChunk]:
        if not chunks:
            return []

        pairs = [(query, chunk.content[:512]) for chunk in chunks]
        scores = await asyncio.to_thread(self._score_pairs, pairs)

        for chunk, score in zip(chunks, scores):
            chunk.score = float(score)

        reranked = sorted(chunks, key=lambda c: c.score, reverse=True)[:top_k]
        log.info("reranked", input=len(chunks), output=len(reranked),
                 top_score=reranked[0].score if reranked else 0)
        return reranked
