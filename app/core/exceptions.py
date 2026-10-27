from typing import Any


class AppBaseException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundError(AppBaseException):
    """Raised when an entity is not found in database."""

    pass


class DocumentProcessingError(AppBaseException):
    """Raised when document ingestion or chunking fails."""

    pass


class VectorSearchError(AppBaseException):
    """Raised when vector similarity search fails."""

    pass


class RateLimitExceededError(AppBaseException):
    """Raised when API client exceeds allocated rate limit."""

    pass


class LLMServiceError(AppBaseException):
    """Raised when external LLM provider fails."""

    pass
