import logging
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App Info
    APP_NAME: str = "nexus-rag-core"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "development-insecure-secret-key-32-chars-min"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    SEMANTIC_CACHE_TTL_SECONDS: int = 86400
    SEMANTIC_CACHE_THRESHOLD: float = 0.92

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120

    # AI / LLM Configuration
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = "mock-key"
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # RAG Settings
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    SIMILARITY_TOP_K: int = 5


settings = Settings()


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
