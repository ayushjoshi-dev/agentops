"""
AgentOps — Product Model
==========================

Products that ShopEase sells.
The agent's search_products tool queries this table.

WHY INDEX ON category AND price?
----------------------------------
When a user says "Find laptops under ₹60,000", the query is:
    SELECT * FROM products
    WHERE category = 'Laptop' AND price <= 60000

Without indexes: PostgreSQL scans ALL rows (full table scan) — slow with 50k+ products.
With indexes: PostgreSQL jumps directly to matching rows — millisecond lookup.

Composite index on (category, price) is especially effective for this query pattern.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, Text, DateTime, Boolean, Index, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class Product(Base):
    """Products table — the ShopEase catalog."""
    __tablename__ = "products"

    # ── Primary Key ───────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ── Product Info ──────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,       # Fast lookup by name
        comment="Product name e.g. 'Dell Inspiron 15 3000'"
    )

    # Category for filtering: 'Laptop', 'Mobile', 'Headphones', etc.
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Product category for search filtering"
    )

    # ── Pricing ───────────────────────────────────────────
    # Use Numeric (not Float) for money — floats have precision issues
    # 0.1 + 0.2 = 0.30000000000000004 in float!
    # Numeric is exact decimal arithmetic
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),   # Max 99,999,999.99
        nullable=False,
        comment="Price in INR (Indian Rupees)"
    )

    # Original price before discount — for showing "was ₹X, now ₹Y"
    original_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Original price before discount"
    )

    # ── Inventory ────────────────────────────────────────
    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current stock count"
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="False when out of stock or delisted"
    )

    # ── Details ───────────────────────────────────────────
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Full product description"
    )

    brand: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    # Rating out of 5 (e.g., 4.3)
    rating: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    review_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Flexible extra attributes as JSON
    # e.g., {"weight": "1.5kg", "color": "Silver", "warranty_years": 1}
    attributes: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Flexible product attributes stored as JSON"
    )

    # ── Timestamps ───────────────────────────────────────
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
    order_items = relationship("OrderItem", back_populates="product")

    # ── Composite Index ───────────────────────────────────
    # Optimizes: WHERE category = 'Laptop' AND price <= 60000
    __table_args__ = (
        Index("ix_products_category_price", "category", "price"),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name} price={self.price}>"
