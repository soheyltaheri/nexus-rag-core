from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(..., min_length=1, description="Raw document text content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata tags")


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chunk_index: int
    content: str
    token_count: int


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content_hash: str
    metadata_json: dict[str, Any]
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime
