from __future__ import annotations

import json
import statistics
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ...contracts import (
    EvidenceObject,
    EvidenceType,
    RecoveryCandidate,
    RootCauseCandidate,
    SeverityLevel,
    StateKind,
    StateSnapshot,
)
from ...core.evidence_engine import EvidenceEngine
from .defect_map import actual_defect_rate, generate_clustered_defects, generate_iid_defects
from .functional_yield import compute_c_eff, compute_r_alg, compute_r_conn, compute_y_func
from .percolation import percolation_connectivity

DOMAIN = "semiforge"


@dataclass(frozen=True)
class SemiForgeSimulationConfig:
    """Direct-params configuration for SemiForge simulation (no config.json required)."""
    array_rows: int = 64
    array_cols: int = 64
    defect_rate: float = 0.05
    defect_distribution: str = "iid"
    clustering_factor: float = 0.5
    baseline_accuracy: float = 0.90
    monte_carlo_runs: int = 30
    optimizer: str = "greedy"
    case_id: Optional[str] = None
    asset_id: str = "semiforge_direct"
    analog_penalty: dict = field(default_factory=dict)
    random_seed: Optional[int] = None


def run_semiforge_simulation_from_params(
    *,
    array_size: Optional[int] = None,
    array_rows: int = 64,
    array_cols: int = 64,
    defect_rate: float = 0.05,
    defect_distribution: str = "iid",
    clustering_factor: float = 0.5,
    baseline_accuracy: float = 0.90,
    monte_carlo_runs: int = 30,
    optimizer: str = "greedy",
    case_id: Optional[str] = None,
    asset_id: str = "semiforge_direct",
    analog_penalty: Optional[dict] = None,
    random_seed: Optional[int] = None,
) -> dict:
    """
    Run a SemiForge simulation from direct parameters (no config.json required).
    The returned dict includes config_source = 'direct_params' and array_size.

    array_size is a convenience shorthand for array_rows = array_cols = array_size.
    """
    if array_size is not None:
        array_rows = array_size
        array_cols = array_size

    import os
    import tempfile

    config_dict: dict = {
        "array_rows": array_rows,
        "array_cols": array_cols,
        "defect_rate": defect_rate,
        "defect_distribution": defect_distribution,
        "clustering_factor": clustering_factor,
        "baseline_accuracy": baseline_accuracy,
    }
    if analog_penalty:
        config_dict["analog_penalty"] = analog_penalty
    if random_seed is not None:
        config_dict["random_seed"] = random_seed

    # Write a temp config.json so the existing simulate() path is exercised
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(config_dict, tmp)
        tmp_path = tmp.name

    try:
        sim = SemiForgeSimulator()
        result = sim.simulate(
            config_path=tmp_path,
            case_id=case_id,
            monte_carlo_runs=monte_carlo_runs,
            optimizer=optimizer,
        )
    finally:
        os.unlink(tmp_path)

    result["config_source"] = "direct_params"
    # array_size stores the original shorthand value when supplied; otherwise rows*cols
    result["array_size"] = array_size if array_size is not None else array_rows * array_cols
    return result


class SemiForgeSimulator:
    """
    Defect-tolerant functional yield simulator for crossbar compute arrays.
    Based on: defect mapping, percolation analysis, weight masking, recovery benchmark.
    Read-only analysis — no fab control.
    """

    def __init__(self):
        self._engine = EvidenceEngine()

    def simulate(
        self,
        config_path: str,
        case_id: Optional[str] = None,
        monte_carlo_runs: int = 30,
        optimizer: str = "greedy",
    ) -> dict:
        if not case_id:
            case_id = f"case_semiforge_{uuid.uuid4().hex[:8]}"

        config = self._load_config(config_path)
        rows = config.get("array_rows", 64)
        cols = config.get("array_cols", 64)
        defect_rate = config.get("defect_rate", 0.05)
        distribution = config.get("defect_distribution", "iid")   # iid | clustered
        clustering_factor = config.get("clustering_factor", 3.0)
        baseline_accuracy = config.get("baseline_accuracy", 0.92)
        damaged_accuracy = config.get("damaged_accuracy", None)
        c_fab = config.get("c_fab", 1.0)
        c_ctrl = config.get("c_ctrl", 0.15)
        c_rec = config.get("c_rec", 0.10)
        asset_id = config.get("asset_id", f"crossbar_{rows}x{cols}")

        # Analog penalty sensitivity model (optional, config-driven)
        analog_penalty_cfg = config.get("analog_penalty", {})
        analog_penalty_enabled = isinstance(analog_penalty_cfg, dict) and analog_penalty_cfg.get("enabled", False)
        ap_line_r = analog_penalty_cfg.get("line_resistance_penalty", 0.0) if analog_penalty_enabled else 0.0
        ap_adc_dac = analog_penalty_cfg.get("adc_dac_overhead", 0.0) if analog_penalty_enabled else 0.0
        ap_drift = analog_penalty_cfg.get("device_drift_penalty", 0.0) if analog_penalty_enabled else 0.0
        analog_penalty_total = round(ap_line_r + ap_adc_dac + ap_drift, 4) if analog_penalty_enabled else 0.0

        # --- Monte Carlo ---
        r_conn_samples = []
        actual_dr_samples = []

        for run in range(monte_carlo_runs):
            seed = run * 7 + 13
            if distribution == "clustered":
                grid = generate_clustered_defects(rows, cols, defect_rate, clustering_factor, seed)
            else:
                grid = generate_iid_defects(rows, cols, defect_rate, seed)

            adr = actual_defect_rate(grid)
            actual_dr_samples.append(adr)

            # Use percolation connectivity (faster) for main score
            r_c = percolation_connectivity(grid)
            r_conn_samples.append(r_c)

        r_conn_mean = statistics.mean(r_conn_samples)
        r_conn_std = statistics.stdev(r_conn_samples) if len(r_conn_samples) > 1 else 0.0
        actual_dr_mean = statistics.mean(actual_dr_samples)

        # Estimate damaged_accuracy from defect_rate if not provided
        if damaged_accuracy is None:
            damaged_accuracy = max(0.0, baseline_accuracy * (1 - defect_rate * 2.5))

        # Estimate recovered_accuracy via simple masking model
        # Weight masking can recover ~60-80% of defect-induced loss
        defect_induced_loss = baseline_accuracy - damaged_accuracy
        recovery_ratio = max(0.0, min(0.85, r_conn_mean * 0.9))
        recovered_accuracy = min(baseline_accuracy, damaged_accuracy + defect_induced_loss * recovery_ratio)

        r_conn = compute_r_conn(r_conn_mean)
        r_alg = compute_r_alg(baseline_accuracy, damaged_accuracy, recovered_accuracy)
        y_func = compute_y_func(r_conn, r_alg)
        c_eff = compute_c_eff(c_fab, c_ctrl, c_rec, y_func)

        # --- Evidence objects ---
        evidence_objects = []
        ev_counter = 1

        if defect_rate > 0.10:
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.YIELD_DROP,
                source="semiforge_simulation",
                summary=f"High defect rate ({defect_rate:.1%}) significantly reduces routing connectivity",
                metric="defect_rate",
                value=round(actual_dr_mean, 4),
                baseline=0.05,
                unit="ratio",
                confidence=0.90,
            )
            evidence_objects.append(ev)
            ev_counter += 1

        if r_conn_mean < 0.70:
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.PATTERN_ANOMALY,
                source="percolation_analysis",
                summary=f"Percolation connectivity {r_conn_mean:.1%} ± {r_conn_std:.1%} below functional threshold",
                metric="r_conn",
                value=round(r_conn_mean, 4),
                baseline=0.70,
                unit="ratio",
                confidence=min(0.95, 0.6 + (0.70 - r_conn_mean) * 2),
            )
            evidence_objects.append(ev)
            ev_counter += 1

        if distribution == "clustered":
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.SPATIAL_PATTERN,
                source="defect_map_analysis",
                summary=f"Clustered defect distribution (factor={clustering_factor}) detected; routing impact amplified",
                metric="defect_distribution",
                confidence=0.85,
                extra={"clustering_factor": clustering_factor},
            )
            evidence_objects.append(ev)
            ev_counter += 1

        top_conf = max((e.confidence for e in evidence_objects), default=0.40)

        # Classify
        if y_func >= 0.70:
            state_kind = StateKind.NOMINAL
            severity = SeverityLevel.INFO
        elif y_func >= 0.45:
            state_kind = StateKind.FUNCTIONAL_YIELD_ESTIMATED
            severity = SeverityLevel.MEDIUM
        else:
            state_kind = StateKind.DEGRADED
            severity = SeverityLevel.HIGH

        state = StateSnapshot(
            case_id=case_id,
            domain=DOMAIN,
            asset_id=asset_id,
            state=state_kind,
            severity=severity,
            confidence=round(top_conf, 3),
            evidence_refs=[e.evidence_id for e in evidence_objects],
            metrics={
                "array_size": f"{rows}x{cols}",
                "defect_rate_nominal": defect_rate,
                "defect_rate_actual_mean": round(actual_dr_mean, 4),
                "r_conn": r_conn,
                "r_conn_std": round(r_conn_std, 4),
                "r_alg": r_alg,
                "y_func": y_func,
                "baseline_accuracy": baseline_accuracy,
                "damaged_accuracy": round(damaged_accuracy, 4),
                "recovered_accuracy": round(recovered_accuracy, 4),
                "c_eff": c_eff,
                "monte_carlo_runs": monte_carlo_runs,
                "defect_distribution": distribution,
            },
        )

        rca_list = [
            RootCauseCandidate(
                candidate="high defect rate reducing percolation connectivity",
                confidence=round(min(0.90, defect_rate * 4), 3),
                supporting_evidence=[e.evidence_id for e in evidence_objects],
                investigation_hints=[
                    "analyze defect spatial distribution",
                    "compare iid vs clustered model fit",
                    "consider alternative crossbar geometry",
                ],
            ),
        ]
        if distribution == "clustered":
            rca_list.append(RootCauseCandidate(
                candidate="clustered defect formation (e.g. process contamination event)",
                confidence=0.78,
                investigation_hints=["inspect fab logs for contamination events", "check lot-level correlation"],
            ))

        pack = self._engine.build_pack(
            case_id=case_id,
            domain=DOMAIN,
            asset_id=asset_id,
            summary=(
                f"SemiForge crossbar sim {rows}x{cols}: "
                f"defect_rate={defect_rate:.1%}, dist={distribution}, "
                f"Y_func={y_func:.3f}, C_eff={c_eff:.3f} "
                f"(MC runs={monte_carlo_runs})"
            ),
            evidence_objects=evidence_objects,
            root_cause_candidates=rca_list,
            missing_evidence=[
                "measured defect map from actual device",
                "neural network weight distribution",
                "retraining convergence data",
            ],
            state_snapshot_hash=state.snapshot_hash,
        )

        ooda = self._engine.build_ooda(
            case_id=case_id,
            domain=DOMAIN,
            observe=(
                f"Crossbar {asset_id}: defect_rate={defect_rate:.1%}, "
                f"r_conn={r_conn:.3f} ({distribution} distribution)"
            ),
            orient=(
                f"Functional yield Y_func={y_func:.3f}. "
                f"Recovery path: weight masking + remapping recovers {recovery_ratio:.0%} of defect-induced loss. "
                f"Effective cost C_eff={c_eff:.3f}."
            ),
            decide=(
                f"{'Acceptable functional yield.' if y_func >= 0.60 else 'Low functional yield — consider design changes.'} "
                f"Recommend: {'proceed to recovery benchmark' if y_func >= 0.40 else 'redesign array or reduce defect rate target'}."
            ),
            evidence_pack_ref=pack.checksum,
        )

        # Remaining / blocked roles derived from y_func
        if y_func >= 0.70:
            remaining_roles = ["full_compute_eligible", "full_fps_inference_candidate"]
            blocked_roles = []
            bin_class = "full_compute_silver"
            decision_readiness = "PASSPORT_ELIGIBLE"
        elif y_func >= 0.45:
            remaining_roles = ["reduced_compute_eligible", "low_fps_operation_candidate", "background_anomaly_detection"]
            blocked_roles = ["full_fps_inference", "latency_sensitive_inference"]
            bin_class = "reduced_inference_silver"
            decision_readiness = "ACTION_INELIGIBLE"
        else:
            remaining_roles = ["minimal_compute_eligible", "background_health_monitoring"]
            blocked_roles = ["full_fps_inference", "latency_sensitive_inference", "high_power_peak_compute"]
            bin_class = "survival_monitoring_only"
            decision_readiness = "ACTION_INELIGIBLE"

        from ...contracts.input_validation import build_input_validation
        from ...core.functional_yield import build_functional_yield_vector

        role_scores_fyv = {r: 1.0 for r in remaining_roles}
        role_scores_fyv.update({r: 0.0 for r in blocked_roles})
        fyv = build_functional_yield_vector(
            domain="semiforge",
            case_id=case_id,
            asset_id=asset_id,
            component_scores={
                "r_conn": r_conn,
                "r_alg": r_alg,
                "recovered_accuracy_ratio": round(
                    recovered_accuracy / max(baseline_accuracy, 1e-9), 4
                ),
                "analog_factor": round(1.0 - analog_penalty_total, 4),
                "cost_efficiency_proxy": min(1.0, c_eff),
            },
            role_scores=role_scores_fyv,
            evidence_confidence=top_conf,
            missing_inputs=[],
            score_kind="simulation",
            recovery_bonus=recovery_ratio * 0.1,
            model_limitations=["monte_carlo_simulation", "iid_or_clustered_defect_model"],
            domain_adapter="semiforge_crossbar",
            override_yield_score=y_func,
        )
        state.metrics["functional_yield_vector"] = fyv

        forge_passed = bool(config) or (rows > 0 and cols > 0)
        input_validation = build_input_validation(
            case_id=case_id,
            domain_pack="semiforge",
            domain_adapter="semiforge_crossbar",
            status="PASSED" if forge_passed else "FAILED",
            data_level="MINIMUM_RUNNABLE" if forge_passed else "BELOW_MINIMUM",
            found_inputs=list(config.keys()) if config else [],
            missing_inputs=[],
            record_counts={"config_keys": len(config), "monte_carlo_runs": monte_carlo_runs},
            blocking_reasons=[] if forge_passed else ["no config or array dimensions found"],
        )

        recovery = [
            RecoveryCandidate(
                action="simulate_weight_masking_candidate",
                expected_benefit=f"simulate masking {defect_rate:.0%} of defective synapses; estimated recovery ratio {recovery_ratio:.0%}",
                risk="low",
                steps=[
                    "generate defect map from test structures",
                    "simulate zero-masking on defective weight positions",
                    "prepare inference benchmark review for engineer",
                ],
            ),
            RecoveryCandidate(
                action="simulate_redundancy_remap_candidate",
                expected_benefit="simulate routing computation around defect clusters using spare rows/columns",
                risk="low",
                steps=[
                    "identify spare row/col structures",
                    "simulate remapping algorithm",
                    "prepare routing connectivity review",
                ],
            ),
            RecoveryCandidate(
                action="recommend_defect_aware_retraining_experiment",
                expected_benefit=f"recover toward baseline accuracy {baseline_accuracy:.0%} via fine-tuning experiment",
                risk="medium",
                steps=[
                    "prepare defect-aware retraining experiment plan",
                    "draft fine-tuning schedule for engineer review",
                    "prepare recovered accuracy benchmark for review",
                ],
            ),
        ]

        # --- Optional optimizer: rank recovery candidates ---
        optimizer_info = self._run_optimizer(optimizer, recovery)

        return {
            "case_id": case_id,
            "domain": DOMAIN,
            "state": state,
            "evidence_pack": pack,
            "ooda_frame": ooda,
            "recovery_candidates": recovery,
            "optimizer_info": optimizer_info,
            "remaining_roles": remaining_roles,
            "blocked_roles": blocked_roles,
            "bin_class": bin_class,
            "decision_readiness": decision_readiness,
            "input_validation": input_validation,
            "functional_yield_result": {
                "schema": "yieldos.semiforge.functional_yield.v1",
                "array_size": f"{rows}x{cols}",
                "defect_rate": defect_rate,
                "defect_distribution": distribution,
                "r_conn": r_conn,
                "r_conn_std": round(r_conn_std, 4),
                "r_alg": r_alg,
                "y_func": y_func,
                "analog_penalty": analog_penalty_total,
                "analog_penalty_info": {
                    "enabled": analog_penalty_enabled,
                    "line_resistance_penalty": ap_line_r,
                    "adc_dac_overhead": ap_adc_dac,
                    "device_drift_penalty": ap_drift,
                    "note": "sensitivity penalty model, not calibrated device model",
                } if analog_penalty_enabled else {"enabled": False, "note": "set analog_penalty.enabled=true in config to activate"},
                "baseline_accuracy": baseline_accuracy,
                "damaged_accuracy": round(damaged_accuracy, 4),
                "recovered_accuracy": round(recovered_accuracy, 4),
                "c_eff": c_eff,
                "monte_carlo_runs": monte_carlo_runs,
            },
        }

    def _run_optimizer(self, optimizer_name: str, recovery_candidates: list) -> dict:
        """Run optional optimizer to rank recovery candidates. Returns optimizer_info dict."""
        from ...scheduler import OptimizationCandidate, OptimizerScheduler

        _benefit_map = {
            "apply_weight_masking": 0.80,
            "remap_to_redundant_rows_cols": 0.70,
            "retrain_with_defect_aware_training": 0.60,
        }

        candidates = [
            OptimizationCandidate(
                candidate_id=r.action,
                action=r.action,
                benefit_score=_benefit_map.get(r.action, 0.50),
                risk=r.risk,
            )
            for r in recovery_candidates
        ]

        requested = optimizer_name
        used = optimizer_name
        fallback = False
        fallback_reason = ""

        if optimizer_name == "sqbm":
            from ...optimizers.sqbm_optional import SQBMOptimizer
            if not SQBMOptimizer().is_available():
                used = "greedy"
                fallback = True
                fallback_reason = "SQBM backend not installed"

        scheduler = OptimizerScheduler(optimizer_name=used, fallback=False)
        schedule_result = scheduler.schedule(candidates)

        info = {
            "requested": requested,
            "used": used,
            "fallback": fallback,
            "backend_available": not fallback,
            "claim_boundary": (
                "optimizer_fallback_not_sqbm_result" if fallback
                else f"{used}_optimizer_candidate_only"
            ),
        }
        if fallback_reason:
            info["reason"] = fallback_reason
        info["ordered_actions"] = schedule_result.ordered_candidates
        return info

    def _load_config(self, config_path: str) -> dict:
        p = Path(config_path)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return {}
