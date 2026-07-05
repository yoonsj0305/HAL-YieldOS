from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import List, Tuple


class ExecutionMode(str, Enum):
    RECOMMENDATION_ONLY = "recommendation_only"
    HUMAN_REVIEW_REQUIRED = "human_review_required"


SAFE_EXECUTION_MODES = {ExecutionMode.RECOMMENDATION_ONLY, ExecutionMode.HUMAN_REVIEW_REQUIRED}

SAFE_ACTION_PREFIXES: Tuple[str, ...] = (
    "recommend_",
    "request_",
    "suggest_",
    "prepare_",
    "simulate_",
    "draft_",
)

FORBIDDEN_ACTION_PREFIXES: Tuple[str, ...] = (
    "execute_",
    "control_",
    "send_",
    "uplink_",
    "move_",
    "change_",
    "modify_",
    "erase_",
    "schedule_",
    "flag_",
)

DANGEROUS_TERMS: Tuple[str, ...] = (
    "execute",
    "command",
    "uplink",
    "move_robot",
    "set_torque",
    "start_equipment",
    "stop_equipment",
    "change_recipe",
    "modify_recipe",
    "write_controller",
    "update_controller",
    "safe_mode_now",
    "calibrate_now",
    "fire_thruster",
    "deploy",
    "activate",
    "disable_interlock",
)


def validate_recovery_candidate(action: str, expected_benefit: str, steps: List[str]) -> None:
    """Enforce shadow-only safety: all actions must be recommendation/request/draft-form only."""
    action_lower = action.lower()
    if action_lower.startswith(FORBIDDEN_ACTION_PREFIXES):
        raise ValueError(
            f"Forbidden action prefix in: '{action}'. "
            f"Prefixes {FORBIDDEN_ACTION_PREFIXES} are not allowed. "
            "YieldOS produces recommendations only — never execution commands."
        )
    if not action_lower.startswith(SAFE_ACTION_PREFIXES):
        raise ValueError(
            f"Unsafe action name: '{action}'. "
            f"Actions must start with one of: {SAFE_ACTION_PREFIXES}. "
            "YieldOS produces recommendations only — never execution commands."
        )
    text = " ".join([action, expected_benefit, *steps]).lower()
    for term in DANGEROUS_TERMS:
        if term in text:
            raise ValueError(
                f"Dangerous execution term '{term}' found in recovery candidate '{action}'. "
                "Use recommendation, request, schedule, flag, prepare, simulate, or draft forms only."
            )


@dataclass
class RecoveryCandidate:
    action: str
    expected_benefit: str
    risk: str = "low"                        # low | medium | high
    requires_human_review: bool = True
    hardware_execution_enabled: bool = False
    execution_mode: ExecutionMode = ExecutionMode.RECOMMENDATION_ONLY
    estimated_impact_score: float = 0.0      # 0.0 ~ 1.0
    preconditions: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.hardware_execution_enabled:
            raise ValueError(
                "hardware_execution_enabled must be False. "
                "YieldOS never controls hardware."
            )
        if self.execution_mode not in SAFE_EXECUTION_MODES:
            raise ValueError(
                f"execution_mode must be one of {[m.value for m in SAFE_EXECUTION_MODES]}. "
                "YieldOS never executes hardware actions."
            )
        if self.risk not in ("low", "medium", "high"):
            raise ValueError(f"risk must be low/medium/high, got '{self.risk}'")
        validate_recovery_candidate(self.action, self.expected_benefit, self.steps)

    def to_dict(self) -> dict:
        from .meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by
        d = asdict(self)
        d["execution_mode"] = self.execution_mode.value
        d["schema"] = "yieldos.recovery_candidate.v1"
        d["schema_version"] = SCHEMA_VERSION
        d["generated_by"] = generated_by()
        d["safety"] = SAFETY_BLOCK
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
