"""Shared Pydantic request/response schemas."""
from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class QueryType(str, Enum):
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    CONVERSATIONAL = "conversational"
    CODE = "code"
    MULTI_HOP = "multi_hop"


class CRAGGrade(str, Enum):
    CORRECT = "correct"
    AMBIGUOUS = "ambiguous"
    INCORRECT = "incorrect"


# ── Documents ─────────────────────────────────────────────────────────────────

class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0
    source: str = ""


class Citation(BaseModel):
    text: str
    source: str
    chunk_id: str
    score: float


# ── Query ─────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default")
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, Any] = Field(default_factory=dict)
    stream: bool = True


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    query_type: QueryType = QueryType.FACTUAL
    crag_grade: CRAGGrade = CRAGGrade.CORRECT
    cached: bool = False
    trace_id: str = ""
    latency_ms: float = 0.0


# ── Search (debug) ─────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    chunks: list[DocumentChunk]
    latency_ms: float


# ── Ingest ────────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    file_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    doc_id: str
    chunks_indexed: int
    status: str


# ── Health ────────────────────────────────────────────────────────────────────

class ComponentStatus(BaseModel):
    name: str
    healthy: bool
    latency_ms: float | None = None
    detail: str = ""


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded" | "down"
    components: list[ComponentStatus]


# ── SSE streaming ─────────────────────────────────────────────────────────────

class StreamEvent(BaseModel):
    event: str  # "token" | "citations" | "done" | "error"
    data: Any
