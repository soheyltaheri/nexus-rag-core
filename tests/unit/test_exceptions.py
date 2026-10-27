from app.core.exceptions import (
    AppBaseException,
    DocumentProcessingError,
    EntityNotFoundError,
    LLMServiceError,
    RateLimitExceededError,
    VectorSearchError,
)


def test_exception_hierarchy() -> None:
    e1 = EntityNotFoundError("Doc not found", details={"id": "123"})
    assert isinstance(e1, AppBaseException)
    assert e1.message == "Doc not found"
    assert e1.details["id"] == "123"

    e2 = DocumentProcessingError("Chunk failed")
    assert isinstance(e2, AppBaseException)

    e3 = VectorSearchError("Search timeout")
    assert isinstance(e3, AppBaseException)

    e4 = RateLimitExceededError("Too fast")
    assert isinstance(e4, AppBaseException)

    e5 = LLMServiceError("API down")
    assert isinstance(e5, AppBaseException)
