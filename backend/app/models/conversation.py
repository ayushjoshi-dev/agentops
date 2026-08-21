"""
AgentOps — Conversation Model
================================

A conversation is a session between a user and the AI agent.

WHY STORE CONVERSATIONS IN DB?
-------------------------------
If we only kept messages in memory (e.g., a Python dict), they would be
lost when the server restarts. By persisting them in PostgreSQL, users
can pick up where they left off across browser sessions.

This also enables:
- Conversation history in the UI sidebar
- Analytics on agent behavior
- Debugging agent failures
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Conversation(Base):
    """Conversations table — one row per chat session."""
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Auto-generated from first user message
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="Conversation title, derived from first message"
    )

    # Allow anonymous/demo conversations
    is_demo: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
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
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    agent_runs = relationship("AgentRun", back_populates="conversation")

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} user={self.user_id}>"
