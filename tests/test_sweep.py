"""Tests for SemiForge sweep and SemFab synthetic generation."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from yieldos.domains.semfab.cross_step_rca import (
    build_cross_step_graph,
    correlate_drift_to_metrology,
    correlate_drift_to_yield,
)
from yieldos.domains.semfab.synthetic_gen import generate_all
from yieldos.domains.semiforge.sweep import ascii_plot, run_sweep, write_sweep_csv


class TestSemiForgeSwep:
    def test_sweep_returns_correct_points(self):
        results = run_sweep(
            array_rows=16, array_cols=16,
            defect_rates=[0.0, 0.10, 0.20, 0.30],
            distribution="iid",
            monte_carlo_runs=5,
        )
        assert len(results) == 4

    def test_sweep_y_func_decreases_with_defect_rate(self):
        results = run_sweep(
            array_rows=32, array_cols=32,
            defect_rates=[0.0, 0.05, 0.15, 0.30],
            distribution="iid",
            monte_carlo_runs=5,
        )
        y_funcs = [r["y_func"] for r in results]
        # Generally decreasing (not strictly due to randomness, but overall trend)
        assert y_funcs[0] >= y_funcs[-1]

    def test_sweep_zero_defect_near_1(self):
        results = run_sweep(
            array_rows=32, array_cols=32,
            defect_rates=[0.0],
            distribution="iid",
            monte_carlo_runs=5,
        )
        assert results[0]["y_func"] > 0.90

    def test_sweep_required_fields(self):
        results = run_sweep(
            array_rows=16, array_cols=16,
            defect_rates=[0.10],
            distribution="iid",
            monte_carlo_runs=3,
        )
        r = results[0]
        for key in ["defect_rate", "r_conn", "r_alg", "y_func", "c_eff", "mc_runs"]:
            assert key in r, f"Missing key: {key}"

    def test_sweep_clustered_vs_iid(self):
        iid = run_sweep(
            array_rows=32, array_cols=32,
            defect_rates=[0.15],
            distribution="iid",
            monte_carlo_runs=10,
        )
        cl = run_sweep(
            array_rows=32, array_cols=32,
            defect_rates=[0.15],
            distribution="clustered",
            clustering_factor=4.0,
            monte_carlo_runs=10,
        )
        # Clustered defects may or may not be worse depending on seed, but both should run
        assert 0.0 <= cl[0]["y_func"] <= 1.0
        assert 0.0 <= iid[0]["y_func"] <= 1.0

    def test_write_sweep_csv(self):
        import os
        import shutil
        import tempfile
        tmpdir = tempfile.mkdtemp()
        try:
            results = run_sweep(
                array_rows=16, array_cols=16,
                defect_rates=[0.05, 0.10],
                distribution="iid",
                monte_carlo_runs=3,
            )
            path = os.path.join(tmpdir, "sweep.csv")
            write_sweep_csv(results, path)
            assert Path(path).exists()
            with open(path, encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 2
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_ascii_plot_returns_string(self):
        results = run_sweep(
            array_rows=16, array_cols=16,
            defect_rates=[0.0, 0.10, 0.20],
            distribution="iid",
            monte_carlo_runs=3,
        )
        plot = ascii_plot(results, "y_func")
        assert "y_func" in plot
        assert "0.00" in plot


class TestSemFabSyntheticGen:
    def test_generate_produces_files(self):
        import shutil
        import tempfile
        tmpdir = tempfile.mkdtemp()
        try:
            info = generate_all(tmpdir, n_lots=5, wafers_per_lot=3)
            assert info["lots"] == 5
            assert info["wafers"] == 15
            assert Path(tmpdir, "tool_log.csv").exists()
            assert Path(tmpdir, "wafer_map.csv").exists()
            assert Path(tmpdir, "metrology.csv").exists()
            assert Path(tmpdir, "lot_genealogy.csv").exists()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_tool_log_row_count(self):
        import shutil
        import tempfile
        tmpdir = tempfile.mkdtemp()
        try:
            info = generate_all(tmpdir, n_lots=4, wafers_per_lot=5)
            # 4 lots × 5 wafers × 5 steps = 100 rows
            assert info["tool_log_rows"] == 100
            with open(Path(tmpdir) / "tool_log.csv", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            assert len(rows) == 100
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_drift_injected_in_later_lots(self):
        import shutil
        import tempfile
        tmpdir = tempfile.mkdtemp()
        try:
            generate_all(tmpdir, n_lots=10, wafers_per_lot=3)
            with open(Path(tmpdir) / "tool_log.csv", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

            early_step4 = [float(r["rf_power_W"]) for r in rows
                          if r["process_step"] == "STEP_04" and r["lot_id"] in ["L1021", "L1022"]]
            late_step4 = [float(r["rf_power_W"]) for r in rows
                         if r["process_step"] == "STEP_04" and r["lot_id"] in ["L1028", "L1029", "L1030"]]

            if early_step4 and late_step4:
                import statistics
                assert statistics.mean(late_step4) > statistics.mean(early_step4)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_analyze_large_dataset(self):
        import shutil
        import tempfile

        from yieldos.domains.semfab import SemFabAnalyzer
        tmpdir = tempfile.mkdtemp()
        try:
            generate_all(tmpdir, n_lots=20, wafers_per_lot=5)
            result = SemFabAnalyzer().analyze(tmpdir, case_id="test_large")
            state = result["state"]
            pack = result["evidence_pack"]
            assert state.metrics["total_tool_log_rows"] == 500  # 20*5*5
            # Evidence should come from drift, wafer map, or cross-step
            assert len(pack.evidence_objects) >= 1
            # State should not be unknown
            assert state.state.value != "unknown"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestCrossStepRCA:
    def _make_drift_events(self, confidence=0.82):
        return [{
            "step": "STEP_04", "metric": "rf_power_W",
            "step_mean": 470.0, "global_mean": 450.0,
            "sigma_count": 3.5, "shift_ratio": 0.044,
            "confidence": confidence,
        }]

    def _make_metrology(self, affected_lots, cd_shift=3.5):
        rows = []
        base_cd = 65.1
        for lot in ["L1021", "L1022", "L1023", "L1024", "L1025"]:
            cd = (base_cd + cd_shift) if lot in affected_lots else base_cd
            for site in ["CENTER", "EDGE", "MIDPOINT"]:
                rows.append({"lot_id": lot, "wafer_id": "W01", "site": site,
                             "target_cd_nm": "65.0", "cd_nm": str(cd)})
        return rows

    def _make_wafer_map(self, affected_lots, fail_rate=0.25):
        import random
        rng = random.Random(42)
        rows = []
        for lot in ["L1021", "L1022", "L1023", "L1024", "L1025"]:
            for i in range(20):
                p = fail_rate if lot in affected_lots else 0.02
                rows.append({"lot_id": lot, "wafer_id": "W01",
                             "die_row": i // 5, "die_col": i % 5,
                             "bin_result": "FAIL" if rng.random() < p else "PASS",
                             "bin_code": "3" if rng.random() < p else "1"})
        return rows

    def test_cd_correlation_detected(self):
        drifts = self._make_drift_events()
        metro = self._make_metrology(["L1024", "L1025"], cd_shift=3.5)
        hits = correlate_drift_to_metrology(drifts, metro, ["L1024", "L1025"])
        assert len(hits) >= 1
        assert hits[0]["cd_delta_nm"] > 2.0

    def test_no_cd_correlation_when_shift_small(self):
        drifts = self._make_drift_events()
        metro = self._make_metrology(["L1024", "L1025"], cd_shift=0.1)
        hits = correlate_drift_to_metrology(drifts, metro, ["L1024", "L1025"])
        assert len(hits) == 0

    def test_yield_correlation_detected(self):
        drifts = self._make_drift_events()
        wm = self._make_wafer_map(["L1024", "L1025"], fail_rate=0.30)
        hits = correlate_drift_to_yield(drifts, wm, ["L1024", "L1025"])
        assert len(hits) >= 1
        assert hits[0]["relative_increase"] > 0.3

    def test_cross_step_graph_structure(self):
        drifts = self._make_drift_events()
        metro = self._make_metrology(["L1024", "L1025"])
        wm = self._make_wafer_map(["L1024", "L1025"])
        graph = build_cross_step_graph(drifts, ["L1024", "L1025"], metro, wm)
        for key in ["tool_drift", "cd_shift", "yield_loss", "chain_confidence", "chain_interpretation"]:
            assert key in graph

    def test_empty_inputs_no_error(self):
        graph = build_cross_step_graph([], [], [], [])
        assert graph["chain_confidence"] == 0.0
