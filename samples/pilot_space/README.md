# Pilot Sample — Satellite / Space Asset

Sample input data for `yieldos pilot check --domain space`.

## Files

| File | Description |
|------|-------------|
| `telemetry.csv` | Housekeeping telemetry (15 hourly records) |
| `event_log.csv` | Safe-mode event, power anomaly, recovery sequence |
| `mission_config.json` | Generic mission operational envelope |

## Usage

```bash
# Check readiness
yieldos pilot check \
  --domain space \
  --input samples/pilot_space \
  --out output/pilot_check_space
```

## Notes

- Power anomaly and safe-mode sequence visible at 10:00–13:00 UTC.
- Solar array degradation event with recovery.
- Full pilot requires ≥ 200 telemetry records spanning ≥ 7 days.
- spacecraft_id is anonymized (SC_001). mission_id replaced with generic.
