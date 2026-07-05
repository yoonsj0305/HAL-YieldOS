# FYFab Seed Expected Outputs Summary

Expected outputs from `yieldos semiforge fyfab-demo --out output/fyfab_seed`.

## Standard Output Bundle (22 files)

All standard YieldOS output files are generated.

## FYFab-Specific Outputs (7 files)

| File | Description |
|------|-------------|
| `fabricated_structure_map.json` | Grid summary (128 cells, 4 regions) |
| `defect_map_summary.json` | 18 defects, 2 blocked cells |
| `usable_cell_classification.json` | Cell classifications by candidate role |
| `candidate_functional_regions.json` | Grouped candidate regions |
| `reconfiguration_candidate_map.json` | Candidate mappings to target blocks |
| `functional_yield_chip_passport.json` | Chip-level functional passport |
| `fyfab_case_study.json` | FYFab pipeline case study |

## Safety Invariants

- `hardware_execution_enabled: false` in all outputs
- `human_review_required: true` in all outputs
- `candidate_only: true` in all relevant outputs
- No fabrication control claims
- No physical design signoff claims
- No timing closure claims
- No yield guarantee claims
