"""
AgentOps — Unit Tests for RAG Chunking Logic
=============================================
Tests document chunking without needing DB or embeddings.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import pytest


class TestDocumentChunking:
    """Tests for the chunking logic in app/rag/chunking.py."""

    def test_short_text_produces_single_chunk(self):
        from app.rag.chunking import chunk_document
        text = "This is a short policy document."
        chunks = chunk_document(text, "test.txt", "policy")
        assert len(chunks) >= 1

    def test_long_text_produces_multiple_chunks(self):
        from app.rag.chunking import chunk_document
        # 600 chars > typical chunk size of ~500
        text = "A" * 600
        chunks = chunk_document(text, "test.txt", "policy")
        assert len(chunks) >= 2

    def test_each_chunk_has_content_field(self):
        from app.rag.chunking import chunk_document
        text = "This is a valid document with some reasonable content."
        chunks = chunk_document(text, "test.txt", "faq")
        for chunk in chunks:
            assert "content" in chunk
            assert len(chunk["content"]) > 0

    def test_each_chunk_has_metadata(self):
        from app.rag.chunking import chunk_document
        text = "This is a valid document with some reasonable content."
        chunks = chunk_document(text, "test.txt", "policy")
        for chunk in chunks:
            assert "metadata" in chunk

    def test_empty_text_handled_gracefully(self):
        from app.rag.chunking import chunk_document
        chunks = chunk_document("", "test.txt", "policy")
        assert isinstance(chunks, list)


class TestSemanticSearchWithMockedDB:
    """Tests for semantic_search function using a mocked DB."""

    def test_returns_empty_list_on_db_error(self, mock_db):
        from unittest.mock import patch
        from app.rag.retrieval import semantic_search

        # Make execute raise an error
        mock_db.execute.side_effect = Exception("DB connection failed")

        with patch("app.rag.retrieval.embed_text", return_value=[0.1] * 384):
            results = semantic_search("refund policy", mock_db, top_k=5)

        assert results == []

    def test_returns_results_on_success(self, mock_db):
        from unittest.mock import patch, MagicMock
        from app.rag.retrieval import semantic_search

        mock_row = MagicMock()
        mock_row.id = "chunk-uuid-001"
        mock_row.content = "You can return products within 7 days of delivery."
        mock_row.chunk_metadata = {"section": "Return Policy"}
        mock_row.chunk_index = 0
        mock_row.filename = "return_policy.txt"
        mock_row.doc_type = "policy"
        mock_row.similarity = 0.85

        mock_db.execute.side_effect = None
        mock_db.execute.return_value = MagicMock(fetchall=lambda: [mock_row])

        with patch("app.rag.retrieval.embed_text", return_value=[0.1] * 384):
            results = semantic_search("return policy", mock_db, top_k=5)

        assert len(results) == 1
        assert results[0]["filename"] == "return_policy.txt"
        assert "return" in results[0]["content"].lower()
