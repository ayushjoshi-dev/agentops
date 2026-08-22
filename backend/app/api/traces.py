"""
AgentOps - Agent Trace API
============================
Exposes agent execution data (agent_runs and tool_calls) for the frontend trace UI.

Endpoints:
  GET /api/traces              - List recent agent runs for current user
  GET /api/traces/{run_id}     - Get full trace for a specific agent run
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.agent_run import AgentRun
from app.models.conversation import Conversation
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/traces", tags=["Agent Traces"])


@router.get("")
def list_traces(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List recent agent runs for the current user.
    Returns summary data suitable for a trace list view.
    """
    # Get user conversations first, then filter agent_runs by those conversations
    user_conversations = (
        db.query(Conversation.id)
        .filter(Conversation.user_id == current_user.id)
        .subquery()
    )

    runs = (
        db.query(AgentRun)
        .filter(AgentRun.conversation_id.in_(user_conversations))
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(run.id),
            "conversation_id": str(run.conversation_id),
            "status": run.status,
            "duration_ms": run.duration_ms,
            "tool_call_count": run.tool_call_count,
            "created_at": run.created_at.isoformat(),
            "error_message": run.error_message,
        }
        for run in runs
    ]


@router.get("/{run_id}")
def get_trace(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get full trace for a specific agent run, including all tool calls.
    Verifies the run belongs to the current user.
    """
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")

    run = db.query(AgentRun).filter(AgentRun.id == run_uuid).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    # Verify ownership
    conversation = db.query(Conversation).filter(
        Conversation.id == run.conversation_id
    ).first()
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    tool_calls = [
        {
            "id": str(tc.id),
            "tool_name": tc.tool_name,
            "input_data": tc.input_data,
            # Truncate output to prevent huge responses leaking sensitive data
            "output_preview": str(tc.output_data.get("output", ""))[:300] if tc.output_data else "",
            "status": tc.status,
            "duration_ms": tc.duration_ms,
            "sequence": tc.sequence,
            "created_at": tc.created_at.isoformat(),
        }
        for tc in run.tool_calls
    ]

    return {
        "id": str(run.id),
        "conversation_id": str(run.conversation_id),
        "status": run.status,
        "duration_ms": run.duration_ms,
        "tool_call_count": run.tool_call_count,
        "created_at": run.created_at.isoformat(),
        "error_message": run.error_message,
        "tool_calls": tool_calls,
    }
