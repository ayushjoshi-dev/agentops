"""
AgentOps - LangGraph Agent Graph (with HITL)
============================================
Assembles the complete agent graph with Human-In-The-Loop support.

GRAPH STRUCTURE:
----------------
START
  |
  v
[agent_node]       <- calls LLM with tools
  |
  v
[should_continue?]
  |                 |
  v                 v
[action_gate]    [END]
  |
[should_execute_tools?]
  |                 |
  v                 v
[tools_node]     [END]    <- awaiting_confirmation=True, ask user
  |
  v
[agent_node]       <- loop back with tool results
  ...
"""
from functools import partial
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.agents.state import AgentState
from app.agents.nodes import (
    agent_node, action_gate_node, should_continue,
    should_execute_tools, extract_final_response
)
from app.services.llm import get_llm
from app.tools.knowledge_tool import search_knowledge_base
from app.tools.order_tools import get_order_status, get_order_details, get_customer_orders
from app.tools.product_tools import search_products
from app.tools.ticket_tools import create_support_ticket
from app.tools.calculator_tool import calculate
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

ALL_TOOLS = [
    search_knowledge_base,
    get_order_status,
    get_order_details,
    get_customer_orders,
    search_products,
    create_support_ticket,
    calculate,
]


def build_agent_graph():
    """Build and compile the LangGraph agent graph with HITL support."""
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    logger.info(
        "building_agent_graph",
        llm_model=settings.LLM_MODEL,
        num_tools=len(ALL_TOOLS),
        tool_names=[t.name for t in ALL_TOOLS],
    )

    _agent_node = partial(agent_node, llm_with_tools=llm_with_tools)
    tool_node = ToolNode(ALL_TOOLS)

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", _agent_node)
    graph.add_node("action_gate", action_gate_node)
    graph.add_node("tools", tool_node)

    # START -> agent
    graph.add_edge(START, "agent")

    # agent -> action_gate OR end (conditional based on tool_calls presence)
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "action_gate": "action_gate",
            "end": END,
        }
    )

    # action_gate -> tools OR end (conditional based on HITL state)
    graph.add_conditional_edges(
        "action_gate",
        should_execute_tools,
        {
            "tools": "tools",
            "end": END,
        }
    )

    # tools -> agent (always loop back after tool execution)
    graph.add_edge("tools", "agent")

    compiled = graph.compile()
    logger.info("agent_graph_compiled")
    return compiled


_agent_graph = None


def get_agent_graph():
    """Get or create the compiled agent graph (singleton)."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = build_agent_graph()
    return _agent_graph
