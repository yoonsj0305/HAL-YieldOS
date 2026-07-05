# Robot Industrial Sample Data — HAL YieldOS v2.2.0

Synthetic multi-source industrial robot dataset for shadow analysis demonstration.

## Scenario

An industrial robot arm in a manufacturing cell shows progressive joint degradation
across 3 production shifts. The dataset includes correlated telemetry, maintenance
records, operation logs, and environment monitoring data.

## Files

| File | Description |
|------|-------------|
| `robot_telemetry.csv` | Joint sensor telemetry (200 samples) |
| `maintenance_log.csv` | Scheduled and unscheduled maintenance events |
| `operation_log.csv` | Production cycle and task completion records |
| `environment_log.csv` | Cell temperature and vibration monitoring |

## CSV Columns

### robot_telemetry.csv
| Column | Unit | Description |
|--------|------|-------------|
| `timestamp` | ISO 8601 | Sample time |
| `motor_current_A` | A | Joint motor current draw |
| `joint_temp_C` | deg C | Joint bearing temperature |
| `imu_vibration_g` | g | IMU-measured vibration |
| `position_error_mm` | mm | End-effector position error |
| `latency_ms` | ms | Controller loop latency |
| `fault_code` | int | On-board fault code (0=none) |

### maintenance_log.csv
| Column | Description |
|--------|-------------|
| `timestamp` | Event timestamp |
| `event_type` | scheduled / unscheduled / calibration |
| `component` | Affected component |
| `action_taken` | Description of maintenance action |
| `technician_id` | Technician identifier |
| `outcome` | complete / partial / deferred |

### operation_log.csv
| Column | Description |
|--------|-------------|
| `timestamp` | Cycle timestamp |
| `cycle_id` | Production cycle identifier |
| `task` | Task type (pick / place / weld / inspect) |
| `duration_s` | Cycle duration in seconds |
| `result` | pass / fail / retry |
| `payload_kg` | Payload mass in kg |

### environment_log.csv
| Column | Unit | Description |
|--------|------|-------------|
| `timestamp` | ISO 8601 | Sample timestamp |
| `cell_temp_C` | deg C | Cell ambient temperature |
| `floor_vibration_g` | g | Floor-mounted vibration sensor |
| `humidity_pct` | % | Relative humidity |

## Safety Notice

This is synthetic demonstration data. HAL YieldOS produces shadow analysis output
only. No robot commands are generated. Human review required before any action.
