"""
AgentOps - Evaluation API
==========================
Endpoints for triggering and retrieving AI evaluation results.

Endpoints:
  POST /api/evaluation/run    - Run the evaluation suite (authenticated)
  GET  /api/evaluation/latest - Get the latest evaluation report
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path
import json

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

REPORTS_DIR = Path(__file__).parent.parent.parent / "evaluation" / "reports"


@router.get("/latest")
def get_latest_evaluation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the most recent evaluation report.
    Returns metrics and per-test-case results.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = sorted(REPORTS_DIR.glob("eval_*.json"), reverse=True)

    if not reports:
        return {
            "status": "no_reports",
            "message": "No evaluation has been run yet. Use POST /api/evaluation/run to start one.",
            "metrics": None,
            "results": [],
        }

    try:
        with open(reports[0]) as f:
            report = json.load(f)
        return {
            "status": "ok",
            "report_file": reports[0].name,
            **report,
        }
    except Exception as e:
        logger.error("evaluation_report_load_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to load evaluation report")


@router.post("/run")
def trigger_evaluation(
    background_tasks: BackgroundTasks,
    limit: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger a new evaluation run in the background.
    This calls the real Groq LLM, so it may take several minutes.
    """
    try:
        background_tasks.add_task(_run_evaluation_background, limit)
        return {
            "status": "started",
            "message": f"Evaluation started with {limit or 'all'} test cases. Check /api/evaluation/latest for results.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _run_evaluation_background(limit: int = None):
    """Run evaluation in background task."""
    try:
        from evaluation.runner import run_evaluation
        run_evaluation(limit=limit)
        logger.info("background_evaluation_complete")
    except Exception as e:
        logger.error("background_evaluation_failed", error=str(e))


@router.get("/dataset")
def get_evaluation_dataset(
    current_user: User = Depends(get_current_user),
):
    """Get the evaluation dataset (test cases)."""
    dataset_path = Path(__file__).parent.parent.parent / "evaluation" / "dataset.json"
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")
    with open(dataset_path) as f:
        return json.load(f)
