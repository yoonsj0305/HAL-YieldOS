"""
Robot Industrial Data Layer — Incident Memory (v2.2.0)

Builds structured memory records from multi-source industrial robot data:
  - Telemetry CSV (joint sensors)
  - Maintenance log CSV
  - Operation log CSV
  - Environment log CSV

Produces three extra output files:
  - incident_timeline.json        — chronological event sequence
  - industrial_data_record.json   — structured multi-source summary
  - fleet_failure_memory.json     — anonymized failure pattern for fleet learning

Safety invariant: all outputs are shadow analysis records. No robot commands
or hardware control actions are generated. Human review required.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...contracts.meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by

SCHEMA_INCIDENT_TIMELINE = "hal.yieldos.robot.incident_timeline.v1"
SCHEMA_INDUSTRIAL_RECORD = "hal.yieldos.robot.industrial_data_record.v1"
SCHEMA_FLEET_MEMORY = "hal.yieldos.robot.fleet_failure_memory.v1"


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _load_csv(path: str) -> List[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def build_incident_timeline(
    telemetry: List[dict],
    maintenance_log: List[dict],
    operation_log: List[dict],
    case_id: str = "",
    asset_id: str = "",
) -> dict:
    """
    Build a chronological incident timeline merging all data sources.
    Fault codes and failed operation cycles become timeline events.
    """
    events: List[dict] = []

    # Telemetry fault events
    for row in telemetry:
        fc = int(_safe_float(row.get("fault_code", "0")))
        if fc > 0:
            events.append({
                "timestamp": row.get("timestamp", ""),
                "source": "telemetry",
                "event_type": "fault_flag",
                "fault_code": fc,
                "motor_current_A": _safe_float(row.get("motor_current_A")),
                "joint_temp_C": _safe_float(row.get("joint_temp_C")),
                "note": f"On-board fault code {fc} detected",
            })

    # Maintenance events
    for row in maintenance_log:
        events.append({
            "timestamp": row.get("timestamp", ""),
            "source": "maintenance_log",
            "event_type": row.get("event_type", "maintenance"),
            "component": row.get("component", ""),
            "action_taken": row.get("action_taken", ""),
            "outcome": row.get("outcome", ""),
            "technician_id": row.get("technician_id", ""),
        })

    # Failed operation cycles
    for row in operation_log:
        result = row.get("result", "")
        if result in ("fail", "retry"):
            events.append({
                "timestamp": row.get("timestamp", ""),
                "source": "operation_log",
                "event_type": "cycle_failure",
                "cycle_id": row.get("cycle_id", ""),
                "task": row.get("task", ""),
                "result": result,
                "duration_s": _safe_float(row.get("duration_s")),
            })

    events.sort(key=lambda e: e.get("timestamp", ""))

    return {
        "schema": SCHEMA_INCIDENT_TIMELINE,
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "total_events": len(events),
        "fault_events": sum(1 for e in events if e.get("event_type") == "fault_flag"),
        "maintenance_events": sum(1 for e in events if e["source"] == "maintenance_log"),
        "cycle_failures": sum(1 for e in events if e.get("event_type") == "cycle_failure"),
        "timeline": events,
        "human_review_required": True,
        "hardware_execution_enabled": False,
        "generated_by": generated_by(),
        "safety_boundary": SAFETY_BLOCK,
    }


def build_industrial_data_record(
    telemetry: List[dict],
    maintenance_log: List[dict],
    operation_log: List[dict],
    environment_log: List[dict],
    case_id: str = "",
    asset_id: str = "",
) -> dict:
    """
    Build a structured multi-source industrial data record summarizing all inputs.
    """
    n_telemetry = len(telemetry)
    n_maintenance = len(maintenance_log)
    n_operations = len(operation_log)
    n_environment = len(environment_log)

    # Telemetry summary
    motor_currents = [_safe_float(r.get("motor_current_A")) for r in telemetry if r.get("motor_current_A")]
    joint_temps = [_safe_float(r.get("joint_temp_C")) for r in telemetry if r.get("joint_temp_C")]
    vibrations = [_safe_float(r.get("imu_vibration_g")) for r in telemetry if r.get("imu_vibration_g")]
    fault_rows = [r for r in telemetry if int(_safe_float(r.get("fault_code", "0"))) > 0]

    def _stats(vals: List[float]) -> dict:
        if not vals:
            return {"min": None, "max": None, "mean": None}
        return {
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "mean": round(sum(vals) / len(vals), 4),
        }

    # Operation summary
    op_results = {}
    for r in operation_log:
        res = r.get("result", "unknown")
        op_results[res] = op_results.get(res, 0) + 1

    # Maintenance summary
    maint_types = {}
    deferred = [r for r in maintenance_log if r.get("outcome") == "deferred"]
    for r in maintenance_log:
        et = r.get("event_type", "unknown")
        maint_types[et] = maint_types.get(et, 0) + 1

    # Environment summary
    cell_temps = [_safe_float(r.get("cell_temp_C")) for r in environment_log if r.get("cell_temp_C")]
    floor_vibs = [_safe_float(r.get("floor_vibration_g")) for r in environment_log if r.get("floor_vibration_g")]

    return {
        "schema": SCHEMA_INDUSTRIAL_RECORD,
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "data_sources": {
            "telemetry_samples": n_telemetry,
            "maintenance_events": n_maintenance,
            "operation_cycles": n_operations,
            "environment_samples": n_environment,
        },
        "telemetry_summary": {
            "motor_current_A": _stats(motor_currents),
            "joint_temp_C": _stats(joint_temps),
            "imu_vibration_g": _stats(vibrations),
            "fault_flag_samples": len(fault_rows),
            "fault_rate": round(len(fault_rows) / max(n_telemetry, 1), 4),
        },
        "operation_summary": {
            "total_cycles": n_operations,
            "by_result": op_results,
            "failure_rate": round(
                (op_results.get("fail", 0) + op_results.get("retry", 0)) / max(n_operations, 1), 4
            ),
        },
        "maintenance_summary": {
            "total_events": n_maintenance,
            "by_type": maint_types,
            "deferred_events": len(deferred),
            "deferred_components": [r.get("component") for r in deferred],
        },
        "environment_summary": {
            "cell_temp_C": _stats(cell_temps),
            "floor_vibration_g": _stats(floor_vibs),
        },
        "human_review_required": True,
        "hardware_execution_enabled": False,
        "generated_by": generated_by(),
        "safety_boundary": SAFETY_BLOCK,
    }


def build_fleet_failure_memory(
    industrial_record: dict,
    incident_timeline: dict,
    state_snapshot_hash: str = "",
    case_id: str = "",
    asset_id: str = "",
) -> dict:
    """
    Build an anonymized fleet failure memory record for pattern learning.
    No PII or asset-specific identifiers are included in the pattern payload.
    """
    tel = industrial_record.get("telemetry_summary", {})
    maint = industrial_record.get("maintenance_summary", {})
    ops = industrial_record.get("operation_summary", {})

    fault_rate = tel.get("fault_rate", 0.0)
    op_failure_rate = ops.get("failure_rate", 0.0)
    deferred_count = maint.get("deferred_events", 0)
    n_fault_events = incident_timeline.get("fault_events", 0)
    n_cycle_failures = incident_timeline.get("cycle_failures", 0)

    # Compute a pattern fingerprint (non-PII — rates and counts only)
    pattern_payload = json.dumps({
        "fault_rate": round(fault_rate, 3),
        "op_failure_rate": round(op_failure_rate, 3),
        "deferred_maintenance_events": deferred_count,
        "fault_event_count": n_fault_events,
        "cycle_failure_count": n_cycle_failures,
    }, sort_keys=True, separators=(",", ":"))
    pattern_hash = "sha256:" + hashlib.sha256(pattern_payload.encode("utf-8")).hexdigest()

    # Failure severity classification (heuristic, candidate-only)
    if fault_rate > 0.3 or op_failure_rate > 0.2:
        failure_class = "severe_degradation_candidate"
    elif fault_rate > 0.1 or op_failure_rate > 0.1:
        failure_class = "moderate_degradation_candidate"
    elif fault_rate > 0 or deferred_count > 0:
        failure_class = "early_degradation_candidate"
    else:
        failure_class = "nominal"

    return {
        "schema": SCHEMA_FLEET_MEMORY,
        "schema_version": SCHEMA_VERSION,
        "memory_id": f"rfm_{case_id}",
        "failure_class": failure_class,
        "pattern_hash": pattern_hash,
        "fault_rate": round(fault_rate, 4),
        "operation_failure_rate": round(op_failure_rate, 4),
        "deferred_maintenance_events": deferred_count,
        "fault_event_count": n_fault_events,
        "cycle_failure_count": n_cycle_failures,
        "state_snapshot_hash": state_snapshot_hash,
        "causal_claim_boundary": "candidate_only_not_certified_cause",
        "note": (
            "This record is anonymized for fleet pattern learning. "
            "No asset-specific identifiers are included in pattern_hash. "
            "Failure class is a candidate estimate requiring human review."
        ),
        "human_review_required": True,
        "hardware_execution_enabled": False,
        "generated_by": generated_by(),
        "safety_boundary": SAFETY_BLOCK,
    }


def load_industrial_data(
    telemetry_path: str,
    maintenance_log_path: Optional[str] = None,
    operation_log_path: Optional[str] = None,
    environment_log_path: Optional[str] = None,
) -> Dict[str, List[dict]]:
    """
    Load all available industrial data sources. Missing files return empty lists.
    """
    return {
        "telemetry": _load_csv(telemetry_path),
        "maintenance_log": _load_csv(maintenance_log_path) if maintenance_log_path else [],
        "operation_log": _load_csv(operation_log_path) if operation_log_path else [],
        "environment_log": _load_csv(environment_log_path) if environment_log_path else [],
    }
