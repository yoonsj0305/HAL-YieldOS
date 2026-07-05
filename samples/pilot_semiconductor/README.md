# samples/pilot_semiconductor/

HAL YieldOS v3.0.1 - Semiconductor Pilot-Ready Pack sample data.

## Contents

Required inputs:
- tool_log.csv: 20 rows of tool/chamber/process telemetry
- metrology.csv: 20 rows of metrology measurements
- test_results.csv: 20 rows of die test results

Optional inputs:
- wafer_map.csv: spatial die layout with bin codes and region IDs
- lot_genealogy.csv: lot/wafer lineage and tool/chamber routing
- chamber_log.csv: chamber state and maintenance events
- recipe_context_redacted.json: redacted recipe step context (no sensitive values)
- inspection_notes.csv: structured operator/engineer observations
- chip_tile_map.json: 4x4 tile map with usable/weak/defective/unknown classification
- workload_roles.json: 3 candidate workload roles for compiler intake preview
- recovery_constraints.json: simulation-only constraints for compiler intake preview

## Safety Boundaries

- hardware_control_enabled: false
- human_review_required: true
- claim_boundary: candidate_only

## Redaction Policy

All IDs in this sample are synthetic:
- lot_demo, wafer_demo_*, die_*: synthetic identifiers
- tool_hash_*, chamber_hash_*, recipe_hash_*, reviewer_hash_*: anonymized hashes
- No real process parameters, recipe values, or proprietary metrology data.

## Purpose

This sample demonstrates the semiconductor pilot-pack pipeline.
YieldOS reads this data to produce a Functional Yield evidence report.
It does not control tools, modify recipes, certify root cause, or guarantee yield.