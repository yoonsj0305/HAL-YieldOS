# HAL YieldOS — Memory Device Sample Data

This directory contains synthetic memory block health data for the Memory Functional Yield domain.

## Files

- `block_health.csv` — 128 simulated NAND flash blocks with health metrics
- `device_info.json` — Device configuration and policy thresholds

## Schema

### block_health.csv columns

| Column | Required | Description |
|--------|----------|-------------|
| block_id | yes | Unique block identifier (e.g. B0000) |
| block_size_gb | yes | Block size in GB |
| is_factory_bad | yes | Factory bad block flag (true/false) |
| is_runtime_bad | yes | Runtime bad block flag (true/false) |
| corrected_error_count | yes | Total ECC-corrected errors |
| uncorrectable_error_count | yes | Uncorrectable ECC errors |
| pe_cycles | recommended | Program-Erase cycle count |
| max_pe_cycles | recommended | Rated maximum PE cycles |
| retention_hours | recommended | Estimated data retention hours |
| min_retention_hours | recommended | Minimum retention spec |
| temperature_C | recommended | Operating temperature |
| read_count | optional | Total reads |
| write_count | optional | Total writes |
| last_scrub_age_hours | optional | Hours since last ECC scrub |

### device_info.json

Defines policy thresholds for block classification:
- `ecc_policy.corrected_error_warning_threshold` — corrected errors per block above this = at-risk
- `ecc_policy.uncorrectable_error_fail_threshold` — any uncorrectable errors = discard
- `endurance_policy.pe_cycle_warning_ratio` — PE cycle fraction above this = endurance warning
- `retention_policy.min_retention_hours` — minimum acceptable retention

## Classification output

Blocks are classified into:
- **safe** — no degradation signals
- **approximate_cache** — elevated ECC or poor retention; recomputable data only
- **read_only_archive** — write endurance degraded; read access only
- **at_risk** — general degradation not fitting other categories
- **discard** — factory/runtime bad or uncorrectable errors

## Safety

All outputs are candidate estimates requiring human review.
This data does **not** modify device firmware, controller settings, or block mapping.
No user data is stored, moved, or certified.

## Usage

```bash
yieldos memory analyze --input samples/memory_device --out output/memory --asset memdev_01
yieldos validate --case output/memory --strict
```
