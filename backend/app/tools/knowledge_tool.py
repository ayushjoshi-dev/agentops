"""
AgentOps — Knowledge Base Search Tool
========================================

This tool is called by the LangGraph agent when a user asks
a policy-related question (refunds, returns, shipping, etc.)

WHEN DOES THE AGENT CALL THIS TOOL?
------------------------------------
LLM decides based on the user message content:
- "What is your refund policy?" → search_knowledge_base
- "Can I return a product?" → search_knowledge_base
- "How long does shipping take?" → search_knowledge_base
- "Where is my order?" → get_order_status (NOT this tool)

HOW TOOL CALLING WORKS:
------------------------
1. LLM receives the user message + tool definitions
2. LLM outputs a structured "I want to call tool X with args Y"
3. LangGraph intercepts this, runs the actual Python function
4. Result is fed back to LLM as a ToolMessage
5. LLM generates final response using the tool result as context
"""

import json
from typing import Optional, TYPE_CHECKING

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.rag.retrieval import semantic_search
from app.rag.citations import format_context_for_llm, format_citations
from app.core.logging import get_logger

logger = get_logger(__name__)

# We'll inject the db session via a wrapper — see agent_service.py
_db_session: Optional[Session] = None


def set_db_session(db: Session):
    """Inject database session for tool use."""
    global _db_session
    _db_session = db


@tool
def search_knowledge_base(query: str) -> str:
    """
    Search ShopEase's knowledge base for policy information, FAQs, and guidelines.
    
    Use this tool when the user asks about:
    - Refund policy or refund eligibility
    - Return policy or how to return a product
    - Shipping information or delivery timelines
    - Warranty information or warranty claims
    - Cancellation policy
    - FAQs about ShopEase services
    
    Args:
        query: The user's question to search for in the knowledge base
    
    Returns:
        Relevant policy information with source citations
    """
    if _db_session is None:
        logger.error("knowledge_tool_no_db_session")
        return "Error: Knowledge base search unavailable. Database not connected."

    try:
        chunks = semantic_search(query, _db_session, top_k=5)

        if not chunks:
            return "I could not find specific information about this topic in our knowledge base. Please contact our support team for assistance."

        context = format_context_for_llm(chunks)
        citations = format_citations(chunks)

        # Format citations as readable text
        citation_text = "\n".join(
            f"  - {c['source']} (Section: {c['section']})"
            for c in citations
        )

        result = f"""KNOWLEDGE BASE RESULTS:
{context}

SOURCES:
{citation_text}"""

        logger.info(
            "knowledge_search_complete",
            query=query[:100],
            num_chunks=len(chunks),
            num_citations=len(citations),
        )
        return result

    except Exception as e:
        logger.error("knowledge_search_error", error=str(e), query=query)
        return f"Error searching knowledge base: {str(e)}"
