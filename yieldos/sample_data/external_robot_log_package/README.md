# External Robot Log Package — Sample

This is a synthetic demo package for testing `yieldos robot import-check`.

## Contents

- `robot_telemetry.csv` — 20 rows, robot_02, task_arm_motion_087
- `operator_notes.csv` — 2 pre-redacted operator observations
- `maintenance_notes.csv` — 2 pre-redacted maintenance observations
- `sim_expectation.csv` — simulation expectations for task_arm_motion_087

## Data Rules

- All data is synthetic.
- No personal information is included.
- operator_id_hash and technician_id_hash are anonymized hashes.
- robot_id (robot_02) is an anonymized identifier, not a real serial number.
- note_text_redacted contains only pre-redacted text.

## Usage

```bash
yieldos robot import-check \
  --input yieldos/sample_data/external_robot_log_package \
  --out output/import_check

yieldos robot skill-demo \
  --input yieldos/sample_data/external_robot_log_package \
  --out output/robot_skill_external
```

## Safety Boundary

This sample is for read-only analysis only.
YieldOS does not control robots or certify root cause.
