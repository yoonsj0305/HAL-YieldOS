"""
SQBM backend tests — marked with @pytest.mark.sqbm.
These tests only run when the optional SQBM backend is installed.

Run with: pytest -m sqbm
Run without (default): pytest  (skips all tests in this file)

Safety principle:
  Even with SQBM, hardware_execution_enabled must remain False.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _sqbm_available() -> bool:
    try:
        from yieldos.optimizers.sqbm_optional import SQBMOptimizer
        return SQBMOptimizer().is_available()
    except Exception:
        return False


pytestmark = pytest.mark.sqbm


@pytest.mark.sqbm
def test_sqbm_backend_outputs_optimization_result():
    """SQBM backend produces a valid OptimizationResult when installed."""
    from yieldos.optimizers.base import OptimizationResult
    from yieldos.optimizers.sqbm_optional import SQBMOptimizer
    if not _sqbm_available():
        pytest.skip("SQBM backend not installed")
    opt = SQBMOptimizer()
    problem = {
        "candidates": [
            {"action": "a", "risk": "low",    "benefit_score": 0.9},
            {"action": "b", "risk": "medium", "benefit_score": 0.6},
            {"action": "c", "risk": "high",   "benefit_score": 0.8},
        ]
    }
    result = opt.optimize(problem)
    assert isinstance(result, OptimizationResult)
    assert isinstance(result.selected_indices, list)
    assert result.backend == "sqbm"


@pytest.mark.sqbm
def test_sqbm_backend_never_enables_hardware_execution():
    """SQBM result must have hardware_execution_enabled=False."""
    from yieldos.optimizers.sqbm_optional import SQBMOptimizer
    if not _sqbm_available():
        pytest.skip("SQBM backend not installed")
    opt = SQBMOptimizer()
    result = opt.optimize({
        "candidates": [
            {"action": "x", "risk": "low", "benefit_score": 0.7},
        ]
    })
    assert result.hardware_execution_enabled is False


@pytest.mark.sqbm
def test_sqbm_backend_can_be_absent_without_breaking_default_cli():
    """Without SQBM, default CLI must still work (greedy fallback)."""
    from yieldos.optimizers import get_optimizer
    from yieldos.optimizers.greedy import GreedyOptimizer
    # Always possible regardless of SQBM installation
    opt = get_optimizer("greedy")
    assert isinstance(opt, GreedyOptimizer)
    result = opt.optimize({
        "candidates": [{"action": "a", "risk": "low", "benefit_score": 0.8}]
    })
    assert result.hardware_execution_enabled is False
