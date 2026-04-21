"""CRAG document grader — rates retrieved chunk relevance."""
from __future__ import annotations
import structlog
import openai
from app.config import get_settings
from app.models import CRAGGrade, DocumentChunk
from prompts.grading import RELEVANCE_GRADE_PROMPT

log = structlog.get_logger(__name__)
settings = get_settings()


class DocumentGrader:
    """
    For each retrieved chunk, asks the LLM: is this chunk relevant to the query?
    Aggregates chunk-level grades into a document-level CRAGGrade.
    """

    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def grade_chunk(self, query: str, chunk: DocumentChunk) -> float:
        """Returns relevance score 0.0–1.0 for a single chunk."""
        prompt = (
            f"Query: {query}\n\n"
            f"Document chunk:\n{chunk.content[:1000]}\n\n"
            f"Rate relevance 0.0 to 1.0 (output only the number):"
        )
        response = await self._client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=10,
            temperature=0.0,
            messages=[
                {"role": "system", "content": RELEVANCE_GRADE_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        try:
            return float((response.choices[0].message.content or "").strip())
        except ValueError:
            return 0.5

    async def grade(self, query: str, chunks: list[DocumentChunk]) -> tuple[CRAGGrade, list[DocumentChunk]]:
        """
        Grades all chunks and returns:
          - CRAGGrade.CORRECT   → enough relevant chunks found
          - CRAGGrade.AMBIGUOUS → some relevant, some not
          - CRAGGrade.INCORRECT → no relevant chunks
        Also filters out clearly irrelevant chunks.
        """
        threshold = settings.crag_relevance_threshold

        scored: list[tuple[float, DocumentChunk]] = []
        for chunk in chunks:
            score = await self.grade_chunk(query, chunk)
            scored.append((score, chunk))

        relevant = [(s, c) for s, c in scored if s >= threshold]
        good_chunks = [c for _, c in sorted(relevant, key=lambda x: x[0], reverse=True)]

        n_relevant = len(relevant)

        # Grade by absolute relevant count, not ratio.
        # Ratio-based grading breaks for focused corpora where most docs are
        # intentionally about different topics (only 1-2 will ever be relevant).
        if n_relevant >= 2:
            grade = CRAGGrade.CORRECT
        elif n_relevant == 1:
            grade = CRAGGrade.AMBIGUOUS
        else:
            grade = CRAGGrade.INCORRECT

        log.info("crag_grade", grade=grade, relevant=len(relevant), total=len(chunks))
        return grade, good_chunks
