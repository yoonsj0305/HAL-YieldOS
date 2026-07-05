"""
YieldOS Scheduler Layer — recommendation-only candidate ordering.

The scheduler takes recovery candidates and produces a prioritized
ScheduleResult. It does NOT execute actions. It does NOT generate
hardware commands. All output carries:

  execution_mode           = recommendation_only
  hardware_execution_enabled = false
  requires_human_review    = true

Available schedulers:
  HeuristicScheduler   — risk/benefit sort, no optimizer dependency
  OptimizerScheduler   — uses greedy or sqbm backend
"""

from .heuristic_scheduler import HeuristicScheduler
from .models import (
    OptimizationCandidate,
    ResourceConstraint,
    SafetyBoundary,
    ScheduleCandidate,
    ScheduleResult,
)
from .optimizer_scheduler import OptimizerScheduler

__all__ = [
    "OptimizationCandidate",
    "ScheduleCandidate",
    "ScheduleResult",
    "ResourceConstraint",
    "SafetyBoundary",
    "HeuristicScheduler",
    "OptimizerScheduler",
]
