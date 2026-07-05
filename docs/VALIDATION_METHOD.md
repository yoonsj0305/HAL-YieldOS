# HAL YieldOS ??Validation Method

## Overview

HAL YieldOS v3.0.11 is validated using **sample-based validation**.
All validation is performed on synthetic/demo data included in the `samples/` directory.

This is **not** validated on real production systems.

---

## Validation Steps

### 1. Installation Validation

```bash
pip install -e .
yieldos --help
yieldos version
yieldos doctor
```

Expected results:
- Package installs without error
- CLI entrypoint responds correctly
- Version and doctor reports show PASS

### 2. Pytest Validation

```bash
pytest tests/ -v
```

Expected results:
- All tests pass (540+ passed, 2 skipped for optional SQBM)
- No failures

Test categories:
- `tests/test_contracts.py` ??contract schema and field validation
- `tests/test_domains.py` ??domain analyzer unit tests
- `tests/test_golden.py` ??golden output structural invariants
- `tests/test_optimizers.py` ??optimizer and scheduler tests
- `tests/test_safety_regression.py` ??safety boundary regression tests
- `tests/test_semiforge.py` ??SemiForge simulation tests
- `tests/test_sqbm_backend.py` ??optional SQBM backend (skipped by default)
- `tests/test_sweep.py` ??SemiForge sweep tests

### 3. Demo Run Validation

```bash
yieldos demo --all --out output/demo_all
```

Expected results:
- All 5 domain samples analyze without error
- 22 Standard Output Bundle files generated per domain (v2.4+)
- All output files pass strict validation

### 4. Domain Sample Validation

Each domain is validated against its included synthetic sample:

| Domain | Canonical | Command |
|--------|-----------|---------|
| Semiconductor | `semiconductor` | `yieldos demo --demo-domain semiconductor --out output/demo_semi` |
| SemiForge | `semiforge` | `yieldos demo --demo-domain semiforge --out output/demo_semiforge` |
| Robot | `robot` | `yieldos demo --demo-domain robot --out output/demo_robot` |
| Space | `space` | `yieldos demo --demo-domain space --out output/demo_space` |
| Memory | `memory` | `yieldos demo --demo-domain memory --out output/demo_memory` |

### 5. Output Validation

```bash
yieldos validate --case output/demo_all/semiconductor --strict
yieldos validate --case output/demo_all/semiforge --strict
yieldos validate --case output/demo_all/robot --strict
yieldos validate --case output/demo_all/space --strict
yieldos validate --case output/demo_all/memory --strict
```

Validation checks (59 strict items):
- Required output files present (`state_snapshot.json`, `evidence_pack.json`, `ooda_frame.json`, `recovery_candidates.json`, `report.md`, `report.html`)
- EvidencePack checksum verified
- `schema` field present
- `schema_version` field present
- `hardware_execution_enabled = false`
- `causal_claim_boundary = candidate_only_not_certified_cause`
- OODA `act` is `recommendation_only` or equivalent
- No forbidden action strings present

### 6. Safety Boundary Validation

Safety regression tests (`tests/test_safety_regression.py`) verify:
- No `hardware_execution_enabled = true` anywhere in output
- No forbidden action strings in any generated output
- `causal_claim_boundary = candidate_only_not_certified_cause` on all RCA outputs
- All recovery candidates are `recommendation_only` or `human_review_required`
- `generated_by` and `safety` blocks present on all major outputs

### 7. SQBM Fallback Validation

```bash
yieldos semiforge simulate --config samples/semiforge_crossbar/config.json --optimizer sqbm --out output/sqbm_test
```

Expected: Falls back to greedy optimizer when SQBM backend is not installed. No failure.

---

## Validation Limitations

This validation **does not** cover:

- Real fab production data
- Real robot fleet telemetry
- Real satellite operation data
- False positive / false negative rates on real data
- Production deployment performance

See [LIMITATIONS.md](LIMITATIONS.md) for full list.

---

## Validation Report

Each domain case generates a `case_manifest.json` with SHA-256 checksums of all
Standard Output Bundle files. Run strict validation to get a per-case report:

```bash
yieldos validate --case output/demo_all/robot --strict
yieldos validate --case output/demo_all/space --strict
yieldos validate --case output/demo_all/semiconductor --strict
yieldos validate --case output/demo_all/semiforge --strict
yieldos validate --case output/demo_all/memory --strict
```

Note: a consolidated `output/VALIDATION_REPORT.md` is **not** auto-generated.
Run `yieldos validate --case <dir> --strict` per case to inspect results.
