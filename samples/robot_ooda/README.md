# Sample: robot_ooda

**Domain**: Robot Telemetry (RobotOODA)
**Scenario**: Joint J3 showing rising motor current, elevated temperature, and fault code 201 in the final rows of a 15-row telemetry sequence.

---

## What This Sample Represents

A short 15-row robot telemetry sequence. Values are nominal in the early rows, then
motor_current_A and joint_temp_C rise toward the end. The final rows contain
`fault_code = 201`, signaling a detected anomaly at the robot controller.

This sample exercises:
- Trend detection (linear slope significance)
- Fault code detection and evidence generation
- OODA frame construction from robot telemetry
- RecoveryCandidate generation with `human_review_required` mode

---

## Telemetry Columns

| Column | Description |
|--------|-------------|
| `timestamp` | ISO 8601 |
| `joint_id` | e.g. `J3` |
| `motor_current_A` | Motor draw (Amperes) |
| `joint_temp_C` | Joint temperature (Celsius) |
| `imu_vibration_g` | Vibration level (g) |
| `error_count` | Cumulative error count |
| `fault_code` | 0 = nominal; 201 = fault detected |

---

## How to Run

```bash
# Analyze this sample
yieldos robot analyze --input samples/robot_ooda/robot_telemetry.csv --out output/robot_demo

# Or via the unified run command
yieldos run --input samples/robot_ooda/robot_telemetry.csv --domain robot --out output/robot_demo
```

---

## Expected Output

```
output/robot_demo/
  state_snapshot.json     state: fault_candidate  severity: high
  evidence_pack.json      sealed SHA-256 checksum
  ooda_frame.json         act: recommendation_only_no_hardware_action
  recovery_candidates.json  hardware_execution_enabled: false
  report.md
  report.html
```

Typical result:
- `state`: `fault_candidate`
- `severity`: `high`
- `confidence`: ~0.80–0.92
- Root cause candidate: `motor_current_rising_J3` or similar
- Recovery: `recommend_inspection`, `schedule_maintenance`

---

## Larger Dataset

To generate a 500-row dataset with gradual degradation and fault injection:

```bash
yieldos robot gen --out samples/robot_large --samples 500
```

The larger dataset achieves Token Idiot Index ~11x vs the 15-row sample (<1x).

---

## Safety

YieldOS reads the telemetry CSV file only. It does not send ROS commands,
does not send torque or velocity commands, does not trigger calibration sequences,
and does not initiate any robot motion.
