"""
AgentOps — Agent State
========================

State is the data structure that flows through the LangGraph graph.
Every node in the graph reads from and writes to this state.

WHY TYPED STATE?
----------------
Using TypedDict with type hints makes the agent predictable:
- We always know what fields exist
- We catch bugs at development time, not runtime
- LangGraph can checkpoint and restore state

STATE FLOW:
-----------
User sends message
  ↓
State initialized with: messages=[HumanMessage(...)]
  ↓
agent_node runs → adds AIMessage (possibly with tool_calls)
  ↓
tools_node runs → adds ToolMessages for each tool call
  ↓
agent_node runs again → generates final AIMessage
  ↓
State returned: contains full message history + trace
"""

from typing import TypedDict, Annotated, Optional, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The state that flows through the LangGraph agent graph.
    
    Fields:
        messages:         Full conversation message history (auto-appended by add_messages)
        user_id:          UUID of the authenticated user (str)
        user_email:       Email of the user (for tool calls that need it)
        conversation_id:  UUID of the conversation in DB
        tool_calls_trace: List of tool call records for observability
        retrieved_docs:   Documents retrieved from RAG (for citation display)
        final_response:   The agent's final text response
        error:            Error message if something failed
    """
    # Annotated with add_messages: automatically appends new messages
    # instead of replacing the list. This is LangGraph's message accumulator.
    messages: Annotated[List[BaseMessage], add_messages]

    # User context — injected at graph invocation time
    user_id: Optional[str]
    user_email: Optional[str]
    conversation_id: Optional[str]

    # Observability: track what the agent did
    tool_calls_trace: Optional[List[dict]]

    # RAG citations to return alongside the response
    retrieved_docs: Optional[List[dict]]

    # Extracted final response text (same as last AIMessage content)
    final_response: Optional[str]

    # Error tracking
    error: Optional[str]
