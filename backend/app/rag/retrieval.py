"""
AgentOps — Semantic Search (RAG Retrieval)
============================================

At query time, find the most relevant document chunks using
vector similarity search via pgvector.

HOW COSINE SIMILARITY WORKS:
-----------------------------
Given user query: "What is the refund timeline?"
1. Embed query → vector Q  [0.12, -0.45, 0.33, ...]
2. For each stored chunk vector C, compute: cos(Q, C) = (Q · C) / (|Q| * |C|)
3. Return chunks with highest similarity (closest to 1.0)

Cosine similarity ranges from -1 to 1:
  1.0  = identical vectors (perfect match)
  0.0  = orthogonal (unrelated)
 -1.0  = opposite meanings

In practice, top results have similarity 0.6-0.9 for relevant chunks.

pgvector operator: <=> = cosine distance (1 - cosine_similarity)
So we ORDER BY embedding <=> query_embedding ASC (smallest distance = most similar)
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger
from app.models.document import DocumentChunk, Document
from app.rag.embeddings import embed_text

logger = get_logger(__name__)


def semantic_search(
    query: str,
    db: Session,
    top_k: int = None,
    doc_type_filter: Optional[str] = None,
    min_similarity: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Find the most semantically similar document chunks to a query.
    
    Args:
        query:           User's natural language question
        db:              Database session
        top_k:           Number of chunks to return (default from config)
        doc_type_filter: Optional filter by doc_type ("policy" | "faq")
        min_similarity:  Minimum similarity score to include (0-1)
    
    Returns:
        List of dicts with content, metadata, and similarity score
    """
    top_k = top_k or settings.RAG_TOP_K

    # Step 1: Embed the query
    logger.info("semantic_search_start", query=query[:100], top_k=top_k)
    query_embedding = embed_text(query)

    # Step 2: Build the pgvector similarity search query
    # We join with documents to get filename for citations
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    filter_clause = ""
    params = {
        "embedding": embedding_str,
        "top_k": top_k,
        "min_distance": 1 - min_similarity,  # Convert similarity to distance
    }

    if doc_type_filter:
        filter_clause = "AND d.doc_type = :doc_type"
        params["doc_type"] = doc_type_filter

    sql = text(f"""
        SELECT 
            dc.id,
            dc.content,
            dc.chunk_metadata,
            dc.chunk_index,
            d.filename,
            d.doc_type,
            1 - (dc.embedding <=> :embedding::vector) AS similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE dc.embedding IS NOT NULL
        {filter_clause}
            AND (dc.embedding <=> :embedding::vector) < :min_distance
        ORDER BY dc.embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    try:
        rows = db.execute(sql, params).fetchall()
    except Exception as e:
        logger.error("semantic_search_failed", error=str(e))
        return []

    results = []
    for row in rows:
        metadata = row.chunk_metadata or {}
        results.append({
            "id": str(row.id),
            "content": row.content,
            "filename": row.filename,
            "doc_type": row.doc_type,
            "section": metadata.get("section", "General"),
            "chunk_index": row.chunk_index,
            "similarity": round(float(row.similarity), 4),
            "metadata": metadata,
        })

    logger.info(
        "semantic_search_complete",
        query=query[:100],
        num_results=len(results),
        top_similarity=results[0]["similarity"] if results else 0,
    )
    return results
