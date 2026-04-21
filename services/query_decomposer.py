"""Query decomposer — breaks complex queries into atomic sub-queries (CRAG gap filling)."""
from __future__ import annotations
import structlog
import openai
from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()


class QueryDecomposer:
    """
    When CRAG grades retrieval as AMBIGUOUS, decomposes the original query
    into 2–4 sub-queries to fill knowledge gaps via targeted re-retrieval.
    """

    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def decompose(self, query: str, gap_context: str = "") -> list[str]:
        """Returns a list of focused sub-queries."""
        system = (
            "You are a query decomposition expert. Break the user's complex question "
            "into 2-4 specific, atomic sub-questions that together cover all aspects. "
            "Output ONLY a JSON array of strings, no explanation."
        )
        context_note = f"\nContext of what was already found: {gap_context}" if gap_context else ""
        user_msg = f"Original question: {query}{context_note}"

        response = await self._client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=256,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
        )

        import json
        try:
            sub_queries = json.loads((response.choices[0].message.content or "").strip())
            assert isinstance(sub_queries, list)
        except (json.JSONDecodeError, AssertionError):
            # Fallback: treat original query as single sub-query
            sub_queries = [query]

        log.info("query_decomposed", original=query[:60], sub_queries=sub_queries)
        return sub_queries
