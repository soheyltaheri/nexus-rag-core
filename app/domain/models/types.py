import json
from typing import Any

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

try:
    from pgvector.sqlalchemy import Vector as PGVector
except ImportError:
    PGVector = None  # type: ignore


class VectorType(TypeDecorator):
    """Platform-independent Vector type.

    Uses native PostgreSQL pgvector Vector when on postgresql,
    and falls back to JSON-serialized Text for SQLite/unit testing.
    """

    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 1536, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql" and PGVector is not None:
            return dialect.type_descriptor(PGVector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql" and PGVector is not None:
            return value
        return json.dumps(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql" and PGVector is not None:
            return list(value)
        if isinstance(value, str):
            return json.loads(value)
        return list(value)
