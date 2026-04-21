"""Query route — SSE streaming + standard JSON."""
import json
import time
import uuid
import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.models import QueryRequest, QueryResponse, StreamEvent
from security.input_guard import InputGuard
from security.output_guard import OutputGuard
from services.rag_pipeline import RAGPipeline

log = structlog.get_logger(__name__)
router = APIRouter(tags=["query"])

input_guard = InputGuard()
output_guard = OutputGuard()
pipeline = RAGPipeline()


@router.post("/query")
async def query(request: QueryRequest, req: Request) -> QueryResponse:
    """Standard JSON query — returns full answer once complete."""
    trace_id = str(uuid.uuid4())
    start = time.perf_counter()

    # 1. Input guard
    safe_query = input_guard.sanitize(request.query)

    # 2. Full pipeline (non-streaming)
    result = await pipeline.run(
        query=safe_query,
        session_id=request.session_id,
        top_k=request.top_k,
        filters=request.filters,
        trace_id=trace_id,
    )

    # 3. Output guard
    result.answer = output_guard.redact(result.answer)
    result.trace_id = trace_id
    result.latency_ms = (time.perf_counter() - start) * 1000

    log.info("query_complete", trace_id=trace_id, cached=result.cached,
             grade=result.crag_grade, latency_ms=result.latency_ms)
    return result


@router.post("/query/stream")
async def query_stream(request: QueryRequest):
    """SSE streaming query — yields tokens as they arrive."""
    trace_id = str(uuid.uuid4())

    safe_query = input_guard.sanitize(request.query)

    async def event_generator():
        try:
            async for event in pipeline.stream(
                query=safe_query,
                session_id=request.session_id,
                top_k=request.top_k,
                filters=request.filters,
                trace_id=trace_id,
            ):
                if event.event == "token":
                    yield {"event": "token", "data": event.data}
                elif event.event == "citations":
                    yield {"event": "citations", "data": json.dumps(event.data)}
                elif event.event == "done":
                    yield {"event": "done", "data": json.dumps(event.data)}
                elif event.event == "error":
                    yield {"event": "error", "data": str(event.data)}
        except Exception as exc:
            log.error("stream_error", trace_id=trace_id, error=str(exc))
            yield {"event": "error", "data": str(exc)}

    return EventSourceResponse(event_generator())
