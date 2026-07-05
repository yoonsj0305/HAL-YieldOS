# HAL YieldOS Developer Validation Guide

HAL YieldOS v2.9.1 introduces a two-tier pytest strategy:

- **Default core suite** ??fast functional-yield validation (runs in < 3 min)
- **Release validation suite** ??packaging, installed-wheel, CLI e2e, release zip checks

---

## Default Developer Validation

Run these for every code change:

```bash
python -m pytest -q
python -m ruff check .
yieldos doctor --deep
```

The default pytest suite validates:
- Core functional-yield contracts
- Domain analyzers (robot, space, semiconductor, SemiForge, memory)
- Functional Passport generation
- EvidencePack / Decision Readiness / Data Quality / Case Manifest
- Functional Yield Essence metadata (all 5 domains)
- Semiconductor process_drift_report.json / semiconductor_confidence_report.json
- Safety boundary invariants
- No-generic-platform-drift static checks
- Strict validation (direct internal validation, not subprocess)
- Robot recent-weighted aggregation
- SemiForge direct-parameter simulation
- FYFab Seed

The default suite excludes markers: `release_heavy`, `installed_wheel`, `packaging`, `cli_e2e`.

---

## Release Validation

Run these before tagging a release:

```bash
# Release archive checks
python -m pytest -q -m release_heavy

# Installed wheel checks
python -m pytest -q -m installed_wheel

# CLI end-to-end checks
python -m pytest -q -m cli_e2e

# Packaging metadata checks
python -m pytest -q -m packaging

# Or all heavy checks at once
python -m pytest -q -m "release_heavy or installed_wheel or packaging or cli_e2e"
```

---

## Build Validation

```bash
python -m build
python scripts/build_release.py
```

---

## Installed Wheel Validation

```bash
python -m venv /tmp/yieldos-v289-venv
source /tmp/yieldos-v289-venv/bin/activate   # Windows: .venv\Scripts\activate
pip install dist/*.whl

yieldos version
yieldos doctor --deep
yieldos demo --all --out /tmp/yieldos-v289-demo
yieldos validate --case /tmp/yieldos-v289-demo/semiconductor --strict
```

---

## Domain Demo Validation

```bash
yieldos demo --all --out output/demo_all

yieldos validate --case output/demo_all/robot --strict
yieldos validate --case output/demo_all/space --strict
yieldos validate --case output/demo_all/semiconductor --strict
yieldos validate --case output/demo_all/semiforge --strict
yieldos validate --case output/demo_all/memory --strict
```

---

## Robot Validation

```bash
yieldos robot import-check \
  --input yieldos/sample_data/external_robot_log_package \
  --out output/import_check

yieldos robot skill-demo \
  --input yieldos/sample_data/external_robot_log_package \
  --out output/robot_skill_external

yieldos validate --case output/robot_skill_external --strict
```

---

## Semiconductor Validation

```bash
yieldos demo --domain semiconductor --out output/semiconductor_calibrated
yieldos validate --case output/semiconductor_calibrated --strict
yieldos inspect-output output/semiconductor_calibrated

# Confirm extra reports are present
ls output/semiconductor_calibrated/process_drift_report.json
ls output/semiconductor_calibrated/semiconductor_confidence_report.json
```

---

## FYFab / SemiForge Validation

```bash
yieldos semiforge fyfab-demo --out output/fyfab_seed
yieldos validate --case output/fyfab_seed --strict
yieldos inspect-output output/fyfab_seed
```

---

## Release Zip Hygiene

The release zip must not include:

- `build/`
- `dist/`
- `.ruff_cache/`
- `.pytest_cache/`
- `.pytest_tmp/`
- `__pycache__/`
- `*.pyc`
- `*.whl`
- `*.tar.gz`
- `hal_yieldos.egg-info/`
- `.mypy_cache/`
- `htmlcov/`

---

## Runtime Budget

| Suite | Target |
|-------|--------|
| Default `python -m pytest -q` | < 3 minutes |
| Release-heavy `-m release_heavy` | < 10 minutes |
| Full `-m "release_heavy or installed_wheel or packaging or cli_e2e"` | < 20 minutes |

---

## Pilot Readiness Validation

```bash
# Generate pilot init pack (all domains)
yieldos pilot init --domain robot --out output/pilot_robot
yieldos pilot init --domain semiconductor --out output/pilot_semiconductor
yieldos pilot init --domain space --out output/pilot_space
yieldos pilot init --domain memory --out output/pilot_memory
yieldos pilot init --domain semiforge --out output/pilot_semiforge

# Check pilot readiness on sample data
yieldos pilot check --domain robot --input samples/pilot_robot --out output/check_robot
yieldos pilot check --domain semiconductor --input samples/pilot_semiconductor --out output/check_semiconductor
```

---

## What YieldOS Validates

YieldOS validates functional yield evidence ??not AI models, not hardware control,
not root-cause certification, not safety certification, not yield guarantees.

The organizing question remains:

> **"What can still function, what must be blocked, under what valid conditions,
> and based on what evidence?"**

Functional Yield is the organizing principle of every test in this suite.
