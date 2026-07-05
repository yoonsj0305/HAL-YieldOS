"""Tests that semiconductor pilot-pack generates the full standard YieldOS case bundle.

The semiconductor pilot-pack command must produce all standard YieldOS output files
(state_snapshot.json, evidence_pack.json, ooda_frame.json, report.html, etc.)
in addition to the 11 semiconductor pilot-specific reports.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.cli.main import main

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"

# Standard YieldOS case bundle files (must always be present)
STANDARD_BUNDLE_FILES = [
    "state_snapshot.json",
    "evidence_pack.json",
    "ooda_frame.json",
    "report.html",
    "report.md",
    "functional_passport.json",
    "recovery_candidates.json",
    "recovery_route_report.json",
    "failure_scenario_record.json",
    "next_data_request.json",
    "decision_readiness_report.json",
    "functional_yield_scorecard.json",
    "functional_binning_result.json",
    "input_validation.json",
    "case_manifest.json",
    "source_data_manifest.json",
    "analysis_trace.json",
    "data_quality_report.json",
    "evidence_pack.md",
]

# Semiconductor pilot-specific files (13 reports — 11 + 2 new in v3.0.3)
PILOT_SPECIFIC_FILES = [
    "semiconductor_pilot_readiness_report.json",
    "semiconductor_evidence_completeness_report.json",
    "semiconductor_wafer_die_summary.json",
    "semiconductor_functional_region_map.json",
    "semiconductor_role_candidate_map.json",
    "semiconductor_valid_conditions_report.json",
    "semiconductor_process_evidence_report.json",
    "semiconductor_human_review_packet.json",
    "semiconductor_missing_evidence_request.json",
    "semiconductor_recovery_compiler_intake_preview.json",
    "semiconductor_recovery_compiler_handoff_boundary.json",
    "semiconductor_recovery_compiler_export.json",
    "semiconductor_handoff_manifest.json",
    "semiconductor_pilot_case_summary.md",
]


@pytest.fixture(scope="module")
def pilot_output(tmp_path_factory):
    if not SAMPLE_DIR.exists() or not (SAMPLE_DIR / "tool_log.csv").exists():
        pytest.skip("pilot_semiconductor samples not found")
    out = tmp_path_factory.mktemp("semi_pilot_standard")
    rc = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(out),
        "--asset", "test_chip_bundle",
        "--case", "test_bundle_case_001",
    ])
    assert rc == 0, f"semiconductor pilot-pack failed with exit code {rc}"
    return out


def test_returns_exit_code_zero(tmp_path):
    if not SAMPLE_DIR.exists() or not (SAMPLE_DIR / "tool_log.csv").exists():
        pytest.skip("pilot_semiconductor samples not found")
    rc = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(tmp_path),
    ])
    assert rc == 0


@pytest.mark.parametrize("fname", STANDARD_BUNDLE_FILES)
def test_standard_bundle_file_exists(pilot_output, fname):
    assert (pilot_output / fname).exists(), \
        f"Standard bundle file missing from semiconductor pilot-pack output: {fname}"


@pytest.mark.parametrize("fname", PILOT_SPECIFIC_FILES)
def test_pilot_specific_file_exists(pilot_output, fname):
    assert (pilot_output / fname).exists(), \
        f"Pilot-specific file missing from semiconductor pilot-pack output: {fname}"


def test_state_snapshot_is_read_only(pilot_output):
    data = json.loads((pilot_output / "state_snapshot.json").read_text(encoding="utf-8"))
    assert data.get("mode") == "read_only_shadow"
    assert data.get("safety", {}).get("hardware_execution_enabled") is False


def test_evidence_pack_has_valid_checksum(pilot_output):
    import hashlib
    pack = json.loads((pilot_output / "evidence_pack.json").read_text(encoding="utf-8"))
    stored = pack.get("checksum", "")
    payload = {
        "schema": pack.get("schema", ""),
        "case_id": pack.get("case_id", ""),
        "domain": pack.get("domain", ""),
        "asset_id": pack.get("asset_id", ""),
        "summary": pack.get("summary", ""),
        "causal_claim_boundary": pack.get("causal_claim_boundary", ""),
        "evidence_objects": pack.get("evidence_objects", []),
        "root_cause_candidates": pack.get("root_cause_candidates", []),
        "missing_evidence": pack.get("missing_evidence", []),
        "state_snapshot_ref": pack.get("state_snapshot_ref", ""),
        "state_snapshot_hash": pack.get("state_snapshot_hash", ""),
        "created_at": pack.get("created_at", ""),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected = "sha256:" + hashlib.sha256(blob).hexdigest()
    assert stored == expected, "evidence_pack.json checksum mismatch"


def test_ooda_frame_act_value(pilot_output):
    ooda = json.loads((pilot_output / "ooda_frame.json").read_text(encoding="utf-8"))
    act = ooda.get("act", "")
    assert isinstance(act, dict), \
        f"ooda_frame.act must be dict for semiconductor pilot (v3.0.3), got {type(act)}: {act!r}"
    assert act.get("automatic_action_enabled") is False, \
        "ooda_frame.act.automatic_action_enabled must be False"
    assert act.get("hardware_control_enabled") is False, \
        "ooda_frame.act.hardware_control_enabled must be False"
    assert act.get("recipe_control_enabled") is False, \
        "ooda_frame.act.recipe_control_enabled must be False"


def test_case_manifest_includes_standard_outputs(pilot_output):
    manifest = json.loads((pilot_output / "case_manifest.json").read_text(encoding="utf-8"))
    files = manifest.get("files", {})
    # case_manifest does not self-reference itself
    required_keys = {"state_snapshot", "evidence_pack", "ooda_frame", "functional_passport",
                     "source_data_manifest"}
    for key in required_keys:
        assert key in files, f"case_manifest missing standard key: {key}"


def test_source_data_manifest_includes_semiconductor_inputs(pilot_output):
    sdm = json.loads((pilot_output / "source_data_manifest.json").read_text(encoding="utf-8"))
    source_files = sdm.get("input_files") or sdm.get("source_files") or []
    names = {Path(f.get("path", f.get("file_path", ""))).name for f in source_files}
    assert "tool_log.csv" in names, \
        f"source_data_manifest missing tool_log.csv; found: {sorted(names)}"


def test_evidence_pack_domain_is_semiconductor(pilot_output):
    pack = json.loads((pilot_output / "evidence_pack.json").read_text(encoding="utf-8"))
    domain = pack.get("domain", "")
    assert "semiconductor" in domain, \
        f"evidence_pack domain should contain 'semiconductor', got {domain!r}"


def test_recovery_profile_never_generated(pilot_output):
    assert not (pilot_output / "recovery_profile.json").exists(), \
        "YieldOS must NEVER generate recovery_profile.json"


def test_input_validation_status_passed(pilot_output):
    iv = json.loads((pilot_output / "input_validation.json").read_text(encoding="utf-8"))
    assert iv.get("status") == "PASSED", \
        f"input_validation.status should be PASSED, got {iv.get('status')!r}"


def test_functional_passport_hardware_disabled(pilot_output):
    fp = json.loads((pilot_output / "functional_passport.json").read_text(encoding="utf-8"))
    assert fp.get("hardware_execution_enabled") is False


def test_decision_readiness_report_valid_category(pilot_output):
    dr = json.loads((pilot_output / "decision_readiness_report.json").read_text(encoding="utf-8"))
    valid_cats = {"DATA_INCOMPLETE", "RUNNABLE_LOW_CONFIDENCE", "PASSPORT_ELIGIBLE",
                  "ACTION_INELIGIBLE", "DECISION_READY", "RUNTIME_CANDIDATE"}
    cat = dr.get("category", "")
    assert cat in valid_cats, f"decision_readiness category invalid: {cat!r}"


def test_pilot_readiness_report_valid(pilot_output):
    rr = json.loads(
        (pilot_output / "semiconductor_pilot_readiness_report.json").read_text(encoding="utf-8"))
    assert rr.get("hardware_control_enabled") is False
    assert rr.get("human_review_required") is True
    assert rr.get("readiness_status") in {
        "PILOT_READY", "PARTIAL_PILOT_READY", "NOT_PILOT_READY"
    }
    assert 0.0 <= rr.get("readiness_score", -1) <= 1.0


def test_total_output_file_count(pilot_output):
    json_files = list(pilot_output.glob("*.json"))
    md_files = list(pilot_output.glob("*.md"))
    html_files = list(pilot_output.glob("*.html"))
    total = len(json_files) + len(md_files) + len(html_files)
    # Standard bundle (~19 JSON + 2 MD + 1 HTML) + 11 pilot JSON + 1 pilot MD + extras ≥ 30
    assert total >= 30, \
        f"Expected ≥30 output files, got {total} (json={len(json_files)}, md={len(md_files)}, html={len(html_files)})"
