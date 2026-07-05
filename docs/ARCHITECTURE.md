# Architecture

HAL YieldOS v3.0.11

---

## High-level model

```
Input logs and structured sample files (CSV, JSON)
  → Domain pack analyzers
  → EvidencePack
  → StateSnapshot
  → FunctionalPassport
  → DecisionReadinessReport
  → Human-readable report (report.html, report.md)
  → Optional candidate-only Recovery Compiler export (semiconductor only)
```

## Core invariants

All outputs from HAL YieldOS enforce these invariants:

- **read-only** — YieldOS does not write to hardware, control systems, or external services
- **candidate-only** — all role classifications, recovery candidates, and yield assessments are candidate evidence for human review
- **human-review-required** — no YieldOS output constitutes an operational decision
- **evidence lineage preserved** — all output objects carry provenance, SHA-256 checksums, and claim boundary metadata
- **no hardware control** — no commands are sent to any hardware system
- **no certified root cause** — YieldOS identifies candidate causes, not certified root causes
- **no yield guarantee** — all yield evidence is assessment-only, not a guarantee

---

## Main layers

### CLI layer

Entry point: `yieldos.cli.main`

Commands:

- `yieldos doctor [--deep]` — health check
- `yieldos demo --all` — run all 5 domain demos
- `yieldos validate --case <dir> [--strict]` — validate output bundle
- `yieldos semiconductor pilot-pack` — semiconductor pilot-ready pack
- `yieldos robot pilot-pack` — robot pilot-ready pack
- `yieldos semiforge fyfab-demo` — FYFab simulation seed

### Core evidence layer

Responsible for:

- evidence pack creation and sealing (SHA-256)
- manifests and source data tracking
- data quality reports
- decision readiness assessment
- functional passports (remaining/blocked/bin-class)
- OODA frame generation
- validation contracts (53-point strict check)

### Domain packs

**Robot:**
- role reclassification (remaining vs. blocked)
- valid condition identification
- missing evidence tracking
- human review packet generation
- skill memory evidence

**Semiconductor:**
- wafer/die summary
- functional region mapping
- role candidate map
- SemFab confidence report
- Recovery Compiler export and handoff manifest (candidate-only, offline testing)

**Space:**
- mission salvage evidence
- remaining mission roles vs. blocked roles

**Memory:**
- bad block / ECC / retention style evidence
- functional rebinning

**SemiForge / FYFab:**
- simulation-only functional-yield fab seed
- conceptual demo only

### Validation layer

- strict validation (`--strict` flag, 53-point contract)
- release hygiene validation
- safety boundary assertions
- public docs content checks

---

## Recovery Compiler boundary

HAL YieldOS may generate candidate-only intake/export files for HAL Recovery Compiler.

HAL YieldOS does not:

- run HAL Recovery Compiler
- generate `recovery_profile.json`
- apply recovery profiles to any system
- control hardware
- modify semiconductor recipes
- perform timing closure
- execute any recovery action

`semiconductor_recovery_compiler_export.json` and `semiconductor_handoff_manifest.json` are candidate-only artifacts for offline Recovery Compiler testing by a human operator. They are not production handoff authorizations.

---

## Output bundle

Every analysis produces a standard output bundle. Key files:

| File | Purpose |
|------|---------|
| `state_snapshot.json` | Current state, severity, confidence |
| `evidence_pack.json` | Sealed evidence bundle with SHA-256 |
| `functional_passport.json` | Remaining roles, blocked roles, bin class |
| `ooda_frame.json` | OODA loop frame (read-only evidence mode) |
| `recovery_candidates.json` | Candidate-only recovery actions for human review |
| `decision_readiness_report.json` | Decision readiness assessment |
| `data_quality_report.json` | Input data quality assessment |
| `report.html` | Styled HTML report |
| `report.md` | Human-readable Markdown report |
| `case_manifest.json` | SHA-256 checksums of all output files |

Semiconductor pilot-pack adds domain-specific files including `semiconductor_confidence_report.json` and `semiconductor_recovery_compiler_export.json`.

---

*This document is part of HAL YieldOS v3.0.11.*
