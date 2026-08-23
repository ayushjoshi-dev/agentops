"""
AgentOps — AI Evaluation Runner
=================================
Runs the evaluation dataset against the live agent and records results.

USAGE:
    cd backend
    python -m evaluation.runner

    # Or with specific output file:
    python -m evaluation.runner --output evaluation/reports/run_$(date +%Y%m%d).json

NOTE: This calls the REAL Groq LLM. Requires GROQ_API_KEY in environment.
Label these as "live" tests in pytest with @pytest.mark.live.

HOW IT WORKS:
1. Load dataset.json
2. For each test case, call the agent service (same code as production)
3. Record which tools were called, latency, and whether response was valid
4. Calculate metrics with metrics.py
5. Save results to evaluation/reports/
"""
import json
import sys
import os
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

DATASET_PATH = Path(__file__).parent / "dataset.json"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

DEMO_USER_ID = "40a68a79-aab7-4995-a489-f0915d3dbaef"
DEMO_EMAIL = "demo@shopease.com"


def run_evaluation(limit: int = None, output_path: str = None) -> dict:
    """
    Run the full evaluation suite against the live agent.
    
    Args:
        limit: If set, only run first N test cases (useful for quick smoke tests)
        output_path: Where to save the JSON report
    
    Returns:
        dict with results and metrics
    """
    from app.core.database import SessionLocal
    from app.services.agent_service import run_agent
    from evaluation.metrics import calculate_metrics, format_report

    print(f"Loading evaluation dataset from {DATASET_PATH}...")
    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    if limit:
        dataset = dataset[:limit]

    print(f"Running {len(dataset)} test cases against live agent...")
    print("-" * 60)

    results = []
    db = SessionLocal()

    try:
        for i, case in enumerate(dataset):
            print(f"[{i+1}/{len(dataset)}] {case['id']}: {case['question'][:60]}...")

            start_time = time.time()
            tools_called = []
            success = False
            response_text = ""
            error_msg = None

            try:
                result = run_agent(
                    user_message=case["question"],
                    user_id=DEMO_USER_ID,
                    user_email=DEMO_EMAIL,
                    db=db,
                    is_demo=True,
                )

                latency_ms = int((time.time() - start_time) * 1000)
                response_text = result.get("response", "")
                tools_called = [tc["tool"] for tc in result.get("tool_calls_trace", [])]

                # Success = non-empty response without error prefix
                success = (
                    bool(response_text)
                    and not response_text.startswith("I encountered an error")
                    and len(response_text) > 20
                )

                status_icon = "✅" if success else "❌"
                print(f"   {status_icon} Tools: {tools_called} | {latency_ms}ms")

            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                error_msg = str(e)
                success = False
                print(f"   ❌ ERROR: {error_msg[:80]}")

            results.append({
                "id": case["id"],
                "category": case["category"],
                "question": case["question"],
                "expected_tools": case.get("expected_tools", []),
                "expected_behavior": case.get("expected_behavior", ""),
                "tools_called": tools_called,
                "response_preview": response_text[:200] if response_text else "",
                "success": success,
                "latency_ms": latency_ms,
                "error": error_msg,
            })

    finally:
        db.close()

    # Calculate metrics
    from evaluation.metrics import calculate_metrics, format_report
    metrics = calculate_metrics(results)

    print("\n" + format_report(metrics))

    # Save report
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if not output_path:
        output_path = str(REPORTS_DIR / f"eval_{timestamp}.json")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(dataset),
        "metrics": metrics,
        "results": results,
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {output_path}")
    return report


def get_latest_report() -> dict:
    """Load the most recent evaluation report from disk."""
    reports = sorted(REPORTS_DIR.glob("eval_*.json"), reverse=True)
    if not reports:
        return {}
    with open(reports[0]) as f:
        return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AgentOps AI evaluation")
    parser.add_argument("--limit", type=int, help="Limit to first N test cases")
    parser.add_argument("--output", type=str, help="Output file path")
    args = parser.parse_args()
    run_evaluation(limit=args.limit, output_path=args.output)
