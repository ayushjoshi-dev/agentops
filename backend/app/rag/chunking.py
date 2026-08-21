"""
AgentOps — Document Chunking
==============================

WHY CHUNK DOCUMENTS?
--------------------
LLMs have a limited context window (e.g. 8K tokens).
We cannot dump an entire 50-page policy document into the prompt.

Instead we:
1. Split documents into small overlapping chunks (~500 chars)
2. Store each chunk with its embedding
3. At query time, retrieve only the 5 most relevant chunks

CHUNK SIZE vs OVERLAP:
----------------------
chunk_size=500 → Each chunk is ~500 characters (~100 words)
overlap=50     → Each chunk shares 50 chars with the next chunk

WHY OVERLAP?
------------
Prevents important context from being split across two chunks.
A sentence that starts at the end of chunk N continues in chunk N+1.
Without overlap, the retrieval system might miss the full context.

RECURSIVE CHARACTER SPLITTER:
------------------------------
LangChain's RecursiveCharacterTextSplitter tries to split on:
1. Double newlines (paragraph breaks)
2. Single newlines
3. Spaces
4. Characters

This preserves natural text boundaries rather than cutting mid-sentence.
"""

from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def chunk_document(
    text: str,
    filename: str,
    doc_type: str = "policy",
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Dict[str, Any]]:
    """
    Split a document into overlapping chunks with metadata.
    
    Args:
        text:         Full document text
        filename:     Source filename (for citations)
        doc_type:     Document type: "policy" | "faq" | "manual"
        chunk_size:   Characters per chunk (default from config)
        chunk_overlap: Overlap characters (default from config)
    
    Returns:
        List of dicts: [{"content": str, "metadata": dict}, ...]
    """
    chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    raw_chunks = splitter.split_text(text)

    chunks = []
    for i, chunk_text in enumerate(raw_chunks):
        chunk_text = chunk_text.strip()
        if not chunk_text:
            continue

        chunks.append({
            "content": chunk_text,
            "metadata": {
                "source": filename,
                "doc_type": doc_type,
                "chunk_index": i,
                "total_chunks": len(raw_chunks),
                # Section detection — simple heuristic
                "section": _detect_section(chunk_text),
            }
        })

    logger.info(
        "document_chunked",
        filename=filename,
        total_chars=len(text),
        num_chunks=len(chunks),
        chunk_size=chunk_size,
        overlap=chunk_overlap,
    )
    return chunks


def _detect_section(text: str) -> str:
    """
    Try to detect the section name from the chunk text.
    Looks for ALL-CAPS lines or lines ending with ':' as section headers.
    """
    lines = text.strip().split("\n")
    for line in lines[:3]:  # Check first 3 lines
        line = line.strip()
        if not line:
            continue
        # All caps with no punctuation = likely a header
        if line.isupper() and len(line) < 80:
            return line
        # Line ending with colon = likely a header
        if line.endswith(":") and len(line) < 80 and not line.startswith(" "):
            return line.rstrip(":")
    return "General"
