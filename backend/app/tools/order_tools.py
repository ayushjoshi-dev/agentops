"""
AgentOps — Order Tools
========================

Tools for querying order information from the database.

These tools are called by the agent when users ask about their orders:
- "Where is my order ORD-1025?"
- "What is the status of my order?"
- "Show me my recent orders"
- "What did I order?"
"""

from typing import Optional
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User
from app.models.product import Product
from app.core.logging import get_logger

logger = get_logger(__name__)

_db_session: Optional[Session] = None


def set_db_session(db: Session):
    global _db_session
    _db_session = db


@tool
def get_order_status(order_number: str) -> str:
    """
    Get the current status of a specific order.
    
    Use this when the user asks about their order status, tracking, or delivery.
    
    Args:
        order_number: The order number (e.g., 'ORD-1025' or just '1025')
    
    Returns:
        Order status, tracking info, and delivery date
    """
    if _db_session is None:
        return "Error: Database not connected."

    # Normalize order number — accept "1025" or "ORD-1025"
    if not order_number.startswith("ORD-"):
        order_number = f"ORD-{order_number}"

    order = _db_session.query(Order).filter(
        Order.order_number == order_number.upper()
    ).first()

    if not order:
        return f"Order {order_number} not found. Please check the order number and try again."

    status_messages = {
        OrderStatus.PLACED: "Your order has been placed and is awaiting processing.",
        OrderStatus.PROCESSING: "Your order is being processed and prepared for shipping.",
        OrderStatus.SHIPPED: "Your order has been shipped and is on its way.",
        OrderStatus.OUT_FOR_DELIVERY: "Your order is out for delivery and will arrive today!",
        OrderStatus.DELIVERED: "Your order has been delivered.",
        OrderStatus.CANCELLED: "This order has been cancelled.",
        OrderStatus.RETURN_REQUESTED: "A return has been requested for this order.",
        OrderStatus.REFUNDED: "This order has been refunded.",
    }

    result_parts = [
        f"Order: {order.order_number}",
        f"Status: {order.status.value}",
        f"Details: {status_messages.get(order.status, 'Status unknown')}",
    ]

    if order.tracking_number:
        result_parts.append(f"Tracking Number: {order.tracking_number}")

    if order.delivery_date:
        date_str = order.delivery_date.strftime("%d %B %Y")
        if order.status == OrderStatus.DELIVERED:
            result_parts.append(f"Delivered On: {date_str}")
        else:
            result_parts.append(f"Expected Delivery: {date_str}")

    result_parts.append(f"Order Total: Rs. {order.total_amount:,.2f}")

    logger.info("order_status_retrieved", order_number=order_number, status=order.status.value)
    return "\n".join(result_parts)


@tool
def get_order_details(order_number: str) -> str:
    """
    Get complete details about an order including all items, prices, and shipping info.
    
    Use this when the user asks for full order details, to check eligibility for
    refund/return, or needs product-level information about their order.
    
    Args:
        order_number: The order number (e.g., 'ORD-1025')
    
    Returns:
        Complete order information including items, prices, and shipping details
    """
    if _db_session is None:
        return "Error: Database not connected."

    if not order_number.startswith("ORD-"):
        order_number = f"ORD-{order_number}"

    order = _db_session.query(Order).filter(
        Order.order_number == order_number.upper()
    ).first()

    if not order:
        return f"Order {order_number} not found."

    result_parts = [
        f"=== Order Details: {order.order_number} ===",
        f"Status: {order.status.value}",
        f"Order Date: {order.created_at.strftime('%d %B %Y')}",
        f"Total Amount: Rs. {order.total_amount:,.2f}",
    ]

    if order.tracking_number:
        result_parts.append(f"Tracking Number: {order.tracking_number}")

    if order.delivery_date:
        date_str = order.delivery_date.strftime("%d %B %Y")
        label = "Delivered On" if order.status == OrderStatus.DELIVERED else "Expected Delivery"
        result_parts.append(f"{label}: {date_str}")

    if order.shipping_address:
        result_parts.append(f"Shipping Address: {order.shipping_address}")

    result_parts.append("\n--- Items Ordered ---")
    for item in order.items:
        result_parts.append(
            f"  - {item.product_name}: Qty {item.quantity} x Rs. {item.unit_price:,.2f} = Rs. {item.subtotal:,.2f}"
        )

    # Refund eligibility info
    result_parts.append("\n--- Eligibility ---")
    if order.status == OrderStatus.DELIVERED and order.delivery_date:
        from datetime import datetime, timezone
        days_since_delivery = (datetime.now(timezone.utc) - order.delivery_date).days
        if days_since_delivery <= 7:
            result_parts.append(f"Refund/Return Eligible: YES (delivered {days_since_delivery} days ago, within 7-day window)")
        else:
            result_parts.append(f"Refund/Return Eligible: POSSIBLY (delivered {days_since_delivery} days ago, beyond standard 7-day window)")
    elif order.status in [OrderStatus.PLACED, OrderStatus.PROCESSING]:
        result_parts.append("Cancellation: Eligible (order not yet shipped)")
    else:
        result_parts.append(f"Current status ({order.status.value}) — contact support for options")

    logger.info("order_details_retrieved", order_number=order_number)
    return "\n".join(result_parts)


@tool
def get_customer_orders(user_email: str, limit: int = 5) -> str:
    """
    Get recent orders for a customer by their email address.
    
    Use this when the user asks to see their orders without specifying an order number,
    or says 'show my orders', 'my recent purchases', etc.
    
    Args:
        user_email: Customer's email address
        limit:      Maximum number of orders to return (default 5)
    
    Returns:
        List of recent orders with status
    """
    if _db_session is None:
        return "Error: Database not connected."

    user = _db_session.query(User).filter(User.email == user_email).first()
    if not user:
        return f"No account found for email: {user_email}"

    orders = (
        _db_session.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )

    if not orders:
        return f"No orders found for {user_email}"

    result_parts = [f"Recent orders for {user.full_name}:"]
    for order in orders:
        date = order.created_at.strftime("%d %b %Y")
        result_parts.append(
            f"  - {order.order_number}: Rs. {order.total_amount:,.2f} | "
            f"Status: {order.status.value} | Placed: {date}"
        )

    logger.info("customer_orders_retrieved", user_email=user_email, count=len(orders))
    return "\n".join(result_parts)
