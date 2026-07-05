"""
Golden output tests for HAL YieldOS.

Tests core structural invariants of domain outputs without relying on
exact values (since timestamps and case_ids change each run).

These tests ensure that schema, domain, safety, and structural fields
remain stable across code changes.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _normalize(d: dict, drop_keys=None) -> dict:
    """Remove volatile keys like timestamps, checksums, case_ids."""
    volatile = {"created_at", "recorded_at", "checksum", "case_id"}
    if drop_keys:
        volatile.update(drop_keys)
    return {k: v for k, v in d.items() if k not in volatile}


class TestGoldenSemFabCoreFields:
    def setup_method(self):
        from yieldos.domains.semfab import SemFabAnalyzer
        self.result = SemFabAnalyzer().analyze(
            data_dir="samples/semfab_tel_like",
            case_id="golden_semfab",
        )

    def test_state_schema(self):
        d = self.result["state"].to_dict()
        assert d["schema"] == "yieldos.state_snapshot.v1"

    def test_state_domain(self):
        assert self.result["state"].domain == "semiconductor_fab"

    def test_state_mode(self):
        assert self.result["state"].mode == "read_only_shadow"

    def test_safety_block(self):
        d = self.result["state"].to_dict()
        assert d["safety"]["hardware_execution_enabled"] is False
        assert d["safety"]["read_only"] is True
        assert d["safety"]["human_review_required"] is True

    def test_causal_claim_boundary(self):
        assert self.result["evidence_pack"].causal_claim_boundary == "candidate_only_not_certified_cause"

    def test_output_files_present(self):
        import shutil
        import tempfile
        from pathlib import Path as _Path

        from yieldos.core.report_writer import ReportWriter
        tmpdir = tempfile.mkdtemp()
        try:
            ReportWriter().write_all(
                tmpdir, self.result["state"], self.result["evidence_pack"],
                self.result["ooda_frame"], recovery_candidates=self.result["recovery_candidates"],
            )
            p = _Path(tmpdir)
            assert (p / "state_snapshot.json").exists()
            assert (p / "evidence_pack.json").exists()
            assert (p / "ooda_frame.json").exists()
            assert (p / "report.html").exists()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_schema_version_present(self):
        d = self.result["state"].to_dict()
        assert "schema_version" in d

    def test_generated_by_present(self):
        d = self.result["state"].to_dict()
        assert "generated_by" in d
        assert d["generated_by"]["product"] == "HAL YieldOS"

    def test_recovery_candidates_count(self):
        assert len(self.result["recovery_candidates"]) <= 3

    def test_missing_evidence_structured(self):
        missing = self.result["evidence_pack"].missing_evidence
        assert len(missing) > 0
        first = missing[0]
        assert isinstance(first, dict)
        assert "item" in first
        assert "reason" in first
        assert "priority" in first

    def test_time_alignment_report(self):
        assert "time_alignment_report" in self.result
        tar = self.result["time_alignment_report"]
        assert tar["schema"] == "yieldos.semfab.time_alignment.v1"
        assert "alignment_quality" in tar

    def test_evidence_graph(self):
        assert "evidence_graph" in self.result
        eg = self.result["evidence_graph"]
        assert eg["schema"] == "yieldos.evidence_graph.v1"
        assert "nodes" in eg
        assert "edges" in eg


class TestGoldenSemiForgeResult:
    def setup_method(self):
        from yieldos.domains.semiforge import SemiForgeSimulator
        self.result = SemiForgeSimulator().simulate(
            config_path="samples/semiforge_crossbar/config.json",
            case_id="golden_semiforge",
            monte_carlo_runs=5,
        )

    def test_state_schema(self):
        d = self.result["state"].to_dict()
        assert d["schema"] == "yieldos.state_snapshot.v1"

    def test_state_domain(self):
        assert self.result["state"].domain == "semiforge"

    def test_functional_yield_result(self):
        fy = self.result["functional_yield_result"]
        assert "y_func" in fy
        assert "r_conn" in fy
        assert "c_eff" in fy
        assert "analog_penalty" in fy
        assert 0.0 <= fy["y_func"] <= 1.0

    def test_optimizer_info(self):
        info = self.result["optimizer_info"]
        assert "used" in info
        assert info["used"] in ("greedy", "sqbm")

    def test_safety_block(self):
        d = self.result["state"].to_dict()
        assert d["safety"]["hardware_execution_enabled"] is False

    def test_schema_version(self):
        d = self.result["state"].to_dict()
        assert "schema_version" in d


class TestGoldenRobotStateSnapshot:
    def setup_method(self):
        from yieldos.domains.robot import RobotAnalyzer
        self.result = RobotAnalyzer().analyze(
            telemetry_path="samples/robot_ooda/robot_telemetry.csv",
            case_id="golden_robot",
        )

    def test_state_schema(self):
        d = self.result["state"].to_dict()
        assert d["schema"] == "yieldos.state_snapshot.v1"

    def test_domain(self):
        assert self.result["state"].domain == "robotics"

    def test_health_components_present(self):
        assert "health_components" in self.result
        hc = self.result["health_components"]
        assert "motion_precision" in hc
        assert "thermal_margin" in hc
        assert "control_latency" in hc
        for v in hc.values():
            assert 0.0 <= v <= 1.0

    def test_safety_block(self):
        d = self.result["state"].to_dict()
        assert d["safety"]["hardware_execution_enabled"] is False

    def test_recovery_max_3(self):
        assert len(self.result["recovery_candidates"]) <= 3

    def test_no_hardware_execution(self):
        for rc in self.result["recovery_candidates"]:
            assert not rc.hardware_execution_enabled


class TestGoldenSatelliteStateSnapshot:
    def setup_method(self):
        from yieldos.domains.satellite import SatGuardAnalyzer
        self.result = SatGuardAnalyzer().analyze(
            telemetry_path="samples/satguard/satellite_telemetry.csv",
            case_id="golden_sat",
        )

    def test_state_schema(self):
        d = self.result["state"].to_dict()
        assert d["schema"] == "yieldos.state_snapshot.v1"

    def test_domain(self):
        assert self.result["state"].domain == "satellite"

    def test_health_components_structured(self):
        hc = self.result["health_components"]
        assert "power" in hc
        assert "thermal" in hc
        assert "attitude" in hc
        assert "comms" in hc
        for v in hc.values():
            assert 0.0 <= v <= 1.0

    def test_mission_readiness(self):
        mr = self.result["mission_readiness"]
        assert 0.0 <= mr <= 1.0

    def test_safety_block(self):
        d = self.result["state"].to_dict()
        assert d["safety"]["hardware_execution_enabled"] is False

    def test_no_hardware_execution(self):
        for rc in self.result["recovery_candidates"]:
            assert not rc.hardware_execution_enabled
