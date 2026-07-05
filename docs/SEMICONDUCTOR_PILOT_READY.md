# HAL YieldOS ??Semiconductor Pilot-Ready Edition (v3.0.11)

## What This Does

`yieldos semiconductor pilot-pack` classifies die, regions, and roles from semiconductor fab data (tool logs, metrology, test results) and generates evidence-backed reports for human review. It answers:

> **"What can still function, what must be blocked, under what valid conditions, and based on what evidence?"**

It does NOT generate recovery profiles, execute recipes, control equipment, or certify root causes.

---

## Quick Start

```bash
yieldos semiconductor pilot-pack \
  --input samples/pilot_semiconductor \
  --out output/semiconductor_pilot_pack
```

Optional arguments:

| Flag | Default | Description |
|------|---------|-------------|
| `--asset` | `chip_demo_001` | Asset ID stamped on all reports |
| `--case` | auto (lot_{asset}) | Case ID for this pilot run |

---

## Input Directory Structure

Place these files in your input directory:

### Required (missing any ??PARTIAL or NOT_READY status)

| File | Description |
|------|-------------|
| `tool_log.csv` | Tool run log with columns: `timestamp`, `tool_id`, `chamber_id`, `lot_id`, `wafer_id`, `step_id`, `rf_power_W`, `pressure_mTorr`, `gas_flow_sccm`, `temperature_C`, `alarm_code`, `run_id` |
| `metrology.csv` | Metrology measurements: `wafer_id`, `step_id`, `metric_name`, `metric_value`, `unit`, `measurement_site`, `spec_low`, `spec_high` |
| `test_results.csv` | Die test results: `wafer_id`, `die_id`, `test_name`, `pass_fail`, `bin_code`, `die_x`, `die_y` |

### Optional (presence improves evidence completeness score and unlocks reports)

| File | Effect when present |
|------|---------------------|
| `wafer_map.csv` | Enables spatial region classification in functional_region_map |
| `lot_genealogy.csv` | Adds lot traceability to evidence |
| `chamber_log.csv` | Adds chamber-level process context |
| `inspection_notes.csv` | Adds inspection evidence to completeness |
| `recipe_context_redacted.json` | Adds redacted process context (no recipe execution) |
| `chip_tile_map.json` | Enables tile-level region map; required for READY compiler handoff |
| `workload_roles.json` | Maps tiles to compute roles; required for READY compiler handoff |
| `recovery_constraints.json` | Defines recovery constraints; required for READY compiler handoff |

---

## Output Files (Full YieldOS Case Bundle + 15 Pilot-Specific Files)

The `semiconductor pilot-pack` command generates a **full standard YieldOS case bundle** (22+ standard files) plus the 15 semiconductor pilot-specific outputs listed below. This means you get the complete YieldOS evidence package ??state_snapshot, evidence_pack, ooda_frame, report.html, functional_passport, case_manifest, and all other standard outputs ??in addition to the pilot-specific reports.

### Pilot-Specific Reports (15 total): 13 JSON reports + 1 field mapping report (conditional) + 1 MD summary.

### Core Reports

| File | Description |
|------|-------------|
| `semiconductor_evidence_completeness_report.json` | Evidence score (0.0-1.0), file-by-file completeness |
| `semiconductor_wafer_die_summary.json` | Total die, pass/fail/bin counts, candidate remaining/blocked die lists |
| `semiconductor_functional_region_map.json` | Per-region classification: candidate_remaining / candidate_blocked / unknown |
| `semiconductor_role_candidate_map.json` | 8 canonical roles ??remaining / reduced / blocked with evidence rationale |
| `semiconductor_valid_conditions_report.json` | Per-role valid operating conditions and what_not_to_do list |
| `semiconductor_process_evidence_report.json` | Candidate process signals and correlations (not root-cause claims) |
| `semiconductor_human_review_packet.json` | Reviewer checklist: review_questions, candidate_decisions, forbidden_decisions |
| `semiconductor_missing_evidence_request.json` | Evidence gaps with why_needed_for_functional_yield |
| `semiconductor_pilot_readiness_report.json` | Overall gate: PILOT_READY / PARTIAL_PILOT_READY / NOT_PILOT_READY (scored 0.0-1.0) |

### Recovery Compiler Handoff Reports

| File | Description |
|------|-------------|
| `semiconductor_recovery_compiler_intake_preview.json` | handoff_status: READY/PARTIAL/NOT_READY ??candidate inputs only, no recovery_profile |
| `semiconductor_recovery_compiler_handoff_boundary.json` | Explicit boundary: what YieldOS does vs. what the Recovery Compiler does |
| `semiconductor_recovery_compiler_export.json` | **(v3.0.5)** Candidate-only export artifact for offline HAL Recovery Compiler testing ??not a recovery profile. human review required before compiler execution. |
| `semiconductor_handoff_manifest.json` | **(v3.0.5)** Authorized handoff file set and conditions for hal-recovery-compiler. Lists forbidden_files (recovery_profile.json etc.). |

### Summary

| File | Description |
|------|-------------|
| `semiconductor_pilot_case_summary.md` | Plain-language summary for human reviewers |
| `semiconductor_field_mapping_report.json` | Field alias remapping applied (only if aliases were detected) |

---

## 8 Canonical Semiconductor Roles

| Role | Description |
|------|-------------|
| `high_speed_compute` | High-performance compute die (fully passing) |
| `low_power_compute` | Low-power compute (reduced-capacity) |
| `cache_assist` | Cache-assist die |
| `background_diagnostics` | Diagnostic and monitoring functions |
| `redundancy_pool` | Spare/redundancy pool |
| `low_priority_batch` | Low-priority batch processing |
| `inspection_only_bin` | Inspection-only, not usable for compute |
| `recovery_candidate_region` | Regions with recovery potential (blocked pending review) |

---

## Recovery Compiler Handoff Status

| Status | Meaning |
|--------|---------|
| `READY_FOR_OFFLINE_COMPILER_TEST` | chip_tile_map + workload_roles + recovery_constraints all present |
| `PARTIAL_FOR_OFFLINE_COMPILER_TEST` | 1-2 of the 3 recovery inputs present |
| `NOT_READY_FOR_COMPILER_HANDOFF` | None of the 3 recovery inputs present |
| `INVALID_COMPILER_INTAKE` | Inputs present but structurally invalid |

YieldOS **never generates `recovery_profile.json`**. Only the Recovery Compiler (a separate system) does.

---

## Safety Invariants (Hard-coded, Non-Negotiable)

All 11 reports always contain:

```json
{
  "hardware_control_enabled": false,
  "human_review_required": true
}
```

These fields cannot be overridden by input data, CLI flags, or configuration.

---

## Strict Validation

```bash
yieldos validate --strict output/semiconductor_pilot_pack
```

Auto-detects semiconductor pilot-pack outputs and checks:
- All 14 required output files present (including v3.0.5: export + handoff_manifest)
- `hardware_control_enabled=false` and `human_review_required=true` on all reports
- `handoff_status` is a valid enum value
- `recovery_profile.json` is **not** generated
- `forbidden_handoff` list is non-empty in handoff boundary
- Human review packet has `review_questions` and `forbidden_decisions`
- No forbidden terms in non-boundary-statement context
- **(v3.0.5)** `functional_passport.semiconductor_pilot_context` has all required refs
- **(v3.0.5)** `decision_readiness_report` has `allowed_decisions` and `forbidden_decisions` lists, `automatic_decision_enabled=false`
- **(v3.0.5)** `state_snapshot.snapshot_type=semiconductor_pilot_candidate_state`, `safety.recovery_profile_generated=false`
- **(v3.0.5)** `semiconductor_recovery_compiler_export.json`: `recovery_profile_generated=false`, `compiler_project=hal-recovery-compiler`, valid `export_status`
- **(v3.0.5)** `semiconductor_handoff_manifest.json`: `forbidden_files` includes `recovery_profile.json`, `allowed_files` includes export

---

## Field Alias Mapping

If your `tool_log.csv` uses legacy column names, YieldOS auto-detects and remaps:

| Legacy Name | Canonical Name |
|-------------|----------------|
| `alarm_flag` | `alarm_code` |
| `chamber_pressure_torr` | `pressure_mTorr` |
| `chamber` | `chamber_id` |
| `lot` | `lot_id` |
| `wafer` | `wafer_id` |
| `step` | `step_id` |

A `semiconductor_field_mapping_report.json` is written when remapping occurs.

---

## Boundary: What YieldOS Is and Is Not

| YieldOS Does | YieldOS Does Not |
|--------------|-----------------|
| Classify candidate remaining/blocked die | Generate recovery_profile.json |
| Map functional regions (chip_tile / wafer_region / die) | Execute equipment control commands |
| Map candidate roles (8 canonical roles) | Perform recipe execution |
| Report valid conditions for each role | Certify root causes of failure |
| Produce Recovery Compiler intake preview (candidate only) | Perform timing closure or physical design signoff |
| Flag missing evidence for human review | Guarantee yield or certify production readiness |

HAL YieldOS is a **read-only functional yield evidence layer**. All outputs are candidates for human review, not operational directives.
