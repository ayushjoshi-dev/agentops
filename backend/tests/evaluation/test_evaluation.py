"""
AgentOps — Evaluation Tests
============================
These tests run the evaluation dataset against the real agent.
Mark as live since they require a real Groq API key.

Run with: pytest tests/evaluation/ -m live
Skip live tests: pytest tests/ -m "not live"
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import pytest
import json
from pathlib import Path

DATASET_PATH = Path(__file__).parent.parent.parent / "evaluation" / "dataset.json"


@pytest.mark.live
def test_evaluation_dataset_is_valid():
    """Verify the evaluation dataset is correctly structured."""
    assert DATASET_PATH.exists(), f"Dataset not found at {DATASET_PATH}"
    with open(DATASET_PATH) as f:
        dataset = json.load(f)
    assert len(dataset) >= 30, "Dataset should have at least 30 test cases"
    required_fields = {"id", "question", "category"}
    for case in dataset:
        missing = required_fields - set(case.keys())
        assert not missing, f"Case {case.get('id')} missing fields: {missing}"


def test_metrics_calculation_with_perfect_results():
    """Test that metrics.py correctly calculates scores from mock results."""
    from evaluation.metrics import calculate_metrics
    mock_results = [
        {"id": "order_001", "category": "order", "expected_tools": ["get_order_status"],
         "tools_called": ["get_order_status"], "success": True, "latency_ms": 1200},
        {"id": "rag_001", "category": "rag", "expected_tools": ["search_knowledge_base"],
         "tools_called": ["search_knowledge_base"], "success": True, "latency_ms": 1800},
        {"id": "security_001", "category": "security", "expected_tools": [],
         "tools_called": [], "success": True, "latency_ms": 900},
    ]
    metrics = calculate_metrics(mock_results)
    assert metrics["tool_selection_accuracy"] == 100.0
    assert metrics["task_success_rate"] == 100.0
    assert metrics["rag_trigger_rate"] == 100.0


def test_metrics_with_failures():
    """Test metrics calculation with some failures."""
    from evaluation.metrics import calculate_metrics
    mock_results = [
        {"id": "order_001", "category": "order", "expected_tools": ["get_order_status"],
         "tools_called": ["search_products"],  # wrong tool
         "success": True, "latency_ms": 1200},
        {"id": "error_001", "category": "order", "expected_tools": [],
         "tools_called": [], "success": False, "latency_ms": 0, "error": "DB error"},
    ]
    metrics = calculate_metrics(mock_results)
    assert metrics["tool_selection_accuracy"] == 0.0  # wrong tool called
    assert metrics["task_success_rate"] == 50.0  # one failed
    assert metrics["error_rate"] == 50.0


def test_metrics_empty_expected_tools_not_counted():
    """Cases with no expected tools should not affect tool accuracy."""
    from evaluation.metrics import calculate_metrics
    mock_results = [
        {"id": "ood_001", "category": "out_of_domain", "expected_tools": [],
         "tools_called": [], "success": True, "latency_ms": 500},
    ]
    metrics = calculate_metrics(mock_results)
    # No expected tools → tool accuracy should be 0 (no cases to evaluate)
    assert metrics["tool_selection_accuracy"] == 0.0
    assert metrics["task_success_rate"] == 100.0
