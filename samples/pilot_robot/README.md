# Pilot Sample — Industrial Robot

Sample input data for `yieldos pilot check --domain robot`.

## Files

| File | Description |
|------|-------------|
| `robot_telemetry.csv` | Joint health telemetry (18 rows, truncated sample) |
| `operator_notes.csv` | Operator observations during shift |
| `maintenance_log.csv` | Recent maintenance history |

## Usage

```bash
# Check readiness
yieldos pilot check \
  --domain robot \
  --input samples/pilot_robot \
  --out output/pilot_check_robot
```

## Notes

- J4 shows elevated vibration and position error in this sample.
- Full pilot requires ≥ 100 records at ≥ 1 Hz sampling rate.
- This sample is anonymized synthetic data for demonstration only.
