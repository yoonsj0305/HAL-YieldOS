"""Tests for core contract objects and safety invariants."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from yieldos.contracts import (
    EvidenceObject,
    EvidencePack,
    EvidenceType,
    ExecutionMode,
    OODAFrame,
    OutcomeRecord,
    RecoveryCandidate,
    RootCauseCandidate,
    SeverityLevel,
    StateKind,
    StateSnapshot,
)
from yieldos.contracts.evidence_pack import CAUSAL_CLAIM_BOUNDARY
from yieldos.contracts.ooda_frame import ACT_BOUNDARY

# ── StateSnapshot ─────────────────────────────────────────────────────────────

class TestStateSnapshot:
    def test_basic_creation(self):
        s = StateSnapshot(
            case_id="case_001",
            domain="semiconductor_fab",
            asset_id="ETCH_01.CH_A",
            state=StateKind.PROCESS_DRIFT_CANDIDATE,
            severity=SeverityLevel.MEDIUM,
            confidence=0.74,
        )
        assert s.schema == "yieldos.state_snapshot.v1"
        assert s.mode == "read_only_shadow"
        assert s.confidence == 0.74

    def test_to_dict_has_required_fields(self):
        s = StateSnapshot(case_id="c1", domain="robotics", asset_id="arm_01",
                          state=StateKind.NOMINAL, severity=SeverityLevel.INFO, confidence=0.5)
        d = s.to_dict()
        assert "schema" in d
        assert "case_id" in d
        assert "state" in d
        assert "mode" in d
        assert d["mode"] == "read_only_shadow"

    def test_confidence_bounds(self):
        with pytest.raises(ValueError):
            StateSnapshot(case_id="x", domain="d", asset_id="a",
                          state=StateKind.NOMINAL, severity=SeverityLevel.INFO, confidence=1.5)
        with pytest.raises(ValueError):
            StateSnapshot(case_id="x", domain="d", asset_id="a",
                          state=StateKind.NOMINAL, severity=SeverityLevel.INFO, confidence=-0.1)

    def test_mode_is_enforced(self):
        with pytest.raises(ValueError):
            StateSnapshot(case_id="x", domain="d", asset_id="a",
                          state=StateKind.NOMINAL, severity=SeverityLevel.INFO,
                          confidence=0.5, mode="live_control")

    def test_to_json_is_valid(self):
        s = StateSnapshot(case_id="c1", domain="d", asset_id="a",
                          state=StateKind.DEGRADED, severity=SeverityLevel.HIGH, confidence=0.8)
        parsed = json.loads(s.to_json())
        assert parsed["confidence"] == 0.8

    def test_all_state_kinds_valid(self):
        for kind in StateKind:
            s = StateSnapshot(case_id="x", domain="d", asset_id="a",
                              state=kind, severity=SeverityLevel.INFO, confidence=0.5)
            assert s.state == kind


# ── EvidenceObject ────────────────────────────────────────────────────────────

class TestEvidenceObject:
    def test_basic_creation(self):
        ev = EvidenceObject(
            evidence_id="ev_001",
            type=EvidenceType.TREND_SHIFT,
            source="tool_log",
            summary="RF power shifted",
            confidence=0.78,
        )
        assert ev.evidence_id == "ev_001"
        assert ev.type == EvidenceType.TREND_SHIFT

    def test_confidence_bounds(self):
        with pytest.raises(ValueError):
            EvidenceObject(evidence_id="e", type=EvidenceType.TREND_SHIFT,
                           source="s", summary="x", confidence=1.1)

    def test_to_dict(self):
        ev = EvidenceObject(evidence_id="ev_001", type=EvidenceType.YIELD_DROP,
                            source="wafer_map", summary="fail rate high", confidence=0.85)
        d = ev.to_dict()
        assert d["type"] == "yield_drop"


# ── EvidencePack ──────────────────────────────────────────────────────────────

class TestEvidencePack:
    def test_causal_claim_boundary_enforced(self):
        with pytest.raises(ValueError):
            EvidencePack(
                case_id="c1", domain="d", asset_id="a",
                causal_claim_boundary="certified_cause",
            )

    def test_seal_sets_checksum(self):
        pack = EvidencePack(
            case_id="c1", domain="semiconductor_fab", asset_id="ETCH_01",
            summary="test",
            causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY,
        ).seal()
        assert pack.checksum.startswith("sha256:")

    def test_checksum_deterministic(self):
        kwargs = dict(case_id="c1", domain="d", asset_id="a", summary="s",
                      causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY, created_at="2026-01-01T00:00:00+00:00")
        p1 = EvidencePack(**kwargs).seal()
        p2 = EvidencePack(**kwargs).seal()
        assert p1.checksum == p2.checksum

    def test_to_json(self):
        pack = EvidencePack(case_id="c1", domain="d", asset_id="a",
                            summary="s", causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY).seal()
        d = json.loads(pack.to_json())
        assert d["causal_claim_boundary"] == CAUSAL_CLAIM_BOUNDARY

    def test_checksum_changes_when_summary_changes(self):
        kw = dict(case_id="c1", domain="d", asset_id="a",
                  causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY,
                  created_at="2026-01-01T00:00:00+00:00")
        p1 = EvidencePack(**kw, summary="summary A").seal()
        p2 = EvidencePack(**kw, summary="summary B").seal()
        assert p1.checksum != p2.checksum

    def test_checksum_changes_when_missing_evidence_changes(self):
        kw = dict(case_id="c1", domain="d", asset_id="a", summary="s",
                  causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY,
                  created_at="2026-01-01T00:00:00+00:00")
        p1 = EvidencePack(**kw, missing_evidence=[]).seal()
        p2 = EvidencePack(**kw, missing_evidence=["chamber_log"]).seal()
        assert p1.checksum != p2.checksum

    def test_checksum_includes_causal_boundary(self):
        # The boundary is part of the seal payload — changing it would change checksum
        # (it can't be changed without raising ValueError, so we verify it's in the payload)
        pack = EvidencePack(case_id="c1", domain="d", asset_id="a", summary="s",
                            causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY,
                            created_at="2026-01-01T00:00:00+00:00").seal()
        assert "sha256:" in pack.checksum
        # Verify payload includes boundary by reconstructing
        import hashlib
        payload = {
            "schema": pack.schema, "case_id": pack.case_id, "domain": pack.domain,
            "asset_id": pack.asset_id, "summary": pack.summary,
            "causal_claim_boundary": pack.causal_claim_boundary,
            "evidence_objects": pack.evidence_objects,
            "root_cause_candidates": pack.root_cause_candidates,
            "missing_evidence": pack.missing_evidence,
            "state_snapshot_ref": pack.state_snapshot_ref,
            "state_snapshot_hash": pack.state_snapshot_hash,
            "created_at": pack.created_at,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected = "sha256:" + hashlib.sha256(blob).hexdigest()
        assert pack.checksum == expected


# ── OODAFrame ─────────────────────────────────────────────────────────────────

class TestOODAFrame:
    def test_act_boundary_enforced(self):
        with pytest.raises(ValueError):
            OODAFrame(case_id="c1", domain="d",
                      observe="o", orient="or", decide="de",
                      act="send_robot_command")

    def test_valid_frame(self):
        f = OODAFrame(case_id="c1", domain="robotics",
                      observe="vibration rising",
                      orient="possible bearing wear",
                      decide="schedule maintenance",
                      act=ACT_BOUNDARY)
        assert f.act == ACT_BOUNDARY
        d = f.to_dict()
        assert d["act"] == "recommendation_only_no_hardware_action"


# ── RootCauseCandidate ────────────────────────────────────────────────────────

class TestRootCauseCandidate:
    def test_claim_boundary_enforced(self):
        with pytest.raises(ValueError):
            RootCauseCandidate(candidate="foo", confidence=0.8,
                               claim_boundary="certified_cause")

    def test_valid_candidate(self):
        r = RootCauseCandidate(candidate="chamber drift", confidence=0.72)
        assert r.requires_engineer_review is True
        assert r.claim_boundary == "candidate_only"

    def test_confidence_bounds(self):
        with pytest.raises(ValueError):
            RootCauseCandidate(candidate="x", confidence=1.5)


# ── RecoveryCandidate ─────────────────────────────────────────────────────────

class TestRecoveryCandidate:
    def test_hardware_execution_blocked(self):
        with pytest.raises(ValueError):
            RecoveryCandidate(action="send_command", expected_benefit="x",
                              hardware_execution_enabled=True)

    def test_execution_mode_human_review_allowed(self):
        # HUMAN_REVIEW_REQUIRED is a safe mode and must be allowed
        r = RecoveryCandidate(action="recommend_a", expected_benefit="b",
                              execution_mode=ExecutionMode.HUMAN_REVIEW_REQUIRED)
        assert r.execution_mode == ExecutionMode.HUMAN_REVIEW_REQUIRED
        assert r.hardware_execution_enabled is False

    def test_valid_candidate(self):
        r = RecoveryCandidate(action="recommend_chamber_inspection", expected_benefit="reduce drift risk")
        assert r.hardware_execution_enabled is False
        assert r.requires_human_review is True

    def test_risk_validation(self):
        with pytest.raises(ValueError):
            RecoveryCandidate(action="a", expected_benefit="b", risk="extreme")


# ── OutcomeRecord ─────────────────────────────────────────────────────────────

class TestOutcomeRecord:
    def test_delta(self):
        r = OutcomeRecord(case_id="c1", domain="d", asset_id="a",
                          selected_action="inspect", outcome="confirmed_drift",
                          before_score=0.62, after_score=0.88)
        assert abs(r.delta() - 0.26) < 1e-6

    def test_to_dict_has_delta(self):
        r = OutcomeRecord(case_id="c1", before_score=0.5, after_score=0.7)
        d = r.to_dict()
        assert "delta" in d


# ── Cross-domain structural equality ─────────────────────────────────────────

class TestCrossDomainStructure:
    """All 3 domains must produce the same top-level object keys."""

    def _assert_state_structure(self, state: StateSnapshot) -> None:
        d = state.to_dict()
        for key in ["schema", "case_id", "domain", "asset_id", "state",
                    "severity", "confidence", "mode", "created_at"]:
            assert key in d, f"Missing key '{key}' in StateSnapshot"

    def _assert_pack_structure(self, pack: EvidencePack) -> None:
        d = pack.to_dict()
        for key in ["schema", "case_id", "domain", "summary",
                    "causal_claim_boundary", "evidence_objects",
                    "root_cause_candidates", "checksum"]:
            assert key in d, f"Missing key '{key}' in EvidencePack"

    def _assert_ooda_structure(self, ooda: OODAFrame) -> None:
        d = ooda.to_dict()
        for key in ["schema", "case_id", "domain", "observe", "orient", "decide", "act"]:
            assert key in d, f"Missing key '{key}' in OODAFrame"

    def test_semfab_domain_structure(self):
        from yieldos.domains.semfab import SemFabAnalyzer
        r = SemFabAnalyzer().analyze("samples/semfab_tel_like", case_id="test_sf")
        self._assert_state_structure(r["state"])
        self._assert_pack_structure(r["evidence_pack"])
        self._assert_ooda_structure(r["ooda_frame"])

    def test_robot_domain_structure(self):
        from yieldos.domains.robot import RobotAnalyzer
        r = RobotAnalyzer().analyze("samples/robot_ooda/robot_telemetry.csv", case_id="test_rb")
        self._assert_state_structure(r["state"])
        self._assert_pack_structure(r["evidence_pack"])
        self._assert_ooda_structure(r["ooda_frame"])

    def test_satellite_domain_structure(self):
        from yieldos.domains.satellite import SatGuardAnalyzer
        r = SatGuardAnalyzer().analyze("samples/satguard/satellite_telemetry.csv", case_id="test_sat")
        self._assert_state_structure(r["state"])
        self._assert_pack_structure(r["evidence_pack"])
        self._assert_ooda_structure(r["ooda_frame"])

    def test_semiforge_domain_structure(self):
        from yieldos.domains.semiforge import SemiForgeSimulator
        r = SemiForgeSimulator().simulate("samples/semiforge_crossbar/config.json",
                                          case_id="test_forge", monte_carlo_runs=5)
        self._assert_state_structure(r["state"])
        self._assert_pack_structure(r["evidence_pack"])
        self._assert_ooda_structure(r["ooda_frame"])

    def test_all_domains_share_same_schema_version(self):
        from yieldos.domains.robot import RobotAnalyzer
        from yieldos.domains.satellite import SatGuardAnalyzer
        from yieldos.domains.semfab import SemFabAnalyzer
        from yieldos.domains.semiforge import SemiForgeSimulator

        results = [
            SemFabAnalyzer().analyze("samples/semfab_tel_like", case_id="v_sf"),
            RobotAnalyzer().analyze("samples/robot_ooda/robot_telemetry.csv", case_id="v_rb"),
            SatGuardAnalyzer().analyze("samples/satguard/satellite_telemetry.csv", case_id="v_sat"),
            SemiForgeSimulator().simulate("samples/semiforge_crossbar/config.json",
                                          case_id="v_forge", monte_carlo_runs=3),
        ]
        schemas = [r["state"].schema for r in results]
        assert all(s == "yieldos.state_snapshot.v1" for s in schemas)

        pack_schemas = [r["evidence_pack"].schema for r in results]
        assert all(s == "yieldos.evidence_pack.v1" for s in pack_schemas)


# ── Safety tests ──────────────────────────────────────────────────────────────

class TestSafetyBoundaries:
    """YieldOS must never allow hardware control or certified RCA."""

    def test_no_live_control_in_recovery(self):
        r = RecoveryCandidate(action="recommend_inspect", expected_benefit="reduce risk")
        assert r.hardware_execution_enabled is False
        assert r.execution_mode == ExecutionMode.RECOMMENDATION_ONLY

    def test_causal_claim_always_candidate(self):
        rc = RootCauseCandidate(candidate="test cause", confidence=0.99)
        assert rc.claim_boundary == "candidate_only"

    def test_ooda_act_never_hardware(self):
        f = OODAFrame(case_id="c", domain="d",
                      observe="o", orient="or", decide="de", act=ACT_BOUNDARY)
        # act value is "recommendation_only_no_hardware_action"
        # it mentions hardware to explicitly deny it, not to enable it
        assert f.act == "recommendation_only_no_hardware_action"
        assert "recommendation" in f.act
        assert "no_hardware" in f.act

    def test_state_mode_always_readonly(self):
        s = StateSnapshot(case_id="c", domain="d", asset_id="a",
                          state=StateKind.NOMINAL, severity=SeverityLevel.INFO, confidence=0.5)
        assert s.mode == "read_only_shadow"

    def test_pack_claim_boundary_immutable(self):
        pack = EvidencePack(case_id="c", domain="d", asset_id="a", summary="s",
                            causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY)
        assert pack.causal_claim_boundary == CAUSAL_CLAIM_BOUNDARY

    def test_recovery_candidate_allows_human_review_required(self):
        r = RecoveryCandidate(action="request_human_review", expected_benefit="expert review",
                              execution_mode=ExecutionMode.HUMAN_REVIEW_REQUIRED)
        assert r.execution_mode == ExecutionMode.HUMAN_REVIEW_REQUIRED
        assert r.hardware_execution_enabled is False

    def test_recovery_candidate_blocks_hardware_execution(self):
        with pytest.raises(ValueError):
            RecoveryCandidate(action="send_command", expected_benefit="x",
                              hardware_execution_enabled=True)

    def test_recovery_candidate_blocks_invalid_execution_mode(self):
        class FakeMode:
            value = "live_control"
        with pytest.raises((ValueError, AttributeError)):
            RecoveryCandidate(action="a", expected_benefit="b",
                              execution_mode=FakeMode())  # type: ignore


# ── SemFab domain-specific tests ─────────────────────────────────────────────

class TestSemFabDomain:
    def test_semfab_top_signal_uses_evidence_fallback(self):
        """Summary should never say 'unknown shift' when evidence objects exist."""
        from yieldos.domains.semfab import SemFabAnalyzer
        result = SemFabAnalyzer().analyze("samples/semfab_tel_like", case_id="test_ts")
        pack = result["evidence_pack"]
        assert "unknown shift" not in pack.summary.lower()
        assert "unknown" not in pack.summary or "unknown" not in pack.summary.split("signal:")[1][:20]

    def test_evidence_objects_sorted_by_confidence(self):
        from yieldos.domains.semfab import SemFabAnalyzer
        result = SemFabAnalyzer().analyze("samples/semfab_tel_like", case_id="test_sort")
        ev = result["evidence_pack"].evidence_objects
        if len(ev) >= 2:
            confs = [e.get("confidence", 0) for e in ev]
            assert confs == sorted(confs, reverse=True), "Evidence not sorted by confidence"


# ── ReportWriter tests ────────────────────────────────────────────────────────

class TestReportWriter:
    def test_report_writer_accepts_recovery_candidates_as_objects(self):
        import shutil
        import tempfile

        from yieldos.contracts import (
            EvidencePack,
            OODAFrame,
            RecoveryCandidate,
            SeverityLevel,
            StateKind,
            StateSnapshot,
        )
        from yieldos.contracts.evidence_pack import CAUSAL_CLAIM_BOUNDARY
        from yieldos.contracts.ooda_frame import ACT_BOUNDARY
        from yieldos.core.report_writer import ReportWriter

        tmpdir = tempfile.mkdtemp()
        try:
            state = StateSnapshot(case_id="rw_test", domain="test", asset_id="a",
                                  state=StateKind.NOMINAL, severity=SeverityLevel.INFO, confidence=0.5)
            pack = EvidencePack(case_id="rw_test", domain="test", asset_id="a",
                                summary="test summary",
                                causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY).seal()
            ooda = OODAFrame(case_id="rw_test", domain="test",
                             observe="o", orient="or", decide="de", act=ACT_BOUNDARY)
            recovery = [RecoveryCandidate(action="recommend_inspection",
                                          expected_benefit="identify issue")]
            writer = ReportWriter()
            paths = writer.write_all(tmpdir, state, pack, ooda, recovery_candidates=recovery)
            assert "report_html" in paths
            from pathlib import Path
            assert Path(paths["report_html"]).exists()
            # recovery_candidates.json written by ReportWriter
            assert (Path(tmpdir) / "recovery_candidates.json").exists()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ── Validate CLI tests ────────────────────────────────────────────────────────

class TestValidateCLI:
    def _write_case(self, tmpdir: str, corrupt_checksum: bool = False,
                    hw_enabled: bool = False) -> None:
        import hashlib
        import json
        from pathlib import Path

        from yieldos.contracts.evidence_pack import CAUSAL_CLAIM_BOUNDARY

        p = Path(tmpdir)
        p.mkdir(parents=True, exist_ok=True)

        ev_objects = []
        rca = []
        missing = []
        pack_data = {
            "schema": "yieldos.evidence_pack.v1",
            "case_id": "val_test", "domain": "test", "asset_id": "a",
            "summary": "test", "causal_claim_boundary": CAUSAL_CLAIM_BOUNDARY,
            "evidence_objects": ev_objects, "root_cause_candidates": rca,
            "missing_evidence": missing, "state_snapshot_ref": "",
            "state_snapshot_hash": "",
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        payload = {k: pack_data[k] for k in pack_data if k != "checksum"}
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        checksum = "sha256:" + hashlib.sha256(blob).hexdigest()
        pack_data["checksum"] = "sha256:baddeadbeef" if corrupt_checksum else checksum
        (p / "evidence_pack.json").write_text(json.dumps(pack_data), encoding="utf-8")

        _generated_by = {"product": "HAL YieldOS", "version": "2.0.0", "mode": "read_only_shadow"}
        _safety = {
            "read_only": True, "shadow_only": True,
            "hardware_execution_enabled": False, "human_review_required": True,
            "causal_claim_boundary": "candidate_only_not_certified_cause",
        }

        pack_data["schema_version"] = "2.0.0"
        pack_data["generated_by"] = _generated_by
        # Rewrite with metadata added (checksum already set)
        (p / "evidence_pack.json").write_text(json.dumps(pack_data), encoding="utf-8")

        state_data = {
            "schema": "yieldos.state_snapshot.v1",
            "schema_version": "2.0.0",
            "mode": "read_only_shadow",
            "case_id": "val_test",
            "generated_by": _generated_by,
            "safety": _safety,
        }
        (p / "state_snapshot.json").write_text(json.dumps(state_data), encoding="utf-8")

        ooda_data = {
            "schema": "yieldos.ooda_frame.v1",
            "act": "recommendation_only_no_hardware_action",
            "case_id": "val_test",
        }
        (p / "ooda_frame.json").write_text(json.dumps(ooda_data), encoding="utf-8")
        (p / "report.html").write_text("<html></html>", encoding="utf-8")

        rec = [{
            "action": "inspect",
            "hardware_execution_enabled": hw_enabled,
            "schema_version": "2.0.0",
            "generated_by": _generated_by,
            "safety": _safety,
        }]
        (p / "recovery_candidates.json").write_text(json.dumps(rec), encoding="utf-8")

    def test_validate_passes_good_case(self):
        import argparse
        import shutil
        import tempfile

        from yieldos.cli.main import cmd_validate
        tmpdir = tempfile.mkdtemp()
        try:
            self._write_case(tmpdir)
            args = argparse.Namespace(case=tmpdir)
            rc = cmd_validate(args)
            assert rc == 0
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_validate_fails_bad_checksum(self):
        import argparse
        import shutil
        import tempfile

        from yieldos.cli.main import cmd_validate
        tmpdir = tempfile.mkdtemp()
        try:
            self._write_case(tmpdir, corrupt_checksum=True)
            args = argparse.Namespace(case=tmpdir)
            rc = cmd_validate(args)
            assert rc != 0
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_validate_fails_hardware_execution_enabled(self):
        import argparse
        import shutil
        import tempfile

        from yieldos.cli.main import cmd_validate
        tmpdir = tempfile.mkdtemp()
        try:
            self._write_case(tmpdir, hw_enabled=True)
            args = argparse.Namespace(case=tmpdir)
            rc = cmd_validate(args)
            assert rc != 0
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
