"""Embeds chunks and upserts them into Qdrant."""
from __future__ import annotations
import uuid
import structlog
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, PayloadSchemaType
)

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

BATCH_SIZE = 32  # embed this many chunks at once


def _ensure_collection(client: QdrantClient, collection: str, dim: int) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if collection not in existing:
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        log.info("qdrant_collection_created", collection=collection)

    # Payload indexes for filtering
    for field in ["source", "doc_type", "category", "language"]:
        try:
            client.create_payload_index(
                collection_name=collection,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass  # already exists


def index_chunks(chunks: list[dict], collection: str | None = None) -> int:
    """
    Embed and upsert chunks into Qdrant.
    Returns number of chunks indexed.
    """
    if not chunks:
        log.warning("index_chunks_empty")
        return 0

    col = collection or settings.qdrant_collection
    encoder = SentenceTransformer(settings.dense_embed_model)
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
        check_compatibility=False,
    )

    _ensure_collection(client, col, settings.embed_dim)

    texts = [c["content"] for c in chunks]
    total_indexed = 0

    # Embed in batches
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[i: i + BATCH_SIZE]
        batch_texts = texts[i: i + BATCH_SIZE]

        log.info("embedding_batch",
                 batch=i // BATCH_SIZE + 1,
                 total_batches=(len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE)

        vectors = encoder.encode(
            batch_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=BATCH_SIZE,
        )

        points = []
        for chunk, vec in zip(batch_chunks, vectors):
            payload = {
                "content": chunk["content"],
                **chunk["metadata"],
            }
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vec.tolist(),
                payload=payload,
            ))

        client.upsert(collection_name=col, points=points)
        total_indexed += len(points)

    info = client.get_collection(col)
    log.info("indexing_complete",
             collection=col,
             indexed_this_run=total_indexed,
             total_in_collection=info.points_count)

    return total_indexed
