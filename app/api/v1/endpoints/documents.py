from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    check_rate_limit,
    get_db,
    get_document_service,
)
from app.application.services.document_service import DocumentService
from app.domain.models.document import Document
from app.domain.schemas.document import DocumentCreateRequest, DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents & Ingestion"])


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_rate_limit)],
)
async def ingest_document(
    doc_in: DocumentCreateRequest,
    db: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Ingest document, chunk text, generate embeddings, and index into vector store."""
    try:
        doc = await service.ingest_document(session=db, doc_in=doc_in)
        return DocumentResponse.model_validate(doc)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed: {e}",
        ) from e


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[DocumentResponse]:
    """List indexed documents with pagination."""
    stmt = select(Document).offset(skip).limit(limit).order_by(Document.created_at.desc())
    result = await db.execute(stmt)
    docs = result.scalars().all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Retrieve document metadata by ID."""
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return DocumentResponse.model_validate(doc)
