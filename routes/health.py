"""Health check route — readiness + dependency checks."""
import time
import asyncio
import structlog
from fastapi import APIRouter
from app.models import HealthResponse, ComponentStatus
from app.config import get_settings

log = structlog.get_logger(__name__)
router = APIRouter(tags=["health"])
settings = get_settings()


async def _check_qdrant() -> ComponentStatus:
    start = time.perf_counter()
    try:
        from qdrant_client import AsyncQdrantClient
        client = AsyncQdrantClient(url=settings.qdrant_url, check_compatibility=False)
        await client.get_collections()
        return ComponentStatus(name="qdrant", healthy=True,
                               latency_ms=(time.perf_counter() - start) * 1000)
    except Exception as e:
        return ComponentStatus(name="qdrant", healthy=False, detail=str(e))


async def _check_redis() -> ComponentStatus:
    start = time.perf_counter()
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        return ComponentStatus(name="redis", healthy=True,
                               latency_ms=(time.perf_counter() - start) * 1000)
    except Exception as e:
        return ComponentStatus(name="redis", healthy=False, detail=str(e))


async def _check_llm() -> ComponentStatus:
    start = time.perf_counter()
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        await client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=10,
            messages=[{"role": "user", "content": "ping"}],
        )
        return ComponentStatus(name="llm", healthy=True,
                               latency_ms=(time.perf_counter() - start) * 1000)
    except Exception as e:
        return ComponentStatus(name="llm", healthy=False, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health():
    results = await asyncio.gather(_check_qdrant(), _check_redis(), _check_llm())
    all_healthy = all(c.healthy for c in results)
    status = "ok" if all_healthy else "degraded"
    log.info("health_check", status=status)
    return HealthResponse(status=status, components=list(results))


@router.get("/health/live")
async def liveness():
    """Kubernetes liveness probe — just confirms process is alive."""
    return {"status": "alive"}
