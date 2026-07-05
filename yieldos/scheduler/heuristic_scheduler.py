"""
YieldOS Review Priority Heuristic — no optimizer dependency.

Sorts recovery candidates by risk (low->medium->high) then
benefit_score (high->low) to produce a human-review-ready priority order.

This is a REVIEW ROUTE PRIORITIZER, not an action scheduler.
It does not execute actions. It does not control hardware.
It produces recommendation_only output for human decision-making.
No hardware commands. No external dependencies.
"""
from __future__ import annotations

from typing import List

from .models import OptimizationCandidate, ScheduleCandidate, ScheduleResult

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


class HeuristicScheduler:
    """
    Priority-based scheduler. No optimizer dependency. Always available.

    Produces ScheduleResult with:
      execution_mode           = recommendation_only
      hardware_execution_enabled = false
      requires_human_review    = true
    """

    def schedule(
        self,
        candidates: List[OptimizationCandidate],
        case_id: str = "",
    ) -> ScheduleResult:
        sorted_cands = sorted(
            candidates,
            key=lambda c: (
                _RISK_ORDER.get(c.risk, 1),
                -c.benefit_score,
            ),
        )

        schedule = [
            ScheduleCandidate(
                rank=i + 1,
                candidate_id=c.candidate_id,
                action=c.action,
                risk=c.risk,
                benefit_score=c.benefit_score,
            )
            for i, c in enumerate(sorted_cands)
        ]

        return ScheduleResult(
            case_id=case_id,
            backend="heuristic",
            ordered_candidates=[c.candidate_id for c in sorted_cands],
            schedule=schedule,
            optimizer_info={"method": "risk_asc_benefit_desc"},
        )
