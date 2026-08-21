"""
AgentOps — Agent Service
==========================

The main entry point for running the AI agent.

This service:
1. Sets up tool database connections
2. Loads conversation history
3. Runs the LangGraph agent
4. Persists messages and observability data
5. Returns the response + tool trace

IMPORTANT DESIGN DECISION:
---------------------------
We inject the database session into tools BEFORE running the agent.
This is because LangChain tools are module-level objects (singletons),
but each request needs its own DB session.

We use module-level _db_session setters in each tool module.
This is a pragmatic approach — a more elegant solution would use
LangGraph's configurable runnables, but this is simpler for learning.
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

# Import tool session setters
from app.tools import knowledge_tool, order_tools, product_tools, ticket_tools
from app.core.logging import get_logger

logger = get_logger(__name__)


def _inject_db_into_tools(db: Session) -> None:
    """
    Inject the database session into all tools.
    
    Tools are singletons but need per-request DB sessions.
    This is called at the start of each agent invocation.
    """
    knowledge_tool.set_db_session(db)
    order_tools.set_db_session(db)
    product_tools.set_db_session(db)
    ticket_tools.set_db_session(db)


def run_agent(
    user_message: str,
    user_id: str,
    user_email: str,
    db: Session,
    conversation_id: Optional[str] = None,
    is_demo: bool = False,
) -> dict:
    """
    Run the LangGraph agent for a user message.
    
    Args:
        user_message:    The user's input text
        user_id:         User's UUID string
        user_email:      User's email (for tool context)
        db:              Database session
        conversation_id: If provided, continue this conversation
        is_demo:         If True, demo mode (no auth required)
    
    Returns:
        dict with: response, conversation_id, tool_calls_trace, sources
    """
    start_time = time.time()

    # Step 1: Inject DB session into all tools
    _inject_db_into_tools(db)

    # Step 2: Get or create conversation
    conversation = get_or_create_conversation(
        user_id=user_id,
        db=db,
        conversation_id=conversation_id,
        is_demo=is_demo,
    )
    conv_id = str(conversation.id)

    # Step 3: Load conversation history
    history = get_conversation_messages(conv_id, db, limit=20)

    # Step 4: Save the user's message
    save_message(
        conversation_id=conv_id,
        role="user",
        content=user_message,
        db=db,
    )
    update_conversation_title(conv_id, user_message, db)

    # Step 5: Build initial state
    initial_state: AgentState = {
        "messages": history + [HumanMessage(content=user_message)],
        "user_id": user_id,
        "user_email": user_email,
        "conversation_id": conv_id,
        "tool_calls_trace": [],
        "retrieved_docs": [],
        "final_response": None,
        "error": None,
    }

    # Step 6: Run the graph
    agent_run = AgentRun(
        conversation_id=conversation.id,
        status="running",
    )
    db.add(agent_run)
    db.flush()

    try:
        graph = get_agent_graph()
        final_state = graph.invoke(initial_state)

        # Step 7: Extract results
        final_response = _extract_final_response(final_state)
        tool_calls_trace = _extract_tool_trace(final_state)
        sources = _extract_sources(final_state)

        # Step 8: Save assistant message
        save_message(
            conversation_id=conv_id,
            role="assistant",
            content=final_response,
            db=db,
            metadata={
                "tool_calls": tool_calls_trace,
                "sources": sources,
            },
        )

        # Step 9: Update AgentRun observability record
        duration_ms = int((time.time() - start_time) * 1000)
        agent_run.status = "completed"
        agent_run.duration_ms = duration_ms
        agent_run.tool_call_count = len(tool_calls_trace)

        # Step 10: Save ToolCall records
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
        )

        return {
            "response": final_response,
            "conversation_id": conv_id,
            "tool_calls_trace": tool_calls_trace,
            "sources": sources,
            "duration_ms": duration_ms,
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
                trace.append({
                    "tool": tc.get("name", "unknown"),
                    "input": tc.get("args", {}),
                    "output": tool_outputs.get(tc.get("id", ""), "")[:500],
                    "tool_call_id": tc.get("id", ""),
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
                        # Parse "- filename.txt (Section: XYZ)"
                        parts = line.lstrip("- ").split("(Section:")
                        source = parts[0].strip()
                        section = parts[1].rstrip(")").strip() if len(parts) > 1 else "General"
                        sources.append({"source": source, "section": section})

    return sources
