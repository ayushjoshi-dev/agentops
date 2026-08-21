"""
AgentOps — Core Configuration
==============================

This module loads all environment variables using Pydantic Settings.

WHY PYDANTIC SETTINGS?
----------------------
pydantic-settings reads from .env files AND environment variables.
It validates types automatically (e.g., int, bool, list).
If a required variable is missing, it raises a clear error at startup —
not silently failing at runtime when the value is first used.

IMPORTANT:
----------
This is the SINGLE SOURCE OF TRUTH for all config.
Never read os.environ directly in other modules.
Always import from here: from app.core.config import settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.
    
    All fields have defaults for development — override in production
    using environment variables on Render.
    """

    # ── Application ───────────────────────────────────────
    APP_ENV: str = "development"
    APP_NAME: str = "AgentOps"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # ── Server ────────────────────────────────────────────
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS origins — comma-separated string in .env, parsed to list
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # ── Database (Supabase PostgreSQL) ────────────────────
    DATABASE_URL: str = Field(
        ...,  # Required — must be set in .env
        description="PostgreSQL connection string from Supabase"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # ── LLM Provider ──────────────────────────────────────
    LLM_PROVIDER: str = "groq"   # "groq" | "openai"
    LLM_API_KEY: str = Field(..., description="API key for LLM provider")
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_MAX_TOKENS: int = 2048
    LLM_TEMPERATURE: float = 0.1

    # ── Embeddings ────────────────────────────────────────
    EMBEDDING_PROVIDER: str = "local"   # "local" | "openai"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_API_KEY: str = ""   # Only needed if EMBEDDING_PROVIDER=openai

    # ── Authentication ────────────────────────────────────
    JWT_SECRET: str = Field(
        default_factory=lambda: secrets.token_hex(32),  # Auto-generate if not set
        description="Secret key for JWT signing — MUST be set in production"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24

    # ── RAG ───────────────────────────────────────────────
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5

    # ── Agent ─────────────────────────────────────────────
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 60

    # ── Pydantic Settings Configuration ──────────────────
    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file in backend/
        env_file_encoding="utf-8",
        case_sensitive=True,       # DATABASE_URL ≠ database_url
        extra="ignore",            # Ignore unknown env vars (don't error)
    )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


# ── Singleton Instance ────────────────────────────────────
# Import this everywhere: from app.core.config import settings
settings = Settings()
