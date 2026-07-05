"""Tests for semiconductor_pilot_readiness_report.json structure (v3.0.1)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


def _gen(input_dir=None, tool_rows=None, metro_rows=None, test_rows=None,
         tool_cols=None, alias_map=None):
    inp = input_dir or SAMPLE_DIR
    if tool_rows is None:
        with (inp / "tool_log.csv").open(encoding="utf-8") as f:
            r = csv.DictReader(f)
            tool_rows = list(r)
            tool_cols = list(r.fieldnames or [])
    if metro_rows is None:
        p = inp / "metrology.csv"
        metro_rows = list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []
    if test_rows is None:
        p = inp / "test_results.csv"
        test_rows = list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []
    return generate_pilot_pack(
        input_dir=str(inp), case_id="rpr_test", asset_id="chip_demo",
        alias_map=alias_map or {}, tool_cols=tool_cols or [],
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )


@pytest.fixture(scope="module")
def rpr():
    return _gen()["semiconductor_pilot_readiness_report"]


def test_readiness_report_schema(rpr):
    assert rpr["schema"] == "hal.yieldos.semiconductor.pilot_readiness_report.v1"


def test_readiness_report_domain(rpr):
    assert rpr["domain"] == "semiconductor"


def test_readiness_report_has_checks(rpr):
    assert isinstance(rpr["checks"], list)
    assert len(rpr["checks"]) > 0


def test_readiness_report_checks_have_status(rpr):
    for c in rpr["checks"]:
        assert c["status"] in ("PASS", "FAIL", "WARN"), f"Unknown check status: {c['status']}"


def test_readiness_report_required_files_lists(rpr):
    assert isinstance(rpr["required_files_present"], list)
    assert isinstance(rpr["required_files_missing"], list)


def test_readiness_report_optional_files(rpr):
    assert isinstance(rpr["optional_files_present"], list)


def test_readiness_report_recovery_compiler_status(rpr):
    assert "recovery_compiler_intake_status" in rpr
    assert rpr["recovery_compiler_intake_status"] in {
        "READY_FOR_OFFLINE_COMPILER_TEST",
        "PARTIAL_FOR_OFFLINE_COMPILER_TEST",
        "NOT_READY_FOR_COMPILER_HANDOFF",
        "INVALID_COMPILER_INTAKE",
    }


def test_readiness_report_not_sufficient_for(rpr):
    assert "not_sufficient_for" in rpr
    nss = rpr["not_sufficient_for"]
    assert "recipe_control" in nss or len(nss) > 0


def test_readiness_report_with_minimal_rows():
    rows = [{"tool_id": "t1", "chamber_id": "c1", "lot_id": "l1",
              "wafer_id": "w1", "step_id": "s1", "alarm_code": "0",
              "rf_power_W": "500", "pressure_mTorr": "30", "gas_flow_sccm": "100",
              "temperature_C": "25", "run_id": "r1", "timestamp": "2024-01-01"}
             for _ in range(5)]
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="min_test", asset_id="chip_min",
        alias_map={}, tool_cols=list(rows[0].keys()),
        tool_rows=rows, metro_rows=rows[:5], test_rows=rows[:5],
    )
    rpr = reports["semiconductor_pilot_readiness_report"]
    assert rpr["readiness_score"] >= 0.0
