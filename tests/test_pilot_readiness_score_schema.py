"""
tests/test_pilot_readiness_score_schema.py

Schema tests for readiness_score and readiness_score_percent fields (v2.9.3).
Verifies both fields exist, are numeric, and maintain the invariant
readiness_score_percent == round(readiness_score * 100, 2) for all domains.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.pilot.readiness import run_pilot_check

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"
DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]


@pytest.fixture(params=DOMAINS)
def score_out(tmp_path, request):
    domain = request.param
    sample_dir = SAMPLES_ROOT / f"pilot_{domain}"
    out = tmp_path / f"score_{domain}"
    run_pilot_check(domain=domain, input_dir=sample_dir, out_dir=out)
    data = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    return domain, data


# ── Field existence ───────────────────────────────────────────────────────────

def test_readiness_score_exists(score_out):
    _, data = score_out
    assert "readiness_score" in data, "readiness_score must exist"


def test_readiness_score_percent_exists(score_out):
    _, data = score_out
    assert "readiness_score_percent" in data, "readiness_score_percent must exist (v2.9.3)"


# ── Type checks ───────────────────────────────────────────────────────────────

def test_readiness_score_is_float(score_out):
    _, data = score_out
    assert isinstance(data["readiness_score"], (int, float))


def test_readiness_score_percent_is_float(score_out):
    _, data = score_out
    assert isinstance(data["readiness_score_percent"], (int, float))


# ── Range checks ──────────────────────────────────────────────────────────────

def test_readiness_score_in_range(score_out):
    domain, data = score_out
    s = data["readiness_score"]
    assert 0.0 <= s <= 1.0, f"{domain}: readiness_score {s} not in [0.0, 1.0]"


def test_readiness_score_percent_in_range(score_out):
    domain, data = score_out
    p = data["readiness_score_percent"]
    assert 0.0 <= p <= 100.0, f"{domain}: readiness_score_percent {p} not in [0.0, 100.0]"


# ── Invariant: percent == round(score * 100, 2) ───────────────────────────────

def test_score_percent_equals_score_times_100(score_out):
    domain, data = score_out
    score = data["readiness_score"]
    percent = data["readiness_score_percent"]
    expected = round(score * 100, 2)
    assert percent == expected, (
        f"{domain}: readiness_score_percent {percent} != round({score} * 100, 2) = {expected}"
    )


# ── Consistency: READY ↔ high score ──────────────────────────────────────────

def test_ready_score_is_high(score_out):
    domain, data = score_out
    if data["readiness_status"] != "READY_FOR_FUNCTIONAL_YIELD_PILOT":
        pytest.skip(f"{domain} sample is not READY")
    assert data["readiness_score"] >= 0.8, (
        f"{domain}: READY status should have score >= 0.8, got {data['readiness_score']}"
    )
    assert data["readiness_score_percent"] >= 80.0


def test_ready_score_percent_not_capped(score_out):
    domain, data = score_out
    if data["readiness_status"] != "READY_FOR_FUNCTIONAL_YIELD_PILOT":
        pytest.skip(f"{domain} sample is not READY")
    assert data["readiness_score_percent"] < 100.0 or data["readiness_score"] == 1.0, (
        "readiness_score_percent may equal 100.0 only when readiness_score == 1.0"
    )
