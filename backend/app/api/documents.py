"""AgentOps — Documents (RAG) API"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.schemas import IngestResponse, DocumentResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents / RAG"])


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    force: bool = False,
):
    """
    Trigger RAG ingestion of all knowledge documents.
    
    Reads all .txt files from the /knowledge directory,
    generates embeddings, and stores chunks in the database.
    
    Set force=True to re-ingest already processed documents.
    
    Note: Requires sentence-transformers installed (requirements-ml.txt)
    """
    try:
        from app.rag.ingestion import ingest_knowledge_documents
        result = ingest_knowledge_documents(db, force=force)
        return IngestResponse(
            total_chunks=result["total_chunks"],
            documents=result["documents"],
            status="completed",
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="sentence-transformers not installed. Run: pip install -r requirements-ml.txt"
        )
    except Exception as e:
        logger.error("ingestion_api_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all ingested documents."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return docs
