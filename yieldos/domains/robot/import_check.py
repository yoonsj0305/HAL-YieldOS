"""
Robot Import Check — validates external robot log packages for readiness.

Read-only structural and privacy check only. No analysis performed.
No robot control. No ROS commands. No recovery execution.

Absolute boundary:
  - hardware_execution_enabled = false always
  - No analysis performed during import-check
  - No robot commands generated
  - All outputs are candidate-only readiness assessments
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

_SCHEMA_VERSION = "2.7.1"

_REQUIRED_FILES = [
    "robot_telemetry.csv",
    "operator_notes.csv",
    "maintenance_notes.csv",
]
_OPTIONAL_FILES = ["sim_expectation.csv"]

_REQUIRED_COLUMNS: dict[str, list[str]] = {
    "robot_telemetry.csv": [
        "timestamp", "robot_id", "task_id", "fault_code",
        "real_success", "human_intervention", "post_intervention_result",
    ],
    "operator_notes.csv": [
        "timestamp", "operator_id_hash", "robot_id", "task_id",
        "note_type", "note_text_redacted", "redaction_status", "contains_personal_data",
    ],
    "maintenance_notes.csv": [
        "timestamp", "technician_id_hash", "robot_id", "task_id",
        "note_type", "note_text_redacted", "redaction_status", "contains_personal_data",
    ],
}

_SENSITIVE_COLUMNS = frozenset({
    "operator_name", "employee_id", "phone_number", "email",
    "home_address", "face_image", "voice_recording", "biometric_id",
    "raw_operator_id", "raw_note", "factory_address", "customer_name",
    "face_image_path", "voice_recording_path", "raw_biometric_id",
    "unredacted_note",
})

_SAFETY_BLOCK = {
    "hardware_execution_enabled": False,
    "human_review_required": True,
    "candidate_only": True,
}


def run_import_check(input_dir: str, out_dir: str) -> tuple:
    """
    Check an external robot log package for schema and privacy readiness.
    Returns (import_check_report, pilot_readiness_report).
    """
    input_path = Path(input_dir)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Required file presence
    required_files_status = {}
    missing_required: list[str] = []
    for f in _REQUIRED_FILES:
        exists = (input_path / f).exists()
        required_files_status[f] = exists
        if not exists:
            missing_required.append(f)

    # 2. Optional file presence
    optional_files_status = {}
    for f in _OPTIONAL_FILES:
        optional_files_status[f] = (input_path / f).exists()

    # 3. Column checks, record counts, sensitive field detection
    missing_required_columns: dict[str, list[str]] = {}
    detected_sensitive: list[str] = []
    privacy_warnings: list[str] = []
    record_counts: dict[str, int] = {}

    all_files = [f for f in _REQUIRED_FILES if (input_path / f).exists()]
    for opt_f in _OPTIONAL_FILES:
        if (input_path / opt_f).exists():
            all_files.append(opt_f)

    for fname in all_files:
        fpath = input_path / fname
        try:
            rows = []
            fieldnames: list[str] = []
            with fpath.open(encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                fieldnames = list(reader.fieldnames or [])
                rows = [dict(row) for row in reader]

            record_counts[fname] = len(rows)

            # Sensitive column detection (case-insensitive)
            for col in fieldnames:
                if col.lower() in _SENSITIVE_COLUMNS:
                    if col not in detected_sensitive:
                        detected_sensitive.append(col)
                    privacy_warnings.append(
                        f"Sensitive column '{col}' detected in {fname}. "
                        "Remove or anonymize before analysis."
                    )

            # Required column check
            if fname in _REQUIRED_COLUMNS:
                missing_cols = [
                    col for col in _REQUIRED_COLUMNS[fname]
                    if col not in fieldnames
                ]
                if missing_cols:
                    missing_required_columns[fname] = missing_cols

            # contains_personal_data row check
            if "contains_personal_data" in fieldnames:
                personal_count = sum(
                    1 for r in rows
                    if str(r.get("contains_personal_data", "false")).strip().lower()
                    in ("true", "1", "yes")
                )
                if personal_count > 0:
                    privacy_warnings.append(
                        f"{personal_count} row(s) in {fname} have "
                        "contains_personal_data=true. Human review required."
                    )
        except Exception as exc:
            missing_required_columns.setdefault(fname, [f"read_error: {exc}"])

    # 4. Determine statuses
    if missing_required:
        schema_status = "FAILED"
    elif missing_required_columns:
        schema_status = "PASSED_WITH_WARNINGS"
    else:
        schema_status = "PASSED"

    if detected_sensitive or privacy_warnings:
        privacy_status = "PASSED_WITH_WARNINGS"
    else:
        privacy_status = "PASSED"

    if schema_status == "FAILED":
        readiness_status = "NOT_READY"
    elif missing_required_columns or privacy_warnings:
        readiness_status = "READY_WITH_LIMITATIONS"
    else:
        readiness_status = "READY"

    next_step = (
        "address_missing_files_before_analysis"
        if schema_status == "FAILED"
        else "ready_for_robot_skill_memory_analysis"
    )

    import_check_report = {
        "schema": "hal.yieldos.robot.import_check_report.v1",
        "schema_version": _SCHEMA_VERSION,
        "input_path": str(input_path),
        "schema_status": schema_status,
        "privacy_status": privacy_status,
        "readiness_status": readiness_status,
        "required_files": required_files_status,
        "optional_files": optional_files_status,
        "missing_required_files": missing_required,
        "missing_required_columns": missing_required_columns,
        "detected_sensitive_fields": detected_sensitive,
        "privacy_warnings": privacy_warnings,
        "record_counts": record_counts,
        "recommended_next_step": next_step,
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }

    available_data = []
    if required_files_status.get("robot_telemetry.csv"):
        available_data.append("robot_telemetry")
    if required_files_status.get("operator_notes.csv"):
        available_data.append("operator_notes")
    if required_files_status.get("maintenance_notes.csv"):
        available_data.append("maintenance_notes")
    if optional_files_status.get("sim_expectation.csv"):
        available_data.append("sim_expectation")

    pilot_report = {
        "schema": "hal.yieldos.robot.pilot_readiness_report.v1",
        "schema_version": _SCHEMA_VERSION,
        "pilot_readiness": readiness_status,
        "ready_for": (
            [
                "read_only_skill_memory_analysis",
                "candidate_functional_reclassification",
                "case_study_generation",
            ]
            if schema_status != "FAILED"
            else []
        ),
        "not_ready_for": [
            "industrial validation",
            "safety review certification",
            "root-cause certification",
            "automatic recovery execution",
            "production deployment",
        ],
        "available_data": available_data,
        "missing_or_limited_data": [
            "long_term_failure_history",
            "calibrated_force_sensor_baseline",
            "multi_robot_comparison",
        ],
        "recommended_next_step": (
            "run_robot_skill_demo_after_human_review"
            if schema_status != "FAILED"
            else "fix_missing_required_files_first"
        ),
        "claim_boundary": "pilot_readiness_not_production_approval",
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }

    _write_json(out_path / "robot_import_check_report.json", import_check_report)
    _write_json(out_path / "pilot_readiness_report.json", pilot_report)

    return import_check_report, pilot_report


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
