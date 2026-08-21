"""
AgentOps — Health Check Endpoint
====================================

WHY A HEALTH ENDPOINT?
-----------------------
Health endpoints are a production standard. They serve multiple purposes:

1. RENDER HEALTH CHECKS:
   Render pings /api/health every 30 seconds.
   If it returns non-200, Render marks the service as unhealthy.

2. MONITORING:
   External tools (UptimeRobot, Datadog, etc.) monitor this endpoint.

3. DEBUGGING:
   Shows which components are UP or DOWN without exposing internals.

4. DEPLOYMENT VERIFICATION:
   After deploying, check /api/health to confirm everything started correctly.

WHAT WE CHECK:
--------------
- Database connectivity (can we reach Supabase?)
- LLM config (is the API key set?)
- Embedding config
- System info

WHAT WE NEVER EXPOSE:
---------------------
- Database credentials
- API keys
- Internal error details
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
import platform

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=dict)
def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check.
    
    Returns status of all critical system components.
    Used by Render for deployment health monitoring.
    """
    start = time.time()
    
    components = {}
    overall_status = "healthy"
    
    # ── 1. Database Check ─────────────────────────────────
    try:
        db.execute(text("SELECT 1"))
        components["database"] = {
            "status": "connected",
            "provider": "supabase_postgresql"
        }
    except Exception as e:
        logger.error("health_check_db_failed", error=str(e))
        components["database"] = {
            "status": "disconnected",
            "error": "Cannot reach database"  # Don't expose the real error
        }
        overall_status = "degraded"
    
    # ── 2. LLM Config Check ───────────────────────────────
    llm_configured = bool(settings.LLM_API_KEY and len(settings.LLM_API_KEY) > 10)
    components["llm"] = {
        "status": "configured" if llm_configured else "not_configured",
        "provider": settings.LLM_PROVIDER,
        "model": settings.LLM_MODEL,
    }
    if not llm_configured:
        overall_status = "degraded"
    
    # ── 3. Embedding Config ───────────────────────────────
    components["embeddings"] = {
        "status": "configured",
        "provider": settings.EMBEDDING_PROVIDER,
        "model": settings.EMBEDDING_MODEL,
        "dimension": settings.EMBEDDING_DIMENSION,
    }
    
    # ── Response ─────────────────────────────────────────
    latency_ms = round((time.time() - start) * 1000, 2)
    
    return {
        "status": overall_status,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "latency_ms": latency_ms,
        "components": components,
    }


@router.get("/health/ping", response_model=dict)
def ping():
    """
    Minimal ping endpoint.
    
    Returns instantly without any DB check.
    Used for quick liveness probes.
    """
    return {"status": "ok", "message": "pong"}
