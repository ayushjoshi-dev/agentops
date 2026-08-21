"""
AgentOps — ToolCall Model
===========================

Each ToolCall is one tool invocation within an AgentRun.

Example AgentRun with 2 tool calls:
  AgentRun
  ├── ToolCall: get_order_details(order_number="ORD-1025")
  │     input:  {"order_number": "ORD-1025"}
  │     output: {"status": "DELIVERED", "total": 55000, ...}
  │     duration: 45ms
  │
  └── ToolCall: create_support_ticket(...)
        input:  {"user_id": "...", "issue": "damaged product"}
        output: {"ticket_number": "TKT-1001", ...}
        duration: 120ms

This gives complete traceability of every action the agent took.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class ToolCall(Base):
    """Tool calls table — one row per tool invocation."""
    __tablename__ = "tool_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ── Tool Info ─────────────────────────────────────────
    tool_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Name of the tool called e.g. get_order_details"
    )

    # Exact input passed to the tool (JSON)
    input_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Tool input arguments as JSON"
    )

    # Exact output returned by the tool (JSON)
    output_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Tool output/result as JSON"
    )

    # ── Performance ───────────────────────────────────────
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Tool execution time in milliseconds"
    )

    # "success" | "error"
    status: Mapped[str] = mapped_column(
        String(20),
        default="success",
        nullable=False
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )

    # Sequence number within the agent run (1st tool call, 2nd, etc.)
    sequence: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Order of this tool call within the agent run"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ── Relationships ─────────────────────────────────────
    agent_run = relationship("AgentRun", back_populates="tool_calls")

    def __repr__(self) -> str:
        return f"<ToolCall tool={self.tool_name} status={self.status} duration={self.duration_ms}ms>"
