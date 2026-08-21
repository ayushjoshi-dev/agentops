"""
AgentOps — SupportTicket Model
================================

Support tickets are created when customers have issues with orders.

PRIORITY LEVELS:
----------------
LOW      → General inquiry, no urgency
MEDIUM   → Issue affecting order, needs attention
HIGH     → Significant problem, customer upset
URGENT   → Escalated, needs immediate resolution

STATUS FLOW:
------------
OPEN → IN_PROGRESS → RESOLVED → CLOSED
OPEN → CLOSED (if customer withdraws)
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class SupportTicket(Base):
    """Support tickets table."""
    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ── Ticket Number ─────────────────────────────────────
    ticket_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Human-readable ticket ID e.g. TKT-1001"
    )

    # ── Foreign Keys ──────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Order is optional — some tickets aren't about a specific order
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # ── Content ───────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Short description of the issue"
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed description of the issue"
    )

    # ── Classification ────────────────────────────────────
    status: Mapped[TicketStatus] = mapped_column(
        SAEnum(TicketStatus, name="ticket_status_enum"),
        default=TicketStatus.OPEN,
        nullable=False,
        index=True
    )

    priority: Mapped[TicketPriority] = mapped_column(
        SAEnum(TicketPriority, name="ticket_priority_enum"),
        default=TicketPriority.MEDIUM,
        nullable=False,
        index=True
    )

    # Notes added by support agent (future: admin panel)
    resolution_notes: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    # ── Timestamps ────────────────────────────────────────
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

    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # ── Relationships ─────────────────────────────────────
    user = relationship("User", back_populates="tickets")
    order = relationship("Order", back_populates="tickets")

    def __repr__(self) -> str:
        return f"<SupportTicket {self.ticket_number} status={self.status} priority={self.priority}>"
