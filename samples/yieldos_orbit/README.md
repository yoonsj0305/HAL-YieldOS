# YieldOS-Orbit Sample — CubeSat Power Degradation

This sample demonstrates YieldOS shadow analysis on a simulated CubeSat
experiencing progressive solar panel degradation during an LEO mission.

## Scenario

A 3U CubeSat in 500 km LEO shows declining battery SOC and bus voltage
following a solar panel partial obscuration event. HAL YieldOS identifies
power margin degradation and recommends mission profile adjustments.

## Files

| File | Description |
|------|-------------|
| `cubesat_power_degradation.csv` | 120 telemetry samples (2-minute cadence) |
| `mission_profile.json` | Mission parameters and operating envelope |

## CSV Columns

| Column | Unit | Description |
|--------|------|-------------|
| `timestamp` | ISO 8601 | Sample timestamp |
| `battery_soc_pct` | % | Battery state of charge |
| `bus_voltage_V` | V | Power bus voltage |
| `panel_current_A` | A | Solar panel output current |
| `temperature_C` | deg C | On-board temperature |
| `attitude_error_deg` | deg | Attitude control error |
| `gyro_drift_deg_s` | deg/s | Gyroscope drift rate |
| `comms_snr_dB` | dB | Communications SNR |
| `payload_current_A` | A | Payload power draw |
| `fault_flag` | 0/1 | On-board fault indicator |

## Analysis

```bash
yieldos sat orbit-demo --out output/yieldos_orbit
```

## Safety Notice

This is synthetic demonstration data. HAL YieldOS produces shadow analysis
output only. No uplink commands are generated. Human review required.
