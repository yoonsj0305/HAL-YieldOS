from __future__ import annotations

import csv
import math
import statistics
import uuid
from pathlib import Path
from typing import Any, List, Optional

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

DOMAIN = "robotics"

# (column, display_name, high_is_bad)
TELEMETRY_METRICS = [
    ("motor_current_A",  "Motor current",      True),
    ("joint_temp_C",     "Joint temperature",  True),
    ("imu_vibration_g",  "IMU vibration",      True),
    ("position_error_mm","Position error",     True),
    ("latency_ms",       "Controller latency", True),
]


RECENT_FRACTION = 0.30
RECENT_WEIGHT = 0.70


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _col_recent_weighted_mean(
    rows: list[dict[str, Any]],
    column: str,
    *,
    recent_fraction: float = RECENT_FRACTION,
    recent_weight: float = RECENT_WEIGHT,
) -> float | None:
    """
    Weighted mean giving recent_weight to the last recent_fraction of values
    and (1 - recent_weight) to the earlier values. This prevents early normal
    data from diluting late-stage degradation signals.
    """
    values: list[float] = []
    for row in rows:
        v = _to_float(row.get(column))
        if v is not None:
            values.append(v)

    if not values:
        return None
    if len(values) == 1:
        return values[0]

    recent_fraction = min(max(recent_fraction, 0.0), 1.0)
    recent_weight = min(max(recent_weight, 0.0), 1.0)

    recent_count = max(1, math.ceil(len(values) * recent_fraction))
    recent_vals = values[-recent_count:]
    old_vals = values[:-recent_count]

    recent_mean = sum(recent_vals) / len(recent_vals)
    if not old_vals:
        return recent_mean

    old_mean = sum(old_vals) / len(old_vals)
    old_weight = 1.0 - recent_weight
    return old_mean * old_weight + recent_mean * recent_weight


def _safe_float(v: str, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _load_telemetry(path: str) -> List[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _trend_score(vals: List[float]) -> float:
    """Linear trend slope as fraction of mean (positive = rising)."""
    if len(vals) < 4:
        return 0.0
    n = len(vals)
    x_mean = (n - 1) / 2
    y_mean = statistics.mean(vals)
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(vals))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / max(den, 1e-12)
    return slope / max(abs(y_mean), 1e-9)


class RobotAnalyzer:
    """
    Read-only shadow analysis for robot telemetry.
    No hardware commands are issued.
    """

    def __init__(self):
        self._engine = EvidenceEngine()

    def analyze(
        self,
        telemetry_path: str,
        case_id: Optional[str] = None,
        asset_id: str = "robot_arm_07",
    ) -> dict:
        if not case_id:
            case_id = f"case_robot_{uuid.uuid4().hex[:8]}"

        rows = _load_telemetry(telemetry_path)
        evidence_objects: List[EvidenceObject] = []
        ev_counter = 1
        anomaly_scores = []
        missing_inputs = []

        # Degraded mode: detect missing optional columns
        available_cols = set(rows[0].keys()) if rows else set()
        for col, label, _ in TELEMETRY_METRICS:
            if col not in available_cols:
                missing_inputs.append(col)

        confidence_penalty = len(missing_inputs) * 0.04

        for col, label, high_is_bad in TELEMETRY_METRICS:
            vals = [_safe_float(r.get(col, "")) for r in rows if r.get(col)]
            if len(vals) < 4:
                continue

            mean = statistics.mean(vals)
            trend = _trend_score(vals)
            recent = statistics.mean(vals[-max(1, len(vals)//5):])
            recent_rise = (recent - mean) / max(abs(mean), 1e-9)

            # Anomaly: rising trend or high recent-vs-mean
            if high_is_bad and (trend > 0.05 or recent_rise > 0.10):
                pct_rise = max(trend, recent_rise)
                confidence = min(0.95, 0.45 + pct_rise * 2.5)
                ev = EvidenceObject(
                    evidence_id=f"ev_{ev_counter:03d}",
                    type=EvidenceType.TREND_SHIFT,
                    source="robot_telemetry",
                    summary=f"{label} rising trend detected: recent avg {recent:.2f} vs mean {mean:.2f} ({pct_rise:+.1%})",
                    metric=col,
                    value=round(recent, 4),
                    baseline=round(mean, 4),
                    confidence=confidence,
                    extra={"trend_slope_fraction": round(trend, 4), "recent_rise": round(recent_rise, 4)},
                )
                evidence_objects.append(ev)
                ev_counter += 1
                anomaly_scores.append(confidence)

        # Fault code check
        fault_rows = [r for r in rows if _safe_float(r.get("controller_fault_code", "0")) != 0]
        if fault_rows:
            fault_codes = list({r.get("controller_fault_code") for r in fault_rows})
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.SENSOR_FAULT,
                source="robot_telemetry",
                summary=f"Controller fault codes detected: {fault_codes} in {len(fault_rows)}/{len(rows)} samples",
                metric="controller_fault_code",
                confidence=0.88,
                extra={"fault_codes": fault_codes, "fault_sample_count": len(fault_rows)},
            )
            evidence_objects.append(ev)
            ev_counter += 1
            anomaly_scores.append(0.88)

        # Error count rising
        error_vals = [_safe_float(r.get("error_count", "")) for r in rows if r.get("error_count")]
        if len(error_vals) >= 4:
            recent_err = statistics.mean(error_vals[-max(1, len(error_vals)//5):])
            early_err = statistics.mean(error_vals[:max(1, len(error_vals)//5)])
            if recent_err > early_err * 1.5:
                ev = EvidenceObject(
                    evidence_id=f"ev_{ev_counter:03d}",
                    type=EvidenceType.TREND_SHIFT,
                    source="robot_telemetry",
                    summary=f"Error count rising: early avg {early_err:.1f} → recent avg {recent_err:.1f}",
                    metric="error_count",
                    value=round(recent_err, 2),
                    baseline=round(early_err, 2),
                    confidence=0.75,
                )
                evidence_objects.append(ev)
                ev_counter += 1
                anomaly_scores.append(0.75)

        top_conf = max(max(anomaly_scores) - confidence_penalty, 0.05) if anomaly_scores else 0.25

        if top_conf >= 0.80:
            state_kind = StateKind.FAULT_CANDIDATE
            severity = SeverityLevel.HIGH
        elif top_conf >= 0.55:
            state_kind = StateKind.JOINT_PRECISION_DEGRADATION_CANDIDATE
            severity = SeverityLevel.MEDIUM
        else:
            state_kind = StateKind.NOMINAL
            severity = SeverityLevel.INFO

        # --- Health components (recent-weighted aggregation) ---
        def _wmean(col: str) -> float:
            v = _col_recent_weighted_mean(rows, col)
            return v if v is not None else 0.0

        def _health(score: float) -> float:
            return round(max(0.0, min(1.0, score)), 3)

        # Normalize relative to nominal baselines using recent-weighted means
        motor_h = _health(1.0 - max(0.0, (_wmean("motor_current_A") - 3.5) / 2.0))
        temp_h   = _health(1.0 - max(0.0, (_wmean("joint_temp_C") - 45.0) / 20.0))
        vib_h    = _health(1.0 - max(0.0, (_wmean("imu_vibration_g") - 0.02) / 0.08))
        lat_h    = _health(1.0 - max(0.0, (_wmean("latency_ms") - 14.0) / 12.0))

        health_components = {
            "motion_precision": _health((motor_h + vib_h) / 2),
            "thermal_margin":   temp_h,
            "power_stability":  _health(1.0 - max(0.0, (4.2 - _wmean("battery_voltage_V")) / 2.5)) if "battery_voltage_V" in available_cols else None,
            "control_latency":  lat_h,
        }
        health_components = {k: v for k, v in health_components.items() if v is not None}

        state = StateSnapshot(
            case_id=case_id,
            domain=DOMAIN,
            asset_id=asset_id,
            state=state_kind,
            severity=severity,
            confidence=round(top_conf, 3),
            evidence_refs=[e.evidence_id for e in evidence_objects],
            metrics={
                "telemetry_samples": len(rows),
                "anomaly_signals": len(evidence_objects),
                "fault_code_samples": len(fault_rows) if fault_rows else 0,
                "health_components": health_components,
                "degraded_mode": len(missing_inputs) > 0,
                "missing_inputs": missing_inputs,
                "confidence_penalty": round(confidence_penalty, 3),
                "aggregation_method": {
                    "kind": "recent_weighted_mean",
                    "recent_fraction": RECENT_FRACTION,
                    "recent_weight": RECENT_WEIGHT,
                    "note": "health components use last 30% of data at 70% weight",
                },
            },
        )

        rca_list = []
        if evidence_objects:
            rca_list.append(RootCauseCandidate(
                candidate="joint mechanical wear or bearing degradation",
                confidence=round(top_conf * 0.85, 3),
                supporting_evidence=[e.evidence_id for e in evidence_objects],
                investigation_hints=["run calibration sequence", "inspect joint backlash"],
            ))
            rca_list.append(RootCauseCandidate(
                candidate="controller tuning drift or firmware issue",
                confidence=round(top_conf * 0.62, 3),
                investigation_hints=["check PID parameters", "compare firmware version"],
            ))
            rca_list.append(RootCauseCandidate(
                candidate="payload overload causing motor stress",
                confidence=round(top_conf * 0.40, 3),
                investigation_hints=["review payload logs", "compare rated vs actual load"],
            ))

        pack = self._engine.build_pack(
            case_id=case_id,
            domain=DOMAIN,
            asset_id=asset_id,
            summary=(
                f"Robot {asset_id}: {len(evidence_objects)} anomaly signals detected. "
                f"Top confidence: {top_conf:.0%}. State: {state_kind.value}."
            ),
            evidence_objects=evidence_objects,
            root_cause_candidates=rca_list,
            missing_evidence=["maintenance log", "payload history", "joint calibration records"],
            state_snapshot_hash=state.snapshot_hash,
        )

        summary_metrics = ", ".join(
            e.metric for e in evidence_objects[:3]
        ) or "no signals"
        ooda = self._engine.build_ooda(
            case_id=case_id,
            domain=DOMAIN,
            observe=f"{len(evidence_objects)} rising-trend signals in {asset_id}: {summary_metrics}",
            orient=(
                f"Possible mechanical degradation or controller drift in {asset_id}. "
                f"Confidence: {top_conf:.0%}."
            ),
            decide="Recommend calibration run and maintenance inspection before next operation cycle.",
            evidence_pack_ref=pack.checksum,
        )

        # Remaining / blocked roles derived from state
        if state_kind == StateKind.FAULT_CANDIDATE and severity == SeverityLevel.HIGH:
            remaining_roles = ["background_monitoring", "safe_return_candidate"]
            blocked_roles = ["normal_payload_operation", "high_speed_autonomous_motion", "normal_speed_operation"]
            bin_class = "mission_survival_candidate"
            decision_readiness = "ACTION_INELIGIBLE"
        elif state_kind in (StateKind.JOINT_PRECISION_DEGRADATION_CANDIDATE,) or severity == SeverityLevel.MEDIUM:
            remaining_roles = ["low_speed_operation_candidate", "background_monitoring"]
            blocked_roles = ["high_speed_autonomous_motion", "normal_payload_operation"]
            bin_class = "degraded_role_candidate"
            decision_readiness = "ACTION_INELIGIBLE"
        else:
            remaining_roles = ["full_operation"]
            blocked_roles = []
            bin_class = "full_operation"
            decision_readiness = "PASSPORT_ELIGIBLE"

        recovery = [
            RecoveryCandidate(
                action="recommend_calibration_review",
                expected_benefit="identify and correct position drift — calibration review for engineer approval",
                risk="low",
                steps=[
                    "prepare calibration review checklist",
                    "schedule calibration window with maintenance team",
                    "compare before/after position error data",
                ],
            ),
            RecoveryCandidate(
                action="recommend_speed_limit_review",
                expected_benefit="reduce mechanical stress while investigation proceeds",
                risk="low",
                steps=[
                    "draft speed-limit change request for engineer approval",
                    "monitor vibration for 1 hour after operator implements reviewed limit",
                ],
            ),
            RecoveryCandidate(
                action="recommend_preventive_maintenance_review",
                expected_benefit="address potential bearing or joint wear before failure",
                risk="medium",
                steps=[
                    "prepare maintenance review ticket",
                    "schedule joint inspection with maintenance team",
                    "flag lubricant replacement as pending review",
                ],
            ),
        ]

        from ...contracts.input_validation import build_input_validation
        from ...core.functional_yield import build_functional_yield_vector

        role_scores_fyv = {r: 1.0 for r in remaining_roles}
        role_scores_fyv.update({r: 0.0 for r in blocked_roles})
        fyv = build_functional_yield_vector(
            domain="robot",
            case_id=case_id,
            asset_id=asset_id,
            component_scores=health_components,
            role_scores=role_scores_fyv,
            evidence_confidence=top_conf,
            missing_inputs=missing_inputs,
            score_kind="heuristic",
            recovery_bonus=0.05 if remaining_roles else 0.0,
            model_limitations=["heuristic_severity_mapping", "sample_telemetry_only"],
            domain_adapter="robotics",
        )
        state.metrics["functional_yield_vector"] = fyv

        found_cols = [col for col, _, _ in TELEMETRY_METRICS if col in available_cols]
        input_validation = build_input_validation(
            case_id=case_id,
            domain_pack="robot",
            domain_adapter="robotics",
            status="PASSED" if len(rows) > 0 else "FAILED",
            data_level="MINIMUM_RUNNABLE" if len(rows) > 0 and not missing_inputs else (
                "BELOW_MINIMUM" if len(rows) > 0 else "EMPTY"
            ),
            found_inputs=found_cols,
            missing_inputs=missing_inputs,
            record_counts={"telemetry_rows": len(rows)},
            blocking_reasons=[] if len(rows) > 0 else ["telemetry_samples == 0"],
        )

        return {
            "case_id": case_id,
            "domain": DOMAIN,
            "state": state,
            "evidence_pack": pack,
            "ooda_frame": ooda,
            "recovery_candidates": recovery[:3],
            "health_components": health_components,
            "degraded_mode": len(missing_inputs) > 0,
            "missing_inputs": missing_inputs,
            "remaining_roles": remaining_roles,
            "blocked_roles": blocked_roles,
            "bin_class": bin_class,
            "decision_readiness": decision_readiness,
            "input_validation": input_validation,
        }
