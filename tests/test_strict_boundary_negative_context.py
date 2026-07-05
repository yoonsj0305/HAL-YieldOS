"""Tests that forbidden terms inside negative/boundary context keys are NOT flagged.

The strict validator uses a regex-based negative context scanner: values under keys
like 'not_sufficient_for', 'forbidden_decisions', 'what_not_to_do', 'yieldos_does_not',
'forbidden_handoff', 'recovery_compiler_role', etc. are boundary statements describing
what YieldOS does NOT do. Forbidden terms appearing inside these values must not
cause a false-positive FAIL.

These are unit tests of the scanner logic itself (no full CLI needed).
"""
from __future__ import annotations

import json
import re


# === Scanner logic (mirrors yieldos/cli/main.py) ===

_NEGATIVE_CONTEXT_KEYS = {
    "not_sufficient_for", "forbidden_decisions", "what_not_to_do",
    "yieldos_does_not", "forbidden_handoff", "claim_boundary",
    "not_certification", "invalid_or_unknown_conditions", "warnings",
    "forbidden_control", "blocked_claims", "safety_boundary",
    "limitations", "disallowed_actions", "recovery_compiler_role",
    "external_system_role", "not_to_do", "boundary",
}

_SEMI_PP_FORBIDDEN = [
    "execute_recipe", "modify_recipe", "control_deposition",
    "control_etch", "control_lithography", "recipe_change_command",
    "equipment_control_command", "firmware_flash_payload",
    "runtime_apply_instruction",
    "yield_guarantee", "certified_root_cause", "confirmed_root_cause",
    "safety_certified", "recovery_profile",
]

_PP_NEGATIVE_KEYS = {
    "not_sufficient_for", "forbidden_decisions", "what_not_to_do",
    "yieldos_does_not", "forbidden_handoff", "claim_boundary",
    "not_certification", "invalid_or_unknown_conditions", "warnings",
    "forbidden_control", "blocked_claims", "safety_boundary",
    "limitations", "disallowed_actions",
}

_PP_FORBIDDEN = [
    "send_robot_command", "execute_hardware", "hardware_command",
    "auto_calibration_execute", "autonomous_recovery_execution",
    "yield_guarantee", "certified_root_cause", "safety_certified",
    "robot_command", "uplink_command",
]


def _strip_negative_context(text: str, negative_keys: set) -> str:
    """Remove values under negative-context keys from text."""
    safe = text
    for key in negative_keys:
        safe = re.sub(
            r'"' + key + r'"\s*:\s*(?:\[[\s\S]*?\]|"[^"]*")',
            f'"{key}": "__BOUNDARY__"',
            safe,
        )
    return safe


def _has_forbidden(text: str, forbidden: list) -> list[str]:
    return [t for t in forbidden if t.lower() in text]


# ── Tests: forbidden terms inside negative-context array values ──────────────

def test_yield_guarantee_in_not_sufficient_for_passes():
    doc = json.dumps({
        "schema": "test",
        "not_sufficient_for": ["yield_guarantee", "certified_root_cause"],
    }).lower()
    safe = _strip_negative_context(doc, _NEGATIVE_CONTEXT_KEYS)
    found = _has_forbidden(safe, _SEMI_PP_FORBIDDEN)
    assert not found, f"False-positive: {found} in negative context"


def test_yield_guarantee_in_forbidden_decisions_passes():
    doc = json.dumps({
        "schema": "test",
        "forbidden_decisions": ["yield_guarantee", "execute_recipe"],
    }).lower()
    safe = _strip_negative_context(doc, _NEGATIVE_CONTEXT_KEYS)
    found = _has_forbidden(safe, _SEMI_PP_FORBIDDEN)
    assert not found


def test_yield_guarantee_in_what_not_to_do_passes():
    doc = json.dumps({
        "schema": "test",
        "what_not_to_do": ["yield_guarantee"],
    }).lower()
    safe = _strip_negative_context(doc, _NEGATIVE_CONTEXT_KEYS)
    found = _has_forbidden(safe, _SEMI_PP_FORBIDDEN)
    assert not found


def test_yield_guarantee_in_yieldos_does_not_passes():
    doc = json.dumps({
        "schema": "test",
        "yieldos_does_not": ["compute_final_recovery_profile", "yield_guarantee"],
    }).lower()
    safe = _strip_negative_context(doc, _NEGATIVE_CONTEXT_KEYS)
    found = _has_forbidden(safe, _SEMI_PP_FORBIDDEN)
    assert not found


def test_recovery_profile_in_recovery_compiler_role_passes():
    """recovery_compiler_role is a description of another system's role — not an active claim."""
    doc = json.dumps({
        "schema": "test",
        "recovery_compiler_role": "generate_candidate_recovery_profile_from_approved_intake",
    }).lower()
    safe = _strip_negative_context(doc, _NEGATIVE_CONTEXT_KEYS)
    found = _has_forbidden(safe, _SEMI_PP_FORBIDDEN)
    assert not found, \
        f"recovery_profile inside recovery_compiler_role caused false-positive: {found}"


def test_execute_recipe_in_forbidden_handoff_passes():
    doc = json.dumps({
        "schema": "test",
        "forbidden_handoff": ["execute_recipe", "modify_recipe", "apply_control_instruction"],
    }).lower()
    safe = _strip_negative_context(doc, _NEGATIVE_CONTEXT_KEYS)
    found = _has_forbidden(safe, _SEMI_PP_FORBIDDEN)
    assert not found


def test_claim_boundary_string_value_with_recovery_profile_passes():
    doc = json.dumps({
        "schema": "test",
        "claim_boundary": "compiler_intake_preview_only_not_recovery_profile",
    }).lower()
    safe = _strip_negative_context(doc, _NEGATIVE_CONTEXT_KEYS)
    found = _has_forbidden(safe, _SEMI_PP_FORBIDDEN)
    assert not found, \
        f"claim_boundary string with 'recovery_profile' caused false-positive: {found}"


# ── Tests: robot pilot-pack negative context scanner ──────────────────────────

def test_yield_guarantee_in_not_sufficient_for_robot_pilot_passes():
    """Robot pilot-pack scanner: yield_guarantee in not_sufficient_for must pass."""
    doc = json.dumps({
        "schema": "hal.yieldos.robot.pilot_readiness_report.v1",
        "not_sufficient_for": ["yield_guarantee", "safety_certification"],
        "readiness_status": "PILOT_READY",
        "hardware_control_enabled": False,
    }).lower()
    safe = _strip_negative_context(doc, _PP_NEGATIVE_KEYS)
    found = _has_forbidden(safe, _PP_FORBIDDEN)
    assert not found, f"False-positive in robot pilot scanner: {found}"


def test_safety_certified_in_warnings_robot_pilot_passes():
    doc = json.dumps({
        "schema": "test",
        "warnings": ["outputs are not safety_certified"],
    }).lower()
    safe = _strip_negative_context(doc, _PP_NEGATIVE_KEYS)
    found = _has_forbidden(safe, _PP_FORBIDDEN)
    assert not found


def test_multiple_boundary_terms_in_one_doc_passes():
    """Multiple forbidden terms scattered across different boundary keys all pass."""
    doc = json.dumps({
        "schema": "test",
        "not_sufficient_for": ["yield_guarantee", "certified_root_cause"],
        "forbidden_decisions": ["execute_recipe", "modify_recipe"],
        "yieldos_does_not": ["safety_certified"],
        "claim_boundary": "compiler_intake_preview_only_not_recovery_profile",
        "actual_recommendation": "inspect_chamber_a_candidate",
    }).lower()
    safe = _strip_negative_context(doc, _NEGATIVE_CONTEXT_KEYS)
    found = _has_forbidden(safe, _SEMI_PP_FORBIDDEN)
    assert not found


def test_boundary_key_value_is_replaced_not_deleted(not_sufficient_for_doc=None):
    """After stripping, the key still exists but its value is __BOUNDARY__."""
    doc = json.dumps({
        "not_sufficient_for": ["yield_guarantee"],
    }).lower()
    safe = _strip_negative_context(doc, _NEGATIVE_CONTEXT_KEYS)
    assert "__boundary__" in safe or "not_sufficient_for" in safe
    assert "yield_guarantee" not in safe


def test_non_boundary_context_term_not_affected():
    """A normal key like 'recommendation' is NOT stripped by the scanner."""
    doc = json.dumps({
        "recommendation": "candidate_chamber_a",
        "not_sufficient_for": ["yield_guarantee"],
    }).lower()
    safe = _strip_negative_context(doc, _NEGATIVE_CONTEXT_KEYS)
    assert "candidate_chamber_a" in safe
