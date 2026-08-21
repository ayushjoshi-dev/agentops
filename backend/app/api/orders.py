"""AgentOps — Orders API"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.order import Order
from app.schemas.schemas import OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=List[OrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
):
    """List all orders for the current user."""
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )
    return orders


@router.get("/{order_number}", response_model=OrderResponse)
def get_order(
    order_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get order details by order number."""
    if not order_number.startswith("ORD-"):
        order_number = f"ORD-{order_number}"

    order = db.query(Order).filter(
        Order.order_number == order_number.upper(),
        Order.user_id == current_user.id,
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_number} not found")

    return order
