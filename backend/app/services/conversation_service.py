"""
AgentOps — Conversation Service
=================================

Manages conversation lifecycle and message persistence.

RESPONSIBILITIES:
-----------------
1. Create new conversations
2. Load existing conversation history
3. Save messages to the database
4. Convert DB messages to LangChain message format

WHY CONVERT TO LANGCHAIN FORMAT?
---------------------------------
LangChain uses its own message classes:
- HumanMessage  (role="user")
- AIMessage     (role="assistant")
- ToolMessage   (role="tool")
- SystemMessage (role="system")

The LLM expects these types, not raw dicts.
We convert from DB format ↔ LangChain format as needed.
"""

import uuid
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
)

from app.models.conversation import Conversation
from app.models.message import Message
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_or_create_conversation(
    user_id: str,
    db: Session,
    conversation_id: Optional[str] = None,
    is_demo: bool = False,
) -> Conversation:
    """
    Get an existing conversation or create a new one.
    
    Args:
        user_id:         User's UUID string
        db:              Database session
        conversation_id: If provided, load this conversation
        is_demo:         If True, mark as demo conversation
    
    Returns:
        Conversation model instance
    """
    if conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == uuid.UUID(conversation_id)
        ).first()
        if conv:
            return conv

    # Create new conversation
    conv = Conversation(
        user_id=uuid.UUID(user_id),
        is_demo=is_demo,
    )
    db.add(conv)
    db.flush()
    logger.info("conversation_created", conversation_id=str(conv.id), user_id=user_id)
    return conv


def get_conversation_messages(
    conversation_id: str,
    db: Session,
    limit: int = 20,
) -> List[BaseMessage]:
    """
    Load conversation history as LangChain messages.
    
    Args:
        conversation_id: Conversation UUID string
        db:              Database session
        limit:           Max messages to load (most recent N)
    
    Returns:
        List of LangChain BaseMessage objects
    """
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == uuid.UUID(conversation_id))
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )

    # Reverse to chronological order
    messages = list(reversed(messages))

    lc_messages = []
    for msg in messages:
        try:
            lc_msg = _db_to_langchain(msg)
            if lc_msg:
                lc_messages.append(lc_msg)
        except Exception as e:
            logger.warning("message_conversion_error", msg_id=str(msg.id), error=str(e))

    return lc_messages


def save_message(
    conversation_id: str,
    role: str,
    content: str,
    db: Session,
    metadata: Optional[dict] = None,
) -> Message:
    """
    Save a message to the database.
    
    Args:
        conversation_id: Conversation UUID string
        role:            "user" | "assistant" | "tool" | "system"
        content:         Message text content
        db:              Database session
        metadata:        Optional additional data (tool calls, citations, etc.)
    
    Returns:
        Saved Message instance
    """
    msg = Message(
        conversation_id=uuid.UUID(conversation_id),
        role=role,
        content=content,
        metadata_=metadata,
    )
    db.add(msg)
    db.flush()
    return msg


def update_conversation_title(
    conversation_id: str,
    first_message: str,
    db: Session,
) -> None:
    """Auto-generate conversation title from first user message."""
    conv = db.query(Conversation).filter(
        Conversation.id == uuid.UUID(conversation_id)
    ).first()
    if conv and not conv.title:
        # Use first 60 chars of message as title
        conv.title = first_message[:60] + ("..." if len(first_message) > 60 else "")
        conv.updated_at = datetime.now(timezone.utc)


def _db_to_langchain(msg: Message) -> Optional[BaseMessage]:
    """Convert a database Message to a LangChain message object."""
    role = msg.role
    content = msg.content or ""

    if role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    elif role == "tool":
        meta = msg.metadata_ or {}
        return ToolMessage(
            content=content,
            tool_call_id=meta.get("tool_call_id", str(msg.id)),
        )
    elif role == "system":
        return SystemMessage(content=content)
    else:
        logger.warning("unknown_message_role", role=role)
        return None
