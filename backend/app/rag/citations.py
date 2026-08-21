"""
AgentOps — Citation Formatting
================================

After semantic search returns chunks, we format them into
human-readable citations for the frontend.

WHAT DOES A CITATION LOOK LIKE?
---------------------------------
{
  "source": "refund_policy.txt",
  "section": "Refund Eligibility",
  "doc_type": "policy",
  "preview": "Refunds can be requested within 7 days of delivery..."
}

WHY ARE CITATIONS IMPORTANT?
-----------------------------
Without citations, the user doesn't know WHERE the AI got its answer.
This is critical for a customer support agent — customers want to
know they're getting official policy information, not AI speculation.

Citations also prevent hallucination: if a claim doesn't have a
citation, the agent shouldn't make it.
"""

from typing import List, Dict, Any


def format_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Convert retrieved chunks into formatted citations.
    
    Args:
        chunks: List of chunk dicts from semantic_search()
    
    Returns:
        Deduplicated list of citation dicts
    """
    seen = set()
    citations = []

    for chunk in chunks:
        # Create a unique key for deduplication
        # Same source + section = one citation, even if multiple chunks
        key = (chunk.get("filename", ""), chunk.get("section", ""))

        if key not in seen:
            seen.add(key)
            citations.append({
                "source": chunk.get("filename", "Unknown"),
                "section": chunk.get("section", "General"),
                "doc_type": chunk.get("doc_type", "policy"),
                "preview": chunk.get("content", "")[:150] + "...",
                "similarity": chunk.get("similarity", 0),
            })

    return citations


def format_context_for_llm(chunks: List[Dict[str, Any]]) -> str:
    """
    Format retrieved chunks into a context string for the LLM.
    
    This is the text injected into the LLM prompt as "knowledge".
    
    Args:
        chunks: List of chunk dicts from semantic_search()
    
    Returns:
        Formatted context string
    """
    if not chunks:
        return "No relevant information found in the knowledge base."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("filename", "Unknown")
        section = chunk.get("section", "General")
        content = chunk.get("content", "")

        parts.append(
            f"[Source {i}: {source} — {section}]\n{content}"
        )

    return "\n\n---\n\n".join(parts)
