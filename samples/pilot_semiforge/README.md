# Pilot Sample — SemiForge Fab Simulation

Sample input data for `yieldos pilot check --domain semiforge`.

## Files

| File | Description |
|------|-------------|
| `synthetic_defect_map.json` | Simulated die-level defect map (11 dies, synthetic) |
| `workload_roles.json` | 4 functional workload role definitions |
| `routing_constraints.json` | 5-step process routing with constraints |

## Usage

```bash
# Check readiness
yieldos pilot check \
  --domain semiforge \
  --input samples/pilot_semiforge \
  --out output/pilot_check_semiforge
```

## Notes

- All data is synthetic simulation output — no real fab parameters.
- Die 3 and Die 7 are non-functional (2+ defects).
- Full pilot requires ≥ 10 die entries (100+ recommended).
- No sanitization required (synthetic data only).
