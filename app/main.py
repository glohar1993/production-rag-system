"""FastAPI runtime application — entry point."""
import structlog
import opik
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import get_settings
from routes.query import router as query_router
from routes.search import router as search_router
from routes.health import router as health_router

log = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    log.info("Starting Production RAG System", env=settings.env)

    # Configure observability
    if settings.opik_api_key:
        opik.configure(api_key=settings.opik_api_key, project_name=settings.opik_project)
        log.info("OPIK tracing enabled", project=settings.opik_project)

    # Warm up models (lazy import triggers download on first use)
    from services.semantic_cache import SemanticCache
    from retrieval.hybrid_retriever import HybridRetriever
    from retrieval.reranker import Reranker

    app.state.cache = SemanticCache()
    app.state.retriever = HybridRetriever()
    app.state.reranker = Reranker()

    log.info("All components initialized")
    yield
    log.info("Shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.env != "production" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(query_router, prefix="/api")
    app.include_router(search_router, prefix="/api")
    app.include_router(health_router)

    # Serve frontend
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/", include_in_schema=False)
        async def frontend():
            return FileResponse(os.path.join(static_dir, "index.html"))

    return app


app = create_app()
