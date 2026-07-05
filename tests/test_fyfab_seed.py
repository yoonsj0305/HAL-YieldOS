"""
Tests for v2.8.0 FYFab Seed (Functional Yield Fab Seed Edition).

Uses tempfile.TemporaryDirectory() for Windows compatibility.
Uses direct Python function calls.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

_FYFAB_SAMPLE = Path(__file__).parent.parent / "yieldos" / "sample_data" / "fyfab_seed"


def _load(path: Path, fname: str) -> dict:
    p = path / fname
    assert p.exists(), f"{fname} not found in {path}"
    return json.loads(p.read_text(encoding="utf-8"))


def _run_fyfab_demo(out_dir: str, input_dir=None):
    from yieldos.domains.semiforge.fyfab import run_fyfab_demo
    return run_fyfab_demo(out_dir=out_dir, input_dir=input_dir)


def _run_validate(case_dir: str, strict: bool = True):
    from yieldos.cli.main import cmd_validate
    ns = argparse.Namespace(case=case_dir, strict=strict)
    return cmd_validate(ns)


def _run_inspect_output(case_dir: str):
    from yieldos.cli.main import cmd_inspect_output
    ns = argparse.Namespace(case_dir=case_dir)
    return cmd_inspect_output(ns)


# ── Test 1: sample data exists ────────────────────────────────────────────────

def test_fyfab_sample_exists():
    assert (_FYFAB_SAMPLE / "fabricated_structure_grid.csv").exists()
    assert (_FYFAB_SAMPLE / "defect_map.csv").exists()
    assert (_FYFAB_SAMPLE / "material_regions.csv").exists()
    assert (_FYFAB_SAMPLE / "target_function_blocks.json").exists()
    assert (_FYFAB_SAMPLE / "README.md").exists()


# ── Test 2: demo CLI runs ─────────────────────────────────────────────────────

def test_fyfab_demo_cli_runs():
    with tempfile.TemporaryDirectory() as tmpdir:
        r = _run_fyfab_demo(tmpdir)
        assert "case_id" in r
        assert "chip_passport" in r
        assert "classification" in r


# ── Test 3: standard output bundle exists ─────────────────────────────────────

def test_fyfab_outputs_exist():
    _STANDARD = [
        "state_snapshot.json", "evidence_pack.json", "ooda_frame.json",
        "recovery_candidates.json", "report.md", "report.html",
        "input_validation.json", "decision_readiness_report.json",
        "functional_yield_scorecard.json", "functional_binning_result.json",
        "functional_passport.json", "evidence_pack.md",
        "recovery_route_report.json", "failure_scenario_record.json",
        "next_data_request.json", "analysis_trace.json",
        "source_data_manifest.json", "data_quality_report.json",
        "evidence_conflict_report.json", "baseline_vs_yieldos.json",
        "business_case_summary.json", "case_manifest.json",
    ]
    _FYFAB = [
        "fabricated_structure_map.json",
        "defect_map_summary.json",
        "usable_cell_classification.json",
        "candidate_functional_regions.json",
        "reconfiguration_candidate_map.json",
        "functional_yield_chip_passport.json",
        "fyfab_case_study.json",
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_fyfab_demo(tmpdir)
        out = Path(tmpdir)
        for fname in _STANDARD + _FYFAB:
            assert (out / fname).exists(), f"{fname} missing"


# ── Test 4: strict validation passes ─────────────────────────────────────────

def test_fyfab_strict_validation_passes():
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_fyfab_demo(tmpdir)
        rc = _run_validate(tmpdir, strict=True)
        assert rc == 0, f"Strict validation returned {rc}"


# ── Test 5: source manifest includes FYFab input files ───────────────────────

def test_fyfab_source_manifest_inputs():
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_fyfab_demo(tmpdir)
        sdm = _load(Path(tmpdir), "source_data_manifest.json")
        files = sdm.get("input_files") or sdm.get("source_files") or []
        names = {Path(f.get("path", "")).name for f in files}
        assert "fabricated_structure_grid.csv" in names
        assert "defect_map.csv" in names
        assert "material_regions.csv" in names


# ── Test 6: functional passport links chip passport ───────────────────────────

def test_fyfab_functional_passport_links_chip_passport():
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_fyfab_demo(tmpdir)
        fp = _load(Path(tmpdir), "functional_passport.json")
        assert "fyfab_chip_passport_ref" in fp, "functional_passport missing fyfab_chip_passport_ref"
        assert fp["fyfab_chip_passport_ref"] == "functional_yield_chip_passport.json"
        assert "fabrication_context" in fp
        assert fp["fabrication_context"]["context_boundary"] == "simulation_only_not_fab_control"


# ── Test 7: OODA links FYFab case study ──────────────────────────────────────

def test_fyfab_ooda_links_case_study():
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_fyfab_demo(tmpdir)
        ooda = _load(Path(tmpdir), "ooda_frame.json")
        assert "fyfab_case_study_ref" in ooda, "ooda_frame missing fyfab_case_study_ref"
        assert ooda["fyfab_case_study_ref"] == "fyfab_case_study.json"
        assert ooda.get("control_loop") is False
        assert ooda.get("human_review_required") is True


# ── Test 8: chip passport has remaining and blocked functions ─────────────────

def test_fyfab_chip_passport_roles():
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_fyfab_demo(tmpdir)
        cp = _load(Path(tmpdir), "functional_yield_chip_passport.json")
        assert isinstance(cp.get("remaining_functions"), list)
        assert isinstance(cp.get("blocked_functions"), list)
        assert len(cp["remaining_functions"]) >= 1
        assert len(cp["blocked_functions"]) >= 1
        assert cp.get("functional_yield_score") is not None
        assert 0.0 <= cp["functional_yield_score"] <= 1.0


# ── Test 9: reconfiguration map uses candidate-only claim boundary ────────────

def test_fyfab_reconfiguration_candidate_boundary():
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_fyfab_demo(tmpdir)
        rmap = _load(Path(tmpdir), "reconfiguration_candidate_map.json")
        assert rmap.get("reconfiguration_mode") == "simulation_candidate_only"
        for m in rmap.get("candidate_mappings", []):
            assert m.get("claim_boundary") == "candidate_mapping_not_routing_signoff"
        forbidden = rmap.get("forbidden_claims", [])
        assert "physical design signoff" in forbidden
        assert "timing closure" in forbidden
        assert "yield guarantee" in forbidden


# ── Test 10: output JSON does not contain forbidden control terms ─────────────

_FYFAB_FORBIDDEN_TERMS = [
    "execute_recipe",
    "modify_recipe",
    "control_deposition",
    "control_etch",
    "control_lithography",
    "physical_design_signoff_certified",
    "timing_closure_certified",
    "yield_guarantee",
    "certified_root_cause",
    "confirmed_root_cause",
    '"hardware_execution_enabled": true',
]

_FYFAB_SPECIFIC_FILES = [
    "fabricated_structure_map.json",
    "defect_map_summary.json",
    "usable_cell_classification.json",
    "candidate_functional_regions.json",
    "reconfiguration_candidate_map.json",
    "functional_yield_chip_passport.json",
    "fyfab_case_study.json",
]


def test_fyfab_output_safety_invariant():
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_fyfab_demo(tmpdir)
        out = Path(tmpdir)
        for fname in _FYFAB_SPECIFIC_FILES:
            fpath = out / fname
            assert fpath.exists(), f"{fname} missing"
            text = fpath.read_text(encoding="utf-8").lower()
            for term in _FYFAB_FORBIDDEN_TERMS:
                assert term.lower() not in text, (
                    f"Forbidden term '{term}' found in {fname}"
                )


# ── Test 11: inspect-output handles FYFab output ─────────────────────────────

def test_fyfab_inspect_output(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_fyfab_demo(tmpdir)
        rc = _run_inspect_output(tmpdir)
        assert rc == 0
        captured = capsys.readouterr()
        assert "FYFab Case:" in captured.out
        assert "functional yield score" in captured.out
        assert "chip bin candidate" in captured.out
        assert "boundary:" in captured.out
