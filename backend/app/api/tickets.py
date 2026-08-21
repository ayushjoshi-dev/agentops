"""AgentOps — Support Tickets API"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.ticket import SupportTicket, TicketStatus, TicketPriority
from app.models.order import Order
from app.schemas.schemas import TicketResponse, CreateTicketRequest
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def _get_next_ticket_number(db: Session) -> str:
    last = db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).first()
    if not last:
        return "TKT-1016"
    try:
        num = int(last.ticket_number.split("-")[1])
        return f"TKT-{num + 1}"
    except Exception:
        return f"TKT-{uuid.uuid4().hex[:6].upper()}"


@router.get("", response_model=List[TicketResponse])
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all support tickets for the current user."""
    tickets = (
        db.query(SupportTicket)
        .filter(SupportTicket.user_id == current_user.id)
        .order_by(SupportTicket.created_at.desc())
        .all()
    )
    return tickets


@router.post("", response_model=TicketResponse, status_code=201)
def create_ticket(
    request: CreateTicketRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new support ticket."""
    priority = request.priority.upper()
    if priority not in {p.value for p in TicketPriority}:
        priority = "MEDIUM"

    order_id = None
    if request.order_number:
        order_num = request.order_number if request.order_number.startswith("ORD-") else f"ORD-{request.order_number}"
        order = db.query(Order).filter(
            Order.order_number == order_num.upper(),
            Order.user_id == current_user.id,
        ).first()
        if order:
            order_id = order.id

    ticket = SupportTicket(
        ticket_number=_get_next_ticket_number(db),
        user_id=current_user.id,
        order_id=order_id,
        title=request.title,
        description=request.description,
        status=TicketStatus.OPEN,
        priority=TicketPriority(priority),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    logger.info("ticket_created_via_api", ticket_number=ticket.ticket_number)
    return ticket


@router.get("/{ticket_number}", response_model=TicketResponse)
def get_ticket(
    ticket_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific support ticket."""
    if not ticket_number.startswith("TKT-"):
        ticket_number = f"TKT-{ticket_number}"

    ticket = db.query(SupportTicket).filter(
        SupportTicket.ticket_number == ticket_number.upper(),
        SupportTicket.user_id == current_user.id,
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_number} not found")

    return ticket
