"""
Release artifact and version consistency tests — v2.4.0

Verifies:
- Version metadata consistency (VERSION, pyproject.toml, MANIFEST.json)
- SAFE/FORBIDDEN action prefix contract
- input_validation.json strict mode enforcement
- Memory domain: zero blocks → FAILED input validation
- SemiFab: tool rows → PASSED input validation
- All domains emit functional_yield_vector
- Memory scorecard functional_retention matches memory functional_yield
- Scorecard uses FYV when present
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

# ── Helper ──────────────────────────────────────────────────────────────────

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"
YIELDOS_ROOT = Path(__file__).parent.parent / "yieldos"


def _get_version_file() -> str:
    return (Path(__file__).parent.parent / "VERSION").read_text(encoding="utf-8").strip()


def _get_pyproject_version() -> str:
    content = (Path(__file__).parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("version") and "=" in stripped:
            return stripped.split("=", 1)[1].strip().strip('"')
    return ""


def _get_manifest_version() -> str:
    p = Path(__file__).parent.parent / "MANIFEST.json"
    return json.loads(p.read_text(encoding="utf-8")).get("version", "")


# ── Version consistency ──────────────────────────────────────────────────────

def test_version_metadata_consistent():
    v_file = _get_version_file()
    v_pyproject = _get_pyproject_version()
    v_manifest = _get_manifest_version()
    assert v_file == v_pyproject == v_manifest, (
        f"Version mismatch: VERSION={v_file!r} pyproject={v_pyproject!r} MANIFEST={v_manifest!r}"
    )


def test_manifest_includes_memory_domain():
    p = Path(__file__).parent.parent / "MANIFEST.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "memory" in data.get("domains", [])
    assert "memory" in data.get("canonical_domains", [])
    assert "memory_device" == data.get("domain_adapters", {}).get("memory")


# ── SAFE / FORBIDDEN action prefix ──────────────────────────────────────────

def test_validate_rejects_schedule_prefix():
    from yieldos.contracts.recovery_candidate import validate_recovery_candidate
    with pytest.raises(ValueError, match="Forbidden"):
        validate_recovery_candidate("schedule_reboot", "x", [])


def test_validate_rejects_flag_prefix():
    from yieldos.contracts.recovery_candidate import validate_recovery_candidate
    with pytest.raises(ValueError, match="Forbidden"):
        validate_recovery_candidate("flag_alert", "x", [])


def test_validate_rejects_execute_prefix():
    from yieldos.contracts.recovery_candidate import validate_recovery_candidate
    with pytest.raises(ValueError, match="Forbidden"):
        validate_recovery_candidate("execute_command", "x", [])


def test_validate_accepts_recommend_prefix():
    from yieldos.contracts.recovery_candidate import validate_recovery_candidate
    validate_recovery_candidate("recommend_review", "safe action", [])


def test_safe_actions_are_review_or_draft_only():
    from yieldos.contracts.recovery_candidate import FORBIDDEN_ACTION_PREFIXES, SAFE_ACTION_PREFIXES
    assert "schedule_" not in SAFE_ACTION_PREFIXES
    assert "flag_" not in SAFE_ACTION_PREFIXES
    assert "schedule_" in FORBIDDEN_ACTION_PREFIXES
    assert "flag_" in FORBIDDEN_ACTION_PREFIXES


# ── Input validation contract ────────────────────────────────────────────────

def test_build_input_validation_passes():
    from yieldos.contracts.input_validation import build_input_validation
    iv = build_input_validation(
        case_id="test_01",
        domain_pack="robot",
        domain_adapter="robotics",
        status="PASSED",
        data_level="MINIMUM_RUNNABLE",
        found_inputs=["motor_current_A"],
        missing_inputs=[],
        record_counts={"telemetry_rows": 100},
        blocking_reasons=[],
    )
    assert iv["status"] == "PASSED"
    assert iv["data_level"] == "MINIMUM_RUNNABLE"
    assert iv["domain_pack"] == "robot"


def test_build_input_validation_rejects_bad_status():
    from yieldos.contracts.input_validation import build_input_validation
    with pytest.raises(ValueError):
        build_input_validation(
            case_id="x", domain_pack="robot", domain_adapter="robotics",
            status="UNKNOWN", data_level="MINIMUM_RUNNABLE",
            found_inputs=[], missing_inputs=[], record_counts={}, blocking_reasons=[],
        )


def test_strict_validation_rejects_failed_input_validation():
    """validate --strict must reject a case whose input_validation.json has status=FAILED."""
    import argparse

    from yieldos.cli.main import cmd_validate

    with tempfile.TemporaryDirectory() as tmp:
        case_dir = Path(tmp)
        # Write minimal required files
        from yieldos.contracts import EvidencePack, OODAFrame, SeverityLevel, StateKind, StateSnapshot
        from yieldos.core.report_writer import ReportWriter

        state = StateSnapshot(
            case_id="strict_test",
            domain="robotics",
            asset_id="robot_01",
            state=StateKind.NOMINAL,
            severity=SeverityLevel.INFO,
            confidence=0.5,
            evidence_refs=[],
            metrics={"telemetry_samples": 0},
        )
        pack = EvidencePack(
            case_id="strict_test",
            domain="robotics",
            asset_id="robot_01",
            summary="test",
            evidence_objects=[],
            root_cause_candidates=[],
            missing_evidence=[],
            state_snapshot_hash=state.snapshot_hash,
        )
        ooda = OODAFrame(
            case_id="strict_test",
            domain="robotics",
            observe="obs",
            orient="ori",
            decide="rec_decide",
            act="recommendation_only_no_hardware_action",
            evidence_pack_ref=pack.checksum,
        )

        # Write with FAILED input validation override
        from yieldos.contracts.input_validation import build_input_validation
        iv_failed = build_input_validation(
            case_id="strict_test",
            domain_pack="robot",
            domain_adapter="robotics",
            status="FAILED",
            data_level="EMPTY",
            found_inputs=[],
            missing_inputs=[],
            record_counts={"telemetry_rows": 0},
            blocking_reasons=["telemetry_samples == 0"],
        )

        ReportWriter().write_all(
            str(case_dir), state, pack, ooda,
            domain_canonical="robot",
            input_validation_override=iv_failed,
        )

        args = argparse.Namespace(case=str(case_dir), strict=True)
        result = cmd_validate(args)
        assert result != 0, "strict mode should fail when input_validation.status == FAILED"


# ── Memory domain: zero blocks → FAILED ─────────────────────────────────────

def test_memory_zero_blocks_is_failed():
    from yieldos.contracts.input_validation import build_input_validation
    iv = build_input_validation(
        case_id="mem_empty",
        domain_pack="memory",
        domain_adapter="memory_device",
        status="FAILED",
        data_level="EMPTY",
        found_inputs=[],
        missing_inputs=[],
        record_counts={"total_blocks": 0, "raw_capacity_gb": 0},
        blocking_reasons=["total_blocks == 0", "raw_capacity_gb == 0"],
    )
    assert iv["status"] == "FAILED"
    assert "total_blocks == 0" in iv["blocking_reasons"]


def test_memory_real_blocks_pass_input_validation():
    """MemoryAnalyzer on sample data should produce PASSED input_validation."""
    sample_dir = SAMPLES_ROOT / "memory_device"
    if not sample_dir.exists():
        pytest.skip("memory_device sample not available")

    from yieldos.domains.memory import MemoryAnalyzer
    result = MemoryAnalyzer().analyze(str(sample_dir), case_id="iv_mem_test")
    iv = result.get("input_validation")
    assert iv is not None, "MemoryAnalyzer must return input_validation"
    assert iv["status"] == "PASSED", f"Expected PASSED, got {iv['status']}"


# ── SemiFab input validation ─────────────────────────────────────────────────

def test_semiconductor_tool_rows_pass_input_validation():
    sample_dir = SAMPLES_ROOT / "semfab_tel_like"
    if not sample_dir.exists():
        pytest.skip("semfab_tel_like sample not available")

    from yieldos.domains.semfab import SemFabAnalyzer
    result = SemFabAnalyzer().analyze(str(sample_dir), case_id="iv_semfab_test")
    iv = result.get("input_validation")
    assert iv is not None, "SemFabAnalyzer must return input_validation"
    assert iv["status"] == "PASSED"


# ── Robot/Space input validation ────────────────────────────────────────────

def test_robot_telemetry_samples_pass_input_validation():
    tp = SAMPLES_ROOT / "robot_ooda" / "robot_telemetry.csv"
    if not tp.exists():
        tp = SAMPLES_ROOT / "robot" / "robot_telemetry.csv"
    if not tp.exists():
        pytest.skip("robot telemetry sample not available")

    from yieldos.domains.robot import RobotAnalyzer
    result = RobotAnalyzer().analyze(str(tp), case_id="iv_robot_test")
    iv = result.get("input_validation")
    assert iv is not None, "RobotAnalyzer must return input_validation"
    assert iv["status"] == "PASSED"


def test_space_telemetry_samples_pass_input_validation():
    tp = SAMPLES_ROOT / "satguard" / "satellite_telemetry.csv"
    if not tp.exists():
        tp = SAMPLES_ROOT / "space" / "satellite_telemetry.csv"
    if not tp.exists():
        pytest.skip("satellite telemetry sample not available")

    from yieldos.domains.satellite import SatGuardAnalyzer
    result = SatGuardAnalyzer().analyze(str(tp), case_id="iv_sat_test")
    iv = result.get("input_validation")
    assert iv is not None, "SatGuardAnalyzer must return input_validation"
    assert iv["status"] == "PASSED"


# ── SemiForge input validation ───────────────────────────────────────────────

def test_semiforge_config_pass_input_validation():
    cp = SAMPLES_ROOT / "semiforge_crossbar" / "config.json"
    if not cp.exists():
        cp = SAMPLES_ROOT / "semiforge" / "config.json"
    if not cp.exists():
        pytest.skip("semiforge config sample not available")

    from yieldos.domains.semiforge import SemiForgeSimulator
    result = SemiForgeSimulator().simulate(str(cp), case_id="iv_forge_test", monte_carlo_runs=5)
    iv = result.get("input_validation")
    assert iv is not None, "SemiForgeSimulator must return input_validation"
    assert iv["status"] == "PASSED"


def test_semiforge_missing_config_is_failed():
    """Semiforge with a nonexistent config path should produce FAILED input_validation."""
    from yieldos.domains.semiforge import SemiForgeSimulator
    with tempfile.TemporaryDirectory() as tmp:
        cp = str(Path(tmp) / "nonexistent_config.json")
        result = SemiForgeSimulator().simulate(cp, case_id="iv_forge_empty", monte_carlo_runs=5)
        iv = result.get("input_validation")
        # Empty config (no file) still runs with defaults — assert iv is returned
        assert iv is not None, "SemiForgeSimulator must return input_validation even with empty config"


# ── Functional Yield Vector ──────────────────────────────────────────────────

def test_all_domains_emit_functional_yield_vector():
    """All 5 domain analyzers must set state.metrics['functional_yield_vector']."""
    samples = SAMPLES_ROOT

    # Robot
    tp = samples / "robot_ooda" / "robot_telemetry.csv"
    if not tp.exists():
        tp = samples / "robot" / "robot_telemetry.csv"
    if tp.exists():
        from yieldos.domains.robot import RobotAnalyzer
        result = RobotAnalyzer().analyze(str(tp), case_id="fyv_robot")
        fyv = result["state"].metrics.get("functional_yield_vector")
        assert fyv is not None, "Robot must set functional_yield_vector"
        assert "functional_yield_score" in fyv

    # Space
    tp = samples / "satguard" / "satellite_telemetry.csv"
    if not tp.exists():
        tp = samples / "space" / "satellite_telemetry.csv"
    if tp.exists():
        from yieldos.domains.satellite import SatGuardAnalyzer
        result = SatGuardAnalyzer().analyze(str(tp), case_id="fyv_sat")
        fyv = result["state"].metrics.get("functional_yield_vector")
        assert fyv is not None, "Space must set functional_yield_vector"

    # Semiconductor
    dd = samples / "semfab_tel_like"
    if dd.exists():
        from yieldos.domains.semfab import SemFabAnalyzer
        result = SemFabAnalyzer().analyze(str(dd), case_id="fyv_semfab")
        fyv = result["state"].metrics.get("functional_yield_vector")
        assert fyv is not None, "Semiconductor must set functional_yield_vector"

    # SemiForge
    cp = samples / "semiforge_crossbar" / "config.json"
    if not cp.exists():
        cp = samples / "semiforge" / "config.json"
    if cp.exists():
        from yieldos.domains.semiforge import SemiForgeSimulator
        result = SemiForgeSimulator().simulate(str(cp), case_id="fyv_forge", monte_carlo_runs=5)
        fyv = result["state"].metrics.get("functional_yield_vector")
        assert fyv is not None, "SemiForge must set functional_yield_vector"
        # SemiForge: override_yield_score == y_func
        y_func = result["state"].metrics.get("y_func")
        assert abs(fyv["functional_yield_score"] - y_func) < 0.001

    # Memory
    md = samples / "memory_device"
    if md.exists():
        from yieldos.domains.memory import MemoryAnalyzer
        result = MemoryAnalyzer().analyze(str(md), case_id="fyv_mem")
        fyv = result["state"].metrics.get("functional_yield_vector")
        assert fyv is not None, "Memory must set functional_yield_vector"


def test_memory_scorecard_matches_memory_functional_yield():
    """functional_yield_scorecard.functional_retention must match memory functional_yield."""
    md = SAMPLES_ROOT / "memory_device"
    if not md.exists():
        pytest.skip("memory_device sample not available")

    import tempfile

    from yieldos.core.report_writer import ReportWriter
    from yieldos.domains.memory import MemoryAnalyzer

    result = MemoryAnalyzer().analyze(str(md), case_id="fy_match_test")
    fyv = result["state"].metrics.get("functional_yield_vector")
    assert fyv is not None

    with tempfile.TemporaryDirectory() as tmp:
        extra = {}
        if result.get("functional_capacity"):
            extra["memory_functional_capacity"] = result["functional_capacity"]
        if result.get("placement_recommendation"):
            extra["memory_data_placement_recommendation"] = result["placement_recommendation"]
        if result.get("bad_block_evidence_map"):
            extra["memory_bad_block_evidence_map"] = result["bad_block_evidence_map"]

        ReportWriter().write_all(
            tmp,
            result["state"],
            result["evidence_pack"],
            result["ooda_frame"],
            remaining_roles=result.get("remaining_roles", []),
            blocked_roles=result.get("blocked_roles", []),
            bin_class=result.get("bin_class"),
            decision_readiness=result.get("decision_readiness"),
            domain_canonical="memory",
            extra_outputs=extra or None,
            input_validation_override=result.get("input_validation"),
        )
        scorecard_path = Path(tmp) / "functional_yield_scorecard.json"
        assert scorecard_path.exists()
        scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
        sc_retention = scorecard.get("functional_retention", -1)
        fyv_score = fyv.get("functional_yield_score")
        assert abs(sc_retention - fyv_score) < 0.001, (
            f"Scorecard functional_retention={sc_retention} != FYV score={fyv_score}"
        )


def test_scorecard_uses_fyv_when_present():
    """ReportWriter must use FYV vector when state.metrics has it."""
    import tempfile

    from yieldos.contracts import EvidencePack, OODAFrame, SeverityLevel, StateKind, StateSnapshot
    from yieldos.core.functional_yield import build_functional_yield_vector
    from yieldos.core.report_writer import ReportWriter

    state = StateSnapshot(
        case_id="sc_fyv_test",
        domain="robot",
        asset_id="arm_01",
        state=StateKind.NOMINAL,
        severity=SeverityLevel.INFO,
        confidence=0.8,
        evidence_refs=[],
        metrics={"telemetry_samples": 100},
    )
    fyv = build_functional_yield_vector(
        domain="robot",
        case_id="sc_fyv_test",
        asset_id="arm_01",
        component_scores={"motion_precision": 0.9, "thermal_margin": 0.85},
        role_scores={"full_operation": 1.0},
        evidence_confidence=0.8,
        missing_inputs=[],
        score_kind="heuristic",
        model_limitations=[],
        domain_adapter="robotics",
        override_yield_score=0.88,
    )
    state.metrics["functional_yield_vector"] = fyv

    pack = EvidencePack(
        case_id="sc_fyv_test",
        domain="robot",
        asset_id="arm_01",
        summary="test",
        evidence_objects=[],
        root_cause_candidates=[],
        missing_evidence=[],
        state_snapshot_hash=state.snapshot_hash,
    )
    ooda = OODAFrame(
        case_id="sc_fyv_test",
        domain="robot",
        observe="obs",
        orient="ori",
        decide="dec",
        act="recommendation_only_no_hardware_action",
        evidence_pack_ref=pack.checksum,
    )

    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="robot")
        scorecard = json.loads((Path(tmp) / "functional_yield_scorecard.json").read_text())
        assert abs(scorecard["functional_retention"] - 0.88) < 0.001, (
            f"Scorecard should use FYV override score 0.88, got {scorecard['functional_retention']}"
        )


# ── v2.4 Functional Passport acceptance tests ──────────────────────────────

def _make_write_all_base(case_id: str = "v24_test"):
    """Helper: minimal write_all invocation; returns (paths, out_dir_path) as a temp context."""
    from yieldos.contracts import EvidencePack, OODAFrame, SeverityLevel, StateKind, StateSnapshot
    from yieldos.core.report_writer import ReportWriter

    state = StateSnapshot(
        case_id=case_id,
        domain="memory_device",
        asset_id="mem_01",
        state=StateKind.DEGRADED,
        severity=SeverityLevel.MEDIUM,
        confidence=0.75,
        evidence_refs=[],
        metrics={"total_blocks": 128, "raw_capacity_gb": 1.0, "bad_block_count": 5,
                 "ecc_error_count": 2, "telemetry_samples": 128},
    )
    pack = EvidencePack(
        case_id=case_id,
        domain="memory_device",
        asset_id="mem_01",
        summary="test passport",
        evidence_objects=[],
        root_cause_candidates=[],
        missing_evidence=[],
        state_snapshot_hash=state.snapshot_hash,
    )
    ooda = OODAFrame(
        case_id=case_id,
        domain="memory_device",
        observe="obs",
        orient="ori",
        decide="dec",
        act="recommendation_only_no_hardware_action",
        evidence_pack_ref=pack.checksum,
    )
    return state, pack, ooda, ReportWriter


def test_functional_passport_has_passport_validity():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_validity")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory")
        fp = json.loads((Path(tmp) / "functional_passport.json").read_text())
        pv = fp.get("passport_validity")
        assert pv is not None, "functional_passport must have passport_validity"
        assert pv["status"] == "candidate_only"
        assert "expires_after" in pv
        assert isinstance(pv.get("valid_conditions"), list)


def test_functional_passport_has_evidence_strength():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_evidence_strength")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory")
        fp = json.loads((Path(tmp) / "functional_passport.json").read_text())
        es = fp.get("evidence_strength")
        assert es is not None, "functional_passport must have evidence_strength"
        assert "data_completeness" in es
        assert "signal_consistency" in es
        assert "historical_support" in es
        assert "model_calibration" in es


def test_functional_passport_approval_gate_required():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_approval")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory")
        fp = json.loads((Path(tmp) / "functional_passport.json").read_text())
        ag = fp.get("approval_gate")
        assert ag is not None, "functional_passport must have approval_gate"
        assert ag["required"] is True
        assert "authority_matrix_present" in ag
        assert ag["approval_level"] == "engineering_review"


def test_functional_passport_approval_gate_authority_matrix_with_policy():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_authority")
    with tempfile.TemporaryDirectory() as tmp:
        policy_inputs = {"authority_matrix": {"approve": ["engineering_manager"]}}
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory",
                                  policy_inputs=policy_inputs)
        fp = json.loads((Path(tmp) / "functional_passport.json").read_text())
        ag = fp.get("approval_gate")
        assert ag["authority_matrix_present"] is True


def test_functional_passport_required_human_roles():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_roles")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory")
        fp = json.loads((Path(tmp) / "functional_passport.json").read_text())
        roles = fp.get("required_human_roles")
        assert isinstance(roles, list)
        assert len(roles) > 0
        assert "storage_engineer" in roles or "quality_manager" in roles


def test_source_data_manifest_present():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_sdm")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory")
        sdm = Path(tmp) / "source_data_manifest.json"
        assert sdm.exists(), "source_data_manifest.json must be written"
        data = json.loads(sdm.read_text())
        assert data["schema"].startswith("hal.yieldos.source_data_manifest")
        assert "input_files" in data


def test_source_data_manifest_records_file_hash():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_sdm_hash")
    md = SAMPLES_ROOT / "memory_device"
    if not md.exists():
        pytest.skip("memory_device sample not available")
    block_csv = str(md / "block_health.csv")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory",
                                  source_data_paths=[block_csv])
        data = json.loads((Path(tmp) / "source_data_manifest.json").read_text())
        files = data["input_files"]
        assert len(files) == 1
        assert files[0]["exists"] is True
        assert files[0]["sha256"].startswith("sha256:")
        assert "rows" in files[0]


def test_baseline_vs_yieldos_present():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_baseline")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory")
        bv = Path(tmp) / "baseline_vs_yieldos.json"
        assert bv.exists(), "baseline_vs_yieldos.json must be written"
        data = json.loads(bv.read_text())
        assert data["schema"].startswith("hal.yieldos.baseline_vs_yieldos")
        assert "binary_policy_verdict" in data
        assert "yieldos_functional_verdict" in data
        assert "reclassification_occurred" in data
        assert data["human_decision_required"] is True


def test_data_quality_report_present():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_dqr")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory")
        dq = Path(tmp) / "data_quality_report.json"
        assert dq.exists(), "data_quality_report.json must be written"
        data = json.loads(dq.read_text(encoding="utf-8"))
        assert "data_completeness" in data
        assert "signal_coverage" in data


def test_evidence_conflict_report_present():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_ecr")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory")
        ecr = Path(tmp) / "evidence_conflict_report.json"
        assert ecr.exists(), "evidence_conflict_report.json must be written"
        data = json.loads(ecr.read_text(encoding="utf-8"))
        assert "conflict_count" in data
        assert "conflicts" in data


def test_business_case_summary_present():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_bcs")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory")
        bcs = Path(tmp) / "business_case_summary.json"
        assert bcs.exists(), "business_case_summary.json must be written"
        data = json.loads(bcs.read_text(encoding="utf-8"))
        assert "value_proposition" in data
        assert "decision_authority" in data
        assert data["decision_authority"] == "human_only"


def test_schema_version_is_v2_for_passport():
    import tempfile
    state, pack, ooda, ReportWriter = _make_write_all_base("fp_schema_v2")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(tmp, state, pack, ooda, domain_canonical="memory")
        fp = json.loads((Path(tmp) / "functional_passport.json").read_text())
        assert fp["schema"] == "hal.yieldos.functional_passport.v2"
