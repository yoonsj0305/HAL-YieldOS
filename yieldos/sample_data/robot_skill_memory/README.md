# Robot Skill Memory — Sample Data

HAL YieldOS v2.6.0 Robot Skill Memory MVP sample data.

## Scenario

Robot arm `robot_01` performing payload transport task `task_payload_transport_042`.
The robot experiences gripper instability due to pad wear, leading to slip events and
a human-initiated stop. Operator and maintenance personnel observe and record the
degradation before and after the incident.

**This data is read-only demonstration data.** HAL does not control the robot.
HAL does not certify root cause. All observations are candidate-only.

## Files

| File | Rows | Description |
|---|---|---|
| `robot_telemetry.csv` | 30 | Robot sensor telemetry with standard metrics and skill memory columns |
| `operator_notes.csv` | 3 | Operator field observations (redacted) |
| `maintenance_notes.csv` | 2 | Maintenance technician observations (redacted) |

## Telemetry Columns

Standard (read by RobotAnalyzer):
- `motor_current_A`, `joint_temp_C`, `imu_vibration_g`, `position_error_mm`, `latency_ms`
- `error_count`, `controller_fault_code`

Skill memory (read by RobotSkillMemoryLayer):
- `joint_torque_Nm`, `force_sensor_N`, `gripper_force_N`
- `slip_detected`, `contact_instability`, `payload_kg`
- `surface_type`, `floor_condition`, `lighting_lux`
- `fault_code`, `real_success`, `human_intervention`, `post_intervention_result`

## Safety Boundary

- HAL does not issue robot commands
- HAL does not certify safety or root cause
- All outputs are `candidate_only`, require human review
- `hardware_execution_enabled = false` in all outputs
