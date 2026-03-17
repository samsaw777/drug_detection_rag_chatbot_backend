"""
APDP Backend — Entry Point
Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langsmith import Client as LangSmithClient
from langsmith import traceable

import logging

from config import get_settings
from routes import api_router, main_router
from Agents.query_analyser import QueryAnalyserAgent


logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: build the async agent. Shutdown: cleanup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    app.state.agent = await QueryAnalyserAgent.create()
    logger.info("QueryAnalyserAgent ready")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agentic Data Processing Platform",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def langsmith_trace_middleware(request: Request, call_next):
    """
    Wraps every incoming HTTP request in a LangSmith trace.
    You'll see each request as a run in your LangSmith dashboard
    with the route, method, status code, and latency.
    """

    @traceable(
        name=f"{request.method} {request.url.path}",
        run_type="chain",
        tags=["http", request.method.lower()],
        metadata={
            "route": request.url.path,
            "method": request.method,
            "project": settings.LANGCHAIN_PROJECT,
        },
    )
    async def traced_request():
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} ({duration_ms}ms)"
        )
        return response

    return await traced_request()

# Register routes
app.include_router(api_router)
app.include_router(main_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )