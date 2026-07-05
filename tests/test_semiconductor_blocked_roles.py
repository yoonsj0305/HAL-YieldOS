"""
tests/test_semiconductor_blocked_roles.py

Verifies that the semiconductor domain explicitly declares what YieldOS
cannot do — blocked_roles must be present and contain the required entries.
Also verifies remaining_roles cover the evidence generation capabilities.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SAMPLES_ROOT = ROOT / "samples"

REQUIRED_BLOCKED_ROLES = {
    "certified_root_cause",
    "recipe_change",
    "automatic_lot_hold",
    "equipment_control",
    "process_parameter_update",
    "production_disposition",
}

REQUIRED_REMAINING_ROLES = {
    "shadow_monitoring",
    "evidence_generation",
    "yield_investigation_support",
}


def _find_semfab_dir() -> Path | None:
    for candidate in [
        SAMPLES_ROOT / "semfab_tel_like",
        SAMPLES_ROOT / "semiconductor",
    ]:
        if candidate.exists():
            return candidate
    return None


def _run_semiconductor():
    dd = _find_semfab_dir()
    if dd is None:
        return None
    from yieldos.domains.semfab import SemFabAnalyzer
    return SemFabAnalyzer().analyze(data_dir=str(dd), case_id="case_semi_blocked")


# ── Analyzer returns blocked_roles ────────────────────────────────────────────

def test_semiconductor_analyzer_returns_blocked_roles():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    blocked = result.get("blocked_roles", [])
    assert len(blocked) > 0, "semiconductor analyzer must return non-empty blocked_roles"


def test_semiconductor_blocked_roles_include_recipe_change():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    assert "recipe_change" in result.get("blocked_roles", [])


def test_semiconductor_blocked_roles_include_equipment_control():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    assert "equipment_control" in result.get("blocked_roles", [])


def test_semiconductor_blocked_roles_include_certified_root_cause():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    assert "certified_root_cause" in result.get("blocked_roles", [])


def test_semiconductor_blocked_roles_include_automatic_lot_hold():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    assert "automatic_lot_hold" in result.get("blocked_roles", [])


def test_semiconductor_blocked_roles_include_process_parameter_update():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    assert "process_parameter_update" in result.get("blocked_roles", [])


def test_semiconductor_blocked_roles_include_production_disposition():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    assert "production_disposition" in result.get("blocked_roles", [])


def test_semiconductor_blocked_roles_covers_all_required():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    blocked = set(result.get("blocked_roles", []))
    missing = REQUIRED_BLOCKED_ROLES - blocked
    assert not missing, f"semiconductor missing required blocked_roles: {missing}"


# ── Functional passport carries blocked_roles ─────────────────────────────────

def test_semiconductor_functional_passport_has_blocked_roles():
    dd = _find_semfab_dir()
    if dd is None:
        pytest.skip("semiconductor sample not available")
    from yieldos.cli.main import _run_and_write, _run_semiconductor, _semiconductor_source_data_paths
    result = _run_semiconductor(str(dd), case_id="case_semi_fp")
    with tempfile.TemporaryDirectory() as tmp:
        _run_and_write(result, tmp, "semiconductor",
                       source_data_paths=_semiconductor_source_data_paths(str(dd)))
        fp = json.loads((Path(tmp) / "functional_passport.json").read_text(encoding="utf-8"))
        blocked = fp.get("blocked_roles", [])
        assert len(blocked) > 0, "functional_passport.json must carry blocked_roles"


def test_semiconductor_passport_blocked_roles_include_recipe_change():
    dd = _find_semfab_dir()
    if dd is None:
        pytest.skip("semiconductor sample not available")
    from yieldos.cli.main import _run_and_write, _run_semiconductor
    result = _run_semiconductor(str(dd), case_id="case_semi_fp2")
    with tempfile.TemporaryDirectory() as tmp:
        _run_and_write(result, tmp, "semiconductor")
        fp = json.loads((Path(tmp) / "functional_passport.json").read_text(encoding="utf-8"))
        assert "recipe_change" in fp.get("blocked_roles", [])


def test_semiconductor_passport_blocked_roles_include_equipment_control():
    dd = _find_semfab_dir()
    if dd is None:
        pytest.skip("semiconductor sample not available")
    from yieldos.cli.main import _run_and_write, _run_semiconductor
    result = _run_semiconductor(str(dd), case_id="case_semi_fp3")
    with tempfile.TemporaryDirectory() as tmp:
        _run_and_write(result, tmp, "semiconductor")
        fp = json.loads((Path(tmp) / "functional_passport.json").read_text(encoding="utf-8"))
        assert "equipment_control" in fp.get("blocked_roles", [])


# ── Remaining roles ───────────────────────────────────────────────────────────

def test_semiconductor_remaining_roles_include_shadow_monitoring():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    assert "shadow_monitoring" in result.get("remaining_roles", [])


def test_semiconductor_remaining_roles_include_evidence_generation():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    assert "evidence_generation" in result.get("remaining_roles", [])


def test_semiconductor_remaining_roles_include_drift_investigation():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    assert "drift_investigation_support" in result.get("remaining_roles", [])


def test_semiconductor_remaining_roles_include_cross_step_correlation():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    assert "cross_step_correlation_review" in result.get("remaining_roles", [])


# ── Recovery actions use safe prefixes ───────────────────────────────────────

def test_semiconductor_recovery_actions_are_safe():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    from yieldos.contracts.recovery_candidate import SAFE_ACTION_PREFIXES
    for rc in result.get("recovery_candidates", []):
        action = rc.action if hasattr(rc, "action") else rc.get("action", "")
        assert action.startswith(SAFE_ACTION_PREFIXES), \
            f"Semiconductor recovery action '{action}' uses unsafe prefix"


def test_semiconductor_no_execution_action():
    result = _run_semiconductor()
    if result is None:
        pytest.skip("semiconductor sample not available")
    FORBIDDEN = {"flag_lot", "flag_in_mes", "change_recipe", "hold_lot", "update_process_parameter"}
    for rc in result.get("recovery_candidates", []):
        action = rc.action if hasattr(rc, "action") else rc.get("action", "")
        assert action not in FORBIDDEN, \
            f"Semiconductor recovery action '{action}' is a forbidden execution action"
