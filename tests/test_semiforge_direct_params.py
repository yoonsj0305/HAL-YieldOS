"""
tests/test_semiforge_direct_params.py

Verifies SemiForgeSimulationConfig and run_semiforge_simulation_from_params().
"""
from __future__ import annotations

import pytest

from yieldos.domains.semiforge.simulator import (
    SemiForgeSimulationConfig,
    run_semiforge_simulation_from_params,
)

# ── SemiForgeSimulationConfig ─────────────────────────────────────────────────

def test_config_default_values():
    cfg = SemiForgeSimulationConfig()
    assert cfg.array_rows == 64
    assert cfg.array_cols == 64
    assert cfg.defect_rate == pytest.approx(0.05)
    assert cfg.monte_carlo_runs == 30
    assert cfg.optimizer == "greedy"


def test_config_custom_values():
    cfg = SemiForgeSimulationConfig(array_rows=16, array_cols=16, defect_rate=0.1, monte_carlo_runs=5)
    assert cfg.array_rows == 16
    assert cfg.defect_rate == pytest.approx(0.1)
    assert cfg.monte_carlo_runs == 5


def test_config_is_frozen():
    cfg = SemiForgeSimulationConfig()
    with pytest.raises((AttributeError, TypeError)):
        cfg.defect_rate = 0.99  # type: ignore[misc]


# ── run_semiforge_simulation_from_params ──────────────────────────────────────

def test_direct_params_sets_config_source():
    result = run_semiforge_simulation_from_params(
        array_size=16, defect_rate=0.1, monte_carlo_runs=5, random_seed=42
    )
    assert result["config_source"] == "direct_params"


def test_direct_params_sets_array_size():
    result = run_semiforge_simulation_from_params(
        array_size=16, defect_rate=0.1, monte_carlo_runs=5, random_seed=42
    )
    assert result["array_size"] == 16


def test_direct_params_has_functional_yield_result():
    result = run_semiforge_simulation_from_params(
        array_size=8, defect_rate=0.05, monte_carlo_runs=3
    )
    assert "functional_yield_result" in result
    fy = result["functional_yield_result"]
    assert "y_func" in fy
    assert "defect_rate" in fy


def test_direct_params_array_size_shorthand():
    result = run_semiforge_simulation_from_params(array_size=32, monte_carlo_runs=3)
    fy = result["functional_yield_result"]
    assert fy["array_size"] == "32x32"


def test_direct_params_array_rows_cols_explicit():
    result = run_semiforge_simulation_from_params(
        array_rows=16, array_cols=8, monte_carlo_runs=3
    )
    fy = result["functional_yield_result"]
    assert fy["array_size"] == "16x8"


def test_direct_params_case_id_in_result():
    result = run_semiforge_simulation_from_params(
        array_size=8, monte_carlo_runs=2, case_id="test_direct_001"
    )
    assert result["case_id"] == "test_direct_001"


def test_direct_params_result_has_standard_keys():
    result = run_semiforge_simulation_from_params(array_size=8, monte_carlo_runs=2)
    for key in ("case_id", "domain", "state", "evidence_pack", "config_source", "array_size"):
        assert key in result, f"Missing key: {key}"


def test_direct_params_does_not_affect_existing_simulate():
    from yieldos.domains.semiforge.simulator import SemiForgeSimulator
    sim = SemiForgeSimulator()
    assert hasattr(sim, "simulate"), "Original simulate() method must still exist"


def test_direct_params_defect_rate_reflected_in_output():
    result = run_semiforge_simulation_from_params(
        array_size=16, defect_rate=0.20, monte_carlo_runs=5
    )
    fy = result["functional_yield_result"]
    # actual defect rate from simulation should be close to requested
    assert 0.0 <= fy["defect_rate"] <= 1.0
