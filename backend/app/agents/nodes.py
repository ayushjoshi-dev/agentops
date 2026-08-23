"""
AgentOps - LangGraph Agent Nodes
===================================
Nodes are the processing units of the LangGraph graph.
Each node is a Python function that takes State and returns updated State.

NODE TYPES:
-----------
1. agent_node:       Calls the LLM to decide what to do next.
2. action_gate_node: Intercepts ACTION tool calls and requires confirmation.
3. should_continue:  Routing function - tools or end?

HITL FLOW:
----------
agent_node -> LLM decides to call create_support_ticket
action_gate_node sees ACTION tool -> blocks execution, asks user
  "I am about to create a support ticket. Shall I proceed?"
User says "Yes" -> next request resumes execution
"""
from typing import Literal
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage

from app.agents.state import AgentState
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tool_policy import is_action_tool, is_confirmation, is_cancellation
from app.core.logging import get_logger

logger = get_logger(__name__)


def agent_node(state: AgentState, llm_with_tools) -> AgentState:
    """
    The main reasoning node.
    Calls the LLM with full message history + system prompt + tools.
    Returns updated state with new AIMessage (possibly with tool_calls).
    """
    messages = state["messages"]

    # Build system message with user context
    user_context = ""
    if state.get("user_email"):
        user_context = f"\n\nAuthenticated user email: {state['user_email']}"
    if state.get("user_id"):
        user_context += f"\nUser ID: {state['user_id']}"

    system_content = SYSTEM_PROMPT + user_context
    system_message = SystemMessage(content=system_content)
    llm_messages = [system_message] + list(messages)

    try:
        response = llm_with_tools.invoke(llm_messages)
        logger.info(
            "agent_node_complete",
            has_tool_calls=bool(getattr(response, "tool_calls", None)),
            content_preview=str(response.content)[:100] if response.content else "",
        )
        return {"messages": [response]}
    except Exception as e:
        logger.error("agent_node_error", error=str(e))
        error_msg = AIMessage(
            content="I encountered an error processing your request. Please try again."
        )
        return {"messages": [error_msg], "error": str(e)}


def action_gate_node(state: AgentState) -> AgentState:
    """
    Human-In-The-Loop gate node.

    This node runs AFTER agent_node and BEFORE the ToolNode.
    It inspects the pending tool calls and intercepts any ACTION tools.

    If an ACTION tool is found:
    1. Store it in state.pending_action
    2. Set state.awaiting_confirmation = True
    3. Replace the AIMessage tool_calls with a plain text confirmation request
    4. The graph will route to END instead of tools_node

    The next message from the user (saying "yes") will be processed by
    agent_node again, which will see the pending_action context.

    IMPORTANT: The actual enforcement happens here in Python, not in the LLM prompt.
    Even if the LLM is tricked, this gate will block the action.
    """
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    # Check if there is already a pending action waiting for confirmation
    pending = state.get("pending_action")
    awaiting = state.get("awaiting_confirmation", False)

    if awaiting and pending:
        # The user sent a new message while we're awaiting confirmation
        # Find the latest human message
        human_messages = [m for m in messages if isinstance(m, HumanMessage)]
        if human_messages:
            latest_human = human_messages[-1].content

            if is_confirmation(latest_human):
                # User confirmed! Clear the gate and allow execution.
                logger.info("hitl_confirmed", tool=pending.get("tool"))
                # We need to re-inject the tool call so tools_node can execute it
                # Create a synthetic AIMessage with the pending tool call
                import uuid
                tool_call_id = f"hitl_{str(uuid.uuid4())[:8]}"
                confirm_ai = AIMessage(
                    content="",
                    tool_calls=[{
                        "name": pending["tool"],
                        "args": pending["args"],
                        "id": tool_call_id,
                    }]
                )
                return {
                    "messages": [confirm_ai],
                    "awaiting_confirmation": False,
                    "pending_action": None,
                }

            elif is_cancellation(latest_human):
                # User cancelled
                logger.info("hitl_cancelled", tool=pending.get("tool"))
                cancel_msg = AIMessage(
                    content="Understood. I have cancelled the action. Is there anything else I can help you with?"
                )
                return {
                    "messages": [cancel_msg],
                    "awaiting_confirmation": False,
                    "pending_action": None,
                }

    # Check if the last message (from agent_node) contains ACTION tool calls
    if not isinstance(last_message, AIMessage):
        return {}

    tool_calls = getattr(last_message, "tool_calls", []) or []
    action_calls = [tc for tc in tool_calls if is_action_tool(tc.get("name", ""))]

    if not action_calls:
        # No action tools — pass through unchanged
        return {}

    # Found an ACTION tool call — intercept it
    action_call = action_calls[0]
    tool_name = action_call.get("name")
    tool_args = action_call.get("args", {})

    # Create a human-readable summary of what the action will do
    summary = _create_action_summary(tool_name, tool_args)

    logger.info("hitl_intercepted", tool=tool_name, summary=summary)

    # Store the pending action
    pending_action = {
        "tool": tool_name,
        "args": tool_args,
        "summary": summary,
    }

    # Replace the AIMessage (which had tool_calls) with a confirmation request
    confirmation_message = AIMessage(
        content=(
            f"Before I proceed, I need your confirmation:\n\n"
            f"**Action:** {summary}\n\n"
            f"**Type Yes to confirm or No to cancel.**"
        )
    )

    return {
        "messages": [confirmation_message],
        "awaiting_confirmation": True,
        "pending_action": pending_action,
    }


def _create_action_summary(tool_name: str, tool_args: dict) -> str:
    """Create a user-friendly summary of what action will be taken."""
    if tool_name == "create_support_ticket":
        title = tool_args.get("issue_title", "your issue")
        priority = tool_args.get("priority", "MEDIUM")
        order = tool_args.get("order_number", "")
        order_text = f" for order {order}" if order else ""
        return f"Create a {priority} priority support ticket{order_text}: \"{title}\""
    return f"Execute {tool_name} with args: {tool_args}"


def should_continue(state: AgentState) -> Literal["action_gate", "end"]:
    """
    Routing function: decides whether to go to action_gate (and potentially tools) or END.

    NOTE: The action_gate_node itself decides whether to route to tools or end.
    We always go through action_gate_node after agent_node to check for ACTION tools.
    """
    messages = state["messages"]
    if not messages:
        return "end"

    last_message = messages[-1]

    # If waiting for confirmation, do not loop back to tools
    if state.get("awaiting_confirmation"):
        return "end"

    # If the last message has tool calls, go to action_gate for policy check
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(
            "routing_to_action_gate",
            tools=[tc["name"] for tc in last_message.tool_calls]
        )
        return "action_gate"

    logger.info("routing_to_end")
    return "end"


def should_execute_tools(state: AgentState) -> Literal["tools", "end"]:
    """
    After action_gate_node: decide whether tools should execute or we should end.
    - If awaiting_confirmation is True -> END (we asked for confirmation)
    - If last message has tool_calls -> tools (action was confirmed or read-only)
    - Otherwise -> END
    """
    if state.get("awaiting_confirmation"):
        return "end"

    messages = state["messages"]
    if not messages:
        return "end"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "end"


def extract_final_response(state: AgentState) -> AgentState:
    """Post-processing node: extracts the final text response."""
    messages = state["messages"]
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            return {"final_response": message.content}
    return {"final_response": "I was unable to generate a response. Please try again."}
