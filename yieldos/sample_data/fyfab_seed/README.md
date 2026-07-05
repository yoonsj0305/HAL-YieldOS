# FYFab Seed Sample Data

Synthetic demo data for HAL YieldOS v2.8.0 Functional Yield Fab Seed Edition.

## Purpose

This sample package simulates an imperfect fabricated substrate and provides
input data for the FYFab seed analysis pipeline.

## Files

- `fabricated_structure_grid.csv` — 128-cell synthetic substrate grid (16x8)
- `defect_map.csv` — 18 observed candidate defects across the grid
- `material_regions.csv` — 4 material regions with candidate use classifications
- `target_function_blocks.json` — 2 target functional blocks to map

## Safety Boundary

This data is entirely synthetic. It is not derived from any real fabrication process.

- No real process recipe is represented.
- No real material properties are implied.
- No physical design signoff is expressed or implied.
- No yield guarantee is expressed or implied.
- All outputs from this data are candidate-only and require human review.

## Usage

```bash
yieldos semiforge fyfab-demo --out output/fyfab_seed
yieldos semiforge fyfab-demo --input yieldos/sample_data/fyfab_seed --out output/fyfab_seed
```
