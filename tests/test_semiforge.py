"""Tests for SemiForge functional yield simulator."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from yieldos.domains.semiforge import SemiForgeSimulator
from yieldos.domains.semiforge.defect_map import actual_defect_rate, generate_clustered_defects, generate_iid_defects
from yieldos.domains.semiforge.functional_yield import compute_c_eff, compute_r_alg, compute_y_func
from yieldos.domains.semiforge.percolation import percolation_connectivity


class TestDefectMap:
    def test_iid_defect_rate_approximate(self):
        grid = generate_iid_defects(100, 100, 0.10, seed=42)
        adr = actual_defect_rate(grid)
        assert 0.07 <= adr <= 0.13

    def test_clustered_defect_rate_approximate(self):
        grid = generate_clustered_defects(64, 64, 0.12, clustering_factor=3.0, seed=42)
        adr = actual_defect_rate(grid)
        # Clustered may not hit exact target but should be in range
        assert 0.05 <= adr <= 0.20

    def test_zero_defect_rate(self):
        grid = generate_iid_defects(32, 32, 0.0)
        assert actual_defect_rate(grid) == 0.0

    def test_full_defect(self):
        grid = generate_iid_defects(10, 10, 1.0)
        assert actual_defect_rate(grid) == 1.0

    def test_grid_dimensions(self):
        grid = generate_iid_defects(16, 32, 0.05)
        assert len(grid) == 16
        assert len(grid[0]) == 32


class TestPercolation:
    def test_no_defects_full_connectivity(self):
        grid = [[0] * 10 for _ in range(10)]
        r = percolation_connectivity(grid)
        assert r == 1.0

    def test_all_defects_zero_connectivity(self):
        grid = [[1] * 10 for _ in range(10)]
        r = percolation_connectivity(grid)
        assert r == 0.0

    def test_partial_defects(self):
        grid = generate_iid_defects(32, 32, 0.05, seed=1)
        r = percolation_connectivity(grid)
        assert 0.0 <= r <= 1.0

    def test_high_defect_reduces_connectivity(self):
        low_dr = percolation_connectivity(generate_iid_defects(32, 32, 0.05, seed=7))
        high_dr = percolation_connectivity(generate_iid_defects(32, 32, 0.40, seed=7))
        assert low_dr >= high_dr


class TestFunctionalYield:
    def test_y_func_range(self):
        for r_conn in [0.0, 0.5, 0.9, 1.0]:
            for r_alg in [0.0, 0.5, 0.9, 1.0]:
                y = compute_y_func(r_conn, r_alg)
                assert 0.0 <= y <= 1.0

    def test_c_eff_infinite_when_zero_yield(self):
        assert compute_c_eff(1.0, 0.1, 0.1, 0.0) == float("inf")

    def test_c_eff_increases_with_lower_yield(self):
        c_high = compute_c_eff(1.0, 0.1, 0.1, 0.9)
        c_low = compute_c_eff(1.0, 0.1, 0.1, 0.3)
        assert c_low > c_high

    def test_r_alg_capped_at_1(self):
        r = compute_r_alg(0.9, 0.8, 0.95)
        assert 0.0 <= r <= 1.0

    def test_r_alg_does_not_double_count_r_conn(self):
        r_alg = compute_r_alg(0.9, 0.7, 0.81)
        assert abs(r_alg - 0.9) < 1e-3
        y = compute_y_func(0.5, r_alg)
        assert abs(y - 0.45) < 1e-3


class TestSemiForgeSimulator:
    def test_simulate_iid(self):
        sim = SemiForgeSimulator()
        result = sim.simulate("samples/semiforge_crossbar/config.json",
                              case_id="test_iid", monte_carlo_runs=5)
        fy = result["functional_yield_result"]
        assert 0.0 <= fy["y_func"] <= 1.0
        assert 0.0 <= fy["r_conn"] <= 1.0
        assert fy["c_eff"] > 0

    def test_simulate_output_structure(self):
        sim = SemiForgeSimulator()
        result = sim.simulate("samples/semiforge_crossbar/config.json",
                              case_id="test_struct", monte_carlo_runs=3)
        assert "state" in result
        assert "evidence_pack" in result
        assert "ooda_frame" in result
        assert "recovery_candidates" in result
        assert "functional_yield_result" in result

    def test_functional_yield_result_schema(self):
        sim = SemiForgeSimulator()
        result = sim.simulate("samples/semiforge_crossbar/config.json",
                              case_id="test_schema", monte_carlo_runs=3)
        fy = result["functional_yield_result"]
        assert fy["schema"] == "yieldos.semiforge.functional_yield.v1"
        for key in ["array_size", "defect_rate", "r_conn", "r_alg",
                    "y_func", "baseline_accuracy", "recovered_accuracy", "c_eff"]:
            assert key in fy, f"Missing key: {key}"

    def test_high_defect_lowers_yield(self):
        import json
        import os
        import tempfile
        sim = SemiForgeSimulator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"array_rows": 32, "array_cols": 32, "defect_rate": 0.02,
                       "defect_distribution": "iid", "baseline_accuracy": 0.92}, f)
            low_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"array_rows": 32, "array_cols": 32, "defect_rate": 0.35,
                       "defect_distribution": "iid", "baseline_accuracy": 0.92}, f)
            high_path = f.name

        r_low = sim.simulate(low_path, case_id="low", monte_carlo_runs=5)["functional_yield_result"]
        r_high = sim.simulate(high_path, case_id="high", monte_carlo_runs=5)["functional_yield_result"]

        os.unlink(low_path)
        os.unlink(high_path)

        assert r_low["y_func"] >= r_high["y_func"]
