import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings, setup_logging
from app.core.exceptions import AppBaseException
from app.infrastructure.database import close_db, init_db
from app.infrastructure.redis import close_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management for database and connection pools."""
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] environment...")

    # Initialize tables (safe no-op if Alembic manages schemas)
    await init_db()

    yield

    logger.info("Gracefully shutting down connections...")
    await close_redis()
    await close_db()
    logger.info("Shutdown completed successfully.")


app = FastAPI(
    title="NexusRAG Core — Enterprise AI & Semantic Retrieval Engine",
    description=(
        "Production-grade Asynchronous RAG Backend Architecture featuring Clean Architecture, "
        "PostgreSQL (pgvector), Redis Semantic Caching, Distributed Rate Limiting, and Automated CI/CD."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppBaseException)
async def custom_app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.message, "details": exc.details},
    )


# Register API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root_endpoint() -> dict[str, str]:
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }
