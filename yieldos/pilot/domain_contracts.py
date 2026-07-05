"""
yieldos/pilot/domain_contracts.py

Five domain-specific PilotContract definitions.

Option A (demo-compatible): minimum_viable_rows is set low enough
for built-in sample data to return READY_FOR_FUNCTIONAL_YIELD_PILOT.
recommended_rows shows the real pilot target.
"""
from __future__ import annotations

from .contracts import InputField, PilotContract

_BLOCKED_COMMON = [
    "certified_root_cause",
    "confirmed_root_cause",
    "safety_certification",
    "yield_guarantee",
    "automatic_recovery_execution",
    "hardware_control_commands",
]

_FUNCTIONAL_YIELD_QUESTION = (
    "What can still function, what must be blocked, "
    "under what valid conditions, and based on what evidence?"
)


def _robot_contract() -> PilotContract:
    return PilotContract(
        domain="robot",
        display_name="Industrial Robot Pilot",
        organizing_question=_FUNCTIONAL_YIELD_QUESTION,
        input_fields=[
            InputField(
                name="robot_telemetry.csv",
                description=(
                    "Time-series joint health and motion telemetry from robot controller. "
                    "v3.0.0 canonical format: motor_current_A, joint_temp_C, "
                    "imu_vibration_g, position_error_mm, latency_ms."
                ),
                format="csv",
                required=True,
                columns=[
                    "timestamp", "robot_id", "task_id", "joint_id",
                    "motor_current_A", "joint_temp_C", "imu_vibration_g",
                    "position_error_mm", "latency_ms",
                    "controller_fault_code", "error_count",
                    "force_sensor_N", "gripper_force_N",
                    "slip_detected", "contact_instability",
                    "payload_kg", "surface_type", "floor_condition",
                    "lighting_lux", "real_success", "human_intervention",
                ],
                sensitivity="internal",
                sanitization_notes="Remove serial numbers; anonymize robot_id and joint IDs if needed.",
                minimum_viable_rows=10,
                recommended_rows=1000,
                functional_yield_role="evidence_inputs",
            ),
            InputField(
                name="operator_notes.csv",
                description="Structured operator observations (faults, interventions, remarks)",
                format="csv",
                required=True,
                columns=["timestamp", "operator_id", "note_type", "description"],
                sensitivity="internal",
                sanitization_notes="Anonymize operator_id to numeric code before sharing.",
                minimum_viable_rows=3,
                recommended_rows=50,
                functional_yield_role="human_review_inputs",
            ),
            InputField(
                name="maintenance_log.csv",
                description="Maintenance events: part replacements, calibrations, inspections",
                format="csv",
                required=False,
                columns=["date", "maintenance_type", "component", "outcome"],
                sensitivity="internal",
                sanitization_notes="Redact part serial numbers and technician names.",
                minimum_viable_rows=1,
                recommended_rows=20,
                functional_yield_role="valid_conditions_inputs",
            ),
        ],
        blocked_claims=_BLOCKED_COMMON + [
            "real_time_control_loop",
            "predictive_maintenance_schedule",
        ],
        evidence_claims=[
            "functional_yield_score_per_joint",
            "remaining_functional_roles_under_current_conditions",
            "blocked_operating_roles_with_evidence",
            "decision_readiness_report_for_human_review",
            "data_sufficiency_assessment",
        ],
        min_records=10,
        recommended_records=1000,
        pilot_duration_hint="2–3 weeks",
        notes="Robot pilot requires continuous telemetry at ≥1 Hz sampling rate.",
    )


def _semiconductor_contract() -> PilotContract:
    return PilotContract(
        domain="semiconductor",
        display_name="Semiconductor Process Pilot",
        organizing_question=_FUNCTIONAL_YIELD_QUESTION,
        input_fields=[
            InputField(
                name="tool_log.csv",
                description=(
                    "Process tool chamber metrics per wafer run. "
                    "v3.0.1 canonical format: rf_power_W, pressure_mTorr, alarm_code."
                ),
                format="csv",
                required=True,
                columns=[
                    "timestamp", "tool_id", "chamber_id", "lot_id", "wafer_id",
                    "step_id", "rf_power_W", "pressure_mTorr", "gas_flow_sccm",
                    "temperature_C", "alarm_code", "run_id",
                ],
                sensitivity="confidential",
                sanitization_notes=(
                    "Remove equipment serial numbers. Normalize tool_id to "
                    "hashed codes (tool_hash_001, tool_hash_002). Do not include IP."
                ),
                minimum_viable_rows=5,
                recommended_rows=500,
                functional_yield_role="evidence_inputs",
            ),
            InputField(
                name="metrology.csv",
                description="Post-process metrology measurements (etch depth, film thickness, uniformity)",
                format="csv",
                required=True,
                columns=[
                    "wafer_id", "step_id", "metric_name", "metric_value",
                    "unit", "measurement_site", "spec_low", "spec_high",
                ],
                sensitivity="confidential",
                sanitization_notes="Wafer IDs must be anonymized to opaque demo IDs.",
                minimum_viable_rows=5,
                recommended_rows=500,
                functional_yield_role="remaining_functions_inputs",
            ),
            InputField(
                name="test_results.csv",
                description="Die-level electrical test results (parametric / functional)",
                format="csv",
                required=False,
                columns=[
                    "wafer_id", "die_id", "test_name", "pass_fail",
                    "bin_code", "die_x", "die_y",
                ],
                sensitivity="confidential",
                sanitization_notes="Remove lot traceability codes; replace with opaque IDs.",
                minimum_viable_rows=5,
                recommended_rows=500,
                functional_yield_role="blocked_functions_inputs",
            ),
        ],
        blocked_claims=_BLOCKED_COMMON + [
            "process_control_recipe_adjustment",
            "lot_disposition_decision",
            "yield_loss_root_cause_certification",
        ],
        evidence_claims=[
            "functional_yield_score_per_process_step",
            "drift_detection_evidence_report",
            "blocked_process_windows_with_evidence",
            "data_sufficiency_for_drift_analysis",
            "decision_readiness_for_human_engineer_review",
        ],
        min_records=5,
        recommended_records=500,
        pilot_duration_hint="1–2 weeks",
        notes=(
            "Process data must cover ≥1 complete wafer lot (25 wafers) per tool. "
            "Metrology must be time-aligned with tool runs."
        ),
    )


def _space_contract() -> PilotContract:
    return PilotContract(
        domain="space",
        display_name="Satellite / Space Asset Pilot",
        organizing_question=_FUNCTIONAL_YIELD_QUESTION,
        input_fields=[
            InputField(
                name="telemetry.csv",
                description="Spacecraft housekeeping telemetry (power, thermal, attitude, comms)",
                format="csv",
                required=True,
                columns=[
                    "timestamp_utc", "spacecraft_id", "battery_soc_pct",
                    "solar_power_w", "bus_voltage_v", "temperature_c",
                    "attitude_error_deg", "comms_snr_db", "fault_flag",
                ],
                sensitivity="internal",
                sanitization_notes=(
                    "Replace spacecraft_id with generic identifier. "
                    "Timestamps must remain intact (orbital analysis depends on time)."
                ),
                minimum_viable_rows=10,
                recommended_rows=2000,
                functional_yield_role="evidence_inputs",
            ),
            InputField(
                name="event_log.csv",
                description="Spacecraft event log: safe-mode entries, anomalies, commands",
                format="csv",
                required=True,
                columns=["timestamp_utc", "event_type", "subsystem", "severity", "description"],
                sensitivity="internal",
                sanitization_notes="Redact command codes; replace with 'CMD_REDACTED'.",
                minimum_viable_rows=3,
                recommended_rows=100,
                functional_yield_role="blocked_functions_inputs",
            ),
            InputField(
                name="mission_config.json",
                description="Mission operational envelope and constraint definitions",
                format="json",
                required=False,
                json_keys=[
                    "mission_id", "orbit_type", "design_life_years",
                    "power_budget_w", "thermal_limits_c", "attitude_accuracy_deg",
                ],
                sensitivity="internal",
                sanitization_notes="Remove mission_id; use a generic placeholder.",
                minimum_viable_rows=1,
                recommended_rows=1,
                functional_yield_role="valid_conditions_inputs",
            ),
        ],
        blocked_claims=_BLOCKED_COMMON + [
            "orbital_maneuver_commands",
            "fault_protection_activation",
            "mission_abort_decision",
        ],
        evidence_claims=[
            "functional_yield_score_per_subsystem",
            "remaining_mission_roles_under_current_conditions",
            "blocked_mission_roles_with_evidence",
            "anomaly_pattern_evidence_report",
            "decision_readiness_for_mission_operations_review",
        ],
        min_records=10,
        recommended_records=2000,
        pilot_duration_hint="2–4 weeks",
        notes=(
            "Telemetry must cover at least 7 consecutive days. "
            "Safe-mode events must be included in event_log."
        ),
    )


def _memory_contract() -> PilotContract:
    return PilotContract(
        domain="memory",
        display_name="NAND/Flash Memory Device Pilot",
        organizing_question=_FUNCTIONAL_YIELD_QUESTION,
        input_fields=[
            InputField(
                name="bad_block_map.csv",
                description="Block-level health map: factory bad, runtime bad, uncorrectable blocks",
                format="csv",
                required=True,
                columns=[
                    "block_id", "is_factory_bad", "is_runtime_bad",
                    "is_uncorrectable", "erase_count", "read_disturb_count",
                    "retention_errors",
                ],
                sensitivity="internal",
                sanitization_notes=(
                    "Device serial numbers must be removed. "
                    "block_id may remain as sequential integer."
                ),
                minimum_viable_rows=10,
                recommended_rows=512,
                functional_yield_role="evidence_inputs",
            ),
            InputField(
                name="ecc_log.csv",
                description="ECC correction event log per page/block over device lifetime",
                format="csv",
                required=True,
                columns=[
                    "timestamp", "block_id", "page_id", "ecc_errors_corrected",
                    "ecc_errors_uncorrectable", "operation_type",
                ],
                sensitivity="internal",
                sanitization_notes="Remove firmware version strings; use 'FW_REDACTED'.",
                minimum_viable_rows=5,
                recommended_rows=100,
                functional_yield_role="blocked_functions_inputs",
            ),
            InputField(
                name="product_bin_rules.json",
                description="Baseline binning policy (pass/fail thresholds per block category)",
                format="json",
                required=False,
                json_keys=["policy_name", "rules", "schema"],
                sensitivity="internal",
                sanitization_notes="No PII present; share as-is.",
                minimum_viable_rows=1,
                recommended_rows=1,
                functional_yield_role="valid_conditions_inputs",
            ),
        ],
        blocked_claims=_BLOCKED_COMMON + [
            "firmware_flash_commands",
            "block_remapping_execution",
            "certified_safe_for_deployment",
        ],
        evidence_claims=[
            "functional_yield_score_per_block_category",
            "reclassified_functional_roles_with_evidence",
            "blocked_block_roles_with_evidence",
            "capacity_recovery_candidate_estimate",
            "decision_readiness_for_human_qa_review",
        ],
        min_records=10,
        recommended_records=512,
        pilot_duration_hint="1 week",
        notes=(
            "Bad block map must reflect current device state (post-wear). "
            "ECC log should cover ≥30 days of operation."
        ),
    )


def _semiforge_contract() -> PilotContract:
    return PilotContract(
        domain="semiforge",
        display_name="SemiForge Fab Simulation Pilot",
        organizing_question=_FUNCTIONAL_YIELD_QUESTION,
        input_fields=[
            InputField(
                name="synthetic_defect_map.json",
                description="Simulated die-level defect map with defect density and type annotations",
                format="json",
                required=True,
                json_keys=[
                    "schema", "wafer_id", "die_count",
                    "defect_density_per_cm2", "defect_map",
                ],
                sensitivity="internal",
                sanitization_notes=(
                    "Synthetic data — no sanitization required. "
                    "Confirm no real fab process parameters embedded."
                ),
                minimum_viable_rows=5,
                recommended_rows=100,
                functional_yield_role="evidence_inputs",
            ),
            InputField(
                name="workload_roles.json",
                description="Definition of functional workload roles the fab can serve",
                format="json",
                required=True,
                json_keys=["schema", "roles"],
                sensitivity="internal",
                sanitization_notes="Role names may be generic; no PII.",
                minimum_viable_rows=1,
                recommended_rows=1,
                functional_yield_role="remaining_functions_inputs",
            ),
            InputField(
                name="routing_constraints.json",
                description="Process routing constraints and inter-step dependencies",
                format="json",
                required=False,
                json_keys=["schema", "steps", "constraints"],
                sensitivity="confidential",
                sanitization_notes=(
                    "Remove proprietary recipe parameters. "
                    "Replace with normalized ranges."
                ),
                minimum_viable_rows=1,
                recommended_rows=1,
                functional_yield_role="valid_conditions_inputs",
            ),
        ],
        blocked_claims=_BLOCKED_COMMON + [
            "real_fab_process_control",
            "tape_out_decision",
            "process_window_qualification",
        ],
        evidence_claims=[
            "functional_yield_score_from_defect_simulation",
            "functional_roles_viable_under_simulated_conditions",
            "blocked_functional_routes_with_evidence",
            "yield_sensitivity_to_defect_density",
            "decision_readiness_for_fab_engineering_review",
        ],
        min_records=5,
        recommended_records=100,
        pilot_duration_hint="3–5 days",
        notes=(
            "SemiForge uses synthetic simulation data only. "
            "No real fab tool data is required for initial pilot."
        ),
    )


class DomainContracts:
    """Registry of all domain PilotContracts."""

    DOMAINS = ("robot", "semiconductor", "space", "memory", "semiforge")

    _registry: dict[str, PilotContract] = {}

    @classmethod
    def _build(cls) -> None:
        if cls._registry:
            return
        cls._registry = {
            "robot": _robot_contract(),
            "semiconductor": _semiconductor_contract(),
            "space": _space_contract(),
            "memory": _memory_contract(),
            "semiforge": _semiforge_contract(),
        }

    @classmethod
    def get(cls, domain: str) -> PilotContract:
        cls._build()
        if domain not in cls._registry:
            raise ValueError(
                f"Unknown domain '{domain}'. "
                f"Valid domains: {', '.join(cls.DOMAINS)}"
            )
        return cls._registry[domain]

    @classmethod
    def all(cls) -> dict[str, PilotContract]:
        cls._build()
        return dict(cls._registry)
