"""
AgentOps - Agent State
========================
State is the data structure that flows through the LangGraph graph.
Every node reads from and writes to this state.

STATE FLOW (with HITL):
  User message
    -> agent_node (LLM decides tool calls)
    -> action_gate_node (intercept ACTION tools, ask for confirmation)
       READ-ONLY: pass through immediately
       ACTION:    store in pending_action, set awaiting_confirmation=True
    -> tools_node (execute tool calls)
    -> agent_node (generate final response)
"""
from typing import TypedDict, Annotated, Optional, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The state that flows through the LangGraph agent graph.

    Fields:
        messages:             Full conversation message history (auto-appended)
        user_id:              UUID of the authenticated user
        user_email:           Email of the user (for tool calls)
        conversation_id:      UUID of the conversation in DB
        tool_calls_trace:     List of tool call records for observability
        retrieved_docs:       Documents retrieved from RAG
        final_response:       The agent final text response
        error:                Error message if something failed
        awaiting_confirmation: True if agent is waiting for user to confirm an action
        pending_action:       The ACTION tool call waiting for confirmation
                              {"tool": "create_support_ticket", "args": {...}, "summary": "..."}
    """
    messages: Annotated[List[BaseMessage], add_messages]

    user_id: Optional[str]
    user_email: Optional[str]
    conversation_id: Optional[str]

    tool_calls_trace: Optional[List[dict]]
    retrieved_docs: Optional[List[dict]]
    final_response: Optional[str]
    error: Optional[str]

    # Human-In-The-Loop: backend-enforced confirmation for ACTION tools
    awaiting_confirmation: Optional[bool]
    pending_action: Optional[dict]
