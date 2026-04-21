"""Query router — classifies query type and selects the right prompt template."""
from __future__ import annotations
import structlog
import openai
from app.config import get_settings
from app.models import QueryType
from prompts.templates import ROUTING_PROMPT

log = structlog.get_logger(__name__)
settings = get_settings()


class QueryRouter:
    """
    Classifies incoming queries into QueryType so the pipeline can
    select the appropriate retrieval strategy and prompt template.
    """

    _TYPE_MAP = {
        "factual": QueryType.FACTUAL,
        "analytical": QueryType.ANALYTICAL,
        "conversational": QueryType.CONVERSATIONAL,
        "code": QueryType.CODE,
        "multi_hop": QueryType.MULTI_HOP,
    }

    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def classify(self, query: str) -> QueryType:
        """Return the query type for routing decisions."""
        response = await self._client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=20,
            temperature=0.0,
            messages=[
                {"role": "system", "content": ROUTING_PROMPT},
                {"role": "user", "content": query},
            ],
        )
        label = (response.choices[0].message.content or "").strip().lower()
        query_type = self._TYPE_MAP.get(label, QueryType.FACTUAL)
        log.info("query_classified", query=query[:60], type=query_type)
        return query_type

    def top_k_for_type(self, query_type: QueryType, base_k: int) -> int:
        """Analytical and multi-hop queries need more context."""
        multipliers = {
            QueryType.MULTI_HOP: 3,
            QueryType.ANALYTICAL: 2,
            QueryType.CODE: 2,
            QueryType.FACTUAL: 1,
            QueryType.CONVERSATIONAL: 1,
        }
        return base_k * multipliers.get(query_type, 1)
