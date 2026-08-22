"""
AgentOps - Tool Policy
========================
Classifies tools as READ_ONLY or ACTION.

WHY THIS EXISTS:
----------------
READ_ONLY tools: query data, no side effects, safe to run immediately
ACTION tools: write data, create records, have real-world consequences

The backend enforces this separation so the LLM cannot be tricked
into bypassing confirmation for sensitive actions.

INTERVIEW NOTE:
---------------
This is the "Tool Authorization Layer" in a production AI system.
In enterprise settings, you might also have RBAC (Role-Based Access Control)
where different user roles can access different tools.
"""

# Tools that only READ data - safe to execute immediately
READ_ONLY_TOOLS = {
    "get_order_status",
    "get_order_details",
    "get_customer_orders",
    "search_products",
    "search_knowledge_base",
    "calculate",
}

# Tools that WRITE data or have side effects - require user confirmation
ACTION_TOOLS = {
    "create_support_ticket",
}

# Keywords in user messages that strongly indicate confirmation
CONFIRMATION_KEYWORDS = {
    "yes", "yep", "yeah", "confirm", "proceed", "ok", "okay",
    "do it", "create it", "go ahead", "sure", "please", "create the ticket",
    "submit", "create", "raise"
}

# Keywords that indicate cancellation
CANCELLATION_KEYWORDS = {
    "no", "nope", "cancel", "stop", "dont", "don't", "nevermind",
    "never mind", "abort", "wait", "hold on"
}


def is_action_tool(tool_name: str) -> bool:
    """Returns True if the tool requires user confirmation before execution."""
    return tool_name in ACTION_TOOLS


def is_confirmation(user_message: str) -> bool:
    """Check if a user message is a confirmation response."""
    msg_lower = user_message.strip().lower()
    return any(kw in msg_lower for kw in CONFIRMATION_KEYWORDS)


def is_cancellation(user_message: str) -> bool:
    """Check if a user message is a cancellation response."""
    msg_lower = user_message.strip().lower()
    return any(kw in msg_lower for kw in CANCELLATION_KEYWORDS)
