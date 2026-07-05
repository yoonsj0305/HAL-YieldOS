"""
YieldOS SQBM Optional Backend — Simulated Bifurcation Machine optimizer.

This module uses LAZY IMPORT: yieldos_sqbm is NOT imported at module load time.
It is only imported when SQBMOptimizer().optimize() is called.

If yieldos_sqbm is not installed, is_available() returns False and
get_optimizer('sqbm', fallback=True) silently falls back to GreedyOptimizer.

Installation:
  pip install hal-yieldos[sqbm]
  # or
  pip install yieldos-sqbm

Safety invariant: OptimizationResult.hardware_execution_enabled is ALWAYS False.
SQBM finds optimal candidate rankings. It does not execute hardware actions.
"""
from __future__ import annotations

from typing import Any, Dict

from .base import OptimizationResult, OptimizerBackend


class SQBMOptimizer(OptimizerBackend):
    """
    SQBM backend for recovery candidate optimization.

    Uses the Simulated Bifurcation Machine (Goto et al., Science Advances 2019/2021)
    to solve a QUBO formulation of the candidate selection problem.

    Requires: pip install hal-yieldos[sqbm]
    """

    name = "sqbm"

    def __init__(self):
        self._available: bool | None = None  # lazily checked

    def is_available(self) -> bool:
        if self._available is None:
            try:
                import yieldos_sqbm  # noqa: F401
                self._available = True
            except ImportError:
                self._available = False
        return self._available

    def optimize(self, problem: Dict[str, Any]) -> OptimizationResult:
        if not self.is_available():
            raise ImportError(
                "SQBM backend is not installed.\n"
                "Install with: pip install hal-yieldos[sqbm]\n"
                "Or use: yieldos semiforge simulate --optimizer greedy"
            )
        return self._run(problem)

    def _run(self, problem: Dict[str, Any]) -> OptimizationResult:
        import torch
        import yieldos_sqbm

        candidates = problem.get("candidates", [])
        n = len(candidates)

        if n == 0:
            return OptimizationResult(
                backend="sqbm",
                objective_value=0.0,
                selected_indices=[],
                hardware_execution_enabled=False,
            )

        # Build QUBO: maximize Σ score_i * x_i
        # Score = benefit_score - risk_penalty
        _risk_penalty = {"low": 0.05, "medium": 0.30, "high": 0.60}
        scores = [
            c.get("benefit_score", 0.5) - _risk_penalty.get(c.get("risk", "medium"), 0.3)
            for c in candidates
        ]

        # QUBO diagonal: minimize -score_i * x_i  (we minimize, so negate the objective)
        Q = torch.zeros(n, n, dtype=torch.float32)
        for i, s in enumerate(scores):
            Q[i, i] = -float(s)

        J, h = yieldos_sqbm.from_qubo(Q)
        solver = yieldos_sqbm.SQBM(mode="dSB", agents=16, steps=300)
        result = solver.solve_ising(J, h)
        binary = result.to_binary().tolist()

        # Build ordering: selected (binary=1) first by score desc, then unselected
        selected = sorted(
            [i for i, b in enumerate(binary) if b == 1],
            key=lambda i: -scores[i],
        )
        unselected = sorted(
            [i for i, b in enumerate(binary) if b == 0],
            key=lambda i: -scores[i],
        )
        max_select = problem.get("max_select", n)
        ordered = (selected + unselected)[:max_select]

        obj = sum(scores[i] for i in ordered)

        return OptimizationResult(
            backend="sqbm",
            objective_value=round(float(obj), 6),
            selected_indices=ordered,
            hardware_execution_enabled=False,
            metadata={
                "energy": float(result.energy),
                "converged": bool(result.converged),
                "iterations": int(result.iterations),
                "device": str(result.device),
                "n_candidates": n,
            },
        )
