# HAL YieldOS — Sample Data Notice

## Important Notice

All sample data included in HAL YieldOS is **synthetic/demo data**.

Sample data does **not** represent:
- Real customer data
- Real industrial operations data
- Real fab production data
- Real robot fleet telemetry
- Real satellite operation data
- Any specific customer's equipment or process

---

## Included Sample Data

### SemFab Sample (`samples/semfab_tel_like/`)

Synthetic data modeled after semiconductor fab telemetry structure.
- `tool_log.csv` — synthetic tool process log
- `wafer_map.csv` — synthetic wafer yield map
- `metrology.csv` — synthetic metrology measurements
- `test_result.csv` — synthetic test results
- `lot_genealogy.csv` — synthetic lot genealogy

**This is not real fab data from any manufacturer.**

### SemiForge Sample (`samples/semiforge_crossbar/`)

Synthetic crossbar compute array configuration.
- `config.json` — array parameters for defect simulation

**This is a synthetic configuration, not a real device specification.**

### Robot Sample (`samples/robot_ooda/`)

Synthetic robot telemetry data.
- `robot_telemetry.csv` — synthetic joint, vibration, and latency data

**This is not real robot fleet data from any manufacturer or operator.**

### Satellite Sample (`samples/satguard/`)

Synthetic satellite telemetry data.
- `satellite_telemetry.csv` — synthetic power, thermal, attitude, and comms data

**This is not real satellite operation data from any operator or agency.**

---

## Synthetic Data Generation

HAL YieldOS includes synthetic data generators for testing and demonstration:

```bash
# Semiconductor fab (semfab)
yieldos semifab gen --out output/generated_semfab --lots 20 --wafers 5

# Robot
yieldos robot gen --out output/generated_robot --samples 500

# Space / satellite
yieldos sat gen --out output/generated_sat --samples 500

# SemiForge: run simulation with default config (no separate gen needed)
yieldos semiforge simulate --config samples/semiforge_crossbar/config.json --out output/generated_semiforge
```

These generated datasets are for PoC and testing purposes only.

Bundled sample data is included in the installed package at `yieldos/sample_data/`.
No external `samples/` directory is required after `pip install hal-yieldos`.
Large datasets are not included in the package and are managed as future release assets.

---

## Intended Use of Sample Data

Sample data is provided to:
1. Demonstrate the CLI and analysis pipeline
2. Enable `pytest` and `yieldos demo` validation
3. Show output format and structure
4. Allow evaluation without real customer data

---

## For Real Data Integration

To integrate real data with HAL YieldOS:
1. Prepare data in the same CSV column format as the corresponding sample files
2. Point the CLI to the real data directory or file
3. All safety boundaries remain enforced regardless of input data source
4. Human review is required before any operational action

For column schema details, see the `README.md` in each sample directory.
