"""
AgentOps — User Model
======================

WHY THIS FILE?
--------------
This is a SQLAlchemy model — it defines the `users` table in Python.
When Alembic runs migrations, it reads this class and creates the actual
SQL table in Supabase.

WHAT IS A MODEL?
----------------
A model is a Python class that represents a database table.
Each attribute = one column in the table.

Example:
    User.email  →  users.email  (VARCHAR column in PostgreSQL)
    User.id     →  users.id     (UUID primary key)

WHY UUID?
---------
We use UUIDs (Universally Unique Identifiers) instead of integer IDs because:
1. They don't expose how many users you have (int IDs do)
2. They're safe to generate client-side without DB coordination
3. They work better in distributed systems
4. Industry standard for user IDs

FORMAT: 550e8400-e29b-41d4-a716-446655440000
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class User(Base):
    """
    Users table — stores registered customers.

    In our e-commerce scenario, users are ShopEase customers.
    They can log in, chat with the AI agent, and access their orders.
    """
    __tablename__ = "users"

    # ── Primary Key ───────────────────────────────────────
    # UUID generated in Python (not DB) — works with any database
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the user"
    )

    # ── Identity ──────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,      # No two users with same email
        nullable=False,
        index=True,       # Index for fast login lookup
        comment="User's email address — used for login"
    )

    # The full name for display in the UI
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User's display name"
    )

    # ── Authentication ────────────────────────────────────
    # IMPORTANT: This stores the bcrypt HASH, never the plain password
    # Example: $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hash of password — NEVER store plain text"
    )

    # Whether the user's email has been verified
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Soft disable account without deleting (admin feature)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # ── Demo Mode ────────────────────────────────────────
    # Marks seed/demo users for recruiters trying the app
    is_demo: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True for demo/seed users"
    )

    # ── Timestamps ───────────────────────────────────────
    # WHY timezone=True? Always store UTC. Display in user's local time on frontend.
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
    # SQLAlchemy will load related objects automatically
    # 'lazy="select"' = load on first access (default, fine for now)
    conversations = relationship("Conversation", back_populates="user", lazy="select")
    orders = relationship("Order", back_populates="user", lazy="select")
    tickets = relationship("SupportTicket", back_populates="user", lazy="select")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
