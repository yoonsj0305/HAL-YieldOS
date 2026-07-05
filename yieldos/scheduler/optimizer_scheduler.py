"""
YieldOS Recovery Route Prioritizer — pluggable optimizer backend.

Ranks recovery candidates using a pluggable optimizer (greedy or SQBM)
to produce a human-review-ready priority order.

This is a REVIEW ROUTE PRIORITIZER, not an action scheduler.
It does not execute actions. It does not control hardware.
Falls back to deterministic heuristic if SQBM is unavailable.

Safety invariant: ScheduleResult always has hardware_execution_enabled=False.
"""
from __future__ import annotations

from typing import List

from ..optimizers import GreedyOptimizer
from .models import OptimizationCandidate, ScheduleCandidate, ScheduleResult


class OptimizerScheduler:
    """
    Scheduler backed by a pluggable optimizer (greedy or sqbm).

    Parameters
    ----------
    optimizer_name : 'greedy' | 'sqbm'
    fallback       : if True and sqbm unavailable, silently use greedy

    All output is recommendation_only with hardware_execution_enabled=False.
    """

    def __init__(self, optimizer_name: str = "greedy", fallback: bool = True):
        self._requested = optimizer_name
        self._fallback = fallback
        self._used: str = optimizer_name
        self._fallback_reason: str = ""
        self._opt = None

    def _resolve_optimizer(self):
        if self._opt is not None:
            return self._opt

        if self._requested == "sqbm":
            from ..optimizers.sqbm_optional import SQBMOptimizer
            candidate = SQBMOptimizer()
            if candidate.is_available():
                self._opt = candidate
                self._used = "sqbm"
            elif self._fallback:
                self._opt = GreedyOptimizer()
                self._used = "greedy"
                self._fallback_reason = "SQBM backend not installed"
            else:
                raise ImportError(
                    "SQBM backend not installed. "
                    "Install with: pip install hal-yieldos[sqbm]"
                )
        else:
            self._opt = GreedyOptimizer()
            self._used = "greedy"

        return self._opt

    def schedule(
        self,
        candidates: List[OptimizationCandidate],
        case_id: str = "",
    ) -> ScheduleResult:
        opt = self._resolve_optimizer()
        problem = {
            "candidates": [
                {
                    "action": c.action,
                    "risk": c.risk,
                    "benefit_score": c.benefit_score,
                }
                for c in candidates
            ],
            "max_select": len(candidates),
        }
        result = opt.optimize(problem)

        # Reorder candidates by optimizer result; put unselected at end
        selected_set = set(result.selected_indices)
        ordered = (
            [candidates[i] for i in result.selected_indices]
            + [c for i, c in enumerate(candidates) if i not in selected_set]
        )

        schedule = [
            ScheduleCandidate(
                rank=i + 1,
                candidate_id=c.candidate_id,
                action=c.action,
                risk=c.risk,
                benefit_score=c.benefit_score,
            )
            for i, c in enumerate(ordered)
        ]

        _is_fallback = self._used != self._requested
        optimizer_info: dict = {
            "requested": self._requested,
            "used": self._used,
            "fallback": _is_fallback,
            "backend_available": not _is_fallback,
            "claim_boundary": (
                "optimizer_fallback_not_sqbm_result" if _is_fallback
                else f"{self._used}_optimizer_candidate_only"
            ),
        }
        if self._fallback_reason:
            optimizer_info["reason"] = self._fallback_reason
            optimizer_info["warning"] = (
                "Optimizer unavailable. Falling back to deterministic heuristic scheduler."
            )
        optimizer_info.update(result.metadata)

        return ScheduleResult(
            case_id=case_id,
            backend=self._used,
            ordered_candidates=[c.candidate_id for c in ordered],
            schedule=schedule,
            optimizer_info=optimizer_info,
        )
