"""
AgentOps - Chat API
======================
Endpoints:
  POST /api/chat       - Send a message (authenticated)
  POST /api/chat/demo  - Send a message (unauthenticated demo mode)

HITL Changes:
  - ChatRequest now accepts pending_action and awaiting_confirmation
  - ChatResponse now returns awaiting_confirmation and pending_action
  - The frontend uses awaiting_confirmation=True to show confirm/cancel buttons
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.services.agent_service import run_agent
from app.schemas.schemas import ChatRequest, ChatResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"
DEMO_EMAIL = "demo@shopease.com"


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to the AI agent (authenticated endpoint).

    If awaiting_confirmation=True was returned by a previous call,
    include the same pending_action and awaiting_confirmation in this request.
    """
    result = run_agent(
        user_message=request.message,
        user_id=str(current_user.id),
        user_email=current_user.email,
        db=db,
        conversation_id=request.conversation_id,
        is_demo=False,
        pending_action=request.pending_action,
        awaiting_confirmation=request.awaiting_confirmation or False,
    )

    return ChatResponse(
        response=result["response"],
        conversation_id=result["conversation_id"],
        tool_calls_trace=result.get("tool_calls_trace", []),
        sources=result.get("sources", []),
        duration_ms=result.get("duration_ms", 0),
        awaiting_confirmation=result.get("awaiting_confirmation", False),
        pending_action=result.get("pending_action"),
    )


@router.post("/demo", response_model=ChatResponse)
def chat_demo(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI agent (unauthenticated demo mode).
    Uses the demo user account.
    """
    from app.models.user import User
    demo_user = db.query(User).filter(User.email == DEMO_EMAIL).first()

    if not demo_user:
        raise HTTPException(
            status_code=503,
            detail="Demo user not found. Please run the seed script first.",
        )

    result = run_agent(
        user_message=request.message,
        user_id=str(demo_user.id),
        user_email=demo_user.email,
        db=db,
        conversation_id=request.conversation_id,
        is_demo=True,
        pending_action=request.pending_action,
        awaiting_confirmation=request.awaiting_confirmation or False,
    )

    return ChatResponse(
        response=result["response"],
        conversation_id=result["conversation_id"],
        tool_calls_trace=result.get("tool_calls_trace", []),
        sources=result.get("sources", []),
        duration_ms=result.get("duration_ms", 0),
        awaiting_confirmation=result.get("awaiting_confirmation", False),
        pending_action=result.get("pending_action"),
    )
