# Robot Data Schema Guide

HAL YieldOS v3.0.11 - External Robot Log Package Schema

---

## Overview

External robot log packages are folders containing CSV files that YieldOS can check for
readiness via `yieldos robot import-check` and then analyze via `yieldos robot skill-demo`.

All files must be pre-anonymized. No personal information is permitted.

---

## Required Files

### 1. `robot_telemetry.csv`

Timestamped telemetry from the robot controller.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `timestamp` | ISO datetime | Yes | Event time |
| `robot_id` | string | Yes | Anonymized robot identifier |
| `task_id` | string | Yes | Task or trial identifier |
| `fault_code` | string/int | Yes | Controller fault code (NONE if no fault) |
| `real_success` | bool | Yes | Whether the task completed successfully |
| `human_intervention` | bool | Yes | Whether a human intervened during this event |
| `post_intervention_result` | string | Yes | Outcome after intervention (empty if none) |
| `motor_current_A` | float | No | Motor current reading |
| `joint_temp_C` | float | No | Joint temperature |
| `joint_torque_Nm` | float | No | Joint torque |
| `force_sensor_N` | float | No | End-effector force |
| `gripper_force_N` | float | No | Gripper force |
| `slip_detected` | bool | No | Whether slip was observed |
| `contact_instability` | bool | No | Whether contact instability was observed |
| `payload_kg` | float | No | Payload mass |
| `surface_type` | string | No | Surface type (e.g. rubber_mat) |
| `floor_condition` | string | No | Floor condition (clean/wet/dusty) |
| `lighting_lux` | float | No | Ambient light level |

**Forbidden columns** (must not appear):
`operator_name`, `employee_id`, `phone_number`, `email`, `home_address`,
`face_image`, `voice_recording`, `biometric_id`, `raw_biometric_id`

---

### 2. `operator_notes.csv`

Pre-redacted operator observations. No raw text is permitted.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `timestamp` | ISO datetime | Yes | Observation time |
| `operator_id_hash` | string | Yes | Anonymized operator identifier (hash, not real ID) |
| `robot_id` | string | Yes | Robot identifier |
| `task_id` | string | Yes | Task identifier |
| `note_type` | string | Yes | Observation category |
| `note_text_redacted` | string | Yes | Pre-redacted text (no real names or locations) |
| `redaction_status` | string | Yes | Redaction state: `demo_safe`, `redacted`, `reviewed` |
| `contains_personal_data` | bool | Yes | Must be `false` for all rows in the package |
| `suspected_signal` | string | No | Candidate signal name |
| `observed_context` | string | No | Context description |
| `confidence` | float | No | Operator confidence (0-1) |

---

### 3. `maintenance_notes.csv`

Pre-redacted maintenance technician observations.

Same required columns as `operator_notes.csv`, except `operator_id_hash` is replaced by
`technician_id_hash`.

---

## Optional Files

### 4. `sim_expectation.csv`

Simulation-expected values per task_id. Enables sim-to-real gap analysis.

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `task_id` | string | Yes | Task identifier |
| `sim_expected_success` | bool | Yes | Whether the simulator predicted success |
| `expected_payload_kg` | float | No | Expected payload |
| `expected_surface_type` | string | No | Expected surface type |
| `expected_max_joint_torque_Nm` | float | No | Expected maximum joint torque |
| `expected_max_force_sensor_N` | float | No | Expected maximum force |
| `expected_min_gripper_force_N` | float | No | Expected minimum gripper force |

---

## Schema Validation

Run import-check before analysis:

```bash
yieldos robot import-check \
  --input /path/to/external_robot_log_package \
  --out /path/to/output/import_check

yieldos inspect-output /path/to/output/import_check
```

Possible `schema_status` values:
- `PASSED` ??all required files and columns present
- `PASSED_WITH_WARNINGS` ??required files present but some columns missing
- `FAILED` ??one or more required files missing

Possible `privacy_status` values:
- `PASSED` ??no sensitive columns detected, no rows with `contains_personal_data=true`
- `PASSED_WITH_WARNINGS` ??sensitive columns detected or rows flagged

---

## Safety Boundary

- `hardware_execution_enabled: false` ??always
- `human_review_required: true` ??always
- `candidate_only: true` ??always
- YieldOS does not control robots, issue commands, or certify root cause
