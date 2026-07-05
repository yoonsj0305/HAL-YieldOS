# HAL YieldOS ??Delivery Guide

## Deliverable

```
dist/HAL-YieldOS-v3.0.11-poc-release.zip
```

This ZIP contains the complete HAL YieldOS PoC/MVP release including:
- Source code
- Sample data
- CLI entrypoint
- Documentation
- Test suite
- Release metadata (MANIFEST.json, CHECKSUMS.sha256)

---

## ZIP Contents Structure

```
halyieldos/
?흹창????yieldos/              # Core package
??  ?흹창????contracts/        # Data contracts (StateSnapshot, EvidencePack, etc.)
??  ?흹창????core/             # Evidence engine, report writer
??  ?흹창????domains/
??  ??  ?흹창????semfab/       # Semiconductor fab analyzer
??  ??  ?흹창????semiforge/    # Crossbar functional yield simulator
??  ??  ?흹창????robot/        # Robot telemetry analyzer
??  ??  ?흹창????satellite/    # Satellite telemetry analyzer
??  ??  ??씳????memory/       # NAND flash block health analyzer
??  ?흹창????api/              # Tool API
??  ?흹창????cli/              # CLI entrypoint
??  ?흹창????optimizers/       # SQBM optional + greedy optimizer
??  ??씳????scheduler/        # Recovery candidate scheduler
?흹창????samples/              # Synthetic demo data
?흹창????tests/                # Full test suite
?흹창????scripts/              # Demo and build scripts
?흹창????docs/                 # Documentation
?흹창????pyproject.toml
?흹창????VERSION
?흹창????LICENSE.txt
?흹창????RELEASE_NOTES.md
?흹창????MANIFEST.json         # Release metadata
??씳????CHECKSUMS.sha256      # File integrity checksums
```

---

## Installation

### Requirements

- Python 3.10 or later
- pip

### Steps

```bash
# 1. Unzip the release
unzip HAL-YieldOS-v2.8.10-poc-release.zip
cd halyieldos

# 2. (Recommended) Create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Install
pip install -e .
```

---

## Verification After Installation

```bash
# Check version
yieldos version

# Run environment check
yieldos doctor

# Run test suite
pytest tests/ -q
```

Expected output:
```
500+ passed, 2 skipped
```

(2 skipped = optional SQBM backend tests, expected)

---

## Demo Run

```bash
yieldos demo --all --out output/demo_all
```

This runs all 5 domain samples and generates:
- `output/demo_all/robot/` ??Robot analysis outputs
- `output/demo_all/space/` ??Satellite/space analysis outputs
- `output/demo_all/semiconductor/` ??SemFab analysis outputs
- `output/demo_all/semiforge/` ??SemiForge simulation outputs
- `output/demo_all/memory/` ??Memory block health analysis outputs

---

## Output Validation

```bash
yieldos validate --case output/demo_all/robot --strict
yieldos validate --case output/demo_all/space --strict
yieldos validate --case output/demo_all/semiconductor --strict
yieldos validate --case output/demo_all/semiforge --strict
yieldos validate --case output/demo_all/memory --strict
```

Each should report 59 passed, 0 failed.

---

## Inspecting Outputs

```bash
# Summary of a case
yieldos inspect-output output/demo_semfab

# Open HTML report (browser)
# output/demo_semfab/report.html
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `yieldos version` | Show version and environment info |
| `yieldos doctor` | Check installation health |
| `yieldos semifab analyze --input <dir> --out <dir>` | Analyze SemFab telemetry |
| `yieldos robot analyze --input <file> --out <dir>` | Analyze robot telemetry |
| `yieldos sat analyze --input <file> --out <dir>` | Analyze satellite telemetry |
| `yieldos semiforge simulate --config <file> --out <dir>` | Run SemiForge simulation |
| `yieldos semiforge sweep --config <file> --out <dir>` | Run defect rate sweep |
| `yieldos validate --case <dir>` | Validate output case |
| `yieldos inspect-output <dir>` | Inspect output summary |
| `yieldos generate semfab --rows N --fault F --out <dir>` | Generate synthetic SemFab data |
| `yieldos generate robot --rows N --fault F --out <dir>` | Generate synthetic robot data |
| `yieldos generate satellite --rows N --fault F --out <dir>` | Generate synthetic satellite data |
| `yieldos record --case <dir>` | Append to experience graph |

---

## Result Interpretation

### Output Files

| File | Contents |
|------|----------|
| `state_snapshot.json` | Current asset state, severity, confidence, metrics |
| `evidence_pack.json` | Evidence objects, root cause candidates, missing evidence |
| `ooda_frame.json` | OODA loop analysis (Observe/Orient/Decide/Act) |
| `recovery_candidates.json` | Recommended recovery actions (human review required) |
| `report.md` | Human-readable markdown report |
| `report.html` | HTML report for browser viewing |
| `time_alignment_report.json` | (SemFab) Time axis quality report |
| `evidence_graph.json` | (SemFab) Evidence relationship graph |

### Safety Fields

All JSON outputs include:
```json
{
  "safety": {
    "read_only": true,
    "shadow_only": true,
    "hardware_execution_enabled": false,
    "human_review_required": true,
    "causal_claim_boundary": "candidate_only_not_certified_cause"
  }
}
```

### Interpretation Rules

1. All `root_cause_candidates` are candidates, not certified causes.
2. All `recovery_candidates` require human review before action.
3. `confidence` values are model estimates on synthetic/demo data.
4. `state` values are classification outputs, not certified diagnoses.

---

## Limitations

This is a PoC/MVP release validated on synthetic sample data.

- Not validated on real production fab data
- Not validated on real robot fleet data
- Not validated on real satellite operation data
- Not a live control system
- Not a certified root-cause engine

See [LIMITATIONS.md](LIMITATIONS.md) for full details.

---

## Rebuilding the Release ZIP

```bash
python scripts/build_release.py
```

Output:
```
dist/HAL-YieldOS-v3.0.11-poc-release.zip
dist/MANIFEST.json
dist/CHECKSUMS.sha256
```

---

## CHECKSUMS.sha256 Verification

The `CHECKSUMS.sha256` file inside the ZIP uses paths prefixed with `halyieldos/`:

```
sha256hash  halyieldos/LICENSE.txt
sha256hash  halyieldos/README.md
...
```

To verify file integrity, run from the **directory that contains the `halyieldos/` folder**
(i.e., the extraction parent directory, not inside `halyieldos/` itself):

```bash
# Linux/Mac
sha256sum -c halyieldos/CHECKSUMS.sha256

# Windows (PowerShell ??manual check)
Get-Content halyieldos\CHECKSUMS.sha256 | ForEach-Object {
    $parts = $_ -split '  ', 2
    $expected = $parts[0]; $file = $parts[1]
    $actual = (Get-FileHash $file -Algorithm SHA256).Hash.ToLower()
    if ($actual -eq $expected) { "OK: $file" } else { "FAIL: $file" }
}
```

> **Note**: Run verification from the extraction parent directory, not from inside `halyieldos/`.

---

## SQBM Notes

- **SQBM optional fallback**: validated ??greedy fallback confirmed when `yieldos-sqbm` is not installed
- **Actual SQBM backend execution**: not validated unless `yieldos-sqbm` optional package is installed
- SQBM is a candidate optimizer, not an execution engine ??safety boundaries apply regardless

```bash
# To enable SQBM (when package is available)
pip install hal-yieldos[sqbm]
```

---

## Support

For questions or issues, contact the delivery team.
This release is sample-validated and intended for research, PoC, and MVP evaluation.
It does not certify industrial performance on real production systems.첵첼