"""Core RAG pipeline — orchestrates the full query flow."""
from __future__ import annotations
import time
import asyncio
from typing import AsyncIterator
import structlog
import openai
import opik

from app.config import get_settings
from app.models import (
    QueryResponse, DocumentChunk, Citation, CRAGGrade, QueryType, StreamEvent
)
from services.semantic_cache import SemanticCache
from services.conversation import ConversationMemory
from services.query_router import QueryRouter
from services.document_grader import DocumentGrader
from services.query_decomposer import QueryDecomposer
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker
from retrieval.filters import MetadataFilter
from agents.crag import CRAGAgent
from security.output_guard import OutputGuard
from prompts.templates import build_rag_prompt

log = structlog.get_logger(__name__)
settings = get_settings()


class RAGPipeline:
    """
    Full query pipeline:
    Input Guard → Memory → Semantic Cache → Query Router → Hybrid Retrieval
    → Reranker → CRAG Grading → (Decompose+Re-retrieve if AMBIGUOUS)
    → Generate → Citations → Output Guard → Response
    """

    def __init__(self) -> None:
        self._llm = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self._cache = SemanticCache()
        self._memory = ConversationMemory()
        self._router = QueryRouter()
        self._retriever = HybridRetriever()
        self._reranker = Reranker()
        self._grader = DocumentGrader()
        self._decomposer = QueryDecomposer()
        self._crag = CRAGAgent()
        self._filter = MetadataFilter()
        self._output_guard = OutputGuard()

    @opik.track(name="rag_pipeline")
    async def run(
        self,
        query: str,
        session_id: str,
        top_k: int,
        filters: dict,
        trace_id: str,
    ) -> QueryResponse:
        start = time.perf_counter()

        # ── 1. Memory: rewrite follow-up queries ─────────────────────────────
        standalone_query = await self._memory.rewrite_query(session_id, query, self._llm)

        # ── 2. Semantic cache check ───────────────────────────────────────────
        cached_answer = await self._cache.get(standalone_query)
        if cached_answer:
            await self._memory.add_turn(session_id, "user", query)
            await self._memory.add_turn(session_id, "assistant", cached_answer)
            return QueryResponse(
                answer=cached_answer,
                cached=True,
                trace_id=trace_id,
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        # ── 3. Query classification ───────────────────────────────────────────
        query_type = await self._router.classify(standalone_query)
        retrieval_k = self._router.top_k_for_type(query_type, top_k)

        # ── 4. Hybrid retrieval ───────────────────────────────────────────────
        chunks = await self._retriever.retrieve(
            query=standalone_query,
            top_k=retrieval_k * 4,
            filters=filters,
        )

        # ── 5. Rerank ─────────────────────────────────────────────────────────
        chunks = await self._reranker.rerank(standalone_query, chunks, top_k=retrieval_k)

        # ── 6. CRAG grading ───────────────────────────────────────────────────
        grade, good_chunks = await self._grader.grade(standalone_query, chunks)

        if grade == CRAGGrade.INCORRECT:
            # Refuse gracefully — no good evidence
            answer = (
                "I couldn't find reliable information to answer your question. "
                "Please try rephrasing or provide more context."
            )
            return QueryResponse(
                answer=answer,
                crag_grade=grade,
                query_type=query_type,
                trace_id=trace_id,
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        if grade == CRAGGrade.AMBIGUOUS:
            # Decompose + re-retrieve to fill gaps
            sub_queries = await self._decomposer.decompose(standalone_query)
            extra_chunks = await self._crag.retrieve_and_merge(sub_queries, filters)
            good_chunks = self._deduplicate(good_chunks + extra_chunks)

        # ── 7. Generate ───────────────────────────────────────────────────────
        history = await self._memory.get_history(session_id)
        prompt_system, prompt_user = build_rag_prompt(
            query=standalone_query,
            chunks=good_chunks,
            query_type=query_type,
            history=history,
        )

        response = await self._llm.chat.completions.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user},
            ],
        )
        answer = response.choices[0].message.content or ""

        # ── 8. Citations ──────────────────────────────────────────────────────
        citations = self._extract_citations(good_chunks)

        # ── 9. Output guard ───────────────────────────────────────────────────
        answer = self._output_guard.redact(answer)

        # ── 10. Cache + memory ────────────────────────────────────────────────
        await self._cache.set(standalone_query, answer)
        await self._memory.add_turn(session_id, "user", query)
        await self._memory.add_turn(session_id, "assistant", answer)

        return QueryResponse(
            answer=answer,
            citations=citations,
            query_type=query_type,
            crag_grade=grade,
            cached=False,
            trace_id=trace_id,
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    async def stream(
        self,
        query: str,
        session_id: str,
        top_k: int,
        filters: dict,
        trace_id: str,
    ) -> AsyncIterator[StreamEvent]:
        """SSE streaming variant — yields token events then a done event."""
        # Run retrieval synchronously first
        standalone_query = await self._memory.rewrite_query(session_id, query, self._llm)

        cached_answer = await self._cache.get(standalone_query)
        if cached_answer:
            yield StreamEvent(event="token", data=cached_answer)
            yield StreamEvent(event="done", data={"cached": True, "trace_id": trace_id})
            return

        query_type = await self._router.classify(standalone_query)
        retrieval_k = self._router.top_k_for_type(query_type, top_k)
        chunks = await self._retriever.retrieve(standalone_query, top_k=retrieval_k * 4, filters=filters)
        chunks = await self._reranker.rerank(standalone_query, chunks, top_k=retrieval_k)
        grade, good_chunks = await self._grader.grade(standalone_query, chunks)

        if grade == CRAGGrade.INCORRECT:
            yield StreamEvent(event="token", data="I couldn't find reliable information to answer your question.")
            yield StreamEvent(event="done", data={"cached": False, "grade": grade, "trace_id": trace_id})
            return

        if grade == CRAGGrade.AMBIGUOUS:
            sub_queries = await self._decomposer.decompose(standalone_query)
            extra = await self._crag.retrieve_and_merge(sub_queries, filters)
            good_chunks = self._deduplicate(good_chunks + extra)

        history = await self._memory.get_history(session_id)
        prompt_system, prompt_user = build_rag_prompt(
            query=standalone_query, chunks=good_chunks,
            query_type=query_type, history=history,
        )

        full_answer = ""
        stream = await self._llm.chat.completions.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user},
            ],
            stream=True,
        )
        async for chunk in stream:
            text = chunk.choices[0].delta.content or ""
            if text:
                full_answer += text
                yield StreamEvent(event="token", data=text)

        citations = self._extract_citations(good_chunks)
        full_answer = self._output_guard.redact(full_answer)

        await self._cache.set(standalone_query, full_answer)
        await self._memory.add_turn(session_id, "user", query)
        await self._memory.add_turn(session_id, "assistant", full_answer)

        yield StreamEvent(event="citations", data=[c.model_dump() for c in citations])
        yield StreamEvent(event="done", data={"cached": False, "grade": grade, "trace_id": trace_id})

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_citations(self, chunks: list[DocumentChunk]) -> list[Citation]:
        return [
            Citation(
                text=chunk.content[:200],
                source=chunk.source or chunk.metadata.get("source", "unknown"),
                chunk_id=chunk.id,
                score=chunk.score,
            )
            for chunk in chunks
        ]

    def _deduplicate(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        seen: set[str] = set()
        result = []
        for chunk in chunks:
            if chunk.id not in seen:
                seen.add(chunk.id)
                result.append(chunk)
        return result
