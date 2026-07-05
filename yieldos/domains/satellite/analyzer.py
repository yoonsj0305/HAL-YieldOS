from __future__ import annotations

import csv
import statistics
import uuid
from pathlib import Path
from typing import List, Optional

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

DOMAIN = "satellite"

SUBSYSTEM_METRICS = {
    "power": ["battery_soc_pct", "bus_voltage_V", "panel_current_A"],
    "thermal": ["temperature_C"],
    "attitude": ["attitude_error_deg", "gyro_drift_deg_s"],
    "comms": ["comms_snr_dB"],
    "payload": ["payload_current_A"],
}

# (col, threshold_low, threshold_high, label, high_is_bad)
THRESHOLDS = [
    ("battery_soc_pct",    20.0, 100.0, "Battery SOC",          False),
    ("bus_voltage_V",      22.0,  28.0, "Bus voltage",          False),
    ("temperature_C",     -30.0,  80.0, "Temperature",          False),
    ("attitude_error_deg",  0.0,   2.0, "Attitude error",       True),
    ("comms_snr_dB",        5.0, 100.0, "Comms SNR",            False),
    ("gyro_drift_deg_s",    0.0,   0.05,"Gyro drift",           True),
]


def _safe_float(v: str, default: float = float("nan")) -> float:
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


class SatGuardAnalyzer:
    """
    Read-only shadow analysis for satellite telemetry.
    No uplink commands are generated.
    """

    def __init__(self):
        self._engine = EvidenceEngine()

    def analyze(
        self,
        telemetry_path: str,
        case_id: Optional[str] = None,
        asset_id: str = "cubesat_01",
    ) -> dict:
        if not case_id:
            case_id = f"case_sat_{uuid.uuid4().hex[:8]}"

        rows = _load_telemetry(telemetry_path)
        evidence_objects: List[EvidenceObject] = []
        ev_counter = 1
        health_penalties = []
        missing_inputs = []

        # Degraded mode: detect missing optional columns
        available_cols = set(rows[0].keys()) if rows else set()
        optional_cols = {"gyro_drift_deg_s", "payload_current_A", "panel_current_A"}
        for col in optional_cols:
            if col not in available_cols:
                missing_inputs.append(col)
        confidence_penalty = len(missing_inputs) * 0.03

        # Per-subsystem penalty accumulators (0.0 = healthy, higher = worse)
        subsystem_penalties: dict = {
            "power": [],
            "thermal": [],
            "attitude": [],
            "comms": [],
        }
        _col_to_subsystem = {
            "battery_soc_pct": "power",
            "bus_voltage_V": "power",
            "panel_current_A": "power",
            "temperature_C": "thermal",
            "attitude_error_deg": "attitude",
            "gyro_drift_deg_s": "attitude",
            "comms_snr_dB": "comms",
        }

        for col, lo, hi, label, high_is_bad in THRESHOLDS:
            vals = [_safe_float(r.get(col, "")) for r in rows if r.get(col)]
            vals = [v for v in vals if not (v != v)]  # filter NaN
            if not vals:
                continue

            recent = statistics.mean(vals[-max(1, len(vals)//5):])

            # high_is_bad=True: one-sided upper bound (rising is bad, e.g. attitude_error, gyro_drift)
            # high_is_bad=False: two-sided range (breach if outside [lo, hi], e.g. temperature, battery)
            if high_is_bad:
                breach_lo = False
                breach_hi = recent > hi
            else:
                breach_lo = recent < lo
                breach_hi = recent > hi

            if breach_lo or breach_hi:
                direction = "low" if breach_lo else "high"
                limit = lo if breach_lo else hi
                severity_frac = abs(recent - limit) / max(abs(limit), 1e-6)
                confidence = min(0.97, 0.65 + severity_frac * 0.5)
                ev = EvidenceObject(
                    evidence_id=f"ev_{ev_counter:03d}",
                    type=EvidenceType.THRESHOLD_BREACH,
                    source="satellite_telemetry",
                    summary=f"{label} is {direction}: recent {recent:.3f} vs limit {limit}",
                    metric=col,
                    value=round(recent, 4),
                    baseline=round((lo + hi) / 2, 4),
                    confidence=confidence,
                    extra={"threshold_lo": lo, "threshold_hi": hi, "direction": direction},
                )
                evidence_objects.append(ev)
                ev_counter += 1
                health_penalties.append(confidence)
                subsys = _col_to_subsystem.get(col)
                if subsys:
                    subsystem_penalties[subsys].append(confidence)

        # Fault flag check
        fault_samples = [r for r in rows if _safe_float(r.get("fault_flag", "0")) != 0]
        if fault_samples:
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.SENSOR_FAULT,
                source="satellite_telemetry",
                summary=f"fault_flag active in {len(fault_samples)}/{len(rows)} telemetry samples",
                metric="fault_flag",
                confidence=0.92,
                extra={"fault_sample_count": len(fault_samples), "total_samples": len(rows)},
            )
            evidence_objects.append(ev)
            ev_counter += 1
            health_penalties.append(0.92)

        # Per-subsystem health scores (1.0 = fully healthy, 0.0 = severely degraded)
        def _subsys_health(penalties: list) -> float:
            if not penalties:
                return 1.0
            return round(max(0.0, 1.0 - max(penalties) * 0.6), 3)

        health_scores = {
            "power_health":    _subsys_health(subsystem_penalties["power"]),
            "thermal_health":  _subsys_health(subsystem_penalties["thermal"]),
            "attitude_health": _subsys_health(subsystem_penalties["attitude"]),
            "comms_health":    _subsys_health(subsystem_penalties["comms"]),
        }

        # Structured health_components matching Robot API shape
        health_components = {
            "power":   health_scores["power_health"],
            "thermal": health_scores["thermal_health"],
            "attitude": health_scores["attitude_health"],
            "comms":   health_scores["comms_health"],
        }

        # Mission readiness = 1 - max_penalty
        mission_readiness = max(0.0, 1.0 - (max(health_penalties) if health_penalties else 0.0) * 0.4)
        mission_readiness = round(mission_readiness, 3)
        health_scores["mission_readiness"] = mission_readiness
        top_conf = max(max(health_penalties) - confidence_penalty, 0.05) if health_penalties else 0.20

        if top_conf >= 0.85 or mission_readiness < 0.5:
            state_kind = StateKind.FAULT_CANDIDATE
            severity = SeverityLevel.HIGH
        elif top_conf >= 0.60 or mission_readiness < 0.75:
            state_kind = StateKind.POWER_MARGIN_DEGRADED
            severity = SeverityLevel.MEDIUM
        elif evidence_objects:
            state_kind = StateKind.DEGRADED
            severity = SeverityLevel.LOW
        else:
            state_kind = StateKind.NOMINAL
            severity = SeverityLevel.INFO

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
                "threshold_breaches": len(evidence_objects),
                "fault_flag_samples": len(fault_samples) if fault_samples else 0,
                "mission_readiness": mission_readiness,
                "health_scores": health_scores,
                "health_components": health_components,
                "degraded_mode": len(missing_inputs) > 0,
                "missing_inputs": missing_inputs,
                "confidence_penalty": round(confidence_penalty, 3),
            },
        )

        rca_list = []
        if evidence_objects:
            rca_list.append(RootCauseCandidate(
                candidate="battery degradation or charge controller fault",
                confidence=round(top_conf * 0.80, 3),
                supporting_evidence=[e.evidence_id for e in evidence_objects],
                investigation_hints=["review charge/discharge cycle history", "compare cell voltages"],
            ))
            rca_list.append(RootCauseCandidate(
                candidate="solar panel partial shadowing or degradation",
                confidence=round(top_conf * 0.65, 3),
                investigation_hints=["check orbital eclipse timing", "compare panel current across axes"],
            ))
            rca_list.append(RootCauseCandidate(
                candidate="attitude control subsystem instability",
                confidence=round(top_conf * 0.45, 3),
                investigation_hints=["review reaction wheel RPM history", "check magnetorquer commands"],
            ))

        pack = self._engine.build_pack(
            case_id=case_id,
            domain=DOMAIN,
            asset_id=asset_id,
            summary=(
                f"Satellite {asset_id}: {len(evidence_objects)} telemetry anomalies. "
                f"Mission readiness: {mission_readiness:.0%}. "
                f"State: {state_kind.value}."
            ),
            evidence_objects=evidence_objects,
            root_cause_candidates=rca_list,
            missing_evidence=[
                "battery cell-level voltage history",
                "solar panel I-V curve",
                "reaction wheel RPM log",
                "eclipse schedule for current orbit",
            ],
            state_snapshot_hash=state.snapshot_hash,
        )

        ev_summary = ", ".join(e.metric for e in evidence_objects[:3]) or "no anomalies"
        ooda = self._engine.build_ooda(
            case_id=case_id,
            domain=DOMAIN,
            observe=f"Telemetry anomalies in {asset_id}: {ev_summary}",
            orient=(
                f"Mission readiness estimated at {mission_readiness:.0%}. "
                f"Top risk: {rca_list[0].candidate if rca_list else 'unknown'}."
            ),
            decide=(
                "Recommend reducing payload duty cycle and scheduling ground contact "
                "for detailed subsystem review."
            ),
            evidence_pack_ref=pack.checksum,
        )

        # Remaining / blocked roles derived from state
        if state_kind == StateKind.FAULT_CANDIDATE and severity == SeverityLevel.HIGH:
            remaining_roles = ["low_rate_telemetry", "health_beacon", "delayed_payload_resume_candidate"]
            blocked_roles = ["high_power_payload_operation", "high_rate_downlink", "latency_sensitive_operation"]
            bin_class = "mission_survival_candidate"
            decision_readiness = "ACTION_INELIGIBLE"
        elif state_kind == StateKind.POWER_MARGIN_DEGRADED or severity == SeverityLevel.MEDIUM:
            remaining_roles = ["reduced_payload_operation_candidate", "low_rate_telemetry"]
            blocked_roles = ["high_power_payload_operation"]
            bin_class = "degraded_role_candidate"
            decision_readiness = "ACTION_INELIGIBLE"
        elif state_kind == StateKind.DEGRADED:
            remaining_roles = ["full_mission_operation_with_monitoring"]
            blocked_roles = []
            bin_class = "monitored_operation"
            decision_readiness = "PASSPORT_ELIGIBLE"
        else:
            remaining_roles = ["full_mission_operation"]
            blocked_roles = []
            bin_class = "full_operation"
            decision_readiness = "PASSPORT_ELIGIBLE"

        recovery = [
            RecoveryCandidate(
                action="recommend_payload_duty_cycle_review",
                expected_benefit="lower power demand and extend battery margin — review for ground team",
                risk="low",
                steps=[
                    "prepare payload schedule review for ground team",
                    "flag power telemetry review for 2-orbit window",
                ],
            ),
            RecoveryCandidate(
                action="prepare_safe_mode_review_packet",
                expected_benefit="prepare safe-mode entry criteria review for ground team approval",
                risk="medium",
                steps=[
                    "prepare safe-mode criteria review packet",
                    "draft safe-mode entry sequence for ground team review and approval",
                ],
            ),
            RecoveryCandidate(
                action="recommend_high_power_operation_delay_review",
                expected_benefit="avoid triggering undervoltage protection — delay review for operator",
                risk="low",
                steps=[
                    "flag high-power payload window for postponement review",
                    "prepare rescheduling proposal for next charge cycle",
                ],
            ),
        ]

        from ...contracts.input_validation import build_input_validation
        from ...core.functional_yield import build_functional_yield_vector

        role_scores_fyv = {r: 1.0 for r in remaining_roles}
        role_scores_fyv.update({r: 0.0 for r in blocked_roles})
        fyv = build_functional_yield_vector(
            domain="space",
            case_id=case_id,
            asset_id=asset_id,
            component_scores=health_components,
            role_scores=role_scores_fyv,
            evidence_confidence=top_conf,
            missing_inputs=missing_inputs,
            score_kind="heuristic",
            recovery_bonus=0.05 if remaining_roles else 0.0,
            model_limitations=["threshold_based_heuristic", "sample_telemetry_only"],
            domain_adapter="satellite",
        )
        state.metrics["functional_yield_vector"] = fyv

        sat_found = [col for col, _, _, _, _ in THRESHOLDS if col in available_cols]
        input_validation = build_input_validation(
            case_id=case_id,
            domain_pack="space",
            domain_adapter="satellite",
            status="PASSED" if len(rows) > 0 else "FAILED",
            data_level="MINIMUM_RUNNABLE" if len(rows) > 0 and not missing_inputs else (
                "BELOW_MINIMUM" if len(rows) > 0 else "EMPTY"
            ),
            found_inputs=sat_found,
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
            "mission_readiness": mission_readiness,
            "health_scores": health_scores,
            "health_components": health_components,
            "degraded_mode": len(missing_inputs) > 0,
            "missing_inputs": missing_inputs,
            "remaining_roles": remaining_roles,
            "blocked_roles": blocked_roles,
            "bin_class": bin_class,
            "decision_readiness": decision_readiness,
            "input_validation": input_validation,
        }
