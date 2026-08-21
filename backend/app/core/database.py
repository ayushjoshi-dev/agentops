"""
AgentOps — Database Connection
================================

WHY SQLALCHEMY?
---------------
SQLAlchemy is the standard Python ORM (Object Relational Mapper).
It lets us:
- Define tables as Python classes (models)
- Write queries in Python instead of raw SQL
- Handle connection pooling
- Run database migrations via Alembic

We use SQLAlchemy's ASYNC engine with psycopg2 for Supabase PostgreSQL.

ABOUT CONNECTION POOLING:
--------------------------
Supabase has a limited number of connections on the free tier (~20).
Connection pooling reuses existing connections instead of opening a new one
per request. This is critical for production.

We configure:
- pool_size: Number of persistent connections to keep open
- max_overflow: Extra connections allowed beyond pool_size during spikes
- pool_timeout: How long to wait for a connection from the pool

For Supabase, enable "Connection Pooling" in the Supabase dashboard
and use the pooler connection string (port 6543, not 5432).
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── SQLAlchemy Engine ─────────────────────────────────────
# The engine manages the connection pool to the database.
# We create ONE engine for the entire application lifetime.
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,     # Test connections before using them (catches stale connections)
    echo=settings.is_development,  # Log SQL queries in development
)


# ── Session Factory ───────────────────────────────────────
# SessionLocal() creates a new database session.
# A session is a "unit of work" — it tracks changes and commits them.
SessionLocal = sessionmaker(
    autocommit=False,   # We control commits manually
    autoflush=False,    # Don't flush until we commit
    bind=engine,
)


# ── Base Class ────────────────────────────────────────────
# All SQLAlchemy models inherit from this class.
# WHY DeclarativeBase? It lets SQLAlchemy know which Python classes are tables.
class Base(DeclarativeBase):
    pass


# ── Dependency Injection ──────────────────────────────────
# This is the FastAPI way to inject a database session into route handlers.
# 
# FastAPI calls get_db() for each request.
# The `yield` makes it a context manager:
#   - Before yield: opens the session
#   - After yield: closes the session (even if an exception occurred)
def get_db() -> Generator:
    """
    FastAPI dependency that provides a database session per request.
    
    Usage in route:
        @router.get("/orders")
        def get_orders(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Test that the database is reachable.
    Called during application startup health check.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("database_connected", url=settings.DATABASE_URL.split("@")[-1])
        return True
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        return False
