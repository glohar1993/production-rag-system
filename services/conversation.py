"""Sliding-window conversation memory backed by Redis."""
from __future__ import annotations
import json
import redis.asyncio as aioredis
import structlog
from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()


class ConversationMemory:
    """
    Stores last N turns per session_id in Redis as a JSON list.
    Rewrites follow-up queries into standalone queries using conversation history.
    """

    def __init__(self) -> None:
        self._redis: aioredis.Redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        self._window = settings.conversation_window

    def _key(self, session_id: str) -> str:
        return f"conv:{session_id}"

    async def get_history(self, session_id: str) -> list[dict]:
        raw = await self._redis.get(self._key(session_id))
        if not raw:
            return []
        return json.loads(raw)[-self._window * 2:]  # keep last N turns (user+assistant)

    async def add_turn(self, session_id: str, role: str, content: str) -> None:
        history = await self.get_history(session_id)
        history.append({"role": role, "content": content})
        await self._redis.setex(
            self._key(session_id),
            86400,  # 24h TTL
            json.dumps(history),
        )

    async def rewrite_query(self, session_id: str, query: str, llm_client) -> str:
        """
        If there's conversation history, rewrite the follow-up query into a
        standalone query using the LLM.
        """
        history = await self.get_history(session_id)
        if not history:
            return query

        history_text = "\n".join(
            f"{turn['role'].upper()}: {turn['content']}" for turn in history[-4:]
        )

        prompt = (
            f"Given this conversation history:\n{history_text}\n\n"
            f"Rewrite the follow-up question as a standalone question that captures "
            f"all necessary context.\n\nFollow-up question: {query}\n\n"
            f"Standalone question (output ONLY the rewritten question):"
        )

        response = await llm_client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=256,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        rewritten = (response.choices[0].message.content or "").strip()
        log.info("query_rewritten", original=query, rewritten=rewritten, session=session_id)
        return rewritten

    async def clear(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))
