"""
AgentOps — Document & DocumentChunk Models (RAG Storage)
==========================================================

These two tables power the RAG (Retrieval Augmented Generation) system.

WHAT IS RAG?
------------
Instead of asking the LLM "what is your refund policy?" and hoping it
knows (it doesn't — it wasn't trained on ShopEase's policies), we:

1. Pre-process all policy documents into small chunks
2. Generate vector embeddings for each chunk
3. At query time, find the most similar chunks to the user's question
4. Pass those chunks as context to the LLM
5. LLM generates an answer grounded in the real documents

Document
  ↓ (1 document has many chunks)
DocumentChunk
  ↓ (each chunk has a vector embedding)
pgvector similarity search
  ↓ (find top-5 most relevant chunks)
LLM context window

WHAT IS A VECTOR EMBEDDING?
----------------------------
A text embedding is a list of ~384 numbers (floats) that represent the
"meaning" of the text in a mathematical space.

Similar meanings → similar vectors → close in vector space.

"I want a refund" and "How do I get my money back?" have similar embeddings
even though they use completely different words.

pgvector stores these embeddings and can find nearest neighbors efficiently
using cosine similarity or Euclidean distance.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base

# pgvector SQLAlchemy type
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None


class Document(Base):
    """
    Documents table — one row per source file.
    
    e.g.:
    - refund_policy.txt
    - shipping_policy.txt
    - faq.txt
    """
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Original filename e.g. refund_policy.txt"
    )

    doc_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Document type: policy | faq | manual"
    )

    # Total characters in document (before chunking)
    char_count: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )

    # How many chunks were created
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ── Relationships ─────────────────────────────────────
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document {self.filename} chunks={self.chunk_count}>"


class DocumentChunk(Base):
    """
    Document chunks table — one row per text chunk, with vector embedding.
    
    This is the core of the RAG system. Each chunk is a ~500 character
    segment of a policy document, with a 384-dimensional embedding vector.
    
    At query time, we find the chunks whose embeddings are most similar
    to the user's query embedding.
    """
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # The actual text content of this chunk
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Text content of this chunk"
    )

    # ── pgvector Embedding ────────────────────────────────
    # This is the key field — a 384-dimensional float vector.
    # Vector(384) tells pgvector the dimension.
    # WHY 384? The all-MiniLM-L6-v2 model outputs 384-dim vectors.
    embedding = mapped_column(
        Vector(384) if PGVECTOR_AVAILABLE else Text,
        nullable=True,  # Nullable during ingestion pipeline
        comment="384-dim sentence embedding for semantic search"
    )

    # ── Metadata ──────────────────────────────────────────
    # Stores: source filename, section name, chunk index, etc.
    # Used for citations: "Source: refund_policy.txt — Section: Eligibility"
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Chunk metadata: source, section, chunk_index, doc_type"
    )

    # Position of this chunk within the document (0-indexed)
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ── Relationships ─────────────────────────────────────
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<DocumentChunk doc={self.document_id} index={self.chunk_index}>"
