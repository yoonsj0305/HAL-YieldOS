# HAL YieldOS Pilot Readiness Guide

HAL YieldOS v3.0.0 provides a **Pilot Readiness Pack** — a structured workflow
for enterprise customers to prepare their data before running YieldOS domain analysis.

The canonical output files are now schema-stable and machine-readable. External partners
can parse `pilot_readiness_report.json` and related files against the schemas below.

---

## What Is a Pilot Readiness Pack?

A Pilot Readiness Pack answers two questions:

1. **What data does YieldOS need?** (`yieldos pilot init`)
2. **Is your data sufficient to run YieldOS analysis?** (`yieldos pilot check`)

The organizing question remains unchanged:

> **"What can still function, what must be blocked, under what valid conditions,
> and based on what evidence?"**

Pilot Readiness is not a generic data onboarding tool. It specifically checks whether
the input data enables functional yield candidate evaluation.

---

## Supported Domains

| Domain | CLI name | Description |
|--------|----------|-------------|
| Industrial Robot | `robot` | Joint telemetry, operator notes, maintenance logs |
| Semiconductor Process | `semiconductor` | Tool logs, metrology, electrical test results |
| Satellite / Space | `space` | Housekeeping telemetry, event logs, mission config |
| NAND/Flash Memory | `memory` | Bad block maps, ECC logs, binning policy |
| SemiForge Simulation | `semiforge` | Synthetic defect maps, workload roles, routing |

---

## Step 1: Generate Pilot Init Pack

```bash
yieldos pilot init --domain semiconductor --out output/pilot_semiconductor
```

This generates **6 canonical files** (v2.9.1+):

| File | Purpose |
|------|---------|
| `pilot_input_contract.json` | Domain contract with functional-yield mapping |
| `sample_file_manifest.json` | Required/optional files with minimum_viable_rows |
| `missing_data_request_template.json` | Collection template for your data engineering team |
| `sanitization_checklist.md` | Steps to sanitize data before sharing (Markdown) |
| `pilot_boundary_statement.md` | What YieldOS is and is not (Markdown) |
| `README.md` | Human-readable launch guide |

Share `missing_data_request_template.json` with your data team.
Complete `sanitization_checklist.md` before exporting any data.

---

## Step 2: Check Data Readiness

Once data is collected and sanitized:

```bash
yieldos pilot check \
  --domain semiconductor \
  --input path/to/your/data \
  --out output/pilot_check_semiconductor
```

This generates **4 canonical files** (v2.9.1+):

| File | Purpose |
|------|---------|
| `pilot_readiness_report.json` | Canonical readiness status with structured checks |
| `missing_data_request.json` | Canonical missing arrays with FY relevance |
| `data_sufficiency_preview.json` | Top-level sufficiency status + per-file breakdown |
| `pilot_decision_boundary.json` | Allowed and forbidden decisions for this check run |

---

## pilot_readiness_report.json — Canonical Schema (v3.0.0)

The `pilot_readiness_report.json` file uses **`readiness_status`** as its canonical field.
The legacy `status` key is kept as a compatibility alias.

Key top-level fields:

```json
{
  "schema": "hal.yieldos.pilot.readiness_report.v1",
  "readiness_status": "READY_FOR_FUNCTIONAL_YIELD_PILOT",
  "readiness_score": 0.92,
  "readiness_score_percent": 92.0,
  "required_files_present": ["robot_telemetry.csv", "operator_notes.csv"],
  "required_files_missing": [],
  "column_check": { "passed": ["robot_telemetry.csv"], "failed": [] },
  "minimum_viable_rows_check": { "passed": [...], "failed": [], "warnings": [] },
  "functional_yield_readiness": {
    "remaining_functions_inputs_ready": true,
    "blocked_functions_inputs_ready": true,
    "valid_conditions_inputs_ready": true,
    "evidence_inputs_ready": true,
    "human_review_inputs_ready": true
  },
  "sufficient_for": ["pilot_data_intake_review", "candidate_functional_yield_pilot"],
  "not_sufficient_for": ["certified_root_cause", "safety_certification", "yield_guarantee", "automatic_recovery", "hardware_control"],
  "human_review_required": true,
  "hardware_control_enabled": false,
  "claim_boundary": "pilot_readiness_only_not_certification"
}
```

---

## Readiness Score

Two numeric fields are always present in `pilot_readiness_report.json`:

| Field | Scale | Description |
|-------|-------|-------------|
| `readiness_score` | 0.0 – 1.0 | Normalized readiness score |
| `readiness_score_percent` | 0.0 – 100.0 | Same value expressed as a percentage |

**Invariant:** `readiness_score_percent == round(readiness_score * 100, 2)` always holds.

### Score Cap Semantics

| Condition | Score cap |
|-----------|-----------|
| All required files present, columns correct, all MVR passed | Up to 1.0 |
| Minimum viable rows fail for any required file | < 1.0 (not capped, proportional) |
| Any required file missing | ≤ 0.70 (actual: ≤ 0.40) |
| Required columns missing from any required file | ≤ 0.60 |

Caps are enforced before writing `pilot_readiness_report.json`. The `readiness_score_percent`
reflects the same cap (e.g., score ≤ 0.40 → percent ≤ 40.0).

**READY is never returned when any score cap applies.**

---

## Readiness Status Values

| Status | Meaning |
|--------|---------|
| `READY_FOR_FUNCTIONAL_YIELD_PILOT` | All required files present, columns correct, minimum viable rows met. |
| `PARTIAL_FOR_FUNCTIONAL_YIELD_PILOT` | Required files present but some row counts insufficient. |
| `NOT_READY_FOR_FUNCTIONAL_YIELD_PILOT` | Critical required files missing or unreadable. |
| `INVALID_INPUT` | Malformed files, unreadable CSV, invalid domain, or hardware control attempted. |

**File and column presence alone is not enough for READY.**

READY requires ALL of:

1. All required files present
2. All required columns present
3. Minimum viable rows pass for all required files
4. All five functional-yield input groups ready
5. `hardware_control_enabled = false`
6. No malformed files

If row counts fail for any required file:
- Status must be `PARTIAL_FOR_FUNCTIONAL_YIELD_PILOT` or worse (not READY)
- `readiness_score` must be less than 1.0
- `minimum_viable_rows_check.failed` must contain the failing file(s)

---

## data_sufficiency_preview.json — Canonical Schema (v3.0.0)

The `data_sufficiency_preview.json` file now has top-level semantic fields:

```json
{
  "schema": "hal.yieldos.pilot.data_sufficiency_preview.v1",
  "sufficiency_status": "SUFFICIENT_FOR_CANDIDATE_REVIEW",
  "sufficient_for": ["pilot_data_intake_review", "candidate_functional_yield_pilot"],
  "not_sufficient_for": ["certified_root_cause", "safety_certification", "yield_guarantee", "automatic_recovery", "hardware_control"],
  "functional_yield_gaps": [],
  "claim_boundary": "data_sufficiency_preview_not_analysis_result"
}
```

Sufficiency status values:

| Value | Mapped from readiness_status |
|-------|------------------------------|
| `SUFFICIENT_FOR_CANDIDATE_REVIEW` | READY_FOR_FUNCTIONAL_YIELD_PILOT |
| `PARTIAL_FOR_CANDIDATE_REVIEW` | PARTIAL_FOR_FUNCTIONAL_YIELD_PILOT |
| `INSUFFICIENT_FOR_CANDIDATE_REVIEW` | NOT_READY_FOR_FUNCTIONAL_YIELD_PILOT |
| `INVALID_INPUT` | INVALID_INPUT |

---

## missing_data_request.json — Canonical Schema (v3.0.0)

The `missing_data_request.json` now includes canonical missing arrays:

```json
{
  "schema": "hal.yieldos.pilot.missing_data_request.v1",
  "missing_required_files": ["wafer_map.csv"],
  "missing_required_columns": [{"file": "tool_log.csv", "missing_columns": ["lot_id"]}],
  "missing_units": [],
  "minimum_viable_rows_failures": [{"file": "metrology.csv", "row_count": 2, "minimum_viable_rows": 5}],
  "recommended_optional_files": [],
  "why_needed_for_functional_yield": [
    {
      "missing_item": "wafer_map.csv",
      "needed_for": "blocked_functions_inputs",
      "reason": "determines which functions must be blocked based on current evidence, enabling the blocked_functions candidate list"
    }
  ],
  "human_review_required": true,
  "claim_boundary": "missing_data_request_for_candidate_review_only"
}
```

Every item in `why_needed_for_functional_yield` must reference functional yield concepts:
remaining functions, blocked functions, valid conditions, evidence, or human review.

---

## pilot_decision_boundary.json — Canonical Schema (v3.0.0)

The `pilot_decision_boundary.json` now has explicit allowed and forbidden decisions:

```json
{
  "schema": "hal.yieldos.pilot.decision_boundary.v1",
  "allowed_decisions": [
    "accept_for_offline_functional_yield_pilot",
    "request_missing_data",
    "reject_until_required_inputs_exist"
  ],
  "forbidden_decisions": [
    "execute_recovery",
    "control_hardware",
    "certify_safety",
    "claim_root_cause",
    "guarantee_yield",
    "modify_recipe",
    "send_robot_command",
    "uplink_satellite_command"
  ],
  "human_review_required": true,
  "hardware_control_enabled": false,
  "claim_boundary": "pilot_decision_boundary_not_operational_authority"
}
```

---

## Sample Data Policy

Built-in samples are small synthetic examples designed for demo and CI purposes.
Their `minimum_viable_rows` thresholds are set low enough that sample data always
returns `READY_FOR_FUNCTIONAL_YIELD_PILOT`.

Real pilots should use data meeting the `recommended_rows` threshold (e.g., 500+).

```json
{
  "minimum_viable_rows": 5,
  "recommended_rows": 500
}
```

---

## Step 3: Run Full Domain Analysis

When status is `READY_FOR_FUNCTIONAL_YIELD_PILOT`:

```bash
yieldos semiconductor analyze \
  --input path/to/your/data \
  --out output/semiconductor_analysis

# Or for other domains:
yieldos robot analyze --input path/to/your/data --out output/robot_analysis
yieldos memory analyze --input path/to/your/data --out output/memory_analysis
```

---

## What YieldOS Pilot Will NOT Do

- Certify root causes
- Control hardware or equipment
- Issue safety certifications
- Guarantee yield improvement
- Execute automatic recovery actions
- Replace domain expert human review

All outputs carry:

```json
{
  "human_review_required": true,
  "hardware_control_enabled": false,
  "claim_boundary": "pilot_readiness_only_not_certification"
}
```

---

## Sample Pilot Data

Sample pilot input data is provided for all 5 domains:

```
samples/pilot_robot/         — robot_telemetry.csv, operator_notes.csv, maintenance_log.csv
samples/pilot_semiconductor/ — tool_log.csv, metrology.csv, test_results.csv
samples/pilot_space/         — telemetry.csv, event_log.csv, mission_config.json
samples/pilot_memory/        — bad_block_map.csv, ecc_log.csv, product_bin_rules.json
samples/pilot_semiforge/     — synthetic_defect_map.json, workload_roles.json, routing_constraints.json
```

Run pilot check on sample data:

```bash
yieldos pilot check --domain robot --input samples/pilot_robot --out output/check_robot
yieldos pilot check --domain semiconductor --input samples/pilot_semiconductor --out output/check_semiconductor
yieldos pilot check --domain space --input samples/pilot_space --out output/check_space
yieldos pilot check --domain memory --input samples/pilot_memory --out output/check_memory
yieldos pilot check --domain semiforge --input samples/pilot_semiforge --out output/check_semiforge
```

---

*HAL YieldOS — read-only Functional Yield Evidence Layer.*
*Human review required before any operational decision.*
