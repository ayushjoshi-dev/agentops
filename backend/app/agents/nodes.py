"""
AgentOps — LangGraph Agent Nodes
===================================

Nodes are the processing units of the LangGraph graph.
Each node is a Python function that takes State and returns updated State.

NODE TYPES:
-----------
1. agent_node: Calls the LLM to decide what to do next.
   - Input: current state (messages + context)
   - Output: AIMessage (possibly with tool_calls attached)

2. tools_node: Executes tool calls requested by the LLM.
   - Input: AIMessage with tool_calls
   - Output: ToolMessages (one per tool call)

ROUTING LOGIC:
--------------
After agent_node runs:
  - If AIMessage has tool_calls → go to tools_node
  - If AIMessage has no tool_calls → END (agent is done)

This creates the ReAct loop:
  agent → tools → agent → tools → ... → agent (no tools) → END
"""

from typing import Literal
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from app.agents.state import AgentState
from app.agents.prompts import SYSTEM_PROMPT
from app.core.logging import get_logger

logger = get_logger(__name__)


def agent_node(state: AgentState, llm_with_tools) -> AgentState:
    """
    The main reasoning node.
    
    Calls the LLM with:
    1. System prompt (persona + rules)
    2. Full conversation history
    3. Tools bound to the LLM
    
    Returns:
        Updated state with new AIMessage (possibly with tool_calls)
    """
    messages = state["messages"]

    # Build the full message list for the LLM
    system_message = SystemMessage(content=SYSTEM_PROMPT)

    # Add user context to system message if available
    user_context = ""
    if state.get("user_email"):
        user_context = f"\n\nAuthenticated user email: {state['user_email']}"
    if state.get("user_id"):
        user_context += f"\nUser ID: {state['user_id']}"

    if user_context:
        system_message = SystemMessage(content=SYSTEM_PROMPT + user_context)

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
        error_msg = AIMessage(content=f"I encountered an error processing your request: {str(e)}. Please try again.")
        return {"messages": [error_msg], "error": str(e)}


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """
    Routing function: decides whether to call tools or end.
    
    This is called after every agent_node run.
    Returns "tools" if the last message has tool calls, "end" otherwise.
    """
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM requested tool calls, route to tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(
            "routing_to_tools",
            tools=[tc["name"] for tc in last_message.tool_calls]
        )
        return "tools"

    # No tool calls → agent is done
    logger.info("routing_to_end", response_preview=str(last_message.content)[:100])
    return "end"


def extract_final_response(state: AgentState) -> AgentState:
    """
    Post-processing node: extracts the final text response.
    Called just before END to prepare the output.
    """
    messages = state["messages"]
    
    # Find the last AIMessage with text content
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            return {"final_response": message.content}
    
    return {"final_response": "I was unable to generate a response. Please try again."}
