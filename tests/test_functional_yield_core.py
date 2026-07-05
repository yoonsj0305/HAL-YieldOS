"""
Tests for yieldos.core.functional_yield — Functional Yield Vector Core (v2.2.0)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestClamp01:
    def test_clamp_in_range(self):
        from yieldos.core.functional_yield import clamp01
        assert clamp01(0.5) == 0.5
        assert clamp01(0.0) == 0.0
        assert clamp01(1.0) == 1.0

    def test_clamp_above(self):
        from yieldos.core.functional_yield import clamp01
        assert clamp01(1.5) == 1.0
        assert clamp01(100.0) == 1.0

    def test_clamp_below(self):
        from yieldos.core.functional_yield import clamp01
        assert clamp01(-0.1) == 0.0
        assert clamp01(-100.0) == 0.0


class TestWeightedMean:
    def test_uniform_weights(self):
        from yieldos.core.functional_yield import weighted_mean
        result = weighted_mean([0.5, 0.5, 0.5], [1.0, 1.0, 1.0])
        assert abs(result - 0.5) < 1e-9

    def test_weighted_high(self):
        from yieldos.core.functional_yield import weighted_mean
        result = weighted_mean([1.0, 0.0], [3.0, 1.0])
        assert abs(result - 0.75) < 1e-9

    def test_empty_values(self):
        from yieldos.core.functional_yield import weighted_mean
        assert weighted_mean([], []) == 0.0

    def test_zero_weights_fallback(self):
        from yieldos.core.functional_yield import weighted_mean
        result = weighted_mean([0.4, 0.6], [0.0, 0.0])
        assert abs(result - 0.5) < 1e-9


class TestMissingDataPenalty:
    def test_no_missing(self):
        from yieldos.core.functional_yield import missing_data_penalty
        assert missing_data_penalty([]) == 0.0

    def test_one_missing(self):
        from yieldos.core.functional_yield import missing_data_penalty
        p = missing_data_penalty(["signal_a"])
        assert 0.0 < p <= 0.3

    def test_max_penalty_capped(self):
        from yieldos.core.functional_yield import missing_data_penalty
        p = missing_data_penalty(["a", "b", "c", "d", "e", "f", "g", "h"])
        assert p <= 0.3

    def test_custom_max_penalty(self):
        from yieldos.core.functional_yield import missing_data_penalty
        p = missing_data_penalty(["x", "y"], max_penalty=0.5)
        assert p <= 0.5


class TestBuildFunctionalYieldVector:
    def _build(self, **kwargs):
        from yieldos.core.functional_yield import build_functional_yield_vector
        defaults = {
            "domain": "robot",
            "case_id": "test_001",
            "asset_id": "arm_07",
            "component_scores": {"joint_2": 0.6, "joint_3": 0.9},
            "role_scores": {"pick": 0.7, "place": 0.8},
            "evidence_confidence": 0.75,
            "missing_inputs": [],
            "score_kind": "heuristic",
            "model_limitations": ["sample_data_only"],
        }
        defaults.update(kwargs)
        return build_functional_yield_vector(**defaults)

    def test_schema_field(self):
        v = self._build()
        assert v["schema"] == "hal.yieldos.functional_yield_vector.v1"

    def test_score_in_range(self):
        v = self._build()
        assert 0.0 <= v["functional_yield_score"] <= 1.0

    def test_component_scores_clamped(self):
        v = self._build(component_scores={"motor": 1.5, "sensor": -0.1})
        for score in v["component_scores"].values():
            assert 0.0 <= score <= 1.0

    def test_missing_inputs_penalty(self):
        v_no_miss = self._build(missing_inputs=[])
        v_with_miss = self._build(missing_inputs=["log_a", "log_b", "log_c"])
        assert v_with_miss["functional_yield_score"] <= v_no_miss["functional_yield_score"]

    def test_remaining_and_blocked_roles(self):
        v = self._build(role_scores={"pick": 0.8, "weld": 0.2})
        assert "pick" in v["remaining_roles"]
        assert "weld" in v["blocked_roles"]

    def test_safety_fields_present(self):
        v = self._build()
        assert "cannot_certify_safety" in v
        assert "cannot_authorize_hardware_action" in v

    def test_recovery_bonus_increases_score(self):
        v_base = self._build(recovery_bonus=0.0)
        v_bonus = self._build(recovery_bonus=1.0)
        assert v_bonus["functional_yield_score"] >= v_base["functional_yield_score"]
