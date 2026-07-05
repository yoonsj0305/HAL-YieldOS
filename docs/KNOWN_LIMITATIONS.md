# HAL YieldOS ??Known Limitations

HAL YieldOS v3.0.11 is the current release.

It is a sample-validated PoC/MVP release ??not certified for real production systems.

---

## General Limitations

- SQLite/in-memory storage only (no PostgreSQL)
- No real-time streaming ingestion
- No multi-user authentication
- SemiForge analog penalty model is a placeholder (future extension)
- No Ed25519 ContextPack signing
- No OIDC/JWKS authentication
- sample-validated PoC/MVP ??not certified for real production systems

---

## Robot Skill Memory Case Study

The Robot Skill Memory case study is based on synthetic demo data.

- It is not industrial validation.
- It is not a safety qualification.
- It is not production deployment approval.
- It is not a root-cause certification.

The case study is intended for human review, technical discussion, and pilot planning only.

---

## Physical Reality Gap

The sim-to-real gap analysis compares synthetic demo telemetry against synthetic simulation
expectations.

- Gap factors are candidates, not confirmed causes.
- Force/torque/slip events are observed candidates, not certified physical root causes.
- All outputs require human review before any operational decision.

---

## Import Check / Pilot Readiness

Introduced in v2.7.0.

The import-check is a read-only schema and privacy check only.

- `schema_status: PASSED` does not imply industrial readiness.
- `pilot_readiness: READY` means the log package is structurally suitable for YieldOS analysis.
- It is not a safety audit, regulatory qualification, or production deployment approval.
- Sensitive column detection is best-effort; it does not replace a human privacy review.

---

## Functional Yield Fab Seed

Introduced in v2.8.0.

The FYFab Seed demo is a simulation-only pipeline on synthetic data.

- It does not control any fabrication equipment.
- It does not provide physical design signoff.
- It does not imply timing closure or yield guarantees.
- All cell classifications are candidate-only and require human review.
- The chip passport does not certify any real chip design.

---

## Safety Invariants (always enforced)

Regardless of limitations above, the following invariants are always enforced in code:

- `hardware_execution_enabled = false` in all outputs
- `human_review_required = true` in all outputs
- `candidate_only = true` in all relevant outputs
- No robot control commands are ever issued
- No ROS commands are ever generated
- No hardware commands of any kind are executed
