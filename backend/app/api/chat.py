"""
AgentOps — Chat API
======================

The main endpoint that powers the AI agent chat.

Endpoints:
  POST /api/chat       — Send a message (authenticated)
  POST /api/chat/demo  — Send a message (unauthenticated demo mode)
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

# Demo user UUID — used for unauthenticated requests
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
    
    The agent will:
    1. Understand the user's intent
    2. Call appropriate tools (order lookup, RAG search, etc.)
    3. Return a grounded response with sources
    
    Include the conversation_id from the previous response to continue
    an existing conversation. Omit it to start a new conversation.
    """
    result = run_agent(
        user_message=request.message,
        user_id=str(current_user.id),
        user_email=current_user.email,
        db=db,
        conversation_id=request.conversation_id,
        is_demo=False,
    )

    return ChatResponse(
        response=result["response"],
        conversation_id=result["conversation_id"],
        tool_calls_trace=result.get("tool_calls_trace", []),
        sources=result.get("sources", []),
        duration_ms=result.get("duration_ms", 0),
    )


@router.post("/demo", response_model=ChatResponse)
def chat_demo(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI agent (unauthenticated demo mode).
    
    Uses the demo user account. Perfect for recruiters and demos.
    The demo user is pre-seeded with orders and tickets.
    """
    # Find demo user
    from app.models.user import User
    demo_user = db.query(User).filter(User.email == DEMO_EMAIL).first()

    if not demo_user:
        raise HTTPException(
            status_code=503,
            detail="Demo user not found. Please run the seed script first."
        )

    result = run_agent(
        user_message=request.message,
        user_id=str(demo_user.id),
        user_email=demo_user.email,
        db=db,
        conversation_id=request.conversation_id,
        is_demo=True,
    )

    return ChatResponse(
        response=result["response"],
        conversation_id=result["conversation_id"],
        tool_calls_trace=result.get("tool_calls_trace", []),
        sources=result.get("sources", []),
        duration_ms=result.get("duration_ms", 0),
    )
