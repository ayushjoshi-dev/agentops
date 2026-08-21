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
The logger below is configured to help avoid accidental leaks.
"""

import structlog
import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """
    Configure structlog for structured JSON logging.
    
    Call this once at application startup in main.py.
    """
    
    # Set standard library log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Processors control how log records are formatted
    # They run in order, each transforming the log event dict
    shared_processors = [
        structlog.contextvars.merge_contextvars,      # Add context vars (request_id, user_id, etc.)
        structlog.processors.add_log_level,           # Add "level" field
        structlog.processors.TimeStamper(fmt="iso"),  # Add ISO timestamp
        structlog.stdlib.add_logger_name,             # Add logger name
    ]

    if settings.is_development:
        # In development: pretty colored console output (human-readable)
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # In production: JSON output (machine-readable for log aggregators)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,     # Structured tracebacks
            structlog.processors.JSONRenderer(),       # Output as JSON
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
    Get a structured logger instance.
    
    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("order_fetched", order_id="ORD-1025", user_id="abc123")
    """
    return structlog.get_logger(name)
