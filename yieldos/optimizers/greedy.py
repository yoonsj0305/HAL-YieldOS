"""
YieldOS Greedy Optimizer — pure Python, no external dependencies.

Sorts recovery candidates by risk (low first) then benefit_score (high first).
Used as the default backend when SQBM is not installed.
Always produces recommendation_only results with hardware_execution_enabled=False.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base import OptimizationResult, OptimizerBackend

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


class GreedyOptimizer(OptimizerBackend):
    """
    Pure-Python greedy optimizer for recovery candidate prioritization.

    Algorithm:
      Sort by (risk_rank ascending, benefit_score descending).
      Select top max_select candidates.

    No external dependencies. Always available.
    """

    name = "greedy"

    def optimize(self, problem: Dict[str, Any]) -> OptimizationResult:
        """
        problem = {
            "candidates": [
                {"action": str, "risk": str, "benefit_score": float},
                ...
            ],
            "max_select": int  (optional, default: all)
        }
        """
        candidates: List[dict] = problem.get("candidates", [])
        max_select: int = problem.get("max_select", len(candidates))

        if not candidates:
            return OptimizationResult(
                backend="greedy",
                objective_value=0.0,
                selected_indices=[],
                hardware_execution_enabled=False,
            )

        scored = sorted(
            enumerate(candidates),
            key=lambda iv: (
                _RISK_ORDER.get(iv[1].get("risk", "medium"), 1),
                -iv[1].get("benefit_score", 0.0),
            ),
        )

        selected = [idx for idx, _ in scored[:max_select]]
        total_benefit = sum(
            candidates[i].get("benefit_score", 0.0) for i in selected
        )

        return OptimizationResult(
            backend="greedy",
            objective_value=round(total_benefit, 6),
            selected_indices=selected,
            hardware_execution_enabled=False,
            metadata={
                "method": "risk_asc_benefit_desc",
                "n_candidates": len(candidates),
                "n_selected": len(selected),
            },
        )

    def is_available(self) -> bool:
        return True
