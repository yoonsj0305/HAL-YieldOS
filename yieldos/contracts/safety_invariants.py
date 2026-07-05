"""
HAL YieldOS Safety Invariants.

These constants define the absolute safety boundary for all YieldOS outputs.
No domain analyzer, optimizer, or CLI command may violate these invariants.

HAL YieldOS MUST NOT:
  - control hardware
  - send robot commands
  - uplink satellite commands
  - change semiconductor recipes
  - modify memory firmware
  - certify safety
  - claim confirmed root cause
  - perform autonomous recovery

HAL YieldOS MAY:
  - read logs
  - generate Evidence Packs
  - generate Functional Passports
  - rank recovery candidates
  - recommend human review routes
  - request missing evidence
  - produce shadow analysis outputs
"""
from __future__ import annotations

from typing import Dict, Tuple

FORBIDDEN_ACTION_TERMS: Tuple[str, ...] = (
    "execute",
    "control_hardware",
    "send_robot_command",
    "move_robot",
    "uplink_command",
    "change_recipe",
    "modify_firmware",
    "erase_block",
    "autonomous_recovery",
    "certify_safety",
    "confirmed_root_cause",
)

REQUIRED_BOUNDARIES: Dict[str, object] = {
    "hardware_execution_enabled": False,
    "human_review_required": True,
    "recommendation_only": True,
    "root_cause_claim_boundary": "candidate_only",
    "ooda_act": "recommendation_only_no_hardware_action",
}

OODA_ACT_EXACT: str = "recommendation_only_no_hardware_action"

SQBM_FALLBACK_WARNING: str = (
    "Optimizer unavailable. Falling back to deterministic heuristic scheduler."
)
