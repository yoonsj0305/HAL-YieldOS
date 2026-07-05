# HAL YieldOS — Repository Map

HAL YieldOS v3.0.7

---

## Top-Level Structure

```
halyieldos/
├── yieldos/                    Core package
├── tests/                      Test suite (2500+ tests)
├── samples/                    Synthetic/sanitized sample input data
├── docs/                       Documentation
├── scripts/                    Release and demo utilities
├── .github/                    GitHub issue templates and PR template
├── README.md                   Public-facing overview
├── CONTRIBUTING.md             Contribution guidelines
├── SECURITY.md                 Security policy
├── CITATION.cff                Citation metadata
├── LICENSE.txt                 License
├── pyproject.toml              Package configuration
├── VERSION                     Current version string
├── MANIFEST.json               Release manifest
├── RELEASE_NOTES.md            Version history
└── .gitignore                  Generated artifact exclusions
```

**Not committed to git (generated):**

```
output/          Generated analysis output (gitignored)
dist/            Release ZIPs and wheels (gitignored)
build/           Build artifacts (gitignored)
.pytest_cache/   Pytest cache (gitignored)
__pycache__/     Python bytecode (gitignored)
```

---

## Core Package: `yieldos/`

```
yieldos/
├── cli/
│   └── main.py                 CLI entry point (all commands)
├── core/
│   ├── report_writer.py        Standard Output Bundle writer (22 files)
│   └── ...
├── contracts/
│   ├── meta.py                 Safety constants and schema versions
│   └── ...                     StateSnapshot, EvidencePack, OODAFrame, etc.
├── domains/
│   ├── semfab/
│   │   ├── analyzer.py         Semiconductor analyzer + _build_confidence_report()
│   │   ├── pilot_pack.py       Semiconductor pilot-pack generator
│   │   └── ...
│   ├── robot/
│   │   ├── analyzer.py         Robot telemetry analyzer
│   │   ├── pilot_pack.py       Robot pilot-pack generator
│   │   └── ...
│   ├── space/
│   ├── memory/
│   └── semiforge/
├── pilot/                      Pilot readiness pack (init/check)
├── sample_data/                Bundled sample data (installed with package)
├── demo_runner.py              Direct Python demo runner (no subprocess)
├── VERSION                     Package version
└── MANIFEST.json               Package manifest
```

---

## Tests: `tests/`

```
tests/
├── test_all.py                              Original comprehensive test suite
├── test_version_hygiene_v302.py             Version sync check
├── test_semiconductor_confidence_*.py       SemFab confidence tests (v3.0.4, v3.0.5)
├── test_semfab_confidence_report_writer_propagation.py  (v3.0.6)
├── test_public_docs_exist.py                (v3.0.7) Public docs existence check
├── test_public_readme_safety_boundary.py    (v3.0.7) README safety content check
├── test_github_templates_exist.py           (v3.0.7) GitHub template existence
├── test_public_demo_script.py               (v3.0.7) Demo script safety check
├── test_gitignore_hygiene.py                (v3.0.7) .gitignore content check
├── test_citation_file.py                    (v3.0.7) CITATION.cff content check
├── helpers.py                               Shared test utilities
└── conftest.py                              Pytest configuration
```

Test suite is organized into two tiers:

- **Default** (`python -m pytest -q`): All tests run in under 2 minutes
- **Marker-specific**: `cli_e2e`, `release_heavy`, `installed_wheel`, `packaging`

See [docs/DEVELOPER_VALIDATION.md](DEVELOPER_VALIDATION.md).

---

## Samples: `samples/`

**All sample data is synthetic or sanitized. No real production data is included.**

```
samples/
├── robot_ooda/                  Robot arm telemetry (J3 joint fault scenario)
├── satguard/                    Satellite telemetry (battery degradation scenario)
├── semfab_tel_like/             Semiconductor fab data (STEP_04 drift scenario)
├── semiforge_crossbar/          64×64 ReRAM crossbar config
├── memory_device/               128-block NAND flash health data
├── product_memory_rebinning_demo/ 32 GB MLC NAND binary-FAIL demo
├── pilot_semiconductor/         Semiconductor pilot-pack sample inputs
├── pilot_robot/                 Robot pilot-pack sample inputs
├── robot_industrial/            Robot industrial scenario
└── yieldos_orbit/               Satellite orbit scenario
```

---

## Docs: `docs/`

```
docs/
├── PUBLIC_SAFETY_BOUNDARY.md    Safety boundary for public review
├── DEMO_GUIDE.md                Step-by-step demo walkthrough
├── PILOT_ONE_PAGER.md           One-pager for pilot evaluation
├── SAMPLE_OUTPUTS_GUIDE.md      What each output file contains
├── GITHUB_RELEASE_CHECKLIST.md  Release checklist
├── REPOSITORY_MAP.md            This file
├── TECHNICAL_SPEC.md            Technical specification
├── ARCHITECTURE.md              Architecture overview
├── SEMICONDUCTOR_PILOT_READY.md Semiconductor pilot-pack reference
├── ROBOT_PILOT_READY.md         Robot pilot-pack reference
├── FUNCTIONAL_YIELD_ESSENCE.md  Functional Yield organizing principle
├── DEVELOPER_VALIDATION.md      Two-tier test strategy
├── DELIVERY_GUIDE.md            Delivery packaging guide
├── KNOWN_LIMITATIONS.md         Current limitations
├── SAFETY_BOUNDARY.md           Internal safety boundary spec
└── ja/                          Japanese documentation
```

---

## Scripts: `scripts/`

```
scripts/
├── build_release.py      Build the release ZIP
├── run_public_demo.py    Public demo runner (all domains + pilot-packs)
├── run_demo.py           (deprecated) Use yieldos demo --all instead
└── make_release_zip.py   (deprecated)
```

---

## `.github/`

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.md
│   ├── sample_data_request.md
│   ├── documentation.md
│   └── config.yml
└── PULL_REQUEST_TEMPLATE.md
```

---

*HAL YieldOS v3.0.7*
