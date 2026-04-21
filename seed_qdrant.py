"""One-time script to create the Qdrant collection and seed sample documents."""
import asyncio
import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, PayloadSchemaType
)

QDRANT_URL = "http://localhost:6333"
COLLECTION = "rag_documents"
EMBED_MODEL = "BAAI/bge-base-en-v1.5"
DIM = 768

SAMPLE_DOCS = [
    {
        "content": (
            "Retrieval-Augmented Generation (RAG) is an AI framework that combines "
            "a retrieval system with a language model. Instead of relying solely on "
            "parametric memory (weights), the model queries an external knowledge base "
            "at inference time to ground its responses in retrieved facts."
        ),
        "source": "rag_overview.md",
        "doc_type": "technical",
        "language": "en",
    },
    {
        "content": (
            "Hybrid retrieval fuses dense (embedding-based) and sparse (BM25 keyword) "
            "search signals via Reciprocal Rank Fusion (RRF). Dense retrieval excels at "
            "semantic matching; sparse retrieval excels at exact keyword matches. "
            "RRF combines ranked lists without requiring score normalization."
        ),
        "source": "hybrid_retrieval.md",
        "doc_type": "technical",
        "language": "en",
    },
    {
        "content": (
            "Corrective RAG (CRAG) adds a self-correction loop: retrieved documents are "
            "graded for relevance before generation. If retrieval quality is AMBIGUOUS, "
            "the query is decomposed and re-retrieved. If INCORRECT, the system falls back "
            "to web search or declines to answer."
        ),
        "source": "crag_paper.md",
        "doc_type": "technical",
        "language": "en",
    },
    {
        "content": (
            "Qdrant is a vector similarity search engine written in Rust. It supports "
            "dense vectors, sparse vectors (SPLADE), named vectors, payload filtering, "
            "and HNSW-based approximate nearest-neighbor search. It exposes both a gRPC "
            "and REST API and is designed for high-throughput production workloads."
        ),
        "source": "qdrant_docs.md",
        "doc_type": "technical",
        "language": "en",
    },
    {
        "content": (
            "Semantic caching stores query embeddings alongside generated answers. "
            "On a new query, the cache computes cosine similarity between the new "
            "embedding and all stored embeddings. If similarity exceeds a threshold "
            "(e.g. 0.92), the cached answer is returned, avoiding an expensive LLM call."
        ),
        "source": "semantic_cache.md",
        "doc_type": "technical",
        "language": "en",
    },
    {
        "content": (
            "Cross-encoder rerankers are more accurate than bi-encoders for relevance "
            "scoring because they jointly encode the query and document. Models like "
            "ms-marco-MiniLM produce calibrated relevance scores used to reorder "
            "candidate chunks retrieved by the faster bi-encoder stage."
        ),
        "source": "reranking.md",
        "doc_type": "technical",
        "language": "en",
    },
    {
        "content": (
            "FastAPI is a modern, high-performance Python web framework built on Starlette "
            "and Pydantic. It provides automatic OpenAPI documentation, async request "
            "handling, dependency injection, and type-checked request/response models. "
            "It is well-suited for building AI inference APIs."
        ),
        "source": "fastapi_intro.md",
        "doc_type": "technical",
        "language": "en",
    },
    {
        "content": (
            "Server-Sent Events (SSE) allow a server to push data to a client over a "
            "single HTTP connection. Unlike WebSockets, SSE is unidirectional (server → "
            "client) and uses a simple text-based protocol. It is ideal for streaming "
            "LLM token-by-token output to a browser or API consumer."
        ),
        "source": "sse_streaming.md",
        "doc_type": "technical",
        "language": "en",
    },
]


async def main():
    client = AsyncQdrantClient(url=QDRANT_URL)
    encoder = SentenceTransformer(EMBED_MODEL)

    # Create collection (idempotent)
    existing = await client.get_collections()
    names = [c.name for c in existing.collections]
    if COLLECTION not in names:
        await client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
        )
        print(f"Created collection '{COLLECTION}'")
    else:
        print(f"Collection '{COLLECTION}' already exists")

    # Index payload fields
    for field in ["source", "doc_type", "language"]:
        try:
            await client.create_payload_index(
                collection_name=COLLECTION,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass

    # Encode and upsert
    texts = [d["content"] for d in SAMPLE_DOCS]
    vectors = encoder.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    points = []
    for doc, vec in zip(SAMPLE_DOCS, vectors):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vec.tolist(),
            payload=doc,
        ))

    await client.upsert(collection_name=COLLECTION, points=points)
    print(f"Indexed {len(points)} documents into '{COLLECTION}'")

    info = await client.get_collection(COLLECTION)
    print(f"Collection now has {info.points_count} points")


if __name__ == "__main__":
    asyncio.run(main())
