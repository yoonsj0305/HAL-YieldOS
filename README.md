# HAL YieldOS

**Read-only Functional Yield Evidence Layer for imperfect industrial systems.**

Version: **3.0.11** | [Release Notes](RELEASE_NOTES.md) | [Docs](docs/) | [License](LICENSE.txt)

![PoC](https://img.shields.io/badge/status-PoC-blue)
![Read Only](https://img.shields.io/badge/mode-read--only-green)
![Candidate Only](https://img.shields.io/badge/outputs-candidate--only-orange)
![Human Review Required](https://img.shields.io/badge/review-human--required-purple)
![No Hardware Control](https://img.shields.io/badge/hardware--control-none-lightgrey)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-Eval--Only-yellow)
[![tests](https://github.com/yoonsj0305/HAL-YieldOS/actions/workflows/tests.yml/badge.svg)](https://github.com/yoonsj0305/HAL-YieldOS/actions/workflows/tests.yml)

---

## Core Question

> **What can still function, what must be blocked, under what valid conditions, and based on what evidence?**

한국어: *이 불완전한 시스템에서 아직 무엇을 쓸 수 있고, 무엇은 막아야 하며, 어떤 조건에서만 유효하고, 어떤 증거로 그렇게 말할 수 있는가?*

---

## What is HAL YieldOS?

HAL YieldOS converts imperfect industrial system data into evidence-backed **Functional Passports** for human review and AI-assisted decision workflows.

**HAL YieldOS is not an AI model.**

It is a **read-only Functional Yield Evidence Layer** — a candidate-only industrial evidence engine that requires human review before any operational action.

```
AI speaks.  YieldOS produces evidence.  Humans decide.
```

---

## What YieldOS Does

- Reads sanitized industrial logs and sample datasets (CSV, JSON).
- Generates state snapshots, evidence packs, functional passports, data quality reports, and decision readiness reports.
- Produces **candidate-only** remaining / blocked role classifications.
- Identifies valid operating conditions and missing evidence gaps.
- Prepares semiconductor Recovery Compiler intake exports without running the compiler.
- Preserves **human review** as the final decision gate for every output.

## What YieldOS Does NOT Do

- Does **not** control hardware.
- Does **not** send robot commands.
- Does **not** modify semiconductor recipes.
- Does **not** replace MES, SCADA, APC, FDC, ROS, flight software, or safety systems.
- Does **not** perform timing closure.
- Does **not** certify root cause.
- Does **not** guarantee yield.
- Does **not** execute recovery profiles.
- Does **not** run HAL Recovery Compiler.
- Does **not** require internet access or external APIs.

All outputs carry:

```
hardware_execution_enabled         = false
causal_claim_boundary              = candidate_only_not_certified_cause
human_review_required              = true
mode                               = read_only_shadow
```

See [docs/PUBLIC_SAFETY_BOUNDARY.md](docs/PUBLIC_SAFETY_BOUNDARY.md) for the complete safety boundary.

---

## Domain Packs

| Domain | Status | Key Outputs |
|--------|--------|-------------|
| **Robot** | Pilot-ready | skill memory, role reclassification, valid conditions, human review packet |
| **Semiconductor** | Pilot-ready | wafer/die summary, functional region map, Recovery Compiler intake/export, confidence report |
| **Space** | Demo pack | mission salvage evidence, remaining mission roles |
| **Memory** | Demo pack | bad block / ECC / retention evidence, functional rebinning |
| **SemiForge / FYFab** | Simulation-only seed | functional-yield fab concept demo |

---

## 5-Minute Quickstart

**Requirements:** Python 3.10+

```bash
# Install
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .

# Health check
yieldos doctor --deep

# Run all 5 domain demos
yieldos demo --all --out output/demo_all

# Validate a case (strict 53-point check)
yieldos validate --case output/demo_all/semiconductor --strict

# Open the HTML report in a browser
# output/demo_all/semiconductor/report.html
```

Or run the demo script directly:

```bash
python scripts/run_public_demo.py
```

To build and verify an official release artifact:

```bash
python scripts/build_release.py
python scripts/check_release_artifact.py dist/HAL-YieldOS-v3.0.11-poc-release.zip
```

Do not manually zip the working directory for GitHub releases.

---

## Standard Output Bundle

Every analysis produces **22 core output files** in the output directory:

| File | Description |
|------|-------------|
| `state_snapshot.json` | Current state, severity, confidence |
| `evidence_pack.json` | Sealed evidence bundle with SHA-256 checksum |
| `ooda_frame.json` | OODA loop frame (read-only evidence mode) |
| `recovery_candidates.json` | Candidate-only recovery actions for human review |
| `report.md` | Human-readable Markdown report |
| `report.html` | Styled HTML report with severity badges |
| `functional_passport.json` | Remaining roles, blocked roles, bin class |
| `decision_readiness_report.json` | Decision readiness assessment |
| `functional_yield_scorecard.json` | Functional yield scores |
| `data_quality_report.json` | Input data quality assessment |
| `evidence_conflict_report.json` | Evidence conflicts and gaps |
| `source_data_manifest.json` | Input file checksums and metadata |
| `analysis_trace.json` | Step-by-step analysis provenance |
| `baseline_vs_yieldos.json` | Binary policy vs. YieldOS reclassification |
| `case_manifest.json` | SHA-256 checksums of all output files |
| *(+ 7 more standard files)* | See [docs/SAMPLE_OUTPUTS_GUIDE.md](docs/SAMPLE_OUTPUTS_GUIDE.md) |

Semiconductor pilot-pack adds 14+ domain-specific outputs including `semiconductor_confidence_report.json` and `functional_passport.json` with `confidence_explanation`.

---

## CLI Reference

```bash
# Version and health
yieldos version
yieldos doctor [--deep]

# Demo (all 5 domains)
yieldos demo --all --out <output_dir>
yieldos demo --demo-domain <domain> --out <output_dir>

# Unified analyze
yieldos analyze --domain <domain> --input <path> --out <output_dir> [--asset <id>]
# domain: robot | space | semiconductor | semiforge | memory
# aliases: satellite/satguard/sat -> space | semfab/edge_ai -> semiconductor

# Robot
yieldos robot analyze --input <telemetry.csv> --out <output_dir>
yieldos robot skill-demo --out <output_dir>
yieldos robot import-check --input <package_dir> --out <output_dir>

# Semiconductor
yieldos semifab analyze --input <data_dir> --out <output_dir>
yieldos semiconductor pilot-pack --input <data_dir> --out <output_dir>

# Space
yieldos sat analyze --input <telemetry.csv> --out <output_dir>

# Memory
yieldos memory product-demo --out <output_dir>

# SemiForge / FYFab
yieldos semiforge simulate --config <config.json> --out <output_dir>
yieldos semiforge fyfab-demo --out <output_dir>

# Validate
yieldos validate --case <output_dir> [--strict]

# Synthetic data generation
yieldos semifab gen --out samples/semfab_large --lots 20 --wafers 5
yieldos robot gen   --out samples/robot_large  --samples 500
```

---

## Sample Data

Sample datasets are bundled in `yieldos/sample_data/` and `samples/`:

```
robot/                         # Robot arm telemetry, J3 joint, fault code 201
space/                         # Satellite telemetry, battery drop to 12%
semiconductor/                 # Tool log with STEP_04 drift, wafer map, metrology
semiforge/                     # 64×64 ReRAM crossbar, 12% clustered defect config
memory_device/                 # 128-block NAND flash health dataset
product_memory_rebinning_demo/ # 32 GB MLC NAND demo (binary FAIL → YieldOS reclassification)
pilot_semiconductor/           # Semiconductor pilot-pack sample data
```

The `yieldos demo` command uses bundled sample data automatically — no extra setup needed.

---

## Evidence Compression Ratio

YieldOS compresses raw industrial logs into structured evidence objects:

| Domain | Raw tokens (est.) | Evidence tokens (est.) | Compression |
|--------|------------------:|----------------------:|------------:|
| Semiconductor fab | 30,690 | 680 | 45× |
| Robot | 7,987 | 736 | 11× |
| Space | 8,810 | 733 | 12× |
| **Total** | **47,487** | **2,149** | **22×** |

*Based on 500-row synthetic datasets. Actual compression varies by dataset size.*

---

## Testing

```bash
# Default test suite (fast, no external deps)
pytest
pytest -q
pytest --cov=yieldos --cov-report=term-missing

# Marker suites
pytest -m cli_e2e       # CLI smoke tests
pytest -m release_heavy # Release archive / packaging
pytest -m installed_wheel

# Strict validation
yieldos validate --case output/demo_all/semiconductor --strict
```

See [docs/DEVELOPER_VALIDATION.md](docs/DEVELOPER_VALIDATION.md) for the two-tier validation strategy.

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/PUBLIC_SAFETY_BOUNDARY.md](docs/PUBLIC_SAFETY_BOUNDARY.md) | Complete safety boundary for public review |
| [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md) | Step-by-step demo walkthrough |
| [docs/SAMPLE_OUTPUTS_GUIDE.md](docs/SAMPLE_OUTPUTS_GUIDE.md) | What each output file contains |
| [docs/PILOT_ONE_PAGER.md](docs/PILOT_ONE_PAGER.md) | One-pager for pilot evaluation |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture overview |
| [docs/REPOSITORY_MAP.md](docs/REPOSITORY_MAP.md) | File and module map |
| [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md) | Technical specification |
| [docs/SEMICONDUCTOR_PILOT_READY.md](docs/SEMICONDUCTOR_PILOT_READY.md) | Semiconductor pilot-pack reference |
| [docs/ROBOT_PILOT_READY.md](docs/ROBOT_PILOT_READY.md) | Robot pilot-pack reference |
| [docs/FUNCTIONAL_YIELD_ESSENCE.md](docs/FUNCTIONAL_YIELD_ESSENCE.md) | Functional Yield organizing principle |
| [docs/DOCS_INDEX.md](docs/DOCS_INDEX.md) | Full documentation index |
| [ROADMAP.md](ROADMAP.md) | Roadmap and non-goals |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [SECURITY.md](SECURITY.md) | Security policy |

---

## Current Limitations

- Sample-validated PoC/MVP — not certified for real production systems
- SQLite/in-memory storage only (no PostgreSQL)
- No real-time streaming ingestion
- SemiForge analog penalty model is a placeholder
- No Ed25519 ContextPack signing

See [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) for the full list.

---

## License & Citation

This software is released for evaluation and research purposes only.
See [LICENSE.txt](LICENSE.txt) for terms.

If you use HAL YieldOS in research or publications, please cite using [CITATION.cff](CITATION.cff).

---

*HAL YieldOS v3.0.11 — Read-only Functional Yield evidence for human review.*
