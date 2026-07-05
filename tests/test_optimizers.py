"""
Tests for YieldOS Optimizer and Scheduler layers.

Safety principle tested:
  - Optimizers NEVER enable hardware execution
  - Schedulers NEVER output hardware commands
  - All results are recommendation_only
  - SQBM is optional; greedy always works without it
  - SQBM absence falls back gracefully
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Optimizer base contract ────────────────────────────────────────────────────

class TestOptimizationResultSafetyInvariant:
    def test_hardware_execution_always_false(self):
        from yieldos.optimizers.base import OptimizationResult
        r = OptimizationResult(
            backend="greedy",
            objective_value=1.0,
            selected_indices=[0, 1],
            hardware_execution_enabled=False,
        )
        assert r.hardware_execution_enabled is False

    def test_hardware_execution_true_raises(self):
        from yieldos.optimizers.base import OptimizationResult
        with pytest.raises(ValueError, match="hardware_execution_enabled"):
            OptimizationResult(
                backend="greedy",
                objective_value=1.0,
                selected_indices=[0],
                hardware_execution_enabled=True,
            )


# ── Greedy optimizer ──────────────────────────────────────────────────────────

class TestGreedyOptimizer:
    def _make_problem(self, candidates=None):
        if candidates is None:
            candidates = [
                {"action": "inspect", "risk": "low",    "benefit_score": 0.9},
                {"action": "hold",    "risk": "medium", "benefit_score": 0.6},
                {"action": "retrain", "risk": "high",   "benefit_score": 0.8},
            ]
        return {"candidates": candidates}

    def test_greedy_is_always_available(self):
        from yieldos.optimizers.greedy import GreedyOptimizer
        assert GreedyOptimizer().is_available() is True

    def test_greedy_returns_result(self):
        from yieldos.optimizers.greedy import GreedyOptimizer
        result = GreedyOptimizer().optimize(self._make_problem())
        assert result.backend == "greedy"
        assert isinstance(result.selected_indices, list)

    def test_greedy_never_enables_hardware(self):
        from yieldos.optimizers.greedy import GreedyOptimizer
        result = GreedyOptimizer().optimize(self._make_problem())
        assert result.hardware_execution_enabled is False

    def test_greedy_low_risk_first(self):
        from yieldos.optimizers.greedy import GreedyOptimizer
        candidates = [
            {"action": "high_risk_op", "risk": "high",   "benefit_score": 1.0},
            {"action": "low_risk_op",  "risk": "low",    "benefit_score": 0.5},
            {"action": "med_risk_op",  "risk": "medium", "benefit_score": 0.7},
        ]
        result = GreedyOptimizer().optimize({"candidates": candidates})
        # First selected should be the low-risk one (index 1)
        assert result.selected_indices[0] == 1

    def test_greedy_empty_candidates(self):
        from yieldos.optimizers.greedy import GreedyOptimizer
        result = GreedyOptimizer().optimize({"candidates": []})
        assert result.selected_indices == []
        assert result.objective_value == 0.0

    def test_greedy_max_select(self):
        from yieldos.optimizers.greedy import GreedyOptimizer
        candidates = [
            {"action": f"action_{i}", "risk": "low", "benefit_score": float(i) / 10}
            for i in range(6)
        ]
        result = GreedyOptimizer().optimize({"candidates": candidates, "max_select": 3})
        assert len(result.selected_indices) == 3


# ── SQBM optional backend ─────────────────────────────────────────────────────

class TestSQBMOptionalBackend:
    def test_sqbm_optional_import(self):
        """SQBMOptimizer can be imported without torch/yieldos_sqbm installed."""
        from yieldos.optimizers.sqbm_optional import SQBMOptimizer
        opt = SQBMOptimizer()
        assert hasattr(opt, "is_available")

    def test_sqbm_is_available_returns_bool(self):
        from yieldos.optimizers.sqbm_optional import SQBMOptimizer
        opt = SQBMOptimizer()
        result = opt.is_available()
        assert isinstance(result, bool)

    def test_sqbm_not_installed_raises_import_error(self):
        """When SQBM is not installed, optimize() raises ImportError."""
        from yieldos.optimizers.sqbm_optional import SQBMOptimizer
        opt = SQBMOptimizer()
        if not opt.is_available():
            with pytest.raises(ImportError, match="SQBM"):
                opt.optimize({"candidates": [{"action": "a", "risk": "low", "benefit_score": 0.5}]})

    def test_sqbm_never_enables_hardware_when_available(self):
        """If SQBM is installed, result must still have hardware_execution_enabled=False."""
        from yieldos.optimizers.sqbm_optional import SQBMOptimizer
        opt = SQBMOptimizer()
        if opt.is_available():
            result = opt.optimize({
                "candidates": [
                    {"action": "a", "risk": "low",    "benefit_score": 0.9},
                    {"action": "b", "risk": "medium", "benefit_score": 0.6},
                ]
            })
            assert result.hardware_execution_enabled is False


# ── get_optimizer fallback ────────────────────────────────────────────────────

class TestOptimizerFallback:
    def test_greedy_name_returns_greedy(self):
        from yieldos.optimizers import get_optimizer
        from yieldos.optimizers.greedy import GreedyOptimizer
        opt = get_optimizer("greedy")
        assert isinstance(opt, GreedyOptimizer)

    def test_unknown_name_raises(self):
        from yieldos.optimizers import get_optimizer
        with pytest.raises(ValueError, match="Unknown optimizer"):
            get_optimizer("nonexistent_optimizer")

    def test_sqbm_fallback_to_greedy_when_unavailable(self):
        """When SQBM is not installed and fallback=True, get_optimizer returns Greedy."""
        from yieldos.optimizers import get_optimizer
        from yieldos.optimizers.greedy import GreedyOptimizer
        from yieldos.optimizers.sqbm_optional import SQBMOptimizer
        if not SQBMOptimizer().is_available():
            opt = get_optimizer("sqbm", fallback=True)
            assert isinstance(opt, GreedyOptimizer)

    def test_sqbm_no_fallback_raises_when_unavailable(self):
        """When SQBM is not installed and fallback=False, get_optimizer raises."""
        from yieldos.optimizers import get_optimizer
        from yieldos.optimizers.sqbm_optional import SQBMOptimizer
        if not SQBMOptimizer().is_available():
            with pytest.raises(ImportError, match="SQBM"):
                get_optimizer("sqbm", fallback=False)


# ── Scheduler models ──────────────────────────────────────────────────────────

class TestSchedulerModels:
    def test_schedule_result_is_recommendation_only(self):
        from yieldos.scheduler.models import ScheduleResult
        r = ScheduleResult(case_id="c1")
        assert r.execution_mode == "recommendation_only"
        assert r.hardware_execution_enabled is False
        assert r.requires_human_review is True

    def test_schedule_result_hardware_true_raises(self):
        from yieldos.scheduler.models import ScheduleResult
        with pytest.raises(ValueError, match="hardware_execution_enabled"):
            ScheduleResult(hardware_execution_enabled=True)

    def test_schedule_result_to_dict(self):
        from yieldos.scheduler.models import ScheduleResult
        r = ScheduleResult(case_id="test_case", backend="greedy")
        d = r.to_dict()
        assert d["hardware_execution_enabled"] is False
        assert d["execution_mode"] == "recommendation_only"
        assert d["requires_human_review"] is True
        assert d["schema"] == "yieldos.schedule_result.v1"

    def test_optimization_candidate_bounds(self):
        from yieldos.scheduler.models import OptimizationCandidate
        with pytest.raises(ValueError, match="benefit_score"):
            OptimizationCandidate(
                candidate_id="c1", action="a",
                benefit_score=1.5, risk="low"
            )
        with pytest.raises(ValueError, match="risk"):
            OptimizationCandidate(
                candidate_id="c1", action="a",
                benefit_score=0.5, risk="extreme"
            )

    def test_safety_boundary_blocks_hardware(self):
        from yieldos.scheduler.models import SafetyBoundary
        boundary = SafetyBoundary(hardware_execution_enabled=True)
        with pytest.raises(ValueError):
            boundary.validate()


# ── HeuristicScheduler ────────────────────────────────────────────────────────

class TestHeuristicScheduler:
    def _make_candidates(self):
        from yieldos.scheduler.models import OptimizationCandidate
        return [
            OptimizationCandidate("c1", "high_risk_action",  0.9, "high"),
            OptimizationCandidate("c2", "low_risk_action",   0.7, "low"),
            OptimizationCandidate("c3", "medium_risk_action", 0.8, "medium"),
        ]

    def test_heuristic_scheduler_returns_schedule_result(self):
        from yieldos.scheduler.heuristic_scheduler import HeuristicScheduler
        result = HeuristicScheduler().schedule(self._make_candidates(), case_id="t1")
        assert result.schema == "yieldos.schedule_result.v1"
        assert len(result.schedule) == 3

    def test_heuristic_scheduler_recommendation_only(self):
        from yieldos.scheduler.heuristic_scheduler import HeuristicScheduler
        result = HeuristicScheduler().schedule(self._make_candidates())
        assert result.hardware_execution_enabled is False
        assert result.execution_mode == "recommendation_only"
        assert result.requires_human_review is True

    def test_heuristic_scheduler_low_risk_first(self):
        from yieldos.scheduler.heuristic_scheduler import HeuristicScheduler
        result = HeuristicScheduler().schedule(self._make_candidates())
        # First in ordered_candidates should be the low_risk_action (c2)
        assert result.ordered_candidates[0] == "c2"

    def test_heuristic_scheduler_no_hardware_command(self):
        from yieldos.scheduler.heuristic_scheduler import HeuristicScheduler
        result = HeuristicScheduler().schedule(self._make_candidates())
        for item in result.schedule:
            assert item.hardware_execution_enabled is False
            assert "command" not in item.action.lower() or "recommend" in item.action.lower()


# ── OptimizerScheduler ────────────────────────────────────────────────────────

class TestOptimizerScheduler:
    def _make_candidates(self):
        from yieldos.scheduler.models import OptimizationCandidate
        return [
            OptimizationCandidate("rec1", "inspect_chamber",  0.85, "low"),
            OptimizationCandidate("rec2", "hold_lot",         0.70, "medium"),
            OptimizationCandidate("rec3", "request_evidence", 0.65, "low"),
        ]

    def test_optimizer_scheduler_greedy_default(self):
        from yieldos.scheduler.optimizer_scheduler import OptimizerScheduler
        sched = OptimizerScheduler(optimizer_name="greedy")
        result = sched.schedule(self._make_candidates(), case_id="t1")
        assert result.backend == "greedy"
        assert result.hardware_execution_enabled is False

    def test_optimizer_scheduler_sqbm_fallback(self):
        """When SQBM unavailable and fallback=True, uses greedy silently."""
        from yieldos.optimizers.sqbm_optional import SQBMOptimizer
        from yieldos.scheduler.optimizer_scheduler import OptimizerScheduler
        if not SQBMOptimizer().is_available():
            sched = OptimizerScheduler(optimizer_name="sqbm", fallback=True)
            result = sched.schedule(self._make_candidates(), case_id="t1")
            assert result.backend == "greedy"
            assert result.optimizer_info.get("fallback") is True
            assert result.hardware_execution_enabled is False

    def test_optimizer_scheduler_result_no_hardware(self):
        from yieldos.scheduler.optimizer_scheduler import OptimizerScheduler
        sched = OptimizerScheduler(optimizer_name="greedy")
        result = sched.schedule(self._make_candidates())
        for item in result.schedule:
            assert item.hardware_execution_enabled is False
            assert item.requires_human_review is True

    def test_scheduler_never_outputs_hardware_command(self):
        from yieldos.scheduler.optimizer_scheduler import OptimizerScheduler
        sched = OptimizerScheduler(optimizer_name="greedy")
        result = sched.schedule(self._make_candidates())
        prohibited = {
            "live_control", "hardware_command", "execute_hardware",
            "send_robot_command", "send_satellite_command", "uplink_command",
            "change_recipe", "modify_recipe", "equipment_start", "equipment_stop",
        }
        for item in result.schedule:
            assert item.action not in prohibited


# ── SemiForge optimizer integration ──────────────────────────────────────────

class TestSemiForgeOptimizerIntegration:
    def test_semiforge_greedy_optimizer_default(self):
        """SemiForge simulate with greedy optimizer (default) works without SQBM."""
        from yieldos.domains.semiforge import SemiForgeSimulator
        result = SemiForgeSimulator().simulate(
            config_path="samples/semiforge_crossbar/config.json",
            monte_carlo_runs=5,
            optimizer="greedy",
        )
        assert "optimizer_info" in result
        assert result["optimizer_info"]["used"] == "greedy"

    def test_semiforge_sqbm_fallback_when_unavailable(self):
        """When SQBM not installed, --optimizer sqbm falls back to greedy."""
        from yieldos.domains.semiforge import SemiForgeSimulator
        from yieldos.optimizers.sqbm_optional import SQBMOptimizer
        if not SQBMOptimizer().is_available():
            result = SemiForgeSimulator().simulate(
                config_path="samples/semiforge_crossbar/config.json",
                monte_carlo_runs=5,
                optimizer="sqbm",
            )
            info = result["optimizer_info"]
            assert info["requested"] == "sqbm"
            assert info["used"] == "greedy"
            assert info["fallback"] is True

    def test_semiforge_optimizer_never_enables_hardware(self):
        """Optimizer result from SemiForge never has hardware_execution_enabled=True."""
        from yieldos.domains.semiforge import SemiForgeSimulator
        result = SemiForgeSimulator().simulate(
            config_path="samples/semiforge_crossbar/config.json",
            monte_carlo_runs=5,
        )
        for rec in result["recovery_candidates"]:
            assert rec.hardware_execution_enabled is False
