"""
tests/test_pilot_canonical_filenames.py

Regression test: canonical pilot init and pilot check output filenames (v2.9.1+).
Does NOT rely on v2.9.0 alias names as canonical.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.pilot.init_pack import generate_init_pack
from yieldos.pilot.readiness import run_pilot_check

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"
DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]

CANONICAL_INIT_FILES = [
    "pilot_input_contract.json",
    "sample_file_manifest.json",
    "missing_data_request_template.json",
    "sanitization_checklist.md",
    "pilot_boundary_statement.md",
    "README.md",
]

CANONICAL_CHECK_FILES = [
    "pilot_readiness_report.json",
    "missing_data_request.json",
    "data_sufficiency_preview.json",
    "pilot_decision_boundary.json",
]


@pytest.fixture(params=DOMAINS)
def init_out(tmp_path, request):
    domain = request.param
    out = tmp_path / f"init_{domain}"
    generate_init_pack(domain=domain, out_dir=out)
    return domain, out


@pytest.fixture(params=DOMAINS)
def check_out(tmp_path, request):
    domain = request.param
    sample_dir = SAMPLES_ROOT / f"pilot_{domain}"
    out = tmp_path / f"check_{domain}"
    run_pilot_check(domain=domain, input_dir=sample_dir, out_dir=out)
    return domain, out


# ── Canonical init files exist ────────────────────────────────────────────────

@pytest.mark.parametrize("fname", CANONICAL_INIT_FILES)
def test_canonical_init_file_exists(init_out, fname):
    domain, out = init_out
    assert (out / fname).exists(), (
        f"{domain}: canonical init file '{fname}' must be generated"
    )


# ── Canonical check files exist ───────────────────────────────────────────────

@pytest.mark.parametrize("fname", CANONICAL_CHECK_FILES)
def test_canonical_check_file_exists(check_out, fname):
    domain, out = check_out
    assert (out / fname).exists(), (
        f"{domain}: canonical check file '{fname}' must be generated"
    )


# ── pilot_input_contract.json schema ─────────────────────────────────────────

def test_pilot_input_contract_schema(init_out):
    domain, out = init_out
    data = json.loads((out / "pilot_input_contract.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.input_contract.v1"
    assert data["domain"] == domain


# ── sample_file_manifest.json schema ─────────────────────────────────────────

def test_sample_file_manifest_schema(init_out):
    domain, out = init_out
    data = json.loads((out / "sample_file_manifest.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.sample_file_manifest.v1"
    assert data["domain"] == domain


# ── missing_data_request_template.json schema ────────────────────────────────

def test_missing_data_request_template_schema(init_out):
    domain, out = init_out
    data = json.loads((out / "missing_data_request_template.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.missing_data_request_template.v1"
    assert data["domain"] == domain


# ── pilot_readiness_report.json schema ───────────────────────────────────────

def test_pilot_readiness_report_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.readiness_report.v1"
    assert data["domain"] == domain


# ── data_sufficiency_preview.json schema ─────────────────────────────────────

def test_data_sufficiency_preview_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "data_sufficiency_preview.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.data_sufficiency_preview.v1"
    assert data["domain"] == domain


# ── missing_data_request.json schema ─────────────────────────────────────────

def test_missing_data_request_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.missing_data_request.v1"
    assert data["domain"] == domain


# ── pilot_decision_boundary.json schema ──────────────────────────────────────

def test_pilot_decision_boundary_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "pilot_decision_boundary.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.decision_boundary.v1"
    assert data["domain"] == domain
