"""
AgentOps — RAG Ingestion Pipeline
====================================

Reads knowledge documents, chunks them, generates embeddings,
and stores them in Supabase's pgvector table.

PIPELINE:
---------
knowledge/*.txt
  |
  v
Read file text
  |
  v
Chunk into ~500 char segments with overlap
  |
  v
Generate 384-dim embedding per chunk
  |
  v
Store in document_chunks table (with VECTOR(384) column)
  |
  v (at query time)
semantic_search() → top-k chunks → LLM context

WHY RUN THIS ONCE?
------------------
Ingestion is expensive (generates many embeddings).
We run it once, store results in DB, and query at runtime.
If documents change, re-run ingestion to update embeddings.
"""

import os
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.document import Document, DocumentChunk
from app.rag.chunking import chunk_document
from app.rag.embeddings import embed_texts

logger = get_logger(__name__)

# Path to the knowledge directory
KNOWLEDGE_DIR = Path(__file__).parent.parent.parent.parent / "knowledge"


def ingest_knowledge_documents(db: Session, force: bool = False) -> dict:
    """
    Ingest all .txt files from the knowledge directory into the RAG store.
    
    Args:
        db:    Database session
        force: If True, re-ingest even if already exists
    
    Returns:
        Summary dict: {"total_chunks": int, "documents": list}
    """
    if not KNOWLEDGE_DIR.exists():
        logger.error("knowledge_dir_not_found", path=str(KNOWLEDGE_DIR))
        raise FileNotFoundError(f"Knowledge directory not found: {KNOWLEDGE_DIR}")

    txt_files = list(KNOWLEDGE_DIR.glob("*.txt"))
    if not txt_files:
        logger.warning("no_knowledge_files_found", path=str(KNOWLEDGE_DIR))
        return {"total_chunks": 0, "documents": []}

    logger.info("starting_ingestion", num_files=len(txt_files))
    results = []
    total_chunks = 0

    for filepath in txt_files:
        filename = filepath.name
        doc_type = _detect_doc_type(filename)

        # Check if already ingested
        existing = db.query(Document).filter(Document.filename == filename).first()
        if existing and not force:
            logger.info("skipping_already_ingested", filename=filename)
            results.append({"filename": filename, "chunks": existing.chunk_count, "status": "skipped"})
            total_chunks += existing.chunk_count
            continue

        # Delete existing if force re-ingest
        if existing and force:
            db.delete(existing)
            db.flush()

        try:
            text = filepath.read_text(encoding="utf-8")
            logger.info("ingesting_document", filename=filename, chars=len(text))

            # Create Document record
            doc = Document(
                filename=filename,
                doc_type=doc_type,
                char_count=len(text),
                chunk_count=0,
            )
            db.add(doc)
            db.flush()  # Get doc.id

            # Chunk the document
            chunks = chunk_document(text, filename, doc_type)

            # Generate all embeddings in one batch (more efficient)
            chunk_texts = [c["content"] for c in chunks]
            embeddings = embed_texts(chunk_texts)

            # Store chunks with embeddings
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    content=chunk["content"],
                    embedding=embedding,
                    chunk_metadata=chunk["metadata"],
                    chunk_index=i,
                )
                db.add(db_chunk)

            doc.chunk_count = len(chunks)
            db.flush()

            total_chunks += len(chunks)
            results.append({"filename": filename, "chunks": len(chunks), "status": "ingested"})
            logger.info("document_ingested", filename=filename, chunks=len(chunks))

        except Exception as e:
            logger.error("ingestion_failed", filename=filename, error=str(e))
            results.append({"filename": filename, "chunks": 0, "status": "failed", "error": str(e)})

    db.commit()
    logger.info("ingestion_complete", total_chunks=total_chunks, documents=len(results))
    return {"total_chunks": total_chunks, "documents": results}


def _detect_doc_type(filename: str) -> str:
    """Detect document type from filename."""
    name = filename.lower()
    if "faq" in name:
        return "faq"
    elif "policy" in name or "policy" in name:
        return "policy"
    elif "manual" in name or "guide" in name:
        return "manual"
    return "policy"
