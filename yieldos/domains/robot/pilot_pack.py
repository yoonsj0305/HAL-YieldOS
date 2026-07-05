"""Robot Pilot-Pack generator.

Generates 7 robot-specific pilot-pack JSON reports to accompany the standard
22-file bundle. The pilot_case_summary.md is written separately by the CLI.
No hardware control. Read-only, shadow-analysis, candidate-only evidence layer.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

CANONICAL_ROBOT_ROLES = [
    "inspection_only_mode",
    "remote_supervised_mode",
    "payload_transport",
    "high_speed_motion",
    "human_nearby_operation",
    "precision_placement",
    "background_diagnostics",
    "recovery_observation_only",
]

REQUIRED_PILOT_FILES = [
    "robot_telemetry.csv",
    "maintenance_log.csv",
    "operator_notes.csv",
    "sim_expectation.csv",
    "intervention_log.csv",
    "force_torque_log.csv",
]

OPTIONAL_PILOT_FILES = [
    "environment_log.csv",
    "operation_log.csv",
    "baseline_policy.json",
]

REQUIRED_TELEMETRY_COLUMNS = [
    "timestamp",
    "motor_current_A",
    "joint_temp_C",
    "imu_vibration_g",
    "position_error_mm",
    "latency_ms",
]

PILOT_COLUMNS = [
    "robot_id",
    "task_id",
    "force_sensor_N",
    "gripper_force_N",
    "slip_detected",
    "contact_instability",
    "payload_kg",
    "surface_type",
    "floor_condition",
    "lighting_lux",
    "real_success",
    "human_intervention",
]

_SAFETY_BOUNDARY = {
    "hardware_execution_enabled": False,
    "human_review_required": True,
    "candidate_only": True,
    "read_only": True,
    "shadow_analysis_only": True,
}


def _load_csv(path: Path) -> tuple[list[str], list[dict]]:
    """Load a CSV file. Returns (columns, rows). Empty if not found."""
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = list(reader.fieldnames or [])
    return columns, rows


def _count_events(rows: list[dict], column: str, truthy_values: set) -> int:
    """Count rows where column value is in truthy_values."""
    return sum(
        1 for r in rows
        if str(r.get(column, "")).strip().lower() in truthy_values
    )


def _unique_values(rows: list[dict], column: str) -> list[str]:
    seen: list[str] = []
    found: set[str] = set()
    for r in rows:
        v = str(r.get(column, "")).strip()
        if v and v not in found:
            found.add(v)
            seen.append(v)
    return seen


def _assess_readiness(
    files_present: list[str],
    files_missing: list[str],
    rows: list[dict],
    columns: list[str],
    task_ids: list[str],
    slip_events: int,
    contact_events: int,
    interventions: int,
) -> tuple[str, float, list[dict]]:
    """Compute readiness_status, readiness_score, and check list."""
    checks: list[dict] = []
    score = 1.0

    # Required files
    ok = not files_missing
    checks.append({
        "check": "required_files",
        "status": "PASS" if ok else "FAIL",
        "detail": f"{len(files_present)}/{len(REQUIRED_PILOT_FILES)} required files present",
        "missing": files_missing,
    })
    if not ok:
        score -= 0.30

    # Minimum row count
    ok = len(rows) >= 20
    checks.append({
        "check": "min_row_count",
        "status": "PASS" if ok else "FAIL",
        "detail": f"{len(rows)} rows (minimum 20 required)",
    })
    if not ok:
        score -= 0.20

    # Task variety
    ok = len(task_ids) >= 3
    checks.append({
        "check": "task_variety",
        "status": "PASS" if ok else "FAIL",
        "detail": f"{len(task_ids)} unique task_id(s): {task_ids[:5]}",
    })
    if not ok:
        score -= 0.15

    # Required telemetry columns
    missing_cols = [c for c in REQUIRED_TELEMETRY_COLUMNS if c not in columns]
    ok = not missing_cols
    checks.append({
        "check": "required_telemetry_columns",
        "status": "PASS" if ok else "FAIL",
        "detail": f"{'All' if ok else 'Missing'}: {missing_cols or 'none'}",
        "missing_columns": missing_cols,
    })
    if not ok:
        score -= 0.15

    # Pilot-specific columns
    pilot_cols_present = [c for c in PILOT_COLUMNS if c in columns]
    pilot_cols_missing = [c for c in PILOT_COLUMNS if c not in columns]
    ok = len(pilot_cols_present) >= 6
    checks.append({
        "check": "pilot_columns",
        "status": "PASS" if ok else "PARTIAL",
        "detail": f"{len(pilot_cols_present)}/{len(PILOT_COLUMNS)} pilot columns present",
        "present": pilot_cols_present,
        "missing": pilot_cols_missing,
    })
    if not ok:
        score -= 0.10

    # Slip events
    has_slip = slip_events > 0
    checks.append({
        "check": "slip_events",
        "status": "PASS" if has_slip else "WARN",
        "detail": f"{slip_events} slip event(s) detected",
    })

    # Contact instability
    has_contact = contact_events > 0
    checks.append({
        "check": "contact_instability",
        "status": "PASS" if has_contact else "WARN",
        "detail": f"{contact_events} contact instability event(s) detected",
    })

    # Human interventions
    has_interventions = interventions > 0
    checks.append({
        "check": "human_interventions",
        "status": "PASS" if has_interventions else "WARN",
        "detail": f"{interventions} human intervention(s) recorded",
    })

    score = round(max(0.0, min(1.0, score)), 4)
    if score >= 0.80:
        status = "PILOT_READY"
    elif score >= 0.50:
        status = "PARTIAL_PILOT_READY"
    else:
        status = "NOT_PILOT_READY"

    return status, score, checks


def _classify_canonical_roles(
    remaining_roles: list[str],
    blocked_roles: list[str],
    bin_class: str,
) -> list[dict]:
    """Map canonical robot roles to remaining/blocked/unknown based on analysis."""
    classified = []
    remaining_set = {r.lower() for r in remaining_roles}
    blocked_set = {r.lower() for r in blocked_roles}

    for canonical_role in CANONICAL_ROBOT_ROLES:
        cr_lower = canonical_role.lower()
        # Check analysis output first
        if any(cr_lower in r.lower() or r.lower() in cr_lower for r in remaining_set):
            status = "REMAINING"
        elif any(cr_lower in b.lower() or b.lower() in cr_lower for b in blocked_set):
            status = "BLOCKED"
        else:
            # Fall back to bin_class heuristic
            if bin_class in ("full_operation", "inspection_candidate"):
                low_risk = {"inspection_only_mode", "background_diagnostics",
                            "recovery_observation_only", "remote_supervised_mode"}
                status = "REMAINING" if canonical_role in low_risk else "CANDIDATE"
            elif bin_class in ("degraded_role_candidate",):
                safe_only = {"inspection_only_mode", "background_diagnostics",
                             "recovery_observation_only"}
                status = "REMAINING" if canonical_role in safe_only else "BLOCKED"
            elif bin_class == "mission_survival_candidate":
                last_resort = {"recovery_observation_only", "background_diagnostics"}
                status = "REMAINING" if canonical_role in last_resort else "BLOCKED"
            else:
                status = "CANDIDATE"

        evidence = []
        if status == "REMAINING":
            evidence = ["telemetry_within_bounds", "no_critical_fault_detected"]
        elif status == "BLOCKED":
            evidence = ["degradation_candidate_detected", "human_review_required_before_reactivation"]

        classified.append({
            "canonical_role": canonical_role,
            "status": status,
            "evidence_basis": evidence,
            "claim_boundary": "candidate_role_classification_not_certified",
            "human_review_required": True,
        })
    return classified


def _conditions_for_role(role: str, status: str) -> list[str]:
    """Return valid conditions for a remaining role."""
    base = [
        "human_review_and_approval_required_before_operation",
        "read_only_shadow_analysis_only",
        "no_autonomous_hardware_action",
    ]
    role_conditions: dict[str, list[str]] = {
        "inspection_only_mode": [
            "reduced_speed_30pct_or_less",
            "human_supervisor_present_at_all_times",
            "no_payload_during_inspection",
        ],
        "remote_supervised_mode": [
            "qualified_operator_monitoring_required",
            "emergency_stop_within_reach",
            "telemetry_stream_active",
        ],
        "payload_transport": [
            "payload_within_rated_capacity",
            "floor_condition_verified_by_human",
            "gripper_force_within_spec",
        ],
        "background_diagnostics": [
            "no_concurrent_production_operation",
            "diagnostic_routine_only",
        ],
        "recovery_observation_only": [
            "observation_mode_only_no_actuation",
            "human_recovery_team_present",
        ],
    }
    if status != "REMAINING":
        return []
    return base + role_conditions.get(role, ["operating_within_validated_envelope"])


def generate_pilot_pack(
    input_dir: str,
    analysis_result: dict,
    case_id: str,
    asset_id: str,
    alias_map: dict[str, str],
    columns: list[str],
    rows: list[dict],
) -> dict[str, Any]:
    """Generate robot pilot-pack reports.

    Returns: {report_key: report_dict} ready for extra_outputs in write_all().
    Keys match the JSON file names (without .json suffix).
    """
    inp = Path(input_dir)
    remaining_roles: list[str] = analysis_result.get("remaining_roles") or []
    blocked_roles: list[str] = analysis_result.get("blocked_roles") or []
    bin_class: str = analysis_result.get("bin_class") or "unknown"
    decision_readiness: str = analysis_result.get("decision_readiness") or "UNKNOWN"

    # ── File completeness ────────────────────────────────────────────────────
    files_present = [f for f in REQUIRED_PILOT_FILES if (inp / f).exists()]
    files_missing = [f for f in REQUIRED_PILOT_FILES if not (inp / f).exists()]
    optional_present = [f for f in OPTIONAL_PILOT_FILES if (inp / f).exists()]

    # ── Pilot column completeness ────────────────────────────────────────────
    pilot_cols_present = [c for c in PILOT_COLUMNS if c in columns]
    pilot_cols_missing = [c for c in PILOT_COLUMNS if c not in columns]

    # ── Event detection ──────────────────────────────────────────────────────
    truthy = {"1", "true", "yes", "y", "1.0"}
    slip_events = _count_events(rows, "slip_detected", truthy)
    contact_events = _count_events(rows, "contact_instability", truthy)
    interventions_tele = _count_events(rows, "human_intervention", truthy)

    # Also load intervention_log.csv for intervention count
    _, interv_rows = _load_csv(inp / "intervention_log.csv")
    total_interventions = interventions_tele + len(interv_rows)

    task_ids = _unique_values(rows, "task_id")

    # ── Readiness assessment ────────────────────────────────────────────────
    readiness_status, readiness_score, pilot_checks = _assess_readiness(
        files_present, files_missing, rows, columns,
        task_ids, slip_events, contact_events, total_interventions,
    )

    # ── Role classification ─────────────────────────────────────────────────
    role_classifications = _classify_canonical_roles(
        remaining_roles, blocked_roles, bin_class
    )
    classified_remaining = [r for r in role_classifications if r["status"] == "REMAINING"]
    classified_blocked = [r for r in role_classifications if r["status"] == "BLOCKED"]

    # ── Missing evidence ────────────────────────────────────────────────────
    missing_required_ev: list[dict] = []
    for mf in files_missing:
        missing_required_ev.append({
            "file": mf,
            "category": "required_file",
            "why_needed": "required for complete pilot readiness assessment",
        })
    for mc in pilot_cols_missing[:5]:
        missing_required_ev.append({
            "column": mc,
            "source_file": "robot_telemetry.csv",
            "category": "pilot_column",
            "why_needed": "required for functional yield evidence completeness",
        })

    # ── Build all 7 JSON reports ────────────────────────────────────────────

    pilot_readiness_report = {
        "schema": "hal.yieldos.robot.pilot_readiness_report.v1",
        "case_id": case_id,
        "domain": "robot",
        "asset_id": asset_id,
        "readiness_status": readiness_status,
        "readiness_score": readiness_score,
        "readiness_score_percent": round(readiness_score * 100, 2),
        "required_files_present": files_present,
        "required_files_missing": files_missing,
        "pilot_checks": pilot_checks,
        "not_sufficient_for": [
            "safety_certification",
            "hardware_deployment_approval",
            "autonomous_operation_approval",
            "yield_guarantee",
            "root_cause_certification",
        ],
        "sufficient_for": [
            "pilot_candidate_review",
            "human_review_preparation",
            "functional_yield_evidence_collection",
        ],
        "hardware_control_enabled": False,
        "human_review_required": True,
        "claim_boundary": "pilot_readiness_candidate_not_certified",
        "safety_boundary": _SAFETY_BOUNDARY,
    }

    evidence_completeness_report = {
        "schema": "hal.yieldos.robot.evidence_completeness_report.v1",
        "case_id": case_id,
        "domain": "robot",
        "completeness_summary": {
            "completeness_status": (
                "SUFFICIENT_FOR_CANDIDATE_REVIEW"
                if not files_missing and len(pilot_cols_present) >= 6
                else "PARTIAL_FOR_CANDIDATE_REVIEW"
            ),
            "files_present": len(files_present),
            "files_missing": len(files_missing),
            "optional_files_present": optional_present,
            "pilot_columns_present": pilot_cols_present,
            "pilot_columns_missing": pilot_cols_missing,
            "slip_events_detected": slip_events,
            "contact_instability_events": contact_events,
            "human_interventions_recorded": total_interventions,
            "unique_task_ids": task_ids,
            "telemetry_row_count": len(rows),
        },
        "file_completeness": {
            "required": {f: (inp / f).exists() for f in REQUIRED_PILOT_FILES},
            "optional": {f: (inp / f).exists() for f in OPTIONAL_PILOT_FILES},
        },
        "column_completeness": {
            "required_telemetry_columns": {
                c: (c in columns) for c in REQUIRED_TELEMETRY_COLUMNS
            },
            "pilot_columns": {c: (c in columns) for c in PILOT_COLUMNS},
        },
        "claim_boundary": "evidence_completeness_is_candidate_assessment_not_certification",
        "safety_boundary": _SAFETY_BOUNDARY,
    }

    role_reclassification_report = {
        "schema": "hal.yieldos.robot.role_reclassification_report.v1",
        "case_id": case_id,
        "domain": "robot",
        "asset_id": asset_id,
        "bin_class": bin_class,
        "decision_readiness": decision_readiness,
        "canonical_roles_assessed": CANONICAL_ROBOT_ROLES,
        "remaining_roles_from_analysis": remaining_roles,
        "blocked_roles_from_analysis": blocked_roles,
        "reclassification_mapping": role_classifications,
        "summary": {
            "remaining_count": len(classified_remaining),
            "blocked_count": len(classified_blocked),
            "candidate_count": len([r for r in role_classifications
                                     if r["status"] == "CANDIDATE"]),
        },
        "claim_boundary": "role_classification_is_candidate_not_certified_operational_mode",
        "safety_boundary": _SAFETY_BOUNDARY,
    }

    valid_conditions_report = {
        "schema": "hal.yieldos.robot.valid_conditions_report.v1",
        "case_id": case_id,
        "domain": "robot",
        "asset_id": asset_id,
        "valid_conditions": [
            {
                "role": r["canonical_role"],
                "status": r["status"],
                "conditions": _conditions_for_role(r["canonical_role"], r["status"]),
                "claim_boundary": "candidate_conditions_not_certified_safe_envelope",
            }
            for r in role_classifications
            if r["status"] in ("REMAINING", "CANDIDATE")
        ],
        "global_conditions": [
            "human_review_and_approval_required_before_any_operation",
            "read_only_shadow_analysis_only",
            "no_autonomous_hardware_action_permitted",
            "safety_officer_sign_off_required",
        ],
        "claim_boundary": "valid_conditions_are_candidate_recommendations_not_safety_certificates",
        "safety_boundary": _SAFETY_BOUNDARY,
    }

    review_items = [
        {
            "item": "Review functional passport remaining_roles list",
            "priority": "HIGH",
            "file_ref": "functional_passport.json",
            "action": "Verify each remaining role is appropriate given operational context",
        },
        {
            "item": "Review evidence_pack root_cause_candidates",
            "priority": "HIGH",
            "file_ref": "evidence_pack.json",
            "action": "Assess confidence of each RCA candidate with domain expert",
        },
        {
            "item": "Review decision_readiness_report",
            "priority": "HIGH",
            "file_ref": "decision_readiness_report.json",
            "action": "Confirm readiness category before scheduling pilot",
        },
        {
            "item": f"Review {slip_events} slip event(s) in telemetry",
            "priority": "HIGH" if slip_events > 0 else "LOW",
            "file_ref": "robot_telemetry.csv",
            "action": "Investigate slip_detected events; assess gripper calibration need",
        },
        {
            "item": f"Review {contact_events} contact instability event(s)",
            "priority": "MEDIUM" if contact_events > 0 else "LOW",
            "file_ref": "force_torque_log.csv",
            "action": "Review force/torque anomalies and correlation with position errors",
        },
        {
            "item": f"Review {total_interventions} human intervention(s)",
            "priority": "MEDIUM" if total_interventions > 0 else "LOW",
            "file_ref": "intervention_log.csv",
            "action": "Verify each intervention reason; check for pattern in task type",
        },
    ]
    if files_missing:
        review_items.append({
            "item": f"Collect missing required files: {files_missing}",
            "priority": "HIGH",
            "file_ref": None,
            "action": "Obtain missing pilot data before proceeding to pilot deployment",
        })

    human_review_packet = {
        "schema": "hal.yieldos.robot.human_review_packet.v1",
        "case_id": case_id,
        "domain": "robot",
        "asset_id": asset_id,
        "review_checklist": review_items,
        "review_summary": {
            "total_items": len(review_items),
            "high_priority": sum(1 for i in review_items if i["priority"] == "HIGH"),
            "medium_priority": sum(1 for i in review_items if i["priority"] == "MEDIUM"),
            "low_priority": sum(1 for i in review_items if i["priority"] == "LOW"),
        },
        "safety_assertions": {
            "hardware_control_enabled": False,
            "autonomous_action_blocked": True,
            "all_outputs_read_only": True,
            "candidate_only": True,
            "human_approval_required_before_any_deployment": True,
        },
        "claim_boundary": "review_packet_is_candidate_checklist_not_safety_clearance",
        "safety_boundary": _SAFETY_BOUNDARY,
    }

    missing_evidence_request = {
        "schema": "hal.yieldos.robot.missing_evidence_request.v1",
        "case_id": case_id,
        "domain": "robot",
        "asset_id": asset_id,
        "missing_required_evidence": missing_required_ev,
        "missing_optional_evidence": [
            {
                "file": f,
                "category": "optional_file",
                "why_useful": "provides additional context for functional yield assessment",
            }
            for f in OPTIONAL_PILOT_FILES
            if not (inp / f).exists()
        ],
        "why_needed_for_functional_yield": {
            "slip_events": "slip_detected events improve gripper health evidence",
            "contact_instability": "contact events support force compliance evidence",
            "sim_expectation": "sim-to-real gap requires expected vs actual comparison",
            "intervention_log": "human interventions are key evidence for safe_return_role",
            "force_torque_log": "force/torque required for precision_placement evidence",
        },
        "claim_boundary": "missing_evidence_list_is_candidate_gap_analysis_not_certification_gate",
        "safety_boundary": _SAFETY_BOUNDARY,
    }

    return {
        "robot_pilot_readiness_report": pilot_readiness_report,
        "robot_evidence_completeness_report": evidence_completeness_report,
        "robot_role_reclassification_report": role_reclassification_report,
        "robot_valid_conditions_report": valid_conditions_report,
        "robot_human_review_packet": human_review_packet,
        "robot_missing_evidence_request": missing_evidence_request,
    }


def build_pilot_case_summary_md(
    case_id: str,
    asset_id: str,
    readiness_status: str,
    readiness_score: float,
    remaining_roles: list[str],
    blocked_roles: list[str],
    bin_class: str,
    slip_events: int,
    contact_events: int,
    interventions: int,
    files_missing: list[str],
) -> str:
    """Generate robot_pilot_case_summary.md content."""
    safety_note = (
        "**SAFETY BOUNDARY**: This is a read-only, shadow-analysis, candidate-only "
        "evidence report. No hardware commands are issued. All findings require human "
        "review and approval before any operational decision."
    )
    remaining_str = "\n".join(f"- {r}" for r in remaining_roles) or "- (none identified)"
    blocked_str = "\n".join(f"- {r}" for r in blocked_roles) or "- (none identified)"
    missing_str = "\n".join(f"- {f}" for f in files_missing) or "- (none)"

    return f"""# Robot Pilot Case Summary

{safety_note}

---

## Case Identity

- **Case ID**: {case_id}
- **Asset ID**: {asset_id}
- **Domain**: robot
- **Analysis Type**: pilot-pack (shadow analysis)

---

## Pilot Readiness Gate

| Field | Value |
|-------|-------|
| Readiness Status | `{readiness_status}` |
| Readiness Score | {readiness_score:.2f} / 1.00 ({round(readiness_score * 100, 1)}%) |
| Functional Bin | `{bin_class}` |

---

## Functional Yield Summary

### Remaining Roles (candidate, human review required)

{remaining_str}

### Blocked Roles (candidate)

{blocked_str}

---

## Evidence Observations

| Signal | Count |
|--------|-------|
| Slip events detected | {slip_events} |
| Contact instability events | {contact_events} |
| Human interventions recorded | {interventions} |

---

## Missing Evidence

{missing_str}

---

## Safety Boundary

- `hardware_execution_enabled: false`
- `human_review_required: true`
- `candidate_only: true`
- `read_only: true`
- All role classifications are candidate assessments, not certified operational modes.
- No robot commands may be issued based on this report.
- Human approval is required before any pilot deployment decision.

---

*Generated by HAL YieldOS robot pilot-pack. Human review required.*
*Candidate-only evidence. Not certified for operational deployment.*
"""
