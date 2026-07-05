# HAL YieldOS — Public Safety Boundary

HAL YieldOS v3.0.7

---

## Summary

HAL YieldOS is a **read-only Functional Yield Evidence Layer**.

It reads sanitized industrial data. It produces structured evidence for human review. It does not act on hardware.

---

## Non-Control Guarantee

YieldOS enforces the following at the code level and cannot be overridden:

- **No hardware control.** YieldOS does not send commands to any hardware system.
- **No robot commands.** YieldOS does not send motion, torque, joint, or payload commands.
- **No satellite uplink.** YieldOS does not transmit commands to spacecraft.
- **No semiconductor recipe modification.** YieldOS does not change process recipes, tool settings, or equipment parameters.
- **No firmware flashing.** YieldOS does not write firmware to any device.
- **No runtime profile application.** YieldOS does not apply recovery profiles to running systems.
- **No automatic recovery.** YieldOS does not trigger, schedule, or execute any form of automated recovery.

All output objects carry:

```
hardware_execution_enabled    = false
causal_claim_boundary         = candidate_only_not_certified_cause
human_review_required         = true
mode                          = read_only_shadow
```

---

## Candidate-Only Outputs

Every YieldOS output is **candidate evidence for human review**, not a decision or certification:

| Output | What it is | What it is NOT |
|--------|-----------|----------------|
| `functional_passport.json` | Candidate remaining/blocked role assessment | Safety certification |
| `decision_readiness_report.json` | Evidence completeness assessment | Operational decision authority |
| `recovery_candidates.json` | Candidate-only recommended actions | Executable recovery instructions |
| `semiconductor_recovery_compiler_export.json` | Candidate export artifact for offline Recovery Compiler testing | Recovery profile or recipe change |
| `semiconductor_handoff_manifest.json` | Authorized handoff file set documentation | Production handoff authorization |
| `confidence_explanation` in passport | Analysis confidence in data quality | Safety confidence or certification |
| `valid_conditions` outputs | Valid-condition evidence candidates | Safety approval or qualification |

---

## Human Review Required

Every YieldOS output that influences operational decisions **requires human review before action**:

- A human reviewer must evaluate the evidence before any recovery action.
- A human reviewer must approve before any data is handed off to the Recovery Compiler.
- A human reviewer must validate robot reclassification before robot redeployment.
- YieldOS approval gates are internal to the evidence software only — they do not constitute external safety approval.

---

## Domain-Specific Boundaries

### Robot Domain

YieldOS is not:
- A ROS replacement or integration layer
- A motion planner or trajectory generator
- A robot safety certification tool
- A torque or force command system

YieldOS **does**:
- Read robot telemetry (read-only)
- Classify remaining vs. blocked roles (candidate-only)
- Generate human review packets for engineer evaluation
- Record skill memory evidence for AI-assisted analysis

### Semiconductor Domain

YieldOS is not:
- A MES, SCADA, APC, or FDC replacement
- A timing closure tool
- A recipe controller
- A yield guarantee system
- A Recovery Compiler (it generates intake evidence for the compiler, but does not run it)
- A generator of `recovery_profile.json` — YieldOS never generates recovery_profile.json; that file is produced only by the Recovery Compiler, which YieldOS does not run

YieldOS **does**:
- Read tool logs, metrology, and test results (read-only)
- Generate wafer/die functional yield evidence
- Prepare Recovery Compiler intake/export artifacts (candidate-only, offline testing only)
- Produce confidence reports showing data quality and missing watched metrics

### Space Domain

YieldOS is not:
- A flight software system
- A command uplink system
- A mission authority
- A satellite ACS/GNC replacement

YieldOS **does**:
- Read satellite telemetry (read-only)
- Classify remaining mission roles vs. blocked roles (candidate-only)
- Generate mission salvage evidence for human review

### Memory Domain

YieldOS is not:
- A firmware repair or flashing tool
- A data recovery guarantee system
- A TRIM or secure-erase tool

YieldOS **does**:
- Read block health data (read-only)
- Classify safe/approximate-cache/read-only-archive/discard per block (candidate-only)
- Compute functional yield evidence for human review

### FYFab / SemiForge Domain

YieldOS is **simulation-only** for these domains:
- Not a manufacturing validation tool
- Not a fab replacement
- Not a production chip design tool
- Conceptual simulation of future functional-yield fab flows only

---

## Forbidden Claims

The following claims are **never made by YieldOS outputs** and must not be inferred from them:

- "certified root cause"
- "safety certification"
- "production qualification"
- "yield guarantee"
- "timing closure"
- "autonomous recovery"
- "hardware execution readiness"
- "recipe approved for production"
- "recovery profile ready to apply"

---

## Enforcement

Safety invariants enforced in code (see `yieldos/contracts/`):

| Field | Enforced Value |
|-------|---------------|
| `StateSnapshot.mode` | `read_only_shadow` |
| `EvidencePack.causal_claim_boundary` | `candidate_only_not_certified_cause` |
| `OODAFrame.act` | `recommendation_only_no_hardware_action` |
| `RecoveryCandidate.hardware_execution_enabled` | `false` |
| `RecoveryCandidate.execution_mode` | `recommendation_only` or `human_review_required` |
| `RecoveryCandidate.requires_human_review` | `true` |
| `RootCauseCandidate.claim_boundary` | `candidate_only` |

These fields are validated by `yieldos validate --strict`.

---

*This document is part of HAL YieldOS v3.0.7.*
