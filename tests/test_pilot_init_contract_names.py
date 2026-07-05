"""
tests/test_pilot_init_contract_names.py

Tests canonical output file names for `yieldos pilot init` (v2.9.1).
Verifies all 6 canonical files are generated with correct schemas.
"""
from __future__ import annotations

import json

import pytest

from yieldos.pilot.init_pack import generate_init_pack

DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]

CANONICAL_INIT_FILES = [
    "pilot_input_contract.json",
    "sample_file_manifest.json",
    "missing_data_request_template.json",
    "sanitization_checklist.md",
    "pilot_boundary_statement.md",
    "README.md",
]


@pytest.fixture(params=DOMAINS)
def init_out(tmp_path, request):
    domain = request.param
    out = tmp_path / f"init_{domain}"
    generate_init_pack(domain=domain, out_dir=out)
    return domain, out


# ── All canonical files exist ─────────────────────────────────────────────────

def test_canonical_init_files_exist(init_out):
    domain, out = init_out
    for fname in CANONICAL_INIT_FILES:
        assert (out / fname).exists(), f"{domain}: canonical file '{fname}' not generated"


# ── pilot_input_contract.json ─────────────────────────────────────────────────

def test_pilot_input_contract_schema(init_out):
    domain, out = init_out
    data = json.loads((out / "pilot_input_contract.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.input_contract.v1"
    assert data["domain"] == domain


def test_pilot_input_contract_core_question(init_out):
    domain, out = init_out
    data = json.loads((out / "pilot_input_contract.json").read_text(encoding="utf-8"))
    assert "core_question" in data
    assert "functional_yield" in data["core_question"] or "function" in data["core_question"]


def test_pilot_input_contract_has_functional_yield_mapping(init_out):
    domain, out = init_out
    data = json.loads((out / "pilot_input_contract.json").read_text(encoding="utf-8"))
    fym = data["functional_yield_mapping"]
    expected_keys = {
        "remaining_functions_inputs",
        "blocked_functions_inputs",
        "valid_conditions_inputs",
        "evidence_inputs",
        "human_review_inputs",
    }
    assert set(fym.keys()) == expected_keys


def test_pilot_input_contract_has_minimum_viable_rows(init_out):
    domain, out = init_out
    data = json.loads((out / "pilot_input_contract.json").read_text(encoding="utf-8"))
    mvr = data["minimum_viable_rows"]
    assert isinstance(mvr, dict)
    assert len(mvr) >= 2, "Must have minimum_viable_rows for at least 2 required files"
    for fname, rows in mvr.items():
        assert isinstance(rows, int) and rows > 0


def test_pilot_input_contract_not_sufficient_for(init_out):
    domain, out = init_out
    data = json.loads((out / "pilot_input_contract.json").read_text(encoding="utf-8"))
    nsf = data["not_sufficient_for"]
    assert "certified_root_cause" in nsf
    assert "hardware_control" in nsf


def test_pilot_input_contract_safety_boundary(init_out):
    domain, out = init_out
    data = json.loads((out / "pilot_input_contract.json").read_text(encoding="utf-8"))
    sb = data["safety_boundary"]
    assert sb["hardware_control_enabled"] is False
    assert sb["human_review_required"] is True
    assert sb["candidate_only"] is True


def test_pilot_input_contract_has_required_files(init_out):
    domain, out = init_out
    data = json.loads((out / "pilot_input_contract.json").read_text(encoding="utf-8"))
    assert len(data["required_files"]) >= 2


# ── sample_file_manifest.json ─────────────────────────────────────────────────

def test_sample_file_manifest_schema(init_out):
    domain, out = init_out
    data = json.loads((out / "sample_file_manifest.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.sample_file_manifest.v1"
    assert data["domain"] == domain


def test_sample_file_manifest_has_required_files(init_out):
    domain, out = init_out
    data = json.loads((out / "sample_file_manifest.json").read_text(encoding="utf-8"))
    assert len(data["required_sample_files"]) >= 2


def test_sample_file_manifest_items_have_minimum_viable_rows(init_out):
    domain, out = init_out
    data = json.loads((out / "sample_file_manifest.json").read_text(encoding="utf-8"))
    for item in data["required_sample_files"]:
        assert "minimum_viable_rows" in item, f"{domain}: {item['path']} missing minimum_viable_rows"
        assert item["minimum_viable_rows"] > 0
        assert "functional_yield_role" in item


# ── missing_data_request_template.json ───────────────────────────────────────

def test_missing_data_request_template_schema(init_out):
    domain, out = init_out
    data = json.loads((out / "missing_data_request_template.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.missing_data_request_template.v1"


def test_missing_data_request_template_has_template_items(init_out):
    domain, out = init_out
    data = json.loads((out / "missing_data_request_template.json").read_text(encoding="utf-8"))
    assert "template_items" in data
    assert len(data["template_items"]) >= 2


def test_missing_data_request_template_why_needed(init_out):
    domain, out = init_out
    data = json.loads((out / "missing_data_request_template.json").read_text(encoding="utf-8"))
    for item in data["template_items"]:
        assert "why_needed_for_functional_yield" in item, (
            f"{domain}: {item['file']} missing why_needed_for_functional_yield"
        )
        assert len(item["why_needed_for_functional_yield"]) > 10


def test_missing_data_request_template_is_template(init_out):
    domain, out = init_out
    data = json.loads((out / "missing_data_request_template.json").read_text(encoding="utf-8"))
    assert data["status"] == "template_for_data_collection"


# ── sanitization_checklist.md ─────────────────────────────────────────────────

def test_sanitization_checklist_md_exists_and_nonempty(init_out):
    domain, out = init_out
    md = (out / "sanitization_checklist.md").read_text(encoding="utf-8")
    assert len(md) > 100
    assert "PII" in md or "pii" in md.lower()


def test_sanitization_checklist_md_has_required_steps_section(init_out):
    domain, out = init_out
    md = (out / "sanitization_checklist.md").read_text(encoding="utf-8")
    assert "## Required Steps" in md


def test_sanitization_checklist_md_has_sign_off(init_out):
    domain, out = init_out
    md = (out / "sanitization_checklist.md").read_text(encoding="utf-8")
    assert "Sign-Off" in md or "sign_off" in md.lower() or "Sign Off" in md


# ── pilot_boundary_statement.md ───────────────────────────────────────────────

def test_pilot_boundary_statement_md_exists_and_nonempty(init_out):
    domain, out = init_out
    md = (out / "pilot_boundary_statement.md").read_text(encoding="utf-8")
    assert len(md) > 100
    assert "Pilot Boundary Statement" in md


def test_pilot_boundary_statement_md_has_safety_constraints(init_out):
    domain, out = init_out
    md = (out / "pilot_boundary_statement.md").read_text(encoding="utf-8")
    assert "Safety Constraints" in md
    assert "human_review_required" in md
    assert "automatic_decision_enabled" in md


def test_pilot_boundary_statement_md_contains_domain(init_out):
    domain, out = init_out
    md = (out / "pilot_boundary_statement.md").read_text(encoding="utf-8")
    assert domain in md


# ── README.md ─────────────────────────────────────────────────────────────────

def test_readme_exists_and_nonempty(init_out):
    domain, out = init_out
    md = (out / "README.md").read_text(encoding="utf-8")
    assert len(md) > 200
    assert domain in md


def test_readme_has_canonical_file_table(init_out):
    domain, out = init_out
    md = (out / "README.md").read_text(encoding="utf-8")
    assert "pilot_input_contract.json" in md
    assert "sample_file_manifest.json" in md
    assert "missing_data_request_template.json" in md
    assert "sanitization_checklist.md" in md
    assert "pilot_boundary_statement.md" in md


def test_readme_has_next_steps(init_out):
    domain, out = init_out
    md = (out / "README.md").read_text(encoding="utf-8")
    assert "Next Steps" in md
    assert "pilot check" in md


def test_readme_has_functional_yield_mapping(init_out):
    domain, out = init_out
    md = (out / "README.md").read_text(encoding="utf-8")
    assert "Functional Yield Mapping" in md


# ── All domains functional_yield_mapping is populated ─────────────────────────

def test_all_domains_have_evidence_inputs(init_out):
    domain, out = init_out
    data = json.loads((out / "pilot_input_contract.json").read_text(encoding="utf-8"))
    fym = data["functional_yield_mapping"]
    # At least one file must be in evidence_inputs or remaining_functions_inputs
    populated = [k for k, v in fym.items() if v]
    assert len(populated) >= 1, f"{domain}: functional_yield_mapping is entirely empty"
