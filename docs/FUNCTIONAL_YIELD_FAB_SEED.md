# HAL YieldOS — Functional Yield Fab Seed

Version: v2.8.10

---

## Core Boundary

FYFab Seed does not fabricate chips.

It is a simulation-only evidence workflow that explores how imperfect fabricated structures
could be interpreted into candidate functional regions and Functional Yield Chip Passports.

한국어: FYFab Seed는 칩을 제조하지 않는다.
불완전하게 만들어진 구조를 시뮬레이션으로 해석해 후보 기능 영역과 Functional Yield Chip Passport로 바꾸는 evidence workflow다.

---

## What FYFab Seed Does

FYFab Seed introduces the first software layer for a future Functional Yield Fab evidence pipeline.

Given a simulated fabricated structure, defect map, material regions, and target function blocks, it:

1. Loads and summarizes the simulated fabricated substrate (`fabricated_structure_map.json`)
2. Summarizes observed candidate defects (`defect_map_summary.json`)
3. Classifies each cell into candidate use roles (`usable_cell_classification.json`)
4. Groups usable cells into candidate functional regions (`candidate_functional_regions.json`)
5. Maps candidate regions to target functional blocks (`reconfiguration_candidate_map.json`)
6. Issues a Functional Yield Chip Passport (`functional_yield_chip_passport.json`)
7. Produces a case study narrative (`fyfab_case_study.json`)

---

## What FYFab Seed Does Not Do

FYFab Seed is not and will never be:

- A real fabrication tool controller
- An EUV replacement claim
- A lithography, deposition, or etch controller
- A semiconductor process recipe executor
- A production fab automation system
- A certified EDA tool
- A safety or reliability certification system
- A physical design signoff tool
- A timing closure tool
- A yield guarantee system

---

## How It Relates to Future Bottom-Up Fabrication

YieldOS envisions a future where bottom-up fabricated structures (grown via selective
deposition, ALD, CVD, MBE, etc.) will need software tools that can:

- Interpret imperfect structures that emerge from self-assembly or candidate deposition
- Classify which cells are usable and which must be avoided
- Propose candidate reconfiguration paths without modifying the physical substrate
- Issue a chip-level functional passport that describes what the chip can and cannot do

FYFab Seed is the first software seed of this vision — a simulation pipeline only.

---

## Why It Is Simulation-Only

Real bottom-up fabricated structures require:
- Physical measurement (AFM, SEM, EDX, Hall effect, etc.)
- Calibrated process models
- Safety-qualified measurement equipment
- Human engineer interpretation

YieldOS does not have access to real measurement data. It can only simulate the
evidence-generation pipeline using synthetic demo data. All classifications are
candidates that require human review before any operational use.

---

## Connection to Functional Yield Philosophy

The Functional Yield philosophy asks:

> What can we do with an imperfect structure, rather than discarding it entirely?

FYFab Seed applies this philosophy to a simulated fabricated substrate:

- Not every cell needs to be perfect. Some defective cells can be bypassed.
- Remaining usable cells can be grouped into candidate functional regions.
- A partial chip (with blocked functions) may still perform candidate roles.
- A Functional Yield Chip Passport records what remains and what is blocked.

This is the same philosophy applied in:
- Robot Skill Memory (functional roles preserved after task failures)
- Satellite SatGuard (functional orbit modes after anomaly)
- Semiconductor SemFab (functional die bins after wafer defects)

---

## Usage

```bash
# Run with built-in sample data
yieldos semiforge fyfab-demo --out output/fyfab_seed

# Run with custom input folder
yieldos semiforge fyfab-demo --input yieldos/sample_data/fyfab_seed --out output/fyfab_seed

# Validate (strict mode)
yieldos validate --case output/fyfab_seed --strict

# Inspect output summary
yieldos inspect-output output/fyfab_seed
```

---

## Claim Boundary

All FYFab Seed outputs carry one of these claim boundaries:

- `simulation_only` — fabricated_structure_map
- `observed_defect_map_not_root_cause_certification` — defect_map_summary
- `candidate_functional_classification_only` — usable_cell_classification
- `candidate_region_not_physical_design_signoff` — candidate_functional_regions
- `candidate_mapping_not_routing_signoff` — reconfiguration_candidate_map
- `simulation_only_functional_yield_chip_passport` — chip passport
- `simulation_only_case_study_not_manufacturing_evidence` — case study
