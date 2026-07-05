"""
Tests for YieldOS-Orbit demo (v2.2.0)
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

ORBIT_SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "yieldos_orbit"


class TestOrbitDemoRun:
    def test_orbit_demo_runs(self):
        from yieldos.domains.satellite.orbit_demo import run_orbit_demo
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_orbit_demo(out_dir=tmpdir, asset_id="cubesat_test_01")
            assert result is not None

    def test_orbit_demo_produces_standard_bundle(self):
        from yieldos.domains.satellite.orbit_demo import run_orbit_demo
        REQUIRED = [
            "state_snapshot.json",
            "evidence_pack.json",
            "ooda_frame.json",
            "recovery_candidates.json",
            "report.md",
            "functional_passport.json",
            "case_manifest.json",
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            run_orbit_demo(out_dir=tmpdir, asset_id="cubesat_test_01")
            for fname in REQUIRED:
                fpath = Path(tmpdir) / fname
                assert fpath.exists(), f"Missing standard output file: {fname}"

    def test_orbit_mission_recommendation_produced(self):
        from yieldos.domains.satellite.orbit_demo import run_orbit_demo
        with tempfile.TemporaryDirectory() as tmpdir:
            run_orbit_demo(out_dir=tmpdir, asset_id="cubesat_test_01")
            rec_path = Path(tmpdir) / "orbit_mission_recommendation.json"
            assert rec_path.exists()
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
            assert rec["schema"] == "hal.yieldos.orbit_mission_recommendation.v1"
            assert rec["hardware_execution_enabled"] is False
            assert rec["uplink_commands_generated"] is False
            assert rec["human_review_required"] is True

    def test_orbit_recommendation_no_hardware_action(self):
        from yieldos.domains.satellite.orbit_demo import run_orbit_demo
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_orbit_demo(out_dir=tmpdir, asset_id="cubesat_test_01")
            orbit_rec = result["orbit_recommendation"]
            assert orbit_rec["hardware_execution_enabled"] is False
            assert orbit_rec["uplink_commands_generated"] is False

    def test_orbit_recommendation_causal_boundary(self):
        from yieldos.domains.satellite.orbit_demo import run_orbit_demo
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_orbit_demo(out_dir=tmpdir, asset_id="cubesat_test_01")
            rec = result["orbit_recommendation"]
            assert rec["causal_claim_boundary"] == "candidate_only_not_certified_cause"

    def test_orbit_demo_state_has_snapshot_hash(self):
        from yieldos.domains.satellite.orbit_demo import run_orbit_demo
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_orbit_demo(out_dir=tmpdir, asset_id="cubesat_test_01")
            state = result["state"]
            assert state.snapshot_hash.startswith("sha256:")

    def test_orbit_demo_orbit_recommendation_has_snapshot_hash(self):
        from yieldos.domains.satellite.orbit_demo import run_orbit_demo
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_orbit_demo(out_dir=tmpdir, asset_id="cubesat_test_01")
            rec = result["orbit_recommendation"]
            state = result["state"]
            assert rec["state_snapshot_hash"] == state.snapshot_hash

    def test_orbit_sample_files_exist(self):
        assert (ORBIT_SAMPLE_DIR / "cubesat_power_degradation.csv").exists()
        assert (ORBIT_SAMPLE_DIR / "mission_profile.json").exists()
        assert (ORBIT_SAMPLE_DIR / "README.md").exists()

    def test_mission_profile_schema(self):
        mp = json.loads((ORBIT_SAMPLE_DIR / "mission_profile.json").read_text())
        assert mp.get("schema") == "hal.yieldos.mission_profile.v1"
        assert "operating_envelope" in mp
        assert "power_budget" in mp
