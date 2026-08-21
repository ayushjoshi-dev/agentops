"""
AgentOps — Message Model
==========================

Each Message is one turn in a Conversation.

ROLES:
------
"user"      — the customer's message
"assistant" — the AI agent's response
"tool"      — the output of a tool call (hidden from user, seen by LLM)
"system"    — system prompts (not shown in UI)

This matches LangChain's message format:
  HumanMessage → role="user"
  AIMessage     → role="assistant"
  ToolMessage   → role="tool"

WHY STORE TOOL MESSAGES?
-------------------------
LLMs need to see the tool output to generate their final response.
By storing all messages (including tool responses) we can replay the
exact conversation flow for debugging and observability.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class Message(Base):
    """Messages table — one row per message in a conversation."""
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ── Content ───────────────────────────────────────────
    # "user" | "assistant" | "tool" | "system"
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Message role: user | assistant | tool | system"
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message text content"
    )

    # ── Metadata ──────────────────────────────────────────
    # Stores tool call info, citations, agent trace etc.
    # Example: {"tool_calls": [...], "sources": [...], "tokens_used": 150}
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=None,
        comment="Additional metadata: tool calls, citations, tokens"
    )

    # ── Timestamps ────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # ── Relationships ─────────────────────────────────────
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        preview = self.content[:50] if self.content else ""
        return f"<Message role={self.role} content='{preview}...'>"
