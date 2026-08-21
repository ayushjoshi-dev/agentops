"""
AgentOps — Structured Logging
================================

WHY STRUCTURED LOGGING?
-----------------------
Standard Python logging outputs plain text:
    INFO:     GET /api/chat 200 OK

Structured logging outputs JSON:
    {"event": "chat_request", "user_id": "abc", "latency_ms": 123, "level": "info"}

JSON logs are:
- Machine-readable → can be ingested by Datadog, CloudWatch, Grafana Loki
- Filterable → find all logs for user_id="abc" easily
- Searchable → grep for specific conversation_id or agent_run_id

We use `structlog` which makes Python logging produce JSON automatically.

SECURITY NOTE:
--------------
NEVER log passwords, JWT tokens, or API keys.
"""

import structlog
import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """
    Configure structlog for structured logging.

    In development: pretty colored console output.
    In production:  JSON output for log aggregators.

    Call this ONCE at application startup in main.py.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure stdlib logging (used by uvicorn, SQLAlchemy, etc.)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Shared processors — run on every log event regardless of environment
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,       # thread-local context vars
        structlog.processors.add_log_level,            # add "level" field
        structlog.processors.TimeStamper(fmt="iso"),   # ISO timestamp
        # NOTE: add_logger_name removed — incompatible with PrintLoggerFactory
    ]

    if settings.is_development:
        # Development: human-readable colored output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Production: machine-readable JSON
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a bound structlog logger.

    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("order_fetched", order_id="ORD-1025", latency_ms=45)
    """
    return structlog.get_logger(name)
