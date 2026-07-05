"""
Tests for Cross-step RCA guard limits (v2.2.0)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _make_drift_events(n: int) -> list:
    return [
        {
            "step": f"step_{i}",
            "metric": "tool_temp_C",
            "confidence": 0.8,
            "drift_score": 0.5,
        }
        for i in range(n)
    ]


def _make_metrology(n: int, affected: bool) -> list:
    rows = []
    for i in range(n):
        rows.append({
            "lot_id": f"LOT_{'AFFECTED' if affected else 'CLEAN'}_{i:04d}",
            "cd_nm": (25.5 if affected else 24.0) + (i % 3) * 0.1,
            "target_cd_nm": 24.0,
        })
    return rows


def _make_wafer_map(n: int, affected: bool, fail_rate: float = 0.0) -> list:
    import random
    random.seed(42)
    rows = []
    for i in range(n):
        bin_result = "FAIL" if (affected and random.random() < fail_rate) else "PASS"
        rows.append({
            "lot_id": f"LOT_{'AFFECTED' if affected else 'CLEAN'}_{i:04d}",
            "bin_result": bin_result,
        })
    return rows


class TestCrossStepRCAConstants:
    def test_constants_present(self):
        from yieldos.domains.semfab.cross_step_rca import MAX_FEATURES, MAX_STEPS, MIN_SUPPORT, TOP_K
        assert MAX_STEPS == 50
        assert MAX_FEATURES == 100
        assert TOP_K == 10
        assert MIN_SUPPORT == 3

    def test_min_support_enforced_metrology(self):
        from yieldos.domains.semfab.cross_step_rca import correlate_drift_to_metrology
        drift = _make_drift_events(3)
        # Only 2 affected rows (< MIN_SUPPORT=3)
        metrology = _make_metrology(2, True) + _make_metrology(10, False)
        result = correlate_drift_to_metrology(drift, metrology, ["LOT_AFFECTED_0000", "LOT_AFFECTED_0001"])
        assert result == []

    def test_max_steps_truncation(self):
        from yieldos.domains.semfab.cross_step_rca import MAX_STEPS, correlate_drift_to_metrology
        drift = _make_drift_events(MAX_STEPS + 20)
        metrology = _make_metrology(5, True) + _make_metrology(5, False)
        warnings = []
        correlate_drift_to_metrology(drift, metrology, [f"LOT_AFFECTED_{i:04d}" for i in range(5)],
                                      _truncation_warnings=warnings)
        assert any("MAX_STEPS" in w for w in warnings)

    def test_max_features_truncation_metrology(self):
        from yieldos.domains.semfab.cross_step_rca import MAX_FEATURES, correlate_drift_to_metrology
        drift = _make_drift_events(3)
        metrology = _make_metrology(MAX_FEATURES + 50, True) + _make_metrology(10, False)
        warnings = []
        correlate_drift_to_metrology(drift, metrology, [f"LOT_AFFECTED_{i:04d}" for i in range(MAX_FEATURES + 50)],
                                      _truncation_warnings=warnings)
        assert any("MAX_FEATURES" in w for w in warnings)

    def test_max_features_truncation_yield(self):
        from yieldos.domains.semfab.cross_step_rca import MAX_FEATURES, correlate_drift_to_yield
        drift = _make_drift_events(3)
        wafer_map = _make_wafer_map(MAX_FEATURES + 50, True, 0.5) + _make_wafer_map(10, False)
        warnings = []
        correlate_drift_to_yield(drift, wafer_map, [f"LOT_AFFECTED_{i:04d}" for i in range(MAX_FEATURES + 50)],
                                  _truncation_warnings=warnings)
        assert any("MAX_FEATURES" in w for w in warnings)

    def test_min_support_enforced_yield(self):
        from yieldos.domains.semfab.cross_step_rca import correlate_drift_to_yield
        drift = _make_drift_events(3)
        # Only 2 affected wafer rows (< MIN_SUPPORT=3)
        wafer_map = _make_wafer_map(2, True, 0.8) + _make_wafer_map(20, False)
        result = correlate_drift_to_yield(drift, wafer_map, ["LOT_AFFECTED_0000", "LOT_AFFECTED_0001"])
        assert result == []

    def test_truncation_warnings_in_graph(self):
        from yieldos.domains.semfab.cross_step_rca import MAX_STEPS, build_cross_step_graph
        drift = _make_drift_events(MAX_STEPS + 10)
        metrology = _make_metrology(5, True) + _make_metrology(5, False)
        wafer_map = _make_wafer_map(5, True, 0.6) + _make_wafer_map(5, False)
        result = build_cross_step_graph(
            drift, [f"LOT_AFFECTED_{i:04d}" for i in range(5)], metrology, wafer_map
        )
        assert "truncation_warnings" in result
        assert len(result["truncation_warnings"]) > 0

    def test_graph_without_truncation_no_warnings_key(self):
        from yieldos.domains.semfab.cross_step_rca import build_cross_step_graph
        drift = _make_drift_events(3)
        metrology = _make_metrology(5, True) + _make_metrology(5, False)
        wafer_map = _make_wafer_map(5, True, 0.6) + _make_wafer_map(5, False)
        result = build_cross_step_graph(
            drift, [f"LOT_AFFECTED_{i:04d}" for i in range(5)], metrology, wafer_map
        )
        # No truncation warnings expected — key may or may not be present but if present must be empty
        assert result.get("truncation_warnings", []) == []
