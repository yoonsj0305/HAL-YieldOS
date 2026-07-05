"""
tests/test_pipeline_coherence.py

Pipeline coherence tests for v2.5.2:
  1. functional_passport.case_id is not null and equals state.case_id
  2. analysis_trace.input_validation.status mirrors input_validation.json status
  3. recovery_route_report.optimizer_info has backend_available and claim_boundary
  4. ooda_frame declares ooda_mode=read_only_evidence_frame (read-only identity)
  5. Pipeline cross-references consistent: case_manifest.cross_references + functional_passport.evidence_pack_ref
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SAMPLE_DATA = ROOT / "yieldos" / "sample_data"

MEMORY_SAMPLE = SAMPLE_DATA / "memory_device"
ROBOT_SAMPLE = SAMPLE_DATA / "robot" / "robot_telemetry.csv"
SEMIFORGE_SAMPLE = SAMPLE_DATA / "semiforge" / "config.json"


def _has_memory_sample() -> bool:
    return MEMORY_SAMPLE.exists() and (MEMORY_SAMPLE / "block_health.csv").exists()


def _has_robot_sample() -> bool:
    return ROBOT_SAMPLE.exists()


def _has_semiforge_sample() -> bool:
    return SEMIFORGE_SAMPLE.exists()


def _run_memory(tmp: str):
    from yieldos.cli.main import _memory_extra_outputs, _memory_source_data_paths, _run_and_write
    from yieldos.cli.main import _run_memory as run_mem
    result = run_mem(str(MEMORY_SAMPLE), case_id="case_coh_mem", asset_id="memdev_coh")
    extra = _memory_extra_outputs(result)
    paths = _run_and_write(result, tmp, "memory", extra_outputs=extra,
                           source_data_paths=_memory_source_data_paths(str(MEMORY_SAMPLE)))
    return result, paths


def _run_semiforge(tmp: str):
    from yieldos.cli.main import _run_and_write
    from yieldos.cli.main import _run_semiforge as run_sf
    result = run_sf(str(SEMIFORGE_SAMPLE), case_id="case_coh_sf", mc=10, optimizer="greedy")
    paths = _run_and_write(result, tmp, "semiforge")
    return result, paths


def _load(tmp: str, filename: str) -> dict:
    return json.loads((Path(tmp) / filename).read_text(encoding="utf-8"))


# ── Test 1: functional_passport.case_id is non-null and matches state.case_id ─

@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_functional_passport_case_id_not_null():
    with tempfile.TemporaryDirectory() as tmp:
        result, _ = _run_memory(tmp)
        fp = _load(tmp, "functional_passport.json")
        expected_case_id = result["state"].case_id
        assert fp.get("case_id") is not None, "functional_passport.case_id must not be null"
        assert fp["case_id"] != "", "functional_passport.case_id must not be empty"
        assert fp["case_id"] == expected_case_id, (
            f"functional_passport.case_id={fp['case_id']!r} "
            f"!= state.case_id={expected_case_id!r}"
        )


# ── Test 2: analysis_trace.input_validation reflects input_validation.json ───

@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_analysis_trace_reflects_input_validation_status():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory(tmp)
        iv = _load(tmp, "input_validation.json")
        trace = _load(tmp, "analysis_trace.json")

        # Top-level input_validation section must exist in analysis_trace
        iv_in_trace = trace.get("input_validation")
        assert iv_in_trace is not None, "analysis_trace must have top-level 'input_validation' key"

        # Status must mirror the written input_validation.json
        assert iv_in_trace.get("status") == iv.get("status"), (
            f"analysis_trace.input_validation.status={iv_in_trace.get('status')!r} "
            f"!= input_validation.json.status={iv.get('status')!r}"
        )

        # Source must point to input_validation.json
        assert iv_in_trace.get("source") == "input_validation.json", (
            "analysis_trace.input_validation.source must be 'input_validation.json'"
        )

        # First step result must also reflect the same status
        steps = trace.get("steps", [])
        first_step = steps[0] if steps else {}
        assert first_step.get("step") == "input_validation", (
            "First analysis_trace step must be 'input_validation'"
        )
        assert first_step.get("result") == iv.get("status"), (
            f"analysis_trace steps[0].result={first_step.get('result')!r} "
            f"!= input_validation.json.status={iv.get('status')!r}"
        )


# ── Test 3: recovery_route_report.optimizer_info has backend_available, claim_boundary ──

@pytest.mark.skipif(not _has_semiforge_sample(), reason="semiforge sample not available")
def test_recovery_route_report_embeds_optimizer_info():
    with tempfile.TemporaryDirectory() as tmp:
        _run_semiforge(tmp)
        rrr = _load(tmp, "recovery_route_report.json")

        opt = rrr.get("optimizer_info")
        assert opt is not None, "recovery_route_report must have 'optimizer_info' key"
        assert "backend_available" in opt, (
            "recovery_route_report.optimizer_info must have 'backend_available'"
        )
        assert "claim_boundary" in opt, (
            "recovery_route_report.optimizer_info must have 'claim_boundary'"
        )
        assert isinstance(opt["backend_available"], bool), (
            "optimizer_info.backend_available must be a boolean"
        )
        assert opt["claim_boundary"] != "", (
            "optimizer_info.claim_boundary must not be empty"
        )


# ── Test 4: ooda_frame declares read_only_evidence_frame identity ─────────────

@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_ooda_frame_declares_read_only_evidence_frame():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory(tmp)
        ooda = _load(tmp, "ooda_frame.json")

        assert ooda.get("ooda_mode") == "read_only_evidence_frame", (
            f"ooda_frame.ooda_mode must be 'read_only_evidence_frame', got {ooda.get('ooda_mode')!r}"
        )
        assert ooda.get("control_loop") is False, (
            "ooda_frame.control_loop must be false"
        )
        assert ooda.get("hardware_action_enabled") is False, (
            "ooda_frame.hardware_action_enabled must be false"
        )
        assert ooda.get("human_review_required") is True, (
            "ooda_frame.human_review_required must be true"
        )
        # Existing invariant: act must always be the boundary string
        assert ooda.get("act") == "recommendation_only_no_hardware_action", (
            "ooda_frame.act must be 'recommendation_only_no_hardware_action'"
        )


# ── Test 5: pipeline cross-references are internally consistent ───────────────

@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_pipeline_cross_references_consistent():
    with tempfile.TemporaryDirectory() as tmp:
        result, _ = _run_memory(tmp)
        fp = _load(tmp, "functional_passport.json")
        ep = _load(tmp, "evidence_pack.json")
        ooda = _load(tmp, "ooda_frame.json")
        manifest = _load(tmp, "case_manifest.json")

        # functional_passport.evidence_pack_ref must match evidence_pack.checksum
        assert fp.get("evidence_pack_ref") == ep.get("checksum"), (
            f"functional_passport.evidence_pack_ref={fp.get('evidence_pack_ref')!r} "
            f"!= evidence_pack.checksum={ep.get('checksum')!r}"
        )

        # ooda_frame.evidence_pack_ref must match evidence_pack.checksum
        assert ooda.get("evidence_pack_ref") == ep.get("checksum"), (
            f"ooda_frame.evidence_pack_ref={ooda.get('evidence_pack_ref')!r} "
            f"!= evidence_pack.checksum={ep.get('checksum')!r}"
        )

        # case_manifest must have cross_references section with key pipeline artifacts
        cross_refs = manifest.get("cross_references")
        assert cross_refs is not None, "case_manifest must have 'cross_references' key"
        for expected_key in ("state_snapshot", "evidence_pack", "ooda_frame", "functional_passport"):
            assert expected_key in cross_refs, (
                f"case_manifest.cross_references must include '{expected_key}'"
            )
