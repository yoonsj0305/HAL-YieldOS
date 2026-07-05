# HAL YieldOS — Limitations

## What HAL YieldOS Is

HAL YieldOS is a **read-only evidence engine** for industrial telemetry analysis.
It produces root-cause candidates, recovery recommendations, and structured evidence packs.
It does **not** control hardware, modify recipes, or certify root causes.

---

## Known Limitations

### Validation Scope

- **Sample-based validation only.** All included samples are synthetic/demo data.
- Not validated on real production fab data.
- Not validated on real robot fleet data.
- Not validated on real satellite operation data.
- Not a certified root-cause engine for any industrial domain.
- Not a live control system.

### Root Cause Analysis

- All root cause outputs are **candidates only**, not certified causes.
- `causal_claim_boundary = candidate_only_not_certified_cause` is enforced on all outputs.
- Human expert review is required before any operational action is taken.

### Recovery Recommendations

- All recovery outputs are **recommendation-only**.
- `execution_mode = recommendation_only` or `human_review_required` is enforced.
- HAL YieldOS does not execute any recovery action.

### Hardware and Equipment

- `hardware_execution_enabled = false` on all outputs.
- No live hardware control of any kind.
- No semiconductor equipment control.
- No robot commands.
- No satellite commands.
- No recipe modification.

### SemiForge Simulation

- Functional yield simulation is based on synthetic defect models (iid and clustered).
- Analog penalty values are a **sensitivity model**, not calibrated device data.
- Results are not validated against measured device performance.

### SQBM Optimizer

- SQBM is an **optional** optimizer backend.
- When SQBM is unavailable, the system falls back to greedy optimizer.
- **SQBM optional fallback is validated** — greedy fallback is confirmed to work when `yieldos-sqbm` is not installed.
- **Actual SQBM backend execution is not validated** unless `yieldos-sqbm` optional package is present and installed.
- SQBM is a candidate ranker, not an execution engine. Safety boundaries apply regardless of optimizer used.
- No performance claims are made about SQBM advantage without real benchmark data.

### Tool API

- Token estimates are **estimates** (character-count / 4 approximation), not tokenizer-based counts.

---

## Future Validation (with Real Data)

The following validations require real industrial data and are **not** included in this release:

- Real fab yield improvement rate validation
- Real TSMC/Samsung process applicability
- Real TEL/ASML/Lam/KLA equipment log adapter validation
- Real robot fleet fault prediction performance
- Real satellite telemetry anomaly detection performance
- Real customer ROI calculation
- Real false positive / false negative measurement
- Real SQBM large-scale performance comparison

---

## Reference

See also:
- [SAFETY_BOUNDARY.md](SAFETY_BOUNDARY.md) — safety enforcement details
- [VALIDATION_METHOD.md](VALIDATION_METHOD.md) — what was validated and how
- [SAMPLE_DATA_NOTICE.md](SAMPLE_DATA_NOTICE.md) — sample data origin and scope
