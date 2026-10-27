import hashlib
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.models.chunk import Chunk
from app.domain.models.document import Document
from app.domain.schemas.document import DocumentCreateRequest
from app.infrastructure.llm_provider import LLMProviderInterface
from app.infrastructure.vector_store import VectorStoreInterface

logger = logging.getLogger(__name__)


def compute_sha256(text: str) -> str:
    """Compute hex SHA-256 hash of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def recursive_character_chunker(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[str]:
    """Split text into overlapping chunks without splitting words unnecessarily."""
    if not text.strip():
        return []

    words = text.split()
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    for word in words:
        word_len = len(word) + 1  # word plus space
        if current_length + word_len > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Calculate overlap words
            overlap_words: list[str] = []
            overlap_len = 0
            for w in reversed(current_chunk):
                if overlap_len + len(w) + 1 <= chunk_overlap:
                    overlap_words.insert(0, w)
                    overlap_len += len(w) + 1
                else:
                    break
            current_chunk = overlap_words
            current_length = sum(len(w) + 1 for w in current_chunk)

        current_chunk.append(word)
        current_length += word_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


class DocumentService:
    def __init__(
        self,
        vector_store: VectorStoreInterface,
        llm_provider: LLMProviderInterface,
    ) -> None:
        self.vector_store = vector_store
        self.llm_provider = llm_provider

    async def ingest_document(
        self,
        session: AsyncSession,
        doc_in: DocumentCreateRequest,
    ) -> Document:
        """Process document: compute hash, chunk text, generate embeddings, and persist."""
        content_hash = compute_sha256(doc_in.content)

        # Create Document record
        doc = Document(
            title=doc_in.title,
            content_hash=content_hash,
            metadata_json=doc_in.metadata,
            status="processing",
            chunk_count=0,
        )
        session.add(doc)
        await session.flush()

        # Chunk content
        raw_chunks = recursive_character_chunker(
            doc_in.content,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        chunks: list[Chunk] = []
        for idx, text_chunk in enumerate(raw_chunks):
            # Compute dense embedding
            embedding = await self.llm_provider.get_embedding(text_chunk)
            chunk = Chunk(
                document_id=doc.id,
                chunk_index=idx,
                content=text_chunk,
                embedding=embedding,
                token_count=len(text_chunk.split()),
            )
            chunks.append(chunk)

        # Store in vector store
        await self.vector_store.add_chunks(session, chunks)

        doc.chunk_count = len(chunks)
        doc.status = "indexed"
        await session.flush()

        logger.info(f"Ingested document {doc.id} ('{doc.title}') with {len(chunks)} chunks.")
        return doc
