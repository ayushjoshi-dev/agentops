"""
AgentOps — Support Ticket Tool
================================

Creates support tickets in the database when users need help.

AGENT SAFETY:
-------------
The agent should NOT create tickets immediately without confirmation.
The agent should:
1. Gather information
2. Ask "Shall I create a support ticket for this?"
3. Only call create_support_ticket after the user confirms

This is implemented via the agent's system prompt instructions.
"""

from typing import Optional
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.models.ticket import SupportTicket, TicketStatus, TicketPriority
from app.models.order import Order
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)

_db_session: Optional[Session] = None


def set_db_session(db: Session):
    global _db_session
    _db_session = db


def _get_next_ticket_number(db: Session) -> str:
    """Generate the next sequential ticket number."""
    last = (
        db.query(SupportTicket)
        .order_by(SupportTicket.created_at.desc())
        .first()
    )
    if not last or not last.ticket_number:
        return "TKT-1016"
    
    try:
        num = int(last.ticket_number.split("-")[1])
        return f"TKT-{num + 1}"
    except (IndexError, ValueError):
        import uuid
        return f"TKT-{str(uuid.uuid4())[:8].upper()}"


@tool
def create_support_ticket(
    user_email: str,
    issue_title: str,
    issue_description: str,
    priority: str = "MEDIUM",
    order_number: Optional[str] = None,
) -> str:
    """
    Create a support ticket for a customer issue.
    
    IMPORTANT: Only call this tool after the user has explicitly confirmed
    they want to create a ticket. Ask for confirmation first.
    
    Args:
        user_email:        Customer's email address
        issue_title:       Short title of the issue (max 100 chars)
        issue_description: Detailed description of the problem
        priority:          Ticket priority: LOW, MEDIUM, HIGH, or URGENT
        order_number:      Related order number if applicable (e.g., 'ORD-1025')
    
    Returns:
        Confirmation with ticket number and next steps
    """
    if _db_session is None:
        return "Error: Database not connected."

    # Validate priority
    priority = priority.upper()
    valid_priorities = {p.value for p in TicketPriority}
    if priority not in valid_priorities:
        priority = "MEDIUM"

    # Look up user
    user = _db_session.query(User).filter(User.email == user_email).first()
    if not user:
        return f"User not found for email: {user_email}. Please verify the email address."

    # Look up order if provided
    order_id = None
    if order_number:
        if not order_number.startswith("ORD-"):
            order_number = f"ORD-{order_number}"
        order = _db_session.query(Order).filter(
            Order.order_number == order_number.upper()
        ).first()
        if order:
            order_id = order.id
        else:
            logger.warning("order_not_found_for_ticket", order_number=order_number)

    # Create the ticket
    ticket_number = _get_next_ticket_number(_db_session)

    ticket = SupportTicket(
        ticket_number=ticket_number,
        user_id=user.id,
        order_id=order_id,
        title=issue_title[:500],
        description=issue_description,
        status=TicketStatus.OPEN,
        priority=TicketPriority(priority),
    )
    _db_session.add(ticket)
    _db_session.flush()

    logger.info(
        "support_ticket_created",
        ticket_number=ticket_number,
        user_email=user_email,
        priority=priority,
    )

    result = (
        f"Support ticket created successfully!\n"
        f"Ticket Number: {ticket_number}\n"
        f"Priority: {priority}\n"
        f"Status: OPEN\n"
        f"Title: {issue_title[:100]}\n"
    )

    if order_number and order_id:
        result += f"Linked Order: {order_number}\n"

    result += (
        f"\nOur support team will contact you at {user_email} within:\n"
        f"  - URGENT: 2 hours\n"
        f"  - HIGH: 24 hours\n"
        f"  - MEDIUM: 48 hours\n"
        f"  - LOW: 72 hours\n"
        f"\nPlease save your ticket number: {ticket_number}"
    )

    return result
