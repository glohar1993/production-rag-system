"""Centralized configuration via environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "Production RAG System"
    env: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]

    # ── LLM ──────────────────────────────────────────────────────────────────
    openai_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.0

    # ── Embeddings ───────────────────────────────────────────────────────────
    dense_embed_model: str = "BAAI/bge-base-en-v1.5"
    sparse_embed_model: str = "naver/splade-cocondenser-ensemble-distil"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    embed_batch_size: int = 64
    embed_dim: int = 768

    # ── Qdrant ───────────────────────────────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "rag_documents"
    qdrant_payload_index_fields: list[str] = ["source", "doc_type", "language"]

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    semantic_cache_ttl: int = 3600          # seconds
    semantic_cache_threshold: float = 0.92  # cosine similarity cutoff
    conversation_window: int = 10           # turns to keep in memory

    # ── Retrieval ────────────────────────────────────────────────────────────
    top_k_dense: int = 20
    top_k_sparse: int = 20
    top_k_rerank: int = 5
    rrf_k: int = 60                         # RRF constant

    # ── CRAG ─────────────────────────────────────────────────────────────────
    crag_relevance_threshold: float = 0.6   # below → ambiguous/incorrect
    crag_max_web_results: int = 3

    # ── Security ─────────────────────────────────────────────────────────────
    max_query_length: int = 2000
    pii_redaction: bool = True

    # ── Observability ─────────────────────────────────────────────────────────
    # Keep for backward compat (unused)
    anthropic_api_key: str = ""

    opik_api_key: str = ""
    opik_project: str = "production-rag"


@lru_cache
def get_settings() -> Settings:
    return Settings()
