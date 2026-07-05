"""Tests for semiconductor_human_review_packet.json (v3.0.1)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def hrp():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="hrp_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    return reports["semiconductor_human_review_packet"]


def test_hrp_schema(hrp):
    assert hrp["schema"] == "hal.yieldos.semiconductor.human_review_packet.v1"


def test_hrp_review_questions_non_empty(hrp):
    rq = hrp["review_questions"]
    assert isinstance(rq, list)
    assert len(rq) >= 3


def test_hrp_must_review_before_use(hrp):
    assert isinstance(hrp.get("must_review_before_use"), list)


def test_hrp_candidate_decisions_list(hrp):
    cd = hrp["candidate_decisions"]
    assert isinstance(cd, list)
    assert len(cd) > 0


def test_hrp_forbidden_decisions_list(hrp):
    fd = hrp["forbidden_decisions"]
    assert isinstance(fd, list)
    assert len(fd) > 0


def test_hrp_forbidden_has_execute(hrp):
    fd_text = " ".join(hrp["forbidden_decisions"]).lower()
    assert "execute" in fd_text or "control" in fd_text


def test_hrp_linked_reports(hrp):
    lr = hrp["linked_reports"]
    assert isinstance(lr, list)
    assert any("functional_passport" in r for r in lr)


def test_hrp_safety(hrp):
    assert hrp["hardware_control_enabled"] is False
    assert hrp["human_review_required"] is True
    assert "human_review_packet" in hrp["claim_boundary"]
