"""Hybrid retrieval: Dense (Qdrant) + Sparse (BM25) fused via Reciprocal Rank Fusion."""
from __future__ import annotations
import asyncio
import structlog
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, ScoredPoint
from rank_bm25 import BM25Okapi
import nltk

from app.config import get_settings
from app.models import DocumentChunk

log = structlog.get_logger(__name__)
settings = get_settings()

# Download NLTK tokenizer silently
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)


def _tokenize(text: str) -> list[str]:
    return nltk.word_tokenize(text.lower())


def _rrf_score(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank)


class HybridRetriever:
    """
    1. Dense retrieval via Qdrant (cosine similarity on BGE embeddings)
    2. Sparse retrieval via BM25Okapi over stored corpus
    3. RRF fusion of both result lists
    """

    def __init__(self) -> None:
        self._qdrant = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            check_compatibility=False,
        )
        self._encoder = SentenceTransformer(settings.dense_embed_model)
        self._collection = settings.qdrant_collection
        # BM25 corpus is rebuilt from Qdrant at startup for small datasets
        # For large corpora, maintain a separate BM25 index in Redis/disk
        self._bm25: BM25Okapi | None = None
        self._corpus_ids: list[str] = []
        self._corpus_texts: list[str] = []

    async def _load_bm25_corpus(self) -> None:
        """Load all document texts from Qdrant to build BM25 index."""
        try:
            all_docs, _ = await self._qdrant.scroll(
                collection_name=self._collection,
                limit=10_000,
                with_payload=True,
                with_vectors=False,
            )
            self._corpus_texts = [p.payload.get("content", "") for p in all_docs]
            self._corpus_ids = [str(p.id) for p in all_docs]
            tokenized = [_tokenize(t) for t in self._corpus_texts]
            self._bm25 = BM25Okapi(tokenized)
            log.info("bm25_index_built", n_docs=len(self._corpus_texts))
        except Exception as e:
            log.warning("bm25_corpus_load_failed", error=str(e))

    def _build_qdrant_filter(self, filters: dict) -> Filter | None:
        if not filters:
            return None
        conditions = []
        for k, v in filters.items():
            if isinstance(v, (str, int, bool)):  # MatchValue only accepts scalar types
                conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
        return Filter(must=conditions) if conditions else None  # type: ignore[arg-type]

    async def _dense_retrieve(self, query: str, top_k: int, filters: dict) -> list[ScoredPoint]:
        vec = self._encoder.encode(query, normalize_embeddings=True).tolist()
        results = await self._qdrant.search(
            collection_name=self._collection,
            query_vector=vec,
            limit=top_k,
            query_filter=self._build_qdrant_filter(filters),
            with_payload=True,
        )
        return results

    def _sparse_retrieve(self, query: str, top_k: int) -> list[tuple[str, float]]:
        if self._bm25 is None or not self._corpus_ids:
            return []
        tokens = _tokenize(query)
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self._corpus_ids[i], float(s)) for i, s in ranked]

    async def retrieve(self, query: str, top_k: int, filters: dict) -> list[DocumentChunk]:
        # Lazy load BM25 corpus
        if self._bm25 is None:
            await self._load_bm25_corpus()

        dense_results, sparse_results = await asyncio.gather(
            self._dense_retrieve(query, top_k, filters),
            asyncio.to_thread(self._sparse_retrieve, query, top_k),
        )

        # RRF fusion
        rrf_scores: dict[str, float] = {}
        id_to_payload: dict[str, dict] = {}

        for rank, point in enumerate(dense_results):
            pid = str(point.id)
            rrf_scores[pid] = rrf_scores.get(pid, 0.0) + _rrf_score(rank, settings.rrf_k)
            id_to_payload[pid] = point.payload or {}

        for rank, (doc_id, _) in enumerate(sparse_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + _rrf_score(rank, settings.rrf_k)
            if doc_id not in id_to_payload and doc_id in self._corpus_ids:
                idx = self._corpus_ids.index(doc_id)
                id_to_payload[doc_id] = {"content": self._corpus_texts[idx]}

        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        chunks = []
        for doc_id, score in ranked:
            payload = id_to_payload.get(doc_id, {})
            chunks.append(DocumentChunk(
                id=doc_id,
                content=payload.get("content", ""),
                metadata={k: v for k, v in payload.items() if k != "content"},
                score=score,
                source=payload.get("source", ""),
            ))

        log.info("hybrid_retrieved", n_results=len(chunks), query=query[:60])
        return chunks
