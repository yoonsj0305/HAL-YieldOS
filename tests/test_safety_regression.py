"""
Safety regression tests for HAL YieldOS.

These tests verify that no domain output ever:
- Enables hardware execution
- Uses forbidden action strings as actual action identifiers
- Violates causal claim boundary
- Violates read_only_shadow mode

All tests run WITHOUT real industrial data — only bundled sample data.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

FORBIDDEN_ACTIONS = {
    "change_recipe",
    "modify_recipe",
    "send_robot_command",
    "send_satellite_command",
    "uplink_command",
    "execute_hardware",
    "hardware_command",
    "equipment_start",
    "equipment_stop",
    "auto_calibration_execute",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_semfab():
    from yieldos.domains.semfab import SemFabAnalyzer
    return SemFabAnalyzer().analyze(
        data_dir="samples/semfab_tel_like",
        case_id="safety_test_semfab",
    )


def _run_semiforge():
    from yieldos.domains.semiforge import SemiForgeSimulator
    return SemiForgeSimulator().simulate(
        config_path="samples/semiforge_crossbar/config.json",
        case_id="safety_test_semiforge",
        monte_carlo_runs=5,
    )


def _run_robot():
    from yieldos.domains.robot import RobotAnalyzer
    return RobotAnalyzer().analyze(
        telemetry_path="samples/robot_ooda/robot_telemetry.csv",
        case_id="safety_test_robot",
    )


def _run_satellite():
    from yieldos.domains.satellite import SatGuardAnalyzer
    return SatGuardAnalyzer().analyze(
        telemetry_path="samples/satguard/satellite_telemetry.csv",
        case_id="safety_test_sat",
    )


# ── Hardware execution ─────────────────────────────────────────────────────────

class TestNoHardwareExecutionAnywhere:
    def test_semfab_no_hardware_execution(self):
        result = _run_semfab()
        for rc in result["recovery_candidates"]:
            assert not rc.hardware_execution_enabled, f"hardware_execution_enabled=True in semfab: {rc.action}"

    def test_semiforge_no_hardware_execution(self):
        result = _run_semiforge()
        for rc in result["recovery_candidates"]:
            assert not rc.hardware_execution_enabled, f"hardware_execution_enabled=True in semiforge: {rc.action}"

    def test_robot_no_hardware_execution(self):
        result = _run_robot()
        for rc in result["recovery_candidates"]:
            assert not rc.hardware_execution_enabled, f"hardware_execution_enabled=True in robot: {rc.action}"

    def test_satellite_no_hardware_execution(self):
        result = _run_satellite()
        for rc in result["recovery_candidates"]:
            assert not rc.hardware_execution_enabled, f"hardware_execution_enabled=True in sat: {rc.action}"


# ── Forbidden action strings ───────────────────────────────────────────────────

class TestNoForbiddenActions:
    def _check_actions(self, result, domain):
        for rc in result["recovery_candidates"]:
            action = rc.action.lower()
            assert action not in FORBIDDEN_ACTIONS, (
                f"[{domain}] Forbidden action '{action}' found in recovery_candidates"
            )

    def test_semfab_no_recipe_change_action(self):
        self._check_actions(_run_semfab(), "semfab")

    def test_semiforge_no_recipe_change_action(self):
        self._check_actions(_run_semiforge(), "semiforge")

    def test_robot_no_robot_command_action(self):
        self._check_actions(_run_robot(), "robot")

    def test_satellite_no_satellite_uplink_action(self):
        self._check_actions(_run_satellite(), "satellite")


# ── Causal claim boundary ──────────────────────────────────────────────────────

class TestCausalClaimBoundary:
    def test_semfab_rca_candidate_only(self):
        result = _run_semfab()
        pack = result["evidence_pack"]
        assert pack.causal_claim_boundary == "candidate_only_not_certified_cause"
        for rca in pack.root_cause_candidates:
            cb = rca.get("claim_boundary") if isinstance(rca, dict) else getattr(rca, "claim_boundary", "candidate_only")
            assert "candidate" in str(cb).lower(), f"RCA claim_boundary not candidate: {cb}"

    def test_semiforge_rca_candidate_only(self):
        result = _run_semiforge()
        pack = result["evidence_pack"]
        assert pack.causal_claim_boundary == "candidate_only_not_certified_cause"

    def test_robot_rca_candidate_only(self):
        result = _run_robot()
        pack = result["evidence_pack"]
        assert pack.causal_claim_boundary == "candidate_only_not_certified_cause"

    def test_satellite_rca_candidate_only(self):
        result = _run_satellite()
        pack = result["evidence_pack"]
        assert pack.causal_claim_boundary == "candidate_only_not_certified_cause"


# ── Recovery recommendation-only ──────────────────────────────────────────────

class TestAllRecoveryCandidatesRecommendationOnly:
    SAFE_MODES = {"recommendation_only", "human_review_required"}

    def _check(self, result, domain):
        for rc in result["recovery_candidates"]:
            mode = rc.execution_mode.value if hasattr(rc.execution_mode, "value") else str(rc.execution_mode)
            assert mode in self.SAFE_MODES, f"[{domain}] execution_mode={mode} is not safe"
            assert rc.requires_human_review is True, f"[{domain}] requires_human_review is False"

    def test_semfab(self): self._check(_run_semfab(), "semfab")
    def test_semiforge(self): self._check(_run_semiforge(), "semiforge")
    def test_robot(self): self._check(_run_robot(), "robot")
    def test_satellite(self): self._check(_run_satellite(), "satellite")


# ── Read-only mode ─────────────────────────────────────────────────────────────

class TestReadOnlyMode:
    def _check(self, result):
        state = result["state"]
        assert state.mode == "read_only_shadow", f"mode={state.mode}"

    def test_semfab_mode(self): self._check(_run_semfab())
    def test_semiforge_mode(self): self._check(_run_semiforge())
    def test_robot_mode(self): self._check(_run_robot())
    def test_satellite_mode(self): self._check(_run_satellite())


# ── All RCA outputs are candidate-only ────────────────────────────────────────

class TestAllRCAOutputsAreCandidateOnly:
    def _check(self, result, domain):
        pack = result["evidence_pack"]
        for rca in pack.root_cause_candidates:
            rca_dict = rca if isinstance(rca, dict) else rca.to_dict()
            cb = rca_dict.get("claim_boundary", "")
            assert "candidate" in cb.lower(), (
                f"[{domain}] RCA claim_boundary does not say 'candidate': {cb}"
            )

    def test_semfab_rca_output(self): self._check(_run_semfab(), "semfab")
    def test_robot_rca_output(self): self._check(_run_robot(), "robot")
    def test_satellite_rca_output(self): self._check(_run_satellite(), "satellite")


# ── Generated metadata blocks ──────────────────────────────────────────────────

class TestGeneratedByAndSafetyBlock:
    def _check_state(self, result):
        d = result["state"].to_dict()
        assert "generated_by" in d, "StateSnapshot missing generated_by"
        assert "safety" in d, "StateSnapshot missing safety block"
        assert d["safety"]["hardware_execution_enabled"] is False

    def _check_pack(self, result):
        d = result["evidence_pack"].to_dict()
        assert "generated_by" in d, "EvidencePack missing generated_by"
        assert "safety" in d, "EvidencePack missing safety block"

    def _check_ooda(self, result):
        d = result["ooda_frame"].to_dict()
        assert "generated_by" in d, "OODAFrame missing generated_by"
        assert "safety" in d, "OODAFrame missing safety block"

    def test_semfab_state_meta(self): self._check_state(_run_semfab())
    def test_semfab_pack_meta(self): self._check_pack(_run_semfab())
    def test_semfab_ooda_meta(self): self._check_ooda(_run_semfab())
    def test_robot_state_meta(self): self._check_state(_run_robot())
    def test_satellite_state_meta(self): self._check_state(_run_satellite())
    def test_semiforge_state_meta(self): self._check_state(_run_semiforge())


# ── Schema version ─────────────────────────────────────────────────────────────

class TestSchemaVersion:
    def test_all_outputs_include_schema(self):
        result = _run_semfab()
        assert "schema" in result["state"].to_dict()
        assert "schema" in result["evidence_pack"].to_dict()
        assert "schema" in result["ooda_frame"].to_dict()

    def test_all_outputs_include_schema_version(self):
        result = _run_semfab()
        d_state = result["state"].to_dict()
        d_pack = result["evidence_pack"].to_dict()
        d_ooda = result["ooda_frame"].to_dict()
        assert "schema_version" in d_state, "StateSnapshot missing schema_version"
        assert "schema_version" in d_pack, "EvidencePack missing schema_version"
        assert "schema_version" in d_ooda, "OODAFrame missing schema_version"

    def test_recovery_candidate_has_schema(self):
        result = _run_semfab()
        for rc in result["recovery_candidates"]:
            d = rc.to_dict()
            assert "schema" in d, "RecoveryCandidate missing schema"
            assert "schema_version" in d, "RecoveryCandidate missing schema_version"


# ── v2.1.1 Hardened safety regression tests ───────────────────────────────────

_FORBIDDEN_TERMS_V211 = [
    "execute",
    "uplink",
    "move_robot",
    "change_recipe",
    "confirmed_root_cause",
    "autonomous_recovery",
    "certify_safety",
    "modify_firmware",
]


def _all_results():
    return [
        ("semfab", _run_semfab()),
        ("semiforge", _run_semiforge()),
        ("robot", _run_robot()),
        ("satellite", _run_satellite()),
    ]


class TestV211SafetyHardening:
    def test_ooda_act_exact_value(self):
        """OODA act must be exactly 'recommendation_only_no_hardware_action'."""
        from yieldos.contracts.ooda_frame import ACT_BOUNDARY
        assert ACT_BOUNDARY == "recommendation_only_no_hardware_action"
        for domain, result in _all_results():
            act = result["ooda_frame"].act
            assert act == "recommendation_only_no_hardware_action", (
                f"[{domain}] ooda.act='{act}' is not the exact required value"
            )

    def test_validate_rejects_execute(self):
        """RecoveryCandidate construction must reject 'execute' as action."""
        import pytest

        from yieldos.contracts.recovery_candidate import RecoveryCandidate
        with pytest.raises((ValueError, AssertionError)):
            RecoveryCandidate(action="execute", expected_benefit="test", steps=[])

    def test_validate_rejects_uplink(self):
        import pytest

        from yieldos.contracts.recovery_candidate import RecoveryCandidate
        with pytest.raises((ValueError, AssertionError)):
            RecoveryCandidate(action="uplink_command", expected_benefit="test", steps=[])

    def test_validate_rejects_move_robot(self):
        import pytest

        from yieldos.contracts.recovery_candidate import RecoveryCandidate
        with pytest.raises((ValueError, AssertionError)):
            RecoveryCandidate(action="move_robot", expected_benefit="test", steps=[])

    def test_validate_rejects_change_recipe(self):
        import pytest

        from yieldos.contracts.recovery_candidate import RecoveryCandidate
        with pytest.raises((ValueError, AssertionError)):
            RecoveryCandidate(action="change_recipe", expected_benefit="test", steps=[])

    def test_validate_requires_human_review(self):
        """All recovery candidates must have requires_human_review=True."""
        for domain, result in _all_results():
            for rc in result["recovery_candidates"]:
                assert rc.requires_human_review is True, (
                    f"[{domain}] requires_human_review=False on action '{rc.action}'"
                )

    def test_recovery_candidates_never_enable_hardware_execution(self):
        """hardware_execution_enabled must be False on every candidate."""
        for domain, result in _all_results():
            for rc in result["recovery_candidates"]:
                assert rc.hardware_execution_enabled is False, (
                    f"[{domain}] hardware_execution_enabled=True on action '{rc.action}'"
                )

    def test_report_does_not_claim_autonomous_recovery(self):
        """Output dicts must not contain autonomous recovery claims."""
        for domain, result in _all_results():
            for rc in result["recovery_candidates"]:
                text = " ".join([
                    rc.action,
                    rc.expected_benefit,
                    *rc.steps,
                ]).lower()
                assert "autonomous_recovery" not in text, (
                    f"[{domain}] 'autonomous_recovery' found in action text: {rc.action}"
                )

    def test_forbidden_terms_not_in_recovery_actions(self):
        """None of the FORBIDDEN_TERMS_V211 may appear as action names."""
        for domain, result in _all_results():
            for rc in result["recovery_candidates"]:
                action = rc.action.lower()
                for term in _FORBIDDEN_TERMS_V211:
                    assert term not in action, (
                        f"[{domain}] forbidden term '{term}' in action: '{rc.action}'"
                    )

    def test_safety_invariants_constants(self):
        """Verify safety_invariants module exports correct constants."""
        from yieldos.contracts.safety_invariants import (
            FORBIDDEN_ACTION_TERMS,
            OODA_ACT_EXACT,
            REQUIRED_BOUNDARIES,
            SQBM_FALLBACK_WARNING,
        )
        assert OODA_ACT_EXACT == "recommendation_only_no_hardware_action"
        assert REQUIRED_BOUNDARIES["hardware_execution_enabled"] is False
        assert REQUIRED_BOUNDARIES["human_review_required"] is True
        assert "execute" in FORBIDDEN_ACTION_TERMS
        assert "uplink_command" in FORBIDDEN_ACTION_TERMS
        assert "Optimizer unavailable" in SQBM_FALLBACK_WARNING
