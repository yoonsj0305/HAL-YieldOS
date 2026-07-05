# Sample: semiforge_crossbar

**Domain**: Defect-Tolerant Computing (SemiForge)
**Scenario**: 64x64 ReRAM crossbar array with 12% clustered defect rate. Monte Carlo simulation estimates functional yield and effective cost.

---

## What This Sample Represents

A crossbar array configuration at a moderately high defect rate with clustered
(non-uniform) defect distribution. Clustered defects reduce percolation connectivity
more severely than IID (independent) defects at the same defect rate, leading to a
lower functional yield than naive estimates suggest.

This sample exercises:
- Clustered defect map generation
- Percolation connectivity (union-find, r_conn)
- Functional yield: Y_func = r_conn x r_alg
- Effective cost: C_eff = (C_fab + C_ctrl + C_rec) / Y_func

---

## Config

```json
{
  "asset_id": "crossbar_64x64_ReRAM",
  "array_rows": 64,
  "array_cols": 64,
  "defect_rate": 0.12,
  "defect_distribution": "clustered",
  "clustering_factor": 3.0,
  "baseline_accuracy": 0.92,
  "c_fab": 1.0,
  "c_ctrl": 0.15,
  "c_rec": 0.10
}
```

---

## How to Run

```bash
# Default 30 Monte Carlo runs
yieldos semiforge simulate --config samples/semiforge_crossbar/config.json --out output/forge_demo

# More runs for better statistics
yieldos semiforge simulate --config samples/semiforge_crossbar/config.json --out output/forge_demo --mc 100

# Y_func vs defect_rate sweep
yieldos semiforge sweep --out output/forge_sweep --rows 64 --cols 64 --dist clustered --mc 30

# Or via the unified run command
yieldos run --input samples/semiforge_crossbar/config.json --domain semiforge --out output/forge_demo
```

---

## Expected Output

```
output/forge_demo/
  state_snapshot.json     state: degraded or fault_candidate
  evidence_pack.json      sealed SHA-256 checksum
  ooda_frame.json         act: recommendation_only_no_hardware_action
  recovery_candidates.json
  functional_yield.json   Y_func vs defect_rate curve (if sweep)
  report.md
  report.html
```

Typical result at 12% clustered:
- `r_conn`: ~0.70–0.80 (connectivity fraction)
- `y_func`: ~0.65–0.75 (functional yield)
- `c_eff`: ~1.7–1.9x the baseline fab cost
- `severity`: `medium` or `high` depending on r_conn value

---

## Safety

YieldOS runs offline Monte Carlo simulation on the supplied config only.
It does not write to any crossbar hardware, does not reconfigure routing tables,
and does not modify firmware parameters.
