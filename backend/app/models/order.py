"""
AgentOps — Order & OrderItem Models
=====================================

WHY TWO TABLES?
---------------
An Order belongs to one User.
An Order can have MANY products (OrderItems).

This is a classic "one-to-many" then "many-to-many" pattern:
  Order → has many → OrderItems
  OrderItem → links to → Product

This is called a "join table" or "association table".

ORDER STATUS FLOW:
------------------
PLACED → PROCESSING → SHIPPED → OUT_FOR_DELIVERY → DELIVERED
                                                  ↘ RETURN_REQUESTED → REFUNDED
PLACED → CANCELLED
"""

import uuid
import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    String, Numeric, Integer, DateTime, Text,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class OrderStatus(str, enum.Enum):
    """
    All possible states of an order.
    
    We use str enum so the values are stored as strings in PostgreSQL,
    not integers. This makes the database human-readable.
    """
    PLACED = "PLACED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    REFUNDED = "REFUNDED"


class Order(Base):
    """Orders table — each row is one customer purchase."""
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Human-readable order number for customer-facing display
    # e.g. "ORD-1001" — what users say to the agent
    order_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Human-readable order ID e.g. ORD-1001"
    )

    # ── Foreign Keys ──────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ── Status ────────────────────────────────────────────
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status_enum"),
        default=OrderStatus.PLACED,
        nullable=False,
        index=True
    )

    # ── Financials ────────────────────────────────────────
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Total order value in INR"
    )

    # ── Shipping ──────────────────────────────────────────
    tracking_number: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment="Carrier tracking number e.g. FEDEX123456"
    )

    shipping_address: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    delivery_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Estimated or actual delivery date"
    )

    notes: Mapped[str] = mapped_column(
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

    # ── Relationships ─────────────────────────────────────
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    tickets = relationship("SupportTicket", back_populates="order")

    def __repr__(self) -> str:
        return f"<Order {self.order_number} status={self.status}>"


class OrderItem(Base):
    """
    Order line items — each row is one product in an order.
    
    Example: Order ORD-1001 has:
    - 1x Dell Laptop at ₹55,000  → subtotal ₹55,000
    - 2x USB Cable at ₹500       → subtotal ₹1,000
    """
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Price per unit at time of purchase"
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="quantity * unit_price"
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Product name snapshot at purchase time"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ── Relationships ─────────────────────────────────────
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self) -> str:
        return f"<OrderItem order={self.order_id} qty={self.quantity}>"
