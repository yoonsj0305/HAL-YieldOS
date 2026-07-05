"""
tests/test_pilot_check.py

Tests for yieldos.pilot.readiness.run_pilot_check().
Tests both happy path (all files present) and blocking cases (missing files).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.pilot.readiness import run_pilot_check

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"

DOMAINS_WITH_SAMPLES = [
    ("robot", SAMPLES_ROOT / "pilot_robot"),
    ("semiconductor", SAMPLES_ROOT / "pilot_semiconductor"),
    ("space", SAMPLES_ROOT / "pilot_space"),
    ("memory", SAMPLES_ROOT / "pilot_memory"),
    ("semiforge", SAMPLES_ROOT / "pilot_semiforge"),
]


@pytest.fixture(params=DOMAINS_WITH_SAMPLES, ids=[d for d, _ in DOMAINS_WITH_SAMPLES])
def check_out(tmp_path, request):
    domain, input_dir = request.param
    out = tmp_path / f"pilot_check_{domain}"
    run_pilot_check(domain=domain, input_dir=input_dir, out_dir=out)
    return domain, out


# ── All 4 output files exist ─────────────────────────────────────────────────

def test_all_check_files_exist(check_out):
    domain, out = check_out
    for f in ["readiness_report.json", "data_sufficiency.json", "blocking_issues.json", "next_steps.json"]:
        assert (out / f).exists(), f"{domain}: {f} not generated"


# ── readiness_report.json ─────────────────────────────────────────────────────

def test_readiness_report_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "readiness_report.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot_readiness_report.v1"
    assert data["domain"] == domain


def test_readiness_report_status_valid(check_out):
    domain, out = check_out
    data = json.loads((out / "readiness_report.json").read_text(encoding="utf-8"))
    assert data["status"] in ("READY", "PARTIAL", "NOT_READY")


def test_readiness_report_score_range(check_out):
    domain, out = check_out
    data = json.loads((out / "readiness_report.json").read_text(encoding="utf-8"))
    score = data["readiness_score"]
    assert 0.0 <= score <= 1.0


def test_readiness_report_human_review(check_out):
    domain, out = check_out
    data = json.loads((out / "readiness_report.json").read_text(encoding="utf-8"))
    assert data["human_review_required"] is True
    assert data["automatic_decision_enabled"] is False


def test_readiness_report_has_generated_by(check_out):
    domain, out = check_out
    data = json.loads((out / "readiness_report.json").read_text(encoding="utf-8"))
    assert "generated_by" in data


# ── data_sufficiency.json ──────────────────────────────────────────────────────

def test_data_sufficiency_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "data_sufficiency.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot_data_sufficiency.v1"


def test_data_sufficiency_has_field_checks(check_out):
    domain, out = check_out
    data = json.loads((out / "data_sufficiency.json").read_text(encoding="utf-8"))
    assert len(data["field_checks"]) >= 2


def test_data_sufficiency_min_records_present(check_out):
    domain, out = check_out
    data = json.loads((out / "data_sufficiency.json").read_text(encoding="utf-8"))
    assert data["min_records_required"] > 0


# ── blocking_issues.json ───────────────────────────────────────────────────────

def test_blocking_issues_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "blocking_issues.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot_blocking_issues.v1"


def test_blocking_issues_has_pilot_can_proceed(check_out):
    domain, out = check_out
    data = json.loads((out / "blocking_issues.json").read_text(encoding="utf-8"))
    assert "pilot_can_proceed" in data


# ── next_steps.json ────────────────────────────────────────────────────────────

def test_next_steps_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "next_steps.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot_next_steps.v1"


def test_next_steps_has_full_analysis_command(check_out):
    domain, out = check_out
    data = json.loads((out / "next_steps.json").read_text(encoding="utf-8"))
    assert "full_analysis_command" in data
    assert domain in data["full_analysis_command"]


# ── Sample data check: sample folders are READY ───────────────────────────────

def test_sample_data_produces_no_missing_required(check_out):
    """All pilot sample folders provide required files — no P0 blocking issues."""
    domain, out = check_out
    blocking = json.loads((out / "blocking_issues.json").read_text(encoding="utf-8"))
    missing_required = [
        i for i in blocking.get("issues", [])
        if "missing" in i.get("issue", "").lower() and "Required file" in i.get("issue", "")
    ]
    assert missing_required == [], (
        f"{domain}: sample data is missing required files: "
        f"{[i['file'] for i in missing_required]}"
    )


# ── Missing data produces blocking issues ─────────────────────────────────────

def test_empty_input_dir_produces_blocking_issues(tmp_path):
    empty = tmp_path / "empty_input"
    empty.mkdir()
    out = tmp_path / "check_out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)

    blocking = json.loads((out / "blocking_issues.json").read_text(encoding="utf-8"))
    assert blocking["blocking_count"] >= 2, "Empty input must produce blocking issues"
    assert blocking["pilot_can_proceed"] is False


def test_empty_input_dir_status_not_ready(tmp_path):
    empty = tmp_path / "empty_input"
    empty.mkdir()
    out = tmp_path / "check_out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)

    report = json.loads((out / "readiness_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "NOT_READY"
    assert report["readiness_score"] < 0.5
