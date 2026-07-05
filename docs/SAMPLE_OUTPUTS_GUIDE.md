# HAL YieldOS — Sample Outputs Guide

HAL YieldOS v3.0.7

Every YieldOS analysis produces a Standard Output Bundle in the specified output directory.

---

## Standard Output Bundle (22 files)

### Core State and Evidence

**`state_snapshot.json`**
Current observed state of the asset. Fields: `schema`, `mode` (always `read_only_shadow`), `state`, `severity`, `confidence`, `metrics`, safety invariants.

**`evidence_pack.json`**
Sealed evidence bundle with SHA-256 checksum. Fields: `schema`, `causal_claim_boundary` (always `candidate_only_not_certified_cause`), `evidence_objects`, `root_cause_candidates`, `checksum`.

**`ooda_frame.json`**
OODA loop frame in read-only evidence mode. The `act` field always has `recommendation_only_no_hardware_action`. `control_loop = false`, `hardware_action_enabled = false`.

### Functional Assessment

**`functional_passport.json`**
The primary output. Contains: `remaining_roles`, `blocked_roles`, `bin_class` (GREEN/YELLOW/ORANGE/RED), `decision_readiness`, `hardware_execution_enabled = false`, `requires_human_review = true`.

For semiconductor analyses, also contains:
- `confidence_explanation` — score, data_status, missing_metrics, missing_metric_messages, available_metrics_summary
- `semiconductor_analysis_context`
- Refs to domain-specific report files

**`functional_yield_scorecard.json`**
Functional yield scores. Not a yield guarantee.

**`functional_binning_result.json`**
Functional bin classification per role.

**`decision_readiness_report.json`**
Assessment of evidence completeness for decision-making. `decision_readiness` values: `PASSPORT_ELIGIBLE`, `CONDITIONAL_ELIGIBLE`, `ACTION_INELIGIBLE`.

### Evidence Quality

**`data_quality_report.json`**
Input data quality assessment: completeness, freshness, conflict flags, per-field status.

**`evidence_conflict_report.json`**
Evidence conflicts and gaps found during analysis.

**`source_data_manifest.json`**
Input file checksums and metadata. Documents what data was analyzed.

**`next_data_request.json`**
Explicit missing data gaps and suggested acquisition steps.

**`input_validation.json`**
Input validation results before analysis.

### Recovery and Analysis

**`recovery_candidates.json`**
Candidate-only recovery actions. Always: `hardware_execution_enabled = false`, `requires_human_review = true`.

**`recovery_route_report.json`**
Recovery route candidates (read-only, candidate-only).

**`failure_scenario_record.json`**
Failure scenario documentation for each blocked role.

**`analysis_trace.json`**
Step-by-step analysis provenance.

**`baseline_vs_yieldos.json`**
Binary policy decision vs. YieldOS reclassification. Shows recovered functional capacity evidence.

**`business_case_summary.json`**
Business impact of functional reclassification (evidence only, not a business decision).

### Reports

**`report.md`**
Human-readable Markdown report.

**`report.html`**
Styled HTML report with severity badges and, for semiconductor analyses, a Semiconductor Process Confidence section.

**`evidence_pack.md`**
Human-readable evidence summary.

**`case_manifest.json`**
SHA-256 checksums of all output files in the bundle. Written last.

---

## Semiconductor-Specific Extra Outputs

When analyzing semiconductor data:

**`process_drift_report.json`**
Per-metric recent trend detection results. Status: `DRIFT_CANDIDATE`, `STABLE_NORMAL`, `INSUFFICIENT_DATA`.

**`semiconductor_confidence_report.json`**
Process confidence analysis. Key section: `confidence_report` with:
- `score` — analysis quality confidence (0.0–1.0)
- `data_status` — `SUFFICIENT`, `PARTIAL_DATA`, or `INSUFFICIENT_DATA`
- `signal_status` — `DRIFT_CANDIDATE`, `STABLE_NORMAL`, `CONFLICTING_SIGNALS`, etc.
- `missing_metrics` — watched metrics with insufficient data (e.g. `["gas_flow_sccm", "endpoint_signal"]`)
- `available_metrics_summary` — with fields: `available_metric_count`, `drift_candidate_count`, `stable_count`, `insufficient_data_count`, `drift_candidate_metrics`, `stable_metrics`, `insufficient_data_metrics`, `summary_text`

Example `summary_text`:
```
1/3 available metrics show drift (pressure_mTorr); 2 watched metrics have no data (gas_flow_sccm, endpoint_signal)
```

---

## Semiconductor Pilot-Pack Extra Outputs (14+ files)

When running `yieldos semiconductor pilot-pack`:

| File | Description |
|------|-------------|
| `semiconductor_evidence_completeness_report.json` | Evidence coverage assessment |
| `semiconductor_wafer_die_summary.json` | Wafer/die pass/fail statistics |
| `semiconductor_functional_region_map.json` | Candidate functional die regions |
| `semiconductor_role_candidate_map.json` | Remaining vs. blocked role candidates |
| `semiconductor_valid_conditions_report.json` | Candidate valid operating conditions |
| `semiconductor_process_evidence_report.json` | Process evidence traceability |
| `semiconductor_human_review_packet.json` | Structured human reviewer checklist |
| `semiconductor_missing_evidence_request.json` | Missing evidence request |
| `semiconductor_recovery_compiler_intake_preview.json` | Recovery Compiler readiness preview |
| `semiconductor_recovery_compiler_handoff_boundary.json` | Handoff boundary documentation |
| `semiconductor_recovery_compiler_export.json` | **Candidate-only** export artifact for offline testing |
| `semiconductor_handoff_manifest.json` | Authorized handoff file set |
| `semiconductor_pilot_case_summary.md` | Human-readable pilot case summary |

> `semiconductor_recovery_compiler_export.json` has `recovery_profile_generated = false`. YieldOS never generates `recovery_profile.json`.

---

## Robot-Specific Extra Outputs

When running `yieldos robot pilot-pack` or `yieldos robot skill-demo`:

| File | Description |
|------|-------------|
| `robot_evidence_completeness_report.json` | Evidence coverage assessment |
| `robot_role_reclassification_report.json` | Remaining vs. blocked role reclassification |
| `robot_valid_conditions_report.json` | Candidate valid operating conditions |
| `robot_human_review_packet.json` | Human reviewer checklist |
| `robot_missing_evidence_request.json` | Missing evidence request |
| `operator_skill_note.json` | Operator skill observations |
| `human_intervention_timeline.json` | Intervention event log |
| `sim_to_real_gap_report.json` | Simulation-to-real-world gap evidence |

---

## Watching Missing Metrics in Semiconductor Reports

The 5 watched metrics for semiconductor analysis are:

```
rf_power_W
pressure_mTorr
gas_flow_sccm
temperature_C
endpoint_signal
```

If any watched metric has insufficient data:

1. `semiconductor_confidence_report.json` → `confidence_report.missing_metrics` lists them
2. `functional_passport.json` → `confidence_explanation.missing_metric_messages` shows e.g.:
   ```
   "gas_flow_sccm: no data"
   "endpoint_signal: no data"
   ```
3. `report.html` → Semiconductor Process Confidence table shows "no data" for each missing metric
4. `report.md` → Semiconductor Confidence section has the metric table

---

## Inspecting Outputs

```bash
# View all files in an output bundle
yieldos inspect-output output/demo_all/semiconductor

# View a specific file
cat output/demo_all/semiconductor/functional_passport.json

# Validate strict (53-point check)
yieldos validate --case output/demo_all/semiconductor --strict
```

---

*HAL YieldOS v3.0.7*
