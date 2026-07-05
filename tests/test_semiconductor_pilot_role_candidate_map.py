"""Tests for semiconductor_role_candidate_map.json (v3.0.1)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import SEMICONDUCTOR_ROLES, generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def rcm():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="rcm_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    return reports["semiconductor_role_candidate_map"]


def test_rcm_schema(rcm):
    assert rcm["schema"] == "hal.yieldos.semiconductor.role_candidate_map.v1"


def test_rcm_all_roles_accounted_for(rcm):
    all_classified = (
        set(rcm["remaining_roles"]) |
        set(rcm["reduced_roles"]) |
        set(rcm["blocked_roles"])
    )
    for role in SEMICONDUCTOR_ROLES:
        assert role in all_classified, f"Role '{role}' not classified in any list"


def test_rcm_role_decisions_cover_all_roles(rcm):
    decision_roles = {d["role"] for d in rcm["role_decisions"]}
    for role in SEMICONDUCTOR_ROLES:
        assert role in decision_roles, f"Role '{role}' missing from role_decisions"


def test_rcm_role_decision_classification_valid(rcm):
    for d in rcm["role_decisions"]:
        assert d["classification"] in ("remaining", "reduced", "blocked"), (
            f"Invalid classification: {d['classification']}"
        )


def test_rcm_role_decisions_have_valid_conditions(rcm):
    for d in rcm["role_decisions"]:
        assert isinstance(d.get("valid_conditions"), list)


def test_rcm_role_decisions_have_claim_boundary(rcm):
    for d in rcm["role_decisions"]:
        assert "claim_boundary" in d


def test_rcm_safety(rcm):
    assert rcm["hardware_control_enabled"] is False
    assert rcm["human_review_required"] is True


def test_rcm_inspection_only_bin_always_remaining():
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="iob_test", asset_id="chip_x",
        alias_map={}, tool_cols=[], tool_rows=[], metro_rows=[], test_rows=[],
    )
    rcm = reports["semiconductor_role_candidate_map"]
    assert "inspection_only_bin" in rcm["remaining_roles"]


def test_rcm_semiconductor_roles_constant():
    assert "high_speed_compute" in SEMICONDUCTOR_ROLES
    assert "background_diagnostics" in SEMICONDUCTOR_ROLES
    assert "recovery_candidate_region" in SEMICONDUCTOR_ROLES
    assert len(SEMICONDUCTOR_ROLES) == 8
