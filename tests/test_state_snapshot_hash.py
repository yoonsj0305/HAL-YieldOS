"""
Tests for StateSnapshot.snapshot_hash integrity (v2.2.0)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStateSnapshotHash:
    def _make_snapshot(self, **kwargs):
        from yieldos.contracts.state_snapshot import SeverityLevel, StateKind, StateSnapshot
        defaults = {
            "case_id": "hash_test_01",
            "domain": "robot",
            "asset_id": "arm_01",
            "state": StateKind.DEGRADED,
            "severity": SeverityLevel.MEDIUM,
            "confidence": 0.7,
        }
        defaults.update(kwargs)
        return StateSnapshot(**defaults)

    def test_snapshot_hash_present(self):
        ss = self._make_snapshot()
        assert ss.snapshot_hash
        assert ss.snapshot_hash.startswith("sha256:")

    def test_snapshot_hash_is_deterministic(self):
        ss1 = self._make_snapshot(created_at="2024-01-01T00:00:00+00:00")
        ss2 = self._make_snapshot(created_at="2024-01-01T00:00:00+00:00")
        assert ss1.snapshot_hash == ss2.snapshot_hash

    def test_different_content_different_hash(self):
        ss1 = self._make_snapshot(confidence=0.5, created_at="2024-01-01T00:00:00+00:00")
        ss2 = self._make_snapshot(confidence=0.9, created_at="2024-01-01T00:00:00+00:00")
        assert ss1.snapshot_hash != ss2.snapshot_hash

    def test_hash_in_to_dict(self):
        ss = self._make_snapshot()
        d = ss.to_dict()
        assert "snapshot_hash" in d
        assert d["snapshot_hash"].startswith("sha256:")

    def test_evidence_pack_carries_snapshot_hash(self):
        from yieldos.contracts.evidence_pack import CAUSAL_CLAIM_BOUNDARY, EvidencePack
        ss = self._make_snapshot()
        pack = EvidencePack(
            case_id="hash_test_01",
            domain="robot",
            asset_id="arm_01",
            summary="test",
            causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY,
            state_snapshot_hash=ss.snapshot_hash,
        ).seal()
        assert pack.state_snapshot_hash == ss.snapshot_hash

    def test_functional_passport_carries_snapshot_hash(self):
        from yieldos.contracts.evidence_pack import CAUSAL_CLAIM_BOUNDARY, EvidencePack
        from yieldos.contracts.ooda_frame import ACT_BOUNDARY, OODAFrame
        from yieldos.core.report_writer import ReportWriter

        ss = self._make_snapshot()
        pack = EvidencePack(
            case_id="fp_hash_test",
            domain="robot",
            asset_id="arm_01",
            summary="test",
            causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY,
            state_snapshot_hash=ss.snapshot_hash,
        ).seal()
        ooda = OODAFrame(
            case_id="fp_hash_test",
            domain="robot",
            observe="test",
            orient="test",
            decide="test",
            act=ACT_BOUNDARY,
        )
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ReportWriter()
            writer.write_all(
                out_dir=tmpdir,
                state=ss,
                pack=pack,
                ooda=ooda,
                domain_canonical="robot",
            )
            fp_path = Path(tmpdir) / "functional_passport.json"
            fp = json.loads(fp_path.read_text())
            assert "state_snapshot_hash" in fp
            assert fp["state_snapshot_hash"] == ss.snapshot_hash

    def test_all_domain_snapshots_have_hash(self):
        from yieldos.domains.robot import RobotAnalyzer
        from yieldos.domains.satellite import SatGuardAnalyzer
        from yieldos.domains.semfab import SemFabAnalyzer
        from yieldos.domains.semiforge import SemiForgeSimulator

        results = [
            SemFabAnalyzer().analyze(data_dir="samples/semfab_tel_like", case_id="hash_test_semfab"),
            RobotAnalyzer().analyze(telemetry_path="samples/robot_ooda/robot_telemetry.csv", case_id="hash_test_robot"),
            SatGuardAnalyzer().analyze(telemetry_path="samples/satguard/satellite_telemetry.csv", case_id="hash_test_sat"),
            SemiForgeSimulator().simulate(config_path="samples/semiforge_crossbar/config.json", case_id="hash_test_semiforge", monte_carlo_runs=5),
        ]
        for result in results:
            state = result["state"]
            pack = result["evidence_pack"]
            assert state.snapshot_hash.startswith("sha256:"), f"Missing snapshot_hash in {state.domain}"
            assert pack.state_snapshot_hash == state.snapshot_hash, (
                f"Hash mismatch in {state.domain}: "
                f"pack.state_snapshot_hash={pack.state_snapshot_hash} "
                f"state.snapshot_hash={state.snapshot_hash}"
            )
