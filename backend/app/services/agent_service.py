"""
AgentOps - Agent Service
==========================
The main entry point for running the AI agent.

CHANGES FROM ORIGINAL:
-----------------------
1. Now injects user_email into order_tools for authorization checks
2. Passes awaiting_confirmation and pending_action to/from state
3. Returns awaiting_confirmation in the response so frontend can show confirm UI
"""
import uuid
import time
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.agents.graph import get_agent_graph
from app.agents.state import AgentState
from app.services.conversation_service import (
    get_or_create_conversation,
    get_conversation_messages,
    save_message,
    update_conversation_title,
)
from app.models.agent_run import AgentRun
from app.models.tool_call import ToolCall

from app.tools import knowledge_tool, order_tools, product_tools, ticket_tools
from app.core.logging import get_logger

logger = get_logger(__name__)


def _inject_db_into_tools(db: Session, user_email: str = None) -> None:
    """
    Inject the database session and user context into all tools.
    Called at the start of each agent invocation.
    """
    knowledge_tool.set_db_session(db)
    order_tools.set_db_session(db)
    order_tools.set_user_email(user_email or "")  # for authorization checks
    product_tools.set_db_session(db)
    ticket_tools.set_db_session(db)


def run_agent(
    user_message: str,
    user_id: str,
    user_email: str,
    db: Session,
    conversation_id: Optional[str] = None,
    is_demo: bool = False,
    pending_action: Optional[dict] = None,
    awaiting_confirmation: bool = False,
) -> dict:
    """
    Run the LangGraph agent for a user message.

    Args:
        user_message:         The user input text
        user_id:              User UUID string
        user_email:           User email (for tool context and authorization)
        db:                   Database session
        conversation_id:      If provided, continue this conversation
        is_demo:              If True, demo mode (no auth required)
        pending_action:       Any pending HITL action from previous message
        awaiting_confirmation: Whether we were waiting for confirmation

    Returns:
        dict with: response, conversation_id, tool_calls_trace, sources,
                   awaiting_confirmation, pending_action, duration_ms
    """
    start_time = time.time()

    _inject_db_into_tools(db, user_email)

    conversation = get_or_create_conversation(
        user_id=user_id,
        db=db,
        conversation_id=conversation_id,
        is_demo=is_demo,
    )
    conv_id = str(conversation.id)

    history = get_conversation_messages(conv_id, db, limit=20)

    save_message(
        conversation_id=conv_id,
        role="user",
        content=user_message,
        db=db,
    )
    update_conversation_title(conv_id, user_message, db)

    initial_state: AgentState = {
        "messages": history + [HumanMessage(content=user_message)],
        "user_id": user_id,
        "user_email": user_email,
        "conversation_id": conv_id,
        "tool_calls_trace": [],
        "retrieved_docs": [],
        "final_response": None,
        "error": None,
        "awaiting_confirmation": awaiting_confirmation,
        "pending_action": pending_action,
    }

    agent_run = AgentRun(
        conversation_id=conversation.id,
        status="running",
    )
    db.add(agent_run)
    db.flush()

    try:
        graph = get_agent_graph()
        final_state = graph.invoke(initial_state)

        final_response = _extract_final_response(final_state)
        tool_calls_trace = _extract_tool_trace(final_state)
        sources = _extract_sources(final_state)
        new_awaiting = final_state.get("awaiting_confirmation", False)
        new_pending = final_state.get("pending_action", None)

        # Save assistant message
        save_message(
            conversation_id=conv_id,
            role="assistant",
            content=final_response,
            db=db,
            metadata={
                "tool_calls": tool_calls_trace,
                "sources": sources,
                "awaiting_confirmation": new_awaiting,
                "pending_action": new_pending,
            },
        )

        duration_ms = int((time.time() - start_time) * 1000)
        agent_run.status = "completed"
        agent_run.duration_ms = duration_ms
        agent_run.tool_call_count = len(tool_calls_trace)

        for i, tc in enumerate(tool_calls_trace):
            tool_call_record = ToolCall(
                agent_run_id=agent_run.id,
                tool_name=tc.get("tool", "unknown"),
                input_data=tc.get("input"),
                output_data={"output": tc.get("output", "")},
                status="success",
                sequence=i + 1,
            )
            db.add(tool_call_record)

        db.commit()
        logger.info(
            "agent_run_complete",
            conversation_id=conv_id,
            duration_ms=duration_ms,
            tool_calls=len(tool_calls_trace),
            awaiting_confirmation=new_awaiting,
        )

        return {
            "response": final_response,
            "conversation_id": conv_id,
            "tool_calls_trace": tool_calls_trace,
            "sources": sources,
            "duration_ms": duration_ms,
            "awaiting_confirmation": new_awaiting,
            "pending_action": new_pending,
        }

    except Exception as e:
        logger.error("agent_run_failed", error=str(e), conversation_id=conv_id)
        agent_run.status = "failed"
        agent_run.error_message = str(e)[:1000]
        db.commit()

        return {
            "response": "I encountered an error processing your request. Please try again or contact support.",
            "conversation_id": conv_id,
            "tool_calls_trace": [],
            "sources": [],
            "error": str(e),
            "awaiting_confirmation": False,
            "pending_action": None,
        }


def _extract_final_response(state: AgentState) -> str:
    """Extract the final text response from the state."""
    if state.get("final_response"):
        return state["final_response"]

    messages = state.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content

    return "I was unable to generate a response. Please try again."


def _extract_tool_trace(state: AgentState) -> List[dict]:
    """Extract tool call information from the message history."""
    trace = []
    messages = state.get("messages", [])

    tool_outputs = {}
    for msg in messages:
        if isinstance(msg, ToolMessage):
            tool_outputs[msg.tool_call_id] = msg.content

    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                # Skip synthetic HITL re-injection calls (they have hitl_ prefix)
                call_id = tc.get("id", "")
                if call_id.startswith("hitl_") and tc.get("id") not in tool_outputs:
                    continue
                trace.append({
                    "tool": tc.get("name", "unknown"),
                    "input": tc.get("args", {}),
                    "output": tool_outputs.get(call_id, "")[:500],
                    "tool_call_id": call_id,
                })

    return trace


def _extract_sources(state: AgentState) -> List[dict]:
    """Extract RAG sources from tool outputs."""
    sources = []
    tool_trace = _extract_tool_trace(state)

    for tc in tool_trace:
        if tc["tool"] == "search_knowledge_base":
            output = tc.get("output", "")
            if "SOURCES:" in output:
                sources_section = output.split("SOURCES:")[-1].strip()
                for line in sources_section.split("\n"):
                    line = line.strip()
                    if line.startswith("-"):
                        parts = line.lstrip("- ").split("(Section:")
                        source = parts[0].strip()
                        section = parts[1].rstrip(")").strip() if len(parts) > 1 else "General"
                        sources.append({"source": source, "section": section})

    return sources
