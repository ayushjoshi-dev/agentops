"""
AgentOps — FastAPI Application Entry Point
============================================

This is the main file that boots up the entire backend.

WHAT HAPPENS WHEN THE SERVER STARTS:
1. Python runs this file
2. FastAPI() creates the application instance
3. lifespan() runs startup code (DB check, logging init)
4. All routers (API routes) are registered
5. uvicorn starts listening for HTTP requests

UVICORN:
--------
uvicorn is an ASGI server — it runs FastAPI apps.
Think of it like nginx for Python, but simpler.

Start command: uvicorn app.main:app --host 0.0.0.0 --port 8000

In production on Render:
    uvicorn app.main:app --host 0.0.0.0 --port $PORT
    (Render sets $PORT automatically — never hardcode it)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.database import check_database_connection

# Import API routers (we'll add these in future milestones)
from app.api.health import router as health_router

logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────
# FastAPI's lifespan replaces old @app.on_event("startup").
# Code before `yield` runs at startup.
# Code after `yield` runs at shutdown.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    
    # ── STARTUP ──────────────────────────────────────────
    setup_logging()
    logger.info(
        "agentops_starting",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        llm_model=settings.LLM_MODEL,
    )
    
    # Test database connection
    db_ok = check_database_connection()
    if not db_ok:
        logger.error("startup_failed_no_database")
        # Don't crash — let health endpoint report the issue
    
    logger.info("agentops_ready", host=settings.HOST, port=settings.PORT)
    
    yield  # Application runs here
    
    # ── SHUTDOWN ─────────────────────────────────────────
    logger.info("agentops_shutting_down")


# ── FastAPI Application Instance ──────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## AgentOps — AI-Powered Customer Operations Agent
    
    An Agentic AI system for e-commerce customer support.
    
    ### Features
    - 🤖 **Multi-step AI Agent** powered by LangGraph
    - 📚 **RAG** with semantic search over policy documents
    - 🛠️ **Tool Calling** for order lookup, ticket creation, and more
    - 💬 **Conversational Memory** stored in PostgreSQL
    - 🔍 **Agent Observability** with execution traces
    - 🔐 **JWT Authentication**
    
    ### Architecture
    User → FastAPI → LangGraph Agent → Tools + RAG → Supabase PostgreSQL
    """,
    docs_url="/docs",         # Swagger UI at /docs
    redoc_url="/redoc",       # ReDoc UI at /redoc
    lifespan=lifespan,
)


# ── CORS Middleware ────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
# 
# Browsers block requests from one origin to another by default.
# Our React frontend (localhost:5173) calls the backend (localhost:8000).
# These are different origins, so we need to allow it explicitly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,           # Allow cookies / auth headers
    allow_methods=["*"],              # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],              # Content-Type, Authorization, etc.
)


# ── Routers ───────────────────────────────────────────────
# Each router handles a group of related endpoints.
# We use prefixes to organize routes.
app.include_router(health_router, prefix="/api", tags=["Health"])

# Future milestones will add:
# from app.api.auth import router as auth_router
# from app.api.chat import router as chat_router
# from app.api.conversations import router as conversations_router
# from app.api.orders import router as orders_router
# from app.api.tickets import router as tickets_router
# from app.api.documents import router as documents_router


# ── Root Endpoint ─────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    """Root endpoint — confirms API is running."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "status": "running",
    }
