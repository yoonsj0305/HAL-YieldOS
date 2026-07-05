# HAL YieldOS — Robot Pilot-Ready Edition (v3.0.0)

## Overview

v3.0.0 introduces the **Robot Pilot-Ready** pipeline: a structured, evidence-driven path to determine which robot operating roles can function under current conditions, which must be blocked, and under what valid conditions.

This document describes the new `yieldos robot pilot-pack` command, its canonical data schema, and the 9-file output bundle.

---

## Core Principle

> "What can still function, what must be blocked, under what valid conditions, and based on what evidence?"

HAL YieldOS is a **read-only, evidence-collection layer**. It never issues hardware commands, never autonomously deploys robots, and never certifies safety. All outputs require human review before any operational decision.

---

## Quick Start

```bash
# Run the robot pilot-pack pipeline
yieldos robot pilot-pack \
  --input samples/pilot_robot \
  --out output/robot_pilot_pack \
  --asset my_robot_unit_01
```

### Required Input Files

Place these 6 CSV files in your input directory:

| File | Purpose |
|------|---------|
| `robot_telemetry.csv` | Joint health telemetry (canonical v3.0.0 schema) |
| `maintenance_log.csv` | Part replacements, calibrations, inspections |
| `operator_notes.csv` | Human observations, fault records, remarks |
| `sim_expectation.csv` | Simulation baseline for deviation analysis |
| `intervention_log.csv` | Human intervention events during operation |
| `force_torque_log.csv` | Force/torque sensor readings per joint |

---

## Canonical Robot Telemetry Schema (v3.0.0)

`robot_telemetry.csv` must contain the following columns:

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `timestamp` | string | ISO 8601 | Event timestamp |
| `robot_id` | string | — | Robot unit identifier |
| `task_id` | string | — | Task/mission identifier |
| `joint_id` | string | — | Joint identifier (J1, J4, J6, …) |
| `motor_current_A` | float | Amperes | Motor drive current |
| `joint_temp_C` | float | °C | Joint temperature |
| `imu_vibration_g` | float | g | IMU vibration magnitude |
| `position_error_mm` | float | mm | Position tracking error |
| `latency_ms` | float | ms | Controller loop latency |
| `controller_fault_code` | int | — | Fault code (0 = no fault) |
| `error_count` | int | — | Cumulative error count |
| `force_sensor_N` | float | Newtons | End-effector force |
| `gripper_force_N` | float | Newtons | Gripper clamping force |
| `slip_detected` | int | 0/1 | Slip event flag |
| `contact_instability` | int | 0/1 | Contact instability flag |
| `payload_kg` | float | kg | Current payload mass |
| `surface_type` | string | — | Contact surface type |
| `floor_condition` | string | — | Floor state (dry/damp/wet) |
| `lighting_lux` | int | lux | Ambient lighting level |
| `real_success` | int | 0/1 | Task outcome |
| `human_intervention` | int | 0/1 | Intervention required flag |

**Minimum viable rows**: 10 (for READY status). Recommended: 1000+.

---

## Field Alias Support

If your existing telemetry uses legacy column names, the pilot-pack command automatically detects and maps them:

| Legacy Column | Canonical Column | Unit Conversion |
|--------------|-----------------|----------------|
| `temperature_c` | `joint_temp_C` | none |
| `vibration_rms` | `imu_vibration_g` | none |
| `position_error_deg` | `position_error_mm` | × 17.4533 (1 m arm) |
| `current_a` | `motor_current_A` | none |
| `latency` | `latency_ms` | none |
| `fault_code` | `controller_fault_code` | none |
| `errors` | `error_count` | none |

The `robot_field_mapping_report.json` output records every alias that was applied.

---

## Output Bundle (9 Files)

### Standard YieldOS Outputs (4 files)

| File | Contents |
|------|---------|
| `state_snapshot.json` | Functional yield bin, remaining/blocked roles |
| `evidence_pack.json` | Evidence inventory with source references |
| `functional_passport.json` | Role-level pilot eligibility |
| `case_manifest.json` | Run metadata and file inventory |

### Robot Pilot-Specific Outputs (5 JSON files)

| File | Contents |
|------|---------|
| `robot_pilot_readiness_report.json` | Overall readiness score and status |
| `robot_evidence_completeness_report.json` | Per-file evidence gap analysis |
| `robot_role_reclassification_report.json` | Role eligibility decisions per task |
| `robot_valid_conditions_report.json` | Boundary conditions per remaining role |
| `robot_human_review_packet.json` | Structured checklist for human reviewer |
| `robot_missing_evidence_request.json` | Prioritized list of missing evidence |
| `robot_unit_normalization_report.json` | Unit range validation per column |
| `robot_field_mapping_report.json` | Alias/conversion log (if aliases applied) |

### Summary Output (1 Markdown file)

| File | Contents |
|------|---------|
| `robot_pilot_case_summary.md` | Human-readable pilot case summary |

---

## Canonical Robot Operating Roles

The pipeline evaluates evidence across 8 robot operating roles:

| Role | Description |
|------|------------|
| `inspection_only_mode` | Visual/sensor inspection with no physical contact |
| `remote_supervised_mode` | Teleoperated with human-in-the-loop |
| `payload_transport` | Moving loads along defined paths |
| `high_speed_motion` | High-velocity motion sequences |
| `human_nearby_operation` | Operating in shared human workspace |
| `precision_placement` | Fine positioning and assembly |
| `background_diagnostics` | Self-monitoring and health checks |
| `recovery_observation_only` | Observing recovery scenarios without actuation |

---

## Safety Boundaries (Hard-Coded, Non-Negotiable)

Every output from the pilot-pack pipeline enforces these invariants:

```json
{
  "hardware_execution_enabled": false,
  "human_review_required": true,
  "candidate_only": true,
  "autonomous_action_blocked": true,
  "human_approval_required_before_any_deployment": true
}
```

These values **cannot be overridden** by input data, configuration, or command-line flags.

The `cmd_validate --strict` command verifies these boundaries in any output directory containing a `robot_pilot_readiness_report.json`.

---

## Readiness Status Values

| Status | Meaning |
|--------|---------|
| `PILOT_READY` | All evidence present and within normal ranges |
| `PARTIAL_PILOT_READY` | Evidence present but gaps identified |
| `NOT_PILOT_READY` | Critical evidence missing or out of range |

---

## Validation

```bash
# Validate a pilot-pack output directory
yieldos validate --input output/robot_pilot_pack --strict
```

Strict validation checks:
- All 8 pilot-pack output files exist
- `hardware_execution_enabled: false` in readiness report
- `human_review_required: true` in readiness report
- No forbidden terms (`autonomously deployed`, `hardware control enabled`, etc.)

---

## What This Is NOT

- Not a safety certification system
- Not a real-time control interface
- Not a predictive maintenance scheduler
- Not an autonomous decision-making engine

HAL YieldOS produces **evidence for human review**. All operational decisions remain with qualified human operators.

---

*HAL YieldOS v3.0.0 — Robot Pilot-Ready Edition*
*"What can still function, what must be blocked, under what valid conditions, and based on what evidence?"*
