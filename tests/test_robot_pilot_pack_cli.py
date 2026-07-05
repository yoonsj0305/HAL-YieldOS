"""tests/test_robot_pilot_pack_cli.py

Integration tests for `yieldos robot pilot-pack` CLI command.
Invokes cmd_robot_pilot_pack() directly (no subprocess) on sample data.
v3.0.0 - Robot Pilot-Ready Edition.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

_SAMPLES = Path(__file__).parent.parent / "samples" / "pilot_robot"
_ROOT = Path(__file__).parent.parent


def _run_pilot_pack(out_dir: str) -> int:
    import argparse

    from yieldos.cli.main import cmd_robot_pilot_pack
    args = argparse.Namespace(
        input=str(_SAMPLES),
        out=out_dir,
        asset="robot_pilot_test_01",
        case="case_cli_test_001",
    )
    return cmd_robot_pilot_pack(args)


def test_robot_pilot_pack_returns_exit_code_zero(tmp_path):
    if not _SAMPLES.exists() or not (_SAMPLES / "robot_telemetry.csv").exists():
        pytest.skip("pilot_robot samples not found")
    rc = _run_pilot_pack(str(tmp_path))
    assert rc == 0, f"cmd_robot_pilot_pack returned {rc}"


def test_robot_pilot_pack_creates_standard_bundle(tmp_path):
    if not _SAMPLES.exists() or not (_SAMPLES / "robot_telemetry.csv").exists():
        pytest.skip("pilot_robot samples not found")
    _run_pilot_pack(str(tmp_path))
    for fname in ("state_snapshot.json", "evidence_pack.json", "functional_passport.json",
                  "case_manifest.json"):
        assert (tmp_path / fname).exists(), f"Standard bundle file missing: {fname}"


def test_robot_pilot_pack_creates_pilot_specific_outputs(tmp_path):
    if not _SAMPLES.exists() or not (_SAMPLES / "robot_telemetry.csv").exists():
        pytest.skip("pilot_robot samples not found")
    _run_pilot_pack(str(tmp_path))
    pilot_files = [
        "robot_pilot_readiness_report.json",
        "robot_evidence_completeness_report.json",
        "robot_role_reclassification_report.json",
        "robot_valid_conditions_report.json",
        "robot_human_review_packet.json",
        "robot_missing_evidence_request.json",
        "robot_unit_normalization_report.json",
        "robot_pilot_case_summary.md",
    ]
    for fname in pilot_files:
        assert (tmp_path / fname).exists(), f"Pilot-pack file missing: {fname}"


def test_robot_pilot_pack_readiness_report_valid(tmp_path):
    if not _SAMPLES.exists() or not (_SAMPLES / "robot_telemetry.csv").exists():
        pytest.skip("pilot_robot samples not found")
    _run_pilot_pack(str(tmp_path))
    rpr = json.loads((tmp_path / "robot_pilot_readiness_report.json").read_text(encoding="utf-8"))
    assert rpr["schema"] == "hal.yieldos.robot.pilot_readiness_report.v1"
    assert rpr["hardware_control_enabled"] is False
    assert rpr["human_review_required"] is True
    assert rpr["readiness_status"] in {"PILOT_READY", "PARTIAL_PILOT_READY", "NOT_PILOT_READY"}
    assert 0.0 <= rpr["readiness_score"] <= 1.0
