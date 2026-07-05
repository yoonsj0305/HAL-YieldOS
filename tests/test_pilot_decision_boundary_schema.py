"""
tests/test_pilot_decision_boundary_schema.py

Strict schema tests for pilot_decision_boundary.json (v2.9.2).
Asserts allowed_decisions and forbidden_decisions exist with correct values.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.pilot.readiness import (
    STATUS_READY,
    run_pilot_check,
)

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"
DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]

REQUIRED_FORBIDDEN = [
    "execute_recovery",
    "control_hardware",
    "certify_safety",
    "claim_root_cause",
    "guarantee_yield",
    "modify_recipe",
    "send_robot_command",
    "uplink_satellite_command",
]


@pytest.fixture(params=DOMAINS)
def boundary_out(tmp_path, request):
    domain = request.param
    sample_dir = SAMPLES_ROOT / f"pilot_{domain}"
    out = tmp_path / f"boundary_{domain}"
    run_pilot_check(domain=domain, input_dir=sample_dir, out_dir=out)
    data = json.loads((out / "pilot_decision_boundary.json").read_text(encoding="utf-8"))
    report = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    return domain, data, report


# ── Schema identifier ─────────────────────────────────────────────────────────

def test_schema_field_correct(boundary_out):
    _, data, _ = boundary_out
    assert data["schema"] == "hal.yieldos.pilot.decision_boundary.v1"


def test_domain_field_matches(boundary_out):
    domain, data, _ = boundary_out
    assert data["domain"] == domain


# ── allowed_decisions (v2.9.2) ────────────────────────────────────────────────

def test_allowed_decisions_exists(boundary_out):
    _, data, _ = boundary_out
    assert "allowed_decisions" in data, "canonical 'allowed_decisions' field must exist"


def test_allowed_decisions_is_list(boundary_out):
    _, data, _ = boundary_out
    assert isinstance(data["allowed_decisions"], list)


def test_allowed_decisions_not_empty(boundary_out):
    domain, data, _ = boundary_out
    assert len(data["allowed_decisions"]) >= 1, (
        f"{domain}: allowed_decisions must not be empty"
    )


def test_allowed_decisions_contains_request_missing_data(boundary_out):
    domain, data, _ = boundary_out
    assert "request_missing_data" in data["allowed_decisions"], (
        f"{domain}: 'request_missing_data' must always be in allowed_decisions"
    )


def test_ready_allows_accept_for_pilot(boundary_out):
    domain, data, report = boundary_out
    if report["readiness_status"] != STATUS_READY:
        pytest.skip(f"{domain} sample is not READY")
    assert "accept_for_offline_functional_yield_pilot" in data["allowed_decisions"], (
        f"{domain}: READY status must allow 'accept_for_offline_functional_yield_pilot'"
    )


# ── forbidden_decisions (v2.9.2) ─────────────────────────────────────────────

def test_forbidden_decisions_exists(boundary_out):
    _, data, _ = boundary_out
    assert "forbidden_decisions" in data, "canonical 'forbidden_decisions' field must exist"


def test_forbidden_decisions_is_list(boundary_out):
    _, data, _ = boundary_out
    assert isinstance(data["forbidden_decisions"], list)


@pytest.mark.parametrize("forbidden_item", REQUIRED_FORBIDDEN)
def test_required_forbidden_decision_present(boundary_out, forbidden_item):
    domain, data, _ = boundary_out
    assert forbidden_item in data["forbidden_decisions"], (
        f"{domain}: '{forbidden_item}' must be in forbidden_decisions"
    )


# ── Safety fields ─────────────────────────────────────────────────────────────

def test_human_review_required_is_true(boundary_out):
    _, data, _ = boundary_out
    assert data.get("human_review_required") is True


def test_hardware_control_enabled_is_false(boundary_out):
    _, data, _ = boundary_out
    assert data.get("hardware_control_enabled") is False


def test_claim_boundary_exists(boundary_out):
    _, data, _ = boundary_out
    assert "claim_boundary" in data
    assert data["claim_boundary"]


# ── pilot_can_proceed consistency ─────────────────────────────────────────────

def test_ready_pilot_can_proceed(boundary_out):
    domain, data, report = boundary_out
    if report["readiness_status"] != STATUS_READY:
        pytest.skip(f"{domain} sample is not READY")
    assert data["pilot_can_proceed"] is True


def test_not_ready_pilot_cannot_proceed(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    data = json.loads((out / "pilot_decision_boundary.json").read_text(encoding="utf-8"))
    assert data["pilot_can_proceed"] is False
    assert data.get("hardware_control_enabled") is False
    assert data.get("human_review_required") is True


# ── Forbidden decisions do not appear in allowed_decisions ────────────────────

def test_allowed_and_forbidden_are_disjoint(boundary_out):
    domain, data, _ = boundary_out
    overlap = set(data.get("allowed_decisions", [])) & set(data.get("forbidden_decisions", []))
    assert not overlap, (
        f"{domain}: allowed_decisions and forbidden_decisions must not overlap: {overlap}"
    )
