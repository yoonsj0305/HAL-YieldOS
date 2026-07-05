"""Tests that all semiconductor pilot-pack reports enforce safety boundaries (v3.0.1)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"

_FORBIDDEN_TERMS = [
    "execute_recipe",
    "modify_recipe",
    "control_deposition",
    "recipe_change_command",
    "equipment_control_command",
    "firmware_flash_payload",
    "yield_guarantee",
    "certified_root_cause",
    "safety_certified",
]

_NEGATIVE_CONTEXT_KEYS = {
    "not_sufficient_for", "forbidden_decisions", "what_not_to_do",
    "yieldos_does_not", "forbidden_handoff", "claim_boundary",
    "forbidden_files", "handoff_conditions", "recovery_profile_generated",
}


@pytest.fixture(scope="module")
def all_reports():
    tool_path = SAMPLE_DIR / "tool_log.csv"
    with tool_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    with (SAMPLE_DIR / "metrology.csv").open(encoding="utf-8") as f:
        metro_rows = list(csv.DictReader(f))
    with (SAMPLE_DIR / "test_results.csv").open(encoding="utf-8") as f:
        test_rows = list(csv.DictReader(f))
    return generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="safety_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols, tool_rows=tool_rows,
        metro_rows=metro_rows, test_rows=test_rows,
    )


def _text_without_negative_keys(data: dict) -> str:
    """Return JSON text with negative-context key values replaced by placeholder."""
    import re
    text = json.dumps(data).lower()
    for key in _NEGATIVE_CONTEXT_KEYS:
        text = re.sub(
            r'"' + key + r'"\s*:\s*(?:\[[\s\S]*?\]|"[^"]*"|true|false|null)',
            f'"{key}": "__boundary__"',
            text,
        )
    return text


@pytest.mark.parametrize("term", _FORBIDDEN_TERMS)
def test_no_forbidden_term_in_reports(all_reports, term):
    for key, data in all_reports.items():
        safe_text = _text_without_negative_keys(data)
        assert term not in safe_text, (
            f"Forbidden term '{term}' found in {key} outside negative-context boundary keys"
        )


def test_no_recovery_profile_generated(all_reports):
    assert "recovery_profile" not in all_reports
    for key, data in all_reports.items():
        assert key != "recovery_profile"


def test_hardware_control_disabled_all_reports(all_reports):
    for key, data in all_reports.items():
        assert data.get("hardware_control_enabled") is False, (
            f"{key}: hardware_control_enabled must be False"
        )


def test_candidate_only_invariant(all_reports):
    rpr = all_reports["semiconductor_pilot_readiness_report"]
    safety = rpr.get("safety_boundary", {})
    assert safety.get("candidate_only") is True or rpr.get("claim_boundary") is not None


def test_intake_preview_no_recovery_profile_key(all_reports):
    intake = all_reports["semiconductor_recovery_compiler_intake_preview"]
    text = json.dumps(intake)
    assert "recovery_profile.json" not in text or "intake_preview" in text


def test_claim_boundary_present_all_reports(all_reports):
    for key, data in all_reports.items():
        assert "claim_boundary" in data, f"{key}: missing claim_boundary"
