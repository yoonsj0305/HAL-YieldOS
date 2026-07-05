"""
Robot Skill Memory Layer — read-only preservation of skilled operator observations,
human interventions, maintenance notes, physical reality gap evidence, and case study
narrative as Functional Yield evidence.

HAL does not replace skilled workers.
HAL preserves their field judgment as evidence-backed functional yield data.

Absolute boundary:
  - No robot control commands issued
  - No ROS commands generated
  - No root-cause certification claims
  - No closed-loop control
  - hardware_execution_enabled = false always
  - All outputs are candidate_only, require human review

v2.6.1: adds sim_to_real_gap_report and force_compliance_event_log
v2.6.2: adds robot_skill_memory_case_study, before_after_functional_reclassification,
        links FP and OODA to case study, polishes claim boundary strings
v2.7.0: supports optional --input (external log package folder)
"""
from __future__ import annotations

import csv
import hashlib
import json
import uuid
from pathlib import Path
from typing import Optional

_SCHEMA_VERSION = "2.7.1"

_SAFETY_BLOCK = {
    "hardware_execution_enabled": False,
    "human_review_required": True,
    "candidate_only": True,
    "read_only_shadow": True,
}

ALLOWED_INTERVENTION_TYPES = frozenset({
    "manual_stop_observed",
    "manual_reset_observed",
    "payload_removed_observed",
    "inspection_performed",
    "maintenance_note_added",
    "unknown_human_intervention",
})

_ALLOWED_GAP_FACTORS = frozenset({
    "payload_variation",
    "floor_condition",
    "surface_type",
    "lighting_gap",
    "joint_torque_deviation",
    "force_sensor_deviation",
    "gripper_force_margin_low",
    "grip_slip",
    "contact_instability",
    "position_error_deviation",
    "unknown_gap_factor",
})

_ALLOWED_FORCE_EVENT_TYPES = frozenset({
    "force_spike",
    "torque_anomaly",
    "slip_event",
    "grip_failure_candidate",
    "contact_instability",
    "excessive_payload_resistance",
    "position_error_deviation",
    "unknown_physical_event",
})

_SAMPLE_DIR = Path(__file__).parent.parent.parent / "sample_data" / "robot_skill_memory"


class RobotSkillMemoryLayer:
    """
    Preserves operator skill observations, human interventions, maintenance notes,
    physical reality gap evidence, and case study narrative as read-only Functional
    Yield evidence.

    Does NOT control robots. Does NOT certify root cause. Does NOT issue ROS commands.
    """

    def __init__(self, case_id: Optional[str] = None):
        self.case_id = case_id or f"robot_skill_{uuid.uuid4().hex[:8]}"

    def run_demo(
        self,
        out_dir: str,
        sample_dir: Optional[str] = None,
        asset_id: str = "robot_01",
        input_dir: Optional[str] = None,
    ) -> dict:
        """
        Run Robot Skill Memory demo using built-in or external sample data.
        Generates the standard 22-file output bundle plus skill memory artifacts
        (v2.7.0: input_dir overrides built-in sample data for external packages).
        """
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # input_dir (v2.7.0 --input) takes priority over sample_dir, then default
        if input_dir is not None:
            sd = Path(input_dir)
        elif sample_dir is not None:
            sd = Path(sample_dir)
        else:
            sd = _SAMPLE_DIR
        telemetry_path = str(sd / "robot_telemetry.csv")
        operator_notes_path = str(sd / "operator_notes.csv")
        maintenance_notes_path = str(sd / "maintenance_notes.csv")
        sim_expectations_path = str(sd / "sim_expectation.csv")

        # 1. Standard robot analysis (all 22 bundle files)
        from .analyzer import RobotAnalyzer
        result = RobotAnalyzer().analyze(
            telemetry_path=telemetry_path,
            case_id=self.case_id,
            asset_id=asset_id,
        )

        # 2. Write standard bundle — include all 4 CSVs in source manifest
        from ...cli.main import _run_and_write
        _run_and_write(
            result,
            out_dir,
            "robot",
            source_data_paths=[
                telemetry_path, operator_notes_path,
                maintenance_notes_path, sim_expectations_path,
            ],
        )

        # 3. Load skill-specific inputs
        operator_notes = _load_csv(operator_notes_path)
        maintenance_notes = _load_csv(maintenance_notes_path)
        telemetry_rows = _load_csv(telemetry_path)
        sim_expectations = _load_csv(sim_expectations_path)

        evidence_refs = [
            (ev.get("evidence_id") if isinstance(ev, dict) else getattr(ev, "evidence_id", ""))
            for ev in (result["evidence_pack"].evidence_objects or [])
        ]

        # 4. Build v2.6.0 skill memory artifacts
        skill_note = _build_operator_skill_note(
            self.case_id, asset_id, operator_notes, maintenance_notes, evidence_refs
        )
        timeline = _build_intervention_timeline(
            self.case_id, asset_id, telemetry_rows, operator_notes, evidence_refs
        )

        # 5. Build v2.6.1 physical reality gap artifacts
        gap_report = _build_sim_to_real_gap_report(
            self.case_id, asset_id, telemetry_rows, sim_expectations,
            skill_note, timeline, evidence_refs,
        )
        force_log = _build_force_compliance_event_log(
            self.case_id, asset_id, telemetry_rows, sim_expectations, evidence_refs,
        )

        # 6. Build skill map with cross-references to physical gap events
        force_event_ids = [e["event_id"] for e in force_log.get("events", [])]
        gap_event_ids = [e["event_id"] for e in gap_report.get("gap_events", [])]
        skill_map = _build_skill_to_evidence_map(
            self.case_id, asset_id, skill_note, timeline, result,
            force_event_ids=force_event_ids,
            gap_event_ids=gap_event_ids,
        )

        # 7. Build v2.6.2 case study artifacts
        case_study = _build_case_study(
            self.case_id, asset_id, skill_note, timeline,
            gap_report, force_log, skill_map, result, evidence_refs,
        )
        before_after = _build_before_after_reclassification(
            self.case_id, asset_id, result,
        )
        case_study_md = _build_case_study_md(case_study, before_after)

        # 8. Write all skill memory artifacts
        _write_json(out_path / "operator_skill_note.json", skill_note)
        _write_json(out_path / "human_intervention_timeline.json", timeline)
        _write_json(out_path / "skill_to_evidence_map.json", skill_map)
        _write_json(out_path / "sim_to_real_gap_report.json", gap_report)
        _write_json(out_path / "force_compliance_event_log.json", force_log)
        _write_json(out_path / "robot_skill_memory_case_study.json", case_study)
        _write_json(out_path / "before_after_functional_reclassification.json", before_after)
        (out_path / "robot_skill_memory_case_study.md").write_text(
            case_study_md, encoding="utf-8"
        )

        # 9. Enrich functional_passport with skill context + physical context + case study refs
        _enrich_functional_passport(
            out_path / "functional_passport.json",
            operator_notes, maintenance_notes, timeline,
            gap_report=gap_report, force_log=force_log,
            case_study_ref="robot_skill_memory_case_study.json",
            before_after_ref="before_after_functional_reclassification.json",
        )

        # 10. Enrich ooda_frame with case study reference
        _enrich_ooda_frame(
            out_path / "ooda_frame.json",
            case_study_ref="robot_skill_memory_case_study.json",
        )

        # 11. Refresh case_manifest checksums (modified files + new files + optional_outputs)
        _refresh_case_manifest(out_path)

        return {
            "case_id": self.case_id,
            "operator_skill_note": skill_note,
            "human_intervention_timeline": timeline,
            "skill_to_evidence_map": skill_map,
            "sim_to_real_gap_report": gap_report,
            "force_compliance_event_log": force_log,
            "case_study": case_study,
            "before_after": before_after,
        }


# ── Builder helpers ────────────────────────────────────────────────────────────

def _build_operator_skill_note(
    case_id: str,
    asset_id: str,
    operator_notes: list,
    maintenance_notes: list,
    evidence_refs: list,
) -> dict:
    notes = []
    counter = 1

    for row in operator_notes:
        note_id = f"skill_note_{counter:03d}"
        notes.append({
            "note_id": note_id,
            "timestamp": row.get("timestamp", ""),
            "operator_id_hash": row.get("operator_id_hash", ""),
            "note_type": row.get("note_type", "operator_observation"),
            "note_text_redacted": row.get("note_text_redacted", ""),
            "redaction_status": row.get("redaction_status", "demo_safe"),
            "contains_personal_data": _safe_bool(row.get("contains_personal_data", "false")),
            "structured_observation": {
                "suspected_signal": row.get("suspected_signal", ""),
                "observed_context": row.get("observed_context", ""),
                "confidence": _safe_float(row.get("confidence", "0.5")),
            },
            "claim_boundary": "human_observation_no_root_cause_certification",
            "linked_evidence_refs": evidence_refs[:2],
        })
        counter += 1

    for row in maintenance_notes:
        note_id = f"skill_note_{counter:03d}"
        notes.append({
            "note_id": note_id,
            "timestamp": row.get("timestamp", ""),
            "operator_id_hash": row.get("technician_id_hash", ""),
            "note_type": row.get("note_type", "maintenance_observation"),
            "note_text_redacted": row.get("note_text_redacted", ""),
            "redaction_status": row.get("redaction_status", "demo_safe"),
            "contains_personal_data": _safe_bool(row.get("contains_personal_data", "false")),
            "structured_observation": {
                "suspected_signal": row.get("suspected_signal", ""),
                "observed_context": row.get("observed_context", ""),
                "confidence": _safe_float(row.get("confidence", "0.4")),
            },
            "claim_boundary": "human_observation_no_root_cause_certification",
            "linked_evidence_refs": evidence_refs[:2],
        })
        counter += 1

    return {
        "schema": "hal.yieldos.robot.operator_skill_note.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "note_count": len(notes),
        "notes": notes,
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def _build_intervention_timeline(
    case_id: str,
    asset_id: str,
    telemetry_rows: list,
    operator_notes: list,
    evidence_refs: list,
) -> dict:
    interventions = []
    counter = 1

    for row in telemetry_rows:
        if not _safe_bool(row.get("human_intervention", "false")):
            continue
        if counter > 5:
            break

        int_id = f"hint_{counter:03d}"
        interventions.append({
            "intervention_id": int_id,
            "timestamp": row.get("timestamp", ""),
            "intervention_type": "manual_stop_observed",
            "before_state": {
                "fault_code": row.get("fault_code", "UNKNOWN"),
                "real_success": _safe_bool(row.get("real_success", "false")),
                "slip_detected": _safe_bool(row.get("slip_detected", "false")),
                "controller_fault_code": row.get("controller_fault_code", "0"),
            },
            "after_state": {
                "post_intervention_result": row.get("post_intervention_result", "unknown"),
                "hardware_action_executed_by_yieldos": False,
            },
            "operator_note_ref": "skill_note_001" if operator_notes else "",
            "linked_evidence_refs": evidence_refs[:2],
            "claim_boundary": "observed_intervention_not_yieldos_action",
        })
        counter += 1

    if not interventions and operator_notes:
        row = operator_notes[-1]
        interventions.append({
            "intervention_id": "hint_001",
            "timestamp": row.get("timestamp", ""),
            "intervention_type": "inspection_performed",
            "before_state": {
                "fault_code": "UNKNOWN",
                "real_success": False,
                "slip_detected": False,
                "controller_fault_code": "0",
            },
            "after_state": {
                "post_intervention_result": "inspection_required",
                "hardware_action_executed_by_yieldos": False,
            },
            "operator_note_ref": f"skill_note_{len(operator_notes):03d}",
            "linked_evidence_refs": evidence_refs[:2],
            "claim_boundary": "observed_intervention_not_yieldos_action",
        })

    return {
        "schema": "hal.yieldos.robot.human_intervention_timeline.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "intervention_count": len(interventions),
        "interventions": interventions,
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def _build_skill_to_evidence_map(
    case_id: str,
    asset_id: str,
    skill_note: dict,
    timeline: dict,
    result: dict,
    force_event_ids: Optional[list] = None,
    gap_event_ids: Optional[list] = None,
) -> dict:
    remaining = result.get("remaining_roles", [])
    blocked = result.get("blocked_roles", [])
    evidence_refs = [
        (ev.get("evidence_id") if isinstance(ev, dict) else getattr(ev, "evidence_id", ""))
        for ev in (result["evidence_pack"].evidence_objects or [])
    ]

    notes = skill_note.get("notes", [])
    interventions = timeline.get("interventions", [])

    _force_refs = (force_event_ids or [])[:2]
    _gap_refs = (gap_event_ids or [])[:1]

    mappings = []
    for i, note in enumerate(notes[:3]):
        int_ref = interventions[i]["intervention_id"] if i < len(interventions) else ""
        suspected = note.get("structured_observation", {}).get("suspected_signal", "unknown_signal")
        mappings.append({
            "mapping_id": f"skill_map_{i + 1:03d}",
            "skill_note_id": note["note_id"],
            "intervention_id": int_ref,
            "linked_evidence_refs": evidence_refs[:2],
            "linked_force_event_refs": _force_refs,
            "linked_gap_event_refs": _gap_refs,
            "linked_incident_id": f"inc_{case_id}_{i + 1:04d}",
            "candidate_interpretation": f"{suspected}_correlates_with_sensor_evidence",
            "remaining_roles": remaining,
            "blocked_roles": blocked,
            "claim_boundary": "candidate_only",
        })

    if not mappings:
        mappings.append({
            "mapping_id": "skill_map_001",
            "skill_note_id": "",
            "intervention_id": interventions[0]["intervention_id"] if interventions else "",
            "linked_evidence_refs": evidence_refs[:2],
            "linked_force_event_refs": _force_refs,
            "linked_gap_event_refs": _gap_refs,
            "linked_incident_id": f"inc_{case_id}_0001",
            "candidate_interpretation": "sensor_evidence_correlates_with_observed_anomaly",
            "remaining_roles": remaining,
            "blocked_roles": blocked,
            "claim_boundary": "candidate_only",
        })

    return {
        "schema": "hal.yieldos.robot.skill_to_evidence_map.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "mapping_count": len(mappings),
        "mappings": mappings,
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def _build_sim_to_real_gap_report(
    case_id: str,
    asset_id: str,
    telemetry_rows: list,
    sim_expectations: list,
    skill_note: dict,
    timeline: dict,
    evidence_refs: list,
) -> dict:
    sim_map = {row["task_id"]: row for row in sim_expectations if "task_id" in row}

    task_failures: dict = {}
    for row in telemetry_rows:
        task_id = row.get("task_id", "")
        if not task_id:
            continue
        if not _safe_bool(row.get("real_success", "true")):
            if task_id not in task_failures:
                task_failures[task_id] = []
            task_failures[task_id].append(row)

    gap_events = []
    counter = 1
    for task_id, failure_rows in task_failures.items():
        sim_exp = sim_map.get(task_id)
        if not sim_exp:
            continue
        if not _safe_bool(sim_exp.get("sim_expected_success", "false")):
            continue

        first_failure = failure_rows[0]
        candidate_factors = []

        actual_payload = _safe_float(first_failure.get("payload_kg", "0"))
        expected_payload = _safe_float(sim_exp.get("expected_payload_kg", "0"))
        if expected_payload > 0 and actual_payload > expected_payload * 1.05:
            candidate_factors.append("payload_variation")

        actual_floor = first_failure.get("floor_condition", "").strip().lower()
        expected_floor = sim_exp.get("expected_floor_condition", "").strip().lower()
        if actual_floor and expected_floor and actual_floor != expected_floor:
            candidate_factors.append("floor_condition")

        actual_surface = first_failure.get("surface_type", "").strip().lower()
        expected_surface = sim_exp.get("expected_surface_type", "").strip().lower()
        if actual_surface and expected_surface and actual_surface != expected_surface:
            candidate_factors.append("surface_type")

        actual_torque = _safe_float(first_failure.get("joint_torque_Nm", "0"))
        expected_max_torque = _safe_float(sim_exp.get("expected_max_joint_torque_Nm", "0"))
        if expected_max_torque > 0 and actual_torque > expected_max_torque:
            candidate_factors.append("joint_torque_deviation")

        actual_force = _safe_float(first_failure.get("force_sensor_N", "0"))
        expected_max_force = _safe_float(sim_exp.get("expected_max_force_sensor_N", "0"))
        if expected_max_force > 0 and actual_force > expected_max_force:
            candidate_factors.append("force_sensor_deviation")

        actual_gripper = _safe_float(first_failure.get("gripper_force_N", "0"))
        expected_min_gripper = _safe_float(sim_exp.get("expected_min_gripper_force_N", "0"))
        if expected_min_gripper > 0 and actual_gripper < expected_min_gripper:
            candidate_factors.append("gripper_force_margin_low")

        if _safe_bool(first_failure.get("slip_detected", "false")):
            candidate_factors.append("grip_slip")

        if _safe_bool(first_failure.get("contact_instability", "false")):
            candidate_factors.append("contact_instability")

        actual_lux = _safe_float(first_failure.get("lighting_lux", "0"))
        expected_lux = _safe_float(sim_exp.get("expected_lighting_lux", "0"))
        if expected_lux > 0 and actual_lux < expected_lux * 0.85:
            candidate_factors.append("lighting_gap")

        if not candidate_factors:
            candidate_factors.append("unknown_gap_factor")

        skill_notes_list = skill_note.get("notes", [])
        skill_note_ref = skill_notes_list[0]["note_id"] if skill_notes_list else ""
        interventions_list = timeline.get("interventions", [])
        int_ref = interventions_list[0]["intervention_id"] if interventions_list else ""

        gap_events.append({
            "event_id": f"gap_{counter:03d}",
            "task_id": task_id,
            "sim_expected_success": True,
            "real_success": False,
            "candidate_gap_factors": candidate_factors,
            "observed_context": {
                "expected_payload_kg": expected_payload,
                "actual_payload_kg": actual_payload,
                "expected_floor_condition": sim_exp.get("expected_floor_condition", ""),
                "actual_floor_condition": first_failure.get("floor_condition", ""),
                "expected_lighting_lux": _safe_float(sim_exp.get("expected_lighting_lux", "0")),
                "actual_lighting_lux": actual_lux,
            },
            "linked_evidence_refs": evidence_refs[:2],
            "linked_skill_note_refs": [skill_note_ref] if skill_note_ref else [],
            "linked_intervention_refs": [int_ref] if int_ref else [],
            "claim_boundary": "candidate_only_sim_to_real_gap",
        })
        counter += 1

    gap_factor_counts: dict = {}
    for event in gap_events:
        for factor in event["candidate_gap_factors"]:
            gap_factor_counts[factor] = gap_factor_counts.get(factor, 0) + 1

    task_ids_seen = {row.get("task_id") for row in telemetry_rows if row.get("task_id")}

    return {
        "schema": "hal.yieldos.robot.sim_to_real_gap_report.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "gap_events": gap_events,
        "summary": {
            "total_tasks_compared": len(task_ids_seen),
            "sim_success_real_failure_count": len(gap_events),
            "candidate_gap_factor_counts": gap_factor_counts,
        },
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def _build_force_compliance_event_log(
    case_id: str,
    asset_id: str,
    telemetry_rows: list,
    sim_expectations: list,
    evidence_refs: list,
) -> dict:
    sim_map = {row["task_id"]: row for row in sim_expectations if "task_id" in row}

    events = []
    counter = 1

    for row in telemetry_rows:
        if counter > 10:
            break
        task_id = row.get("task_id", "")
        sim_exp = sim_map.get(task_id, {})

        joint_torque = _safe_float(row.get("joint_torque_Nm", "0"))
        force_sensor = _safe_float(row.get("force_sensor_N", "0"))
        gripper_force = _safe_float(row.get("gripper_force_N", "0"))
        slip = _safe_bool(row.get("slip_detected", "false"))
        contact = _safe_bool(row.get("contact_instability", "false"))
        payload = _safe_float(row.get("payload_kg", "0"))

        exp_max_torque = _safe_float(sim_exp.get("expected_max_joint_torque_Nm", "0"))
        exp_max_force = _safe_float(sim_exp.get("expected_max_force_sensor_N", "0"))
        exp_min_gripper = _safe_float(sim_exp.get("expected_min_gripper_force_N", "0"))

        is_anomalous = False
        event_type = "unknown_physical_event"
        candidate_interp = "unknown_candidate"

        if slip and contact:
            is_anomalous = True
            event_type = "slip_event"
            candidate_interp = "grip_slip_with_contact_instability_candidate"
        elif slip:
            is_anomalous = True
            event_type = "slip_event"
            candidate_interp = "grip_slip_candidate"
        elif contact:
            is_anomalous = True
            event_type = "contact_instability"
            candidate_interp = "contact_instability_candidate"
        elif exp_max_torque > 0 and joint_torque > exp_max_torque:
            is_anomalous = True
            event_type = "torque_anomaly"
            candidate_interp = "joint_torque_exceeds_simulation_expectation"
        elif exp_max_force > 0 and force_sensor > exp_max_force:
            is_anomalous = True
            event_type = "force_spike"
            candidate_interp = "force_sensor_exceeds_simulation_expectation"

        if not is_anomalous:
            continue

        if event_type not in _ALLOWED_FORCE_EVENT_TYPES:
            event_type = "unknown_physical_event"

        events.append({
            "event_id": f"force_evt_{counter:03d}",
            "timestamp": row.get("timestamp", ""),
            "task_id": task_id,
            "event_type": event_type,
            "joint_torque_Nm": joint_torque,
            "expected_max_joint_torque_Nm": exp_max_torque if exp_max_torque > 0 else None,
            "force_sensor_N": force_sensor,
            "expected_max_force_sensor_N": exp_max_force if exp_max_force > 0 else None,
            "gripper_force_N": gripper_force,
            "expected_min_gripper_force_N": exp_min_gripper if exp_min_gripper > 0 else None,
            "slip_detected": slip,
            "contact_instability": contact,
            "payload_kg": payload,
            "candidate_physical_interpretation": candidate_interp,
            "linked_evidence_refs": evidence_refs[:2],
            "claim_boundary": "candidate_physical_event_only",
        })
        counter += 1

    event_type_counts: dict = {}
    for ev in events:
        et = ev["event_type"]
        event_type_counts[et] = event_type_counts.get(et, 0) + 1

    return {
        "schema": "hal.yieldos.robot.force_compliance_event_log.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "events": events,
        "summary": {
            "total_force_events": len(events),
            "event_type_counts": event_type_counts,
        },
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def _build_case_study(
    case_id: str,
    asset_id: str,
    skill_note: dict,
    timeline: dict,
    gap_report: dict,
    force_log: dict,
    skill_map: dict,
    result: dict,
    evidence_refs: list,
) -> dict:
    remaining = result.get("remaining_roles", [])
    blocked = result.get("blocked_roles", [])
    gap_summary = gap_report.get("summary", {})
    force_summary = force_log.get("summary", {})
    gap_events = gap_report.get("gap_events", [])
    force_events = force_log.get("events", [])

    return {
        "schema": "hal.yieldos.robot.skill_memory_case_study.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "title": "Payload lift sim-to-real failure with grip instability",
        "case_summary": {
            "baseline_interpretation": "task_failed",
            "yieldos_interpretation": "degraded_function_candidate",
            "one_sentence_summary": (
                "A robot payload-lift task expected to succeed in simulation failed "
                "in the real environment; YieldOS preserved operator observation, "
                "intervention, force/slip evidence, and candidate remaining roles "
                "without controlling the robot."
            ),
        },
        "timeline": [
            {
                "step": 1,
                "label": "simulation_expectation",
                "summary": "Simulation expected the payload lift task to succeed.",
                "source_refs": ["sim_to_real_gap_report.json"],
            },
            {
                "step": 2,
                "label": "real_world_failure",
                "summary": (
                    "The task failed in the real environment "
                    "with slip and contact instability."
                ),
                "source_refs": ["robot_telemetry.csv", "force_compliance_event_log.json"],
            },
            {
                "step": 3,
                "label": "operator_observation",
                "summary": "The operator observed gripper instability during payload lift.",
                "source_refs": ["operator_skill_note.json"],
            },
            {
                "step": 4,
                "label": "human_intervention",
                "summary": (
                    "A human intervention was observed and recorded as evidence, "
                    "not as a YieldOS action."
                ),
                "source_refs": ["human_intervention_timeline.json"],
            },
            {
                "step": 5,
                "label": "functional_reclassification",
                "summary": (
                    "YieldOS blocked payload transport and high-speed motion while "
                    "preserving inspection-only and remote supervised modes as candidates."
                ),
                "source_refs": ["functional_passport.json", "skill_to_evidence_map.json"],
            },
        ],
        "evidence_summary": {
            "operator_skill_notes": skill_note.get("note_count", 0),
            "human_interventions": timeline.get("intervention_count", 0),
            "sim_to_real_gap_events": gap_summary.get("sim_success_real_failure_count", len(gap_events)),
            "force_compliance_events": force_summary.get("total_force_events", len(force_events)),
            "linked_evidence_refs": evidence_refs[:2],
        },
        "functional_reclassification": {
            "remaining_roles": remaining,
            "blocked_roles": blocked,
            "claim_boundary": "candidate_only_human_review_required",
        },
        "safety_boundary": {
            "hardware_execution_enabled": False,
            "human_review_required": True,
            "candidate_only": True,
            "root_cause_certification": False,
            "safety_certification": False,
        },
        "not_claimed": [
            "hardware control",
            "robot command execution",
            "automatic recovery execution",
            "root-cause certification",
            "safety certification",
            "production deployment approval",
        ],
        "source_outputs": {
            "operator_skill_note": "operator_skill_note.json",
            "human_intervention_timeline": "human_intervention_timeline.json",
            "sim_to_real_gap_report": "sim_to_real_gap_report.json",
            "force_compliance_event_log": "force_compliance_event_log.json",
            "skill_to_evidence_map": "skill_to_evidence_map.json",
            "functional_passport": "functional_passport.json",
            "evidence_pack": "evidence_pack.json",
        },
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def _build_before_after_reclassification(
    case_id: str,
    asset_id: str,
    result: dict,
) -> dict:
    remaining = result.get("remaining_roles", [])
    blocked = result.get("blocked_roles", [])

    return {
        "schema": "hal.yieldos.robot.before_after_functional_reclassification.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "baseline_view": {
            "verdict": "task_failed",
            "interpretation": "payload transport failed",
            "limitation": (
                "binary task success/failure does not preserve remaining functional roles"
            ),
        },
        "yieldos_view": {
            "verdict": "degraded_function_candidate",
            "remaining_roles": remaining,
            "blocked_roles": blocked,
            "claim_boundary": "candidate_only_human_review_required",
        },
        "evidence_links": {
            "operator_skill_note": "operator_skill_note.json",
            "human_intervention_timeline": "human_intervention_timeline.json",
            "sim_to_real_gap_report": "sim_to_real_gap_report.json",
            "force_compliance_event_log": "force_compliance_event_log.json",
            "functional_passport": "functional_passport.json",
        },
        "safety_boundary": {
            "hardware_execution_enabled": False,
            "human_review_required": True,
            "candidate_only": True,
        },
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def _build_case_study_md(case_study: dict, before_after: dict) -> str:
    fc = case_study.get("functional_reclassification", {})
    remaining = fc.get("remaining_roles", [])
    blocked = fc.get("blocked_roles", [])
    ev = case_study.get("evidence_summary", {})

    remaining_list = "\n".join(f"- {r}" for r in remaining) if remaining else "- (none identified)"
    blocked_list = "\n".join(f"- {b}" for b in blocked) if blocked else "- (none identified)"

    return (
        "# Robot Skill Memory Case Study\n\n"
        "## Summary\n\n"
        "A robot payload-lift task was expected to succeed in simulation "
        "but failed in the real environment.\n\n"
        "YieldOS did not control the robot, send commands, or certify a root cause.\n\n"
        "Instead, YieldOS preserved:\n\n"
        "- operator observations\n"
        "- human intervention records\n"
        "- force, torque, slip, and contact evidence\n"
        "- sim-to-real gap evidence\n"
        "- candidate remaining roles\n"
        "- candidate blocked roles\n\n"
        "## Baseline View\n\n"
        "The baseline view marks the task as failed.\n\n"
        "## YieldOS View\n\n"
        "YieldOS reclassifies the failed task into candidate remaining and blocked roles.\n\n"
        "### Remaining Role Candidates\n\n"
        f"{remaining_list}\n\n"
        "### Blocked Role Candidates\n\n"
        f"{blocked_list}\n\n"
        "## Evidence Chain\n\n"
        "1. Simulation expected success.\n"
        "2. Real-world telemetry showed failure.\n"
        f"3. Force and torque deviations were observed "
        f"({ev.get('force_compliance_events', 0)} events).\n"
        "4. Slip and contact instability were recorded.\n"
        f"5. Operator observation described gripper instability "
        f"({ev.get('operator_skill_notes', 0)} notes).\n"
        f"6. Human intervention was recorded as observed evidence "
        f"({ev.get('human_interventions', 0)} events).\n"
        "7. Functional Passport preserved human-review-only candidate roles.\n\n"
        "## Safety Boundary\n\n"
        "YieldOS remains read-only.\n\n"
        "It does not:\n\n"
        "- control robots\n"
        "- send ROS commands\n"
        "- execute recovery\n"
        "- certify root cause\n"
        "- certify safety\n\n"
        "## Claim Boundary\n\n"
        "This case study is sample-based and candidate-only.\n"
        "It is not industrial validation or a safety qualification.\n"
    )


def _enrich_functional_passport(
    fp_path: Path,
    operator_notes: list,
    maintenance_notes: list,
    timeline: dict,
    gap_report: Optional[dict] = None,
    force_log: Optional[dict] = None,
    case_study_ref: Optional[str] = None,
    before_after_ref: Optional[str] = None,
) -> None:
    if not fp_path.exists():
        return
    fp = json.loads(fp_path.read_text(encoding="utf-8"))

    fp["human_skill_context"] = {
        "operator_note_present": len(operator_notes) > 0,
        "maintenance_note_present": len(maintenance_notes) > 0,
        "human_intervention_observed": len(timeline.get("interventions", [])) > 0,
        "skill_capture_status": "partial",
    }
    fp["candidate_validity_conditions"] = [
        "same payload class as observed in demo data",
        "same floor condition as observed in demo data",
        "same robot configuration as observed in demo data",
    ]
    fp["advisory_not_to_do"] = [
        "do not run high-speed motion near people without qualified review",
        "do not resume payload transport without gripper inspection",
    ]
    fp["validity_boundary"] = "candidate_context_not_certification"
    fp["advisory_boundary"] = "advisory_human_review_only"

    if gap_report is not None or force_log is not None:
        _gap_events = (gap_report or {}).get("gap_events", [])
        _force_events = (force_log or {}).get("events", [])
        fp["physical_reality_context"] = {
            "sim_to_real_gap_observed": len(_gap_events) > 0,
            "force_compliance_events_present": len(_force_events) > 0,
            "surface_condition_sensitive": any(
                "surface_type" in e.get("candidate_gap_factors", []) or
                "floor_condition" in e.get("candidate_gap_factors", [])
                for e in _gap_events
            ),
            "payload_variation_sensitive": any(
                "payload_variation" in e.get("candidate_gap_factors", [])
                for e in _gap_events
            ),
            "grip_slip_observed": (
                any(e.get("slip_detected") is True for e in _force_events) or
                any("grip_slip" in e.get("candidate_gap_factors", []) for e in _gap_events)
            ),
            "contact_instability_observed": any(
                e.get("contact_instability") is True for e in _force_events
            ),
            "context_capture_status": "partial",
        }
        fp["physical_context_boundary"] = "candidate_context_not_certification"

    if case_study_ref:
        fp["case_study_ref"] = case_study_ref
    if before_after_ref:
        fp["before_after_ref"] = before_after_ref

    _write_json(fp_path, fp)


def _enrich_ooda_frame(ooda_path: Path, case_study_ref: str) -> None:
    if not ooda_path.exists():
        return
    ooda = json.loads(ooda_path.read_text(encoding="utf-8"))
    ooda["case_study_ref"] = case_study_ref
    _write_json(ooda_path, ooda)


def _refresh_case_manifest(out_path: Path) -> None:
    manifest_path = out_path / "case_manifest.json"
    if not manifest_path.exists():
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files", {})

    for entry in files.values():
        p = out_path / entry.get("path", "")
        if p.exists():
            raw = p.read_bytes()
            entry["sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
            entry["byte_size"] = p.stat().st_size

    for skill_file in [
        "operator_skill_note.json",
        "human_intervention_timeline.json",
        "skill_to_evidence_map.json",
        "sim_to_real_gap_report.json",
        "force_compliance_event_log.json",
    ]:
        key = skill_file.replace(".json", "")
        if key not in files:
            p = out_path / skill_file
            if p.exists():
                raw = p.read_bytes()
                files[key] = {
                    "path": skill_file,
                    "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                    "byte_size": p.stat().st_size,
                }

    manifest["files"] = files
    manifest["file_count"] = len(files)

    optional_outputs: dict = {}
    for opt_file, opt_key in [
        ("robot_skill_memory_case_study.json", "robot_skill_memory_case_study"),
        ("robot_skill_memory_case_study.md", "robot_skill_memory_case_study_markdown"),
        ("before_after_functional_reclassification.json", "before_after_functional_reclassification"),
    ]:
        p = out_path / opt_file
        if p.exists():
            raw = p.read_bytes()
            optional_outputs[opt_key] = {
                "path": opt_file,
                "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "byte_size": p.stat().st_size,
            }
    if optional_outputs:
        manifest["optional_outputs"] = optional_outputs

    _write_json(manifest_path, manifest)


# ── Utilities ──────────────────────────────────────────────────────────────────

def _load_csv(path: str) -> list:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _safe_bool(v: str) -> bool:
    return str(v).strip().lower() in ("true", "1", "yes")


def _safe_float(v) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
