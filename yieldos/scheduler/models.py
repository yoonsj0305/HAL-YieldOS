"""
YieldOS Scheduler Data Models.

All ScheduleResult objects carry:
  execution_mode           = recommendation_only
  hardware_execution_enabled = false
  requires_human_review    = true

The scheduler outputs recommendations for human review.
It does not produce hardware commands, robot commands, satellite commands,
or recipe changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ResourceConstraint:
    """Constraint on resource availability (time, budget, personnel)."""
    resource_type: str          # e.g. "time_hours", "budget_usd", "personnel"
    limit: float
    unit: str = ""


@dataclass
class SafetyBoundary:
    """
    Safety invariants that must be maintained in all schedule outputs.
    These are checked at ScheduleResult construction time.
    """
    hardware_execution_enabled: bool = False
    execution_mode: str = "recommendation_only"
    requires_human_review: bool = True

    def validate(self):
        if self.hardware_execution_enabled:
            raise ValueError(
                "SafetyBoundary: hardware_execution_enabled must be False. "
                "The scheduler produces recommendations only."
            )
        safe_modes = {"recommendation_only", "human_review_required"}
        if self.execution_mode not in safe_modes:
            raise ValueError(
                f"SafetyBoundary: execution_mode must be one of {safe_modes}."
            )


@dataclass
class OptimizationCandidate:
    """
    Input to the scheduler: a candidate action with scoring metadata.
    """
    candidate_id: str
    action: str
    benefit_score: float        # 0.0-1.0; higher is better
    risk: str                   # low | medium | high
    cost: float = 0.0           # normalized cost estimate
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not (0.0 <= self.benefit_score <= 1.0):
            raise ValueError(f"benefit_score must be in [0, 1], got {self.benefit_score}")
        if self.risk not in ("low", "medium", "high"):
            raise ValueError(f"risk must be low/medium/high, got '{self.risk}'")


@dataclass
class ScheduleCandidate:
    """
    One entry in the ordered schedule output.
    Carries safety invariants on every item.
    """
    rank: int
    candidate_id: str
    action: str
    risk: str
    benefit_score: float
    execution_mode: str = "recommendation_only"
    hardware_execution_enabled: bool = False
    requires_human_review: bool = True

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "candidate_id": self.candidate_id,
            "action": self.action,
            "risk": self.risk,
            "benefit_score": self.benefit_score,
            "execution_mode": self.execution_mode,
            "hardware_execution_enabled": self.hardware_execution_enabled,
            "requires_human_review": self.requires_human_review,
        }


@dataclass
class ScheduleResult:
    """
    Output of the scheduler. Recommendation-only.

    Safety invariants (enforced at construction):
      hardware_execution_enabled = False
      execution_mode in {recommendation_only, human_review_required}
      requires_human_review = True
    """
    schema: str = "yieldos.schedule_result.v1"
    case_id: str = ""
    backend: str = "greedy"
    ordered_candidates: List[str] = field(default_factory=list)
    schedule: List[ScheduleCandidate] = field(default_factory=list)
    execution_mode: str = "recommendation_only"
    hardware_execution_enabled: bool = False
    requires_human_review: bool = True
    optimizer_info: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        boundary = SafetyBoundary(
            hardware_execution_enabled=self.hardware_execution_enabled,
            execution_mode=self.execution_mode,
            requires_human_review=self.requires_human_review,
        )
        boundary.validate()

    def to_dict(self) -> dict:
        from pathlib import Path
        _vf = Path(__file__).parent.parent.parent / "VERSION"
        _ver = _vf.read_text().strip() if _vf.exists() else "1.0.0"
        return {
            "schema": self.schema,
            "schema_version": _ver,
            "case_id": self.case_id,
            "backend": self.backend,
            "ordered_candidates": self.ordered_candidates,
            "schedule": [s.to_dict() for s in self.schedule],
            "execution_mode": self.execution_mode,
            "hardware_execution_enabled": self.hardware_execution_enabled,
            "requires_human_review": self.requires_human_review,
            "optimizer_info": self.optimizer_info,
            "generated_by": {"product": "HAL YieldOS", "version": _ver, "mode": "read_only_shadow"},
            "safety": {
                "read_only": True,
                "hardware_execution_enabled": False,
                "human_review_required": True,
            },
        }
