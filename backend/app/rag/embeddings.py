"""
AgentOps — Embedding Service
==============================

Generates vector embeddings from text using sentence-transformers.

WHAT ARE EMBEDDINGS?
--------------------
An embedding is a list of numbers (a vector) that represents the
"meaning" of a piece of text in a high-dimensional space.

Example:
  "I want a refund" → [0.12, -0.45, 0.33, ..., 0.71]  (384 numbers)
  "How do I get money back?" → [0.11, -0.43, 0.35, ..., 0.69]  (384 numbers)

These two vectors are VERY CLOSE in the 384-dimensional space because
they have similar semantic meaning — even though the words are different.

This is the magic that makes RAG work: we find "similar" chunks
mathematically, not by matching keywords.

MODEL: all-MiniLM-L6-v2
-----------------------
- 384-dimensional output
- ~80MB model size
- Fast on CPU (no GPU needed)
- Trained on 1B+ sentence pairs
- Industry standard for semantic search
"""

import os
import sys
from typing import List
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Lazy-loaded model (loaded once on first call)
_embedding_model = None


def get_embedding_model():
    """
    Load the embedding model (lazy initialization).
    
    Why lazy? Loading sentence-transformers takes a few seconds and
    downloads the model on first run. We only load it when needed.
    """
    global _embedding_model

    if _embedding_model is not None:
        return _embedding_model

    if settings.EMBEDDING_PROVIDER == "local":
        try:
            from fastembed import TextEmbedding
            logger.info("loading_embedding_model", model=settings.EMBEDDING_MODEL)
            # The model is strictly sentence-transformers/all-MiniLM-L6-v2
            # Since fastembed is highly optimized, it fits easily in 512MB RAM
            _embedding_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
            logger.info("embedding_model_loaded", model=settings.EMBEDDING_MODEL)
        except ImportError:
            logger.error(
                "fastembed_not_installed",
                hint="Run: pip install -r requirements-ml.txt"
            )
            raise
    elif settings.EMBEDDING_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        _embedding_model = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.EMBEDDING_API_KEY,
        )
    else:
        raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")

    return _embedding_model


def embed_text(text: str) -> List[float]:
    """
    Generate a 384-dimensional embedding for a single text string.
    
    Args:
        text: The text to embed
        
    Returns:
        List of 384 floats (the embedding vector)
    """
    model = get_embedding_model()

    if settings.EMBEDDING_PROVIDER == "local":
        # fastembed returns a generator of numpy arrays
        generator = model.embed([text])
        embedding = next(generator)
        return embedding.tolist()
    else:
        # LangChain OpenAI embeddings
        return model.embed_query(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts at once (more efficient).
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors (one per text)
    """
    model = get_embedding_model()

    if settings.EMBEDDING_PROVIDER == "local":
        # fastembed returns a generator
        generator = model.embed(texts)
        embeddings = [e.tolist() for e in generator]
        return embeddings
    else:
        return model.embed_documents(texts)
