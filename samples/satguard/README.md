# Sample: satguard

**Domain**: Satellite Telemetry (SatGuard)
**Scenario**: LEO satellite with battery state-of-charge dropping to 12% (below nominal 20% floor) in a 15-row telemetry sequence.

---

## What This Sample Represents

A short 15-row satellite telemetry sequence. Battery SoC starts at nominal levels
and degrades across the sequence, breaching the minimum threshold in the final rows.
The attitude error metric is nominal throughout. Mission readiness is computed as a
penalty-weighted composite of all monitored metrics.

This sample exercises:
- Multi-metric threshold monitoring (two-sided and one-sided)
- `high_is_bad` directional logic (battery SoC: low breach; attitude_error: high breach)
- Mission readiness computation
- EvidencePack construction from satellite telemetry

---

## Telemetry Columns

| Column | Threshold type | Normal range |
|--------|---------------|--------------|
| `timestamp` | — | ISO 8601 |
| `battery_soc_pct` | Two-sided (low breach matters) | 20% – 95% |
| `bus_voltage_V` | Two-sided | 27V – 32V |
| `solar_panel_current_A` | Two-sided | 0.8A – 3.5A |
| `attitude_error_deg` | One-sided (`high_is_bad=True`) | < 0.5 deg |
| `gyro_drift_deg_s` | One-sided (`high_is_bad=True`) | < 0.02 deg/s |
| `transmitter_temp_C` | Two-sided | -10C – 50C |
| `comms_rssi_dBm` | One-sided (`high_is_bad=False`, low breach) | > -85 dBm |
| `fault_flag` | — | 0 = nominal |

---

## How to Run

```bash
# Analyze this sample
yieldos sat analyze --input samples/satguard/satellite_telemetry.csv --out output/sat_demo

# Or via the unified run command
yieldos run --input samples/satguard/satellite_telemetry.csv --domain sat --out output/sat_demo
```

---

## Expected Output

```
output/sat_demo/
  state_snapshot.json     state: fault_candidate  severity: high
  evidence_pack.json      sealed SHA-256 checksum
  ooda_frame.json         act: recommendation_only_no_hardware_action
  recovery_candidates.json  hardware_execution_enabled: false
  report.md
  report.html
```

Typical result:
- `state`: `fault_candidate`
- `severity`: `high` (battery below minimum)
- `mission_readiness`: ~0.65–0.75
- Root cause candidate: `battery_soc_breach` (confidence ~0.85)
- Recovery: `reduce_operating_parameter`, `schedule_human_review`

---

## Larger Dataset

To generate a 500-row dataset with gradual LEO orbital degradation:

```bash
yieldos sat gen --out samples/sat_large --samples 500
```

The larger dataset achieves Token Idiot Index ~12x vs the 15-row sample (<1x).

---

## Safety

YieldOS reads the telemetry CSV file only. It does not send uplink commands,
does not switch operational modes, does not command payload instruments,
does not trigger attitude maneuvers, and does not issue any command to the spacecraft.
