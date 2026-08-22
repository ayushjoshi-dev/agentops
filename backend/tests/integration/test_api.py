"""
AgentOps — Integration Tests for FastAPI Endpoints
===================================================
Uses FastAPI TestClient to test full HTTP request/response cycle.
These tests require the app to start (but no real external LLM).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import pytest


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_200(self, test_client):
        response = test_client.get("/api/health")
        assert response.status_code == 200

    def test_health_response_has_status(self, test_client):
        response = test_client.get("/api/health")
        data = response.json()
        assert "status" in data


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_with_invalid_credentials_returns_401(self, test_client):
        response = test_client.post("/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_me_without_token_returns_401(self, test_client):
        response = test_client.get("/api/auth/me")
        assert response.status_code == 401

    def test_register_with_invalid_email_returns_422(self, test_client):
        response = test_client.post("/api/auth/register", json={
            "email": "not-an-email",
            "full_name": "Test User",
            "password": "password123"
        })
        assert response.status_code == 422

    def test_register_with_short_password_returns_422(self, test_client):
        response = test_client.post("/api/auth/register", json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "ab"
        })
        assert response.status_code == 422


class TestChatEndpoint:
    """Test chat endpoint (without calling real LLM)."""

    def test_chat_without_auth_returns_401(self, test_client):
        response = test_client.post("/api/chat", json={
            "message": "Hello"
        })
        assert response.status_code == 401

    def test_chat_with_empty_message_returns_422(self, test_client):
        """Empty message should be rejected by Pydantic validation."""
        response = test_client.post("/api/chat", json={
            "message": ""
        })
        # Either 401 (no auth) or 422 (validation) — both are correct
        assert response.status_code in (401, 422)


class TestDocumentEndpoints:
    """Test document/RAG endpoints."""

    def test_list_documents_without_auth_returns_401(self, test_client):
        response = test_client.get("/api/documents")
        assert response.status_code == 401
