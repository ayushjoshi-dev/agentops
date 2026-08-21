"""
AgentOps — AgentRun Model
===========================

An AgentRun is one full execution of the LangGraph agent.

WHY TRACK AGENT RUNS?
---------------------
This is called "observability" — the ability to inspect what the agent
did, why it did it, and how long it took.

Without this:
- You have no idea why the agent gave a wrong answer
- You can't debug tool failures
- You can't measure latency or cost
- You can't evaluate agent quality

With this:
- Every agent execution is logged
- You can replay any conversation
- You can see exactly which tools were called and with what inputs
- You can calculate token costs

This is similar to what LangSmith provides, but built in-house.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Integer, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AgentRun(Base):
    """
    Agent runs table — one row per agent invocation.
    
    Linked to: Conversation (which conversation triggered it)
    Has many:  ToolCalls (which tools the agent used)
    """
    __tablename__ = "agent_runs"

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

    # ── Execution Info ────────────────────────────────────
    # "completed" | "failed" | "timeout"
    status: Mapped[str] = mapped_column(
        String(20),
        default="completed",
        nullable=False
    )

    # How long the agent ran (milliseconds)
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total agent execution time in milliseconds"
    )

    # Total tokens used across all LLM calls in this run
    total_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    # Number of tool calls made in this run
    tool_call_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Error message if status == "failed"
    error_message: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ── Relationships ─────────────────────────────────────
    conversation = relationship("Conversation", back_populates="agent_runs")
    tool_calls = relationship(
        "ToolCall",
        back_populates="agent_run",
        cascade="all, delete-orphan",
        order_by="ToolCall.created_at"
    )

    def __repr__(self) -> str:
        return f"<AgentRun id={self.id} status={self.status} tools={self.tool_call_count}>"
