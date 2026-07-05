"""Tests for v3.0.7 — public demo script existence and safety boundary."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
DEMO_SCRIPT = ROOT / "scripts" / "run_public_demo.py"


def test_public_demo_script_exists():
    assert DEMO_SCRIPT.exists(), "scripts/run_public_demo.py must exist"


def test_public_demo_script_does_not_call_recovery_compiler():
    text = DEMO_SCRIPT.read_text(encoding="utf-8")
    lower = text.lower()
    assert "run_recovery_compiler" not in lower, \
        "demo script must not call Recovery Compiler directly"
    assert "hal-recovery-compiler" not in lower, \
        "demo script must not invoke hal-recovery-compiler"


def test_public_demo_script_does_not_claim_recovery_profile_as_output():
    text = DEMO_SCRIPT.read_text(encoding="utf-8")
    # Must not say recovery_profile.json IS generated (only that it must NOT be generated)
    assert "recovery_profile.json" not in text or \
           "must not generate" in text or \
           "not generated" in text or \
           "never generates" in text or \
           "not generate" in text, \
        "demo script must not present recovery_profile.json as expected output"


def test_public_demo_script_has_no_hardware_control():
    text = DEMO_SCRIPT.read_text(encoding="utf-8")
    lower = text.lower()
    assert "hardware_control_enabled=true" not in lower
    assert "send_command" not in lower
    assert "robot_command" not in lower


def test_public_demo_script_has_safety_note():
    text = DEMO_SCRIPT.read_text(encoding="utf-8")
    lower = text.lower()
    assert "human_review_required" in lower or "human review" in lower, \
        "demo script must mention human review"
    assert "read_only" in lower or "read-only" in lower or "candidate" in lower, \
        "demo script must mention read-only or candidate"


def test_public_demo_script_checks_recovery_profile_absence():
    text = DEMO_SCRIPT.read_text(encoding="utf-8")
    assert "recovery_profile.json" in text, \
        "demo script must verify that recovery_profile.json was NOT generated"


def test_public_demo_script_runs_all_5_domains():
    text = DEMO_SCRIPT.read_text(encoding="utf-8")
    lower = text.lower()
    for domain in ["robot", "space", "semiconductor", "semiforge", "memory"]:
        assert domain in lower, f"demo script must include {domain} domain"


def test_public_demo_script_is_importable():
    """Demo script must be valid Python syntax."""
    import ast
    source = DEMO_SCRIPT.read_text(encoding="utf-8")
    try:
        ast.parse(source)
    except SyntaxError as e:
        raise AssertionError(f"scripts/run_public_demo.py has syntax error: {e}") from e
