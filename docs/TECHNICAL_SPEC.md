# HAL YieldOS ??Technical Specification

## Overview

HAL YieldOS v3.0.11 is a read-only Functional Yield Evidence Layer. It analyzes imperfect industrial hardware telemetry and produces structured evidence outputs for human review. It does not control hardware, certify systems, or authorize operational decisions.

## Standard Output Bundle (v2.4)

Every analysis case produces the following files:

| File | Description |
|------|-------------|
| `state_snapshot.json` | Normalized hardware state |
| `evidence_pack.json` | Evidence objects, root cause candidates, missing evidence |
| `ooda_frame.json` | OODA loop analysis frame |
| `recovery_candidates.json` | Candidate recovery actions (safe prefix enforced) |
| `report.md` | Human-readable Markdown report |
| `report.html` | Human-readable HTML report |
| `input_validation.json` | Input data quality gate (PASSED/FAILED) |
| `decision_readiness_report.json` | Decision readiness category and limiting factors |
| `functional_yield_scorecard.json` | Functional Yield Vector and component scores |
| `functional_binning_result.json` | Bin class and role assignment |
| `functional_passport.json` | Full passport with validity, approval gate, evidence strength |
| `evidence_pack.md` | Evidence pack in Markdown |
| `recovery_route_report.json` | Recovery routes (all require human approval) |
| `failure_scenario_record.json` | Failure scenario record |
| `next_data_request.json` | Data gaps and improvement requirements |
| `analysis_trace.json` | Step-by-step analysis trace |
| `source_data_manifest.json` | Input file hashes and dimensions |
| `data_quality_report.json` | Data completeness and signal coverage |
| `evidence_conflict_report.json` | Confidence divergence flags |
| `baseline_vs_yieldos.json` | Binary policy vs. YieldOS functional reclassification |
| `business_case_summary.json` | Domain-specific value proposition |
| `case_manifest.json` | SHA-256 checksums of all output files |

## Safety Constraints (Hard-coded)

- `hardware_execution_enabled: false` ??always
- `act: recommendation_only_no_hardware_action` ??always
- `causal_claim_boundary: candidate_only_not_certified_cause` ??always
- `human_approval_required: true` ??always
- All recovery action strings must start with a safe prefix: `recommend_`, `request_`, `suggest_`, `prepare_`, `simulate_`, `draft_`
- Forbidden prefixes: `execute_`, `control_`, `send_`, `uplink_`, `move_`, `change_`, `modify_`, `erase_`, `schedule_`, `flag_`

## Functional Passport Schema (v2.4)

```json
{
  "schema": "hal.yieldos.functional_passport.v2",
  "passport_validity": {
    "status": "candidate_only",
    "expires_after": "requires_new_data_after_context_change",
    "valid_conditions": ["domain-specific conditions..."]
  },
  "operating_constraints": [],
  "required_human_roles": ["domain-specific roles..."],
  "approval_gate": {
    "required": true,
    "authority_matrix_present": false,
    "approval_level": "engineering_review",
    "cvc_present": false,
    "risk_policy_present": false
  },
  "evidence_strength": {
    "data_completeness": 0.0,
    "signal_consistency": 0.0,
    "historical_support": 0.0,
    "model_calibration": 0.0
  },
  "role_confidence": {}
}
```

## Decision Readiness Inputs (Optional)

Provide these files to improve passport completeness:

- `cvc.json` ??Constraint and value priority specification
- `action_authority_matrix.json` ??Who can approve what action
- `operating_envelope.json` ??Safe operating range per role
- `risk_policy.json` ??Risk tolerance policy

Pass via CLI: `--cvc path/cvc.json --authority path/action_authority_matrix.json --envelope path/operating_envelope.json --risk-policy path/risk_policy.json`첵첼