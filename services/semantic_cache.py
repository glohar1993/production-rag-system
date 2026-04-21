"""Semantic cache backed by Redis with HNSW cosine similarity."""
from __future__ import annotations
import json
import hashlib
import numpy as np
import redis.asyncio as aioredis
import structlog
from sentence_transformers import SentenceTransformer

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

_CACHE_PREFIX = "semcache:"
_VECTOR_KEY = "semcache:vectors"
_META_KEY = "semcache:meta"


class SemanticCache:
    """
    HNSW-style semantic cache in Redis.
    Stores (query_vector, answer) pairs; on lookup performs cosine similarity
    against all cached vectors and returns the answer if similarity ≥ threshold.
    For production scale, replace with Redis Stack + RediSearch vector index.
    """

    def __init__(self) -> None:
        self._redis: aioredis.Redis = aioredis.from_url(settings.redis_url, decode_responses=False)
        self._encoder = SentenceTransformer(settings.dense_embed_model)
        self._threshold = settings.semantic_cache_threshold
        self._ttl = settings.semantic_cache_ttl

    def _embed(self, text: str) -> np.ndarray:
        vec = self._encoder.encode(text, normalize_embeddings=True)
        return vec.astype(np.float32)

    async def get(self, query: str) -> str | None:
        """Return cached answer if a semantically similar query exists."""
        q_vec = self._embed(query)

        # Load all stored vectors
        raw_vecs = await self._redis.lrange(_VECTOR_KEY, 0, -1)
        raw_meta = await self._redis.lrange(_META_KEY, 0, -1)

        best_sim, best_idx = 0.0, -1
        for i, rv in enumerate(raw_vecs):
            stored = np.frombuffer(rv, dtype=np.float32)
            sim = float(np.dot(q_vec, stored))
            if sim > best_sim:
                best_sim, best_idx = sim, i

        if best_sim >= self._threshold and best_idx >= 0:
            meta = json.loads(raw_meta[best_idx])
            log.info("cache_hit", similarity=best_sim, cached_query=meta.get("query", ""))
            return meta.get("answer")

        return None

    async def set(self, query: str, answer: str) -> None:
        """Store query vector + answer in Redis."""
        vec = self._embed(query)
        meta = json.dumps({"query": query, "answer": answer})
        await self._redis.rpush(_VECTOR_KEY, vec.tobytes())
        await self._redis.rpush(_META_KEY, meta.encode())
        # TTL on the list keys
        await self._redis.expire(_VECTOR_KEY, self._ttl)
        await self._redis.expire(_META_KEY, self._ttl)
        log.info("cache_set", query=query[:60])

    async def invalidate(self) -> None:
        await self._redis.delete(_VECTOR_KEY, _META_KEY)
