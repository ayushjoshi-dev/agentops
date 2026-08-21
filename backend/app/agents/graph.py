"""
AgentOps — LangGraph Agent Graph
===================================

This file assembles the complete agent graph.

LANGGRAPH CONCEPTS:
-------------------
StateGraph: The main graph object. Nodes are added to it.
           Edges define the flow between nodes.

START: The entry point (built-in)
END:   The exit point (built-in)

COMPILED GRAPH:
---------------
Calling .compile() builds the executable graph.
The compiled graph can be invoked with: graph.invoke(initial_state)

GRAPH STRUCTURE:
----------------
START
  |
  v
[agent_node]   ← calls LLM with tools
  |
  v
[should_continue?]
  |              |
  v              v
[tools_node]   [END]
  |
  v
[agent_node]   ← loop back
  ...

IMPORTANT: LangGraph uses ToolNode from langgraph.prebuilt which
automatically handles executing tool calls from AIMessages.
"""

from functools import partial
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.agents.state import AgentState
from app.agents.nodes import agent_node, should_continue, extract_final_response
from app.services.llm import get_llm
from app.tools.knowledge_tool import search_knowledge_base
from app.tools.order_tools import get_order_status, get_order_details, get_customer_orders
from app.tools.product_tools import search_products
from app.tools.ticket_tools import create_support_ticket
from app.tools.calculator_tool import calculate
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Tool Registry ─────────────────────────────────────────
# All tools available to the agent
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
    """
    Build and compile the LangGraph agent graph.
    
    Returns:
        Compiled LangGraph graph ready to invoke
    """
    # Get the LLM and bind tools to it
    # "bind_tools" tells the LLM about available tools in its system
    # The LLM can then choose to call them by outputting tool_calls
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    logger.info(
        "building_agent_graph",
        llm_model=settings.LLM_MODEL,
        num_tools=len(ALL_TOOLS),
        tool_names=[t.name for t in ALL_TOOLS],
    )

    # Create the agent node with the LLM bound
    # We use functools.partial to inject llm_with_tools
    _agent_node = partial(agent_node, llm_with_tools=llm_with_tools)

    # Create a ToolNode — executes all tool calls from AIMessage
    tool_node = ToolNode(ALL_TOOLS)

    # ── Build the Graph ───────────────────────────────────
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", tool_node)

    # Add edges
    # START → agent (always starts with agent reasoning)
    graph.add_edge(START, "agent")

    # agent → tools OR agent → END (conditional)
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        }
    )

    # tools → agent (always loop back after tool execution)
    graph.add_edge("tools", "agent")

    # Compile — this validates the graph and prepares it for execution
    compiled = graph.compile()

    logger.info("agent_graph_compiled")
    return compiled


# ── Singleton Graph Instance ──────────────────────────────
# Build the graph once at module load time
# Reuse it for all requests (LLM connection is expensive to set up)
_agent_graph = None


def get_agent_graph():
    """Get or create the compiled agent graph (singleton)."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = build_agent_graph()
    return _agent_graph
