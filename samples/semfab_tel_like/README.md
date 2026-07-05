# Sample: semfab_tel_like

**Domain**: Semiconductor Fab (SemFab)
**Scenario**: STEP_04 process tool showing pressure drift that correlates with CD metrology shift and downstream yield drop.

---

## What This Sample Represents

A 25-row synthetic fab dataset designed to trigger the cross-step RCA logic.
`tool_log.csv` contains gradual pressure drift in `STEP_04` starting at row 15.
The drift correlates with a CD measurement shift in `metrology.csv` and an
elevated yield loss visible in `test_result.csv`.

This sample exercises:
- Sigma-based tool drift detection
- Cross-step causal chain: tool drift -> CD shift -> wafer yield loss
- EvidencePack sealing with SHA-256 checksum
- Missing evidence structuring (request for PM log)

---

## Files

| File | Description |
|------|-------------|
| `tool_log.csv` | 25 rows — tool step, metric, value, timestamp |
| `wafer_map.csv` | Per-wafer defect density by row |
| `metrology.csv` | CD (critical dimension) measurements by lot |
| `test_result.csv` | Functional test pass/fail by wafer |

---

## How to Run

```bash
# From the project root
yieldos semifab analyze --input samples/semfab_tel_like --out output/semfab_demo

# Or via the unified run command
yieldos run --input samples/semfab_tel_like --domain semfab --out output/semfab_demo
```

---

## Expected Output

```
output/semfab_demo/
  state_snapshot.json     state: fault_candidate  severity: high
  evidence_pack.json      sealed SHA-256 checksum
  ooda_frame.json         act: recommendation_only_no_hardware_action
  recovery_candidates.json  hardware_execution_enabled: false
  report.md
  report.html
```

Typical result:
- `state`: `fault_candidate` or `under_investigation`
- `severity`: `high`
- `confidence`: ~0.75–0.90
- Root cause candidate: `pressure_torr_drift` in STEP_04
- Missing evidence: `maintenance_log` (PM history needed to confirm)

---

## Larger Dataset

To generate a 500-row dataset with stronger drift signal:

```bash
yieldos semifab gen --out samples/semfab_large --lots 20 --wafers 5
```

---

## Safety

YieldOS reads these files only. It does not modify them, does not connect
to any fab MES, and does not send equipment commands.
