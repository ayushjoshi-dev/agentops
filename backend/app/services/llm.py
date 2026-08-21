"""
AgentOps — LLM Service
========================

Returns a configured LLM instance based on environment settings.

WHY ABSTRACT THIS?
------------------
By centralizing LLM creation here, we can:
1. Switch providers (Groq → OpenAI) by changing one env var
2. Configure temperature, max_tokens in one place
3. Swap in a mock LLM for testing without changing agent code

Currently supported providers:
- groq   (fast, free, uses llama models)
- openai (paid, GPT-4 models)
"""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_llm():
    """
    Create and return a configured LLM instance.
    
    Provider is determined by settings.LLM_PROVIDER:
    - "groq"  → ChatGroq (free, fast)
    - "openai" → ChatOpenAI (paid)
    
    Returns:
        LangChain LLM instance ready for .invoke() or .bind_tools()
    """
    if settings.LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        logger.info("llm_created", provider="groq", model=settings.LLM_MODEL)
        return llm

    elif settings.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        logger.info("llm_created", provider="openai", model=settings.LLM_MODEL)
        return llm

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER}. "
            "Supported: 'groq', 'openai'"
        )
