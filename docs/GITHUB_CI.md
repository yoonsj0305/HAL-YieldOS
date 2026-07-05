# GitHub CI

HAL YieldOS v3.0.11

---

## tests workflow

File: `.github/workflows/tests.yml`

Runs on push and pull request.

Checks:

- Package installs cleanly from source (`pip install -e .`)
- Full test suite passes (`python -m pytest -q`)
- Health check passes (`yieldos doctor --deep`)
- Launch guard passes (`python scripts/check_launch_guard.py`)

## public-demo workflow

File: `.github/workflows/public-demo.yml`

Manual workflow (`workflow_dispatch`).

Checks:

- Package installs cleanly
- Public demo script runs (`python scripts/run_public_demo.py`)
- Output index generated (`output/public_demo/INDEX.md` exists)
- No recovery_profile.json generated

## Why public demo is manual

The public demo runs all 5 domain analyses, semiconductor pilot-pack, and robot pilot-pack.
This takes longer than a typical unit test run.

Running it manually before each release ensures the demo is always valid:

- Every analysis step passes
- Strict validation passes for all domains
- No recovery_profile.json appears in any output

The demo is fully synthetic and deterministic — sample data is bundled in the repository.
It can be triggered anytime from the GitHub Actions tab.

## Launch guard

File: `scripts/check_launch_guard.py`

Fast check for public launch quality:

- Required files exist (README, public docs, GitHub templates, scripts, .gitignore)
- README includes required safety boundary statements
- .gitignore excludes generated artifacts
- Public docs do not include unsafe affirmative safety claims

Run locally:

```bash
python scripts/check_launch_guard.py
```

Expected output:

```
HAL YieldOS launch guard: PASS
```

## Cross-platform path handling

`scripts/check_launch_guard.py` constructs repository-relative paths with
`Path.joinpath(*rel.split("/"))` via the `repo_path()` helper. This resolves
correctly on Linux, macOS, and Windows. The previous pattern
`ROOT / rel.replace("/", "\\")` failed on Linux and macOS because `\` is a
valid filename character there, not a path separator.

The fix was introduced in v3.0.10 and is verified by
`tests/test_launch_guard_cross_platform_paths.py`.

## release-hygiene workflow

File: `.github/workflows/release-hygiene.yml`

Manual workflow (`workflow_dispatch`).

Catches dirty archive mistakes before GitHub upload.

Checks:

- Package installs cleanly
- Release artifact built with `python scripts/build_release.py`
- Artifact hygiene verified with `python scripts/check_release_artifact.py`

Prevents manually zipped working directories from becoming release artifacts.
Verifies that the official `build_release.py` output does not contain build
folders, cache folders, output folders, old `dist_v*` folders, nested zips,
wheels, tarballs, or `__pycache__/`.

Run locally before each GitHub release:

```bash
python scripts/build_release.py
python scripts/check_release_artifact.py dist/HAL-YieldOS-v3.0.11-poc-release.zip
```

Expected:

```
HAL YieldOS release artifact hygiene: PASS
```

## Safety boundary

CI must not:

- use private data
- call external services or APIs
- control hardware
- execute Recovery Compiler
- generate recovery_profile.json
- require secrets (other than standard GITHUB_TOKEN if needed)

All demo data is synthetic. No real industrial data is ever committed to this repository.

---

*This document is part of HAL YieldOS v3.0.11.*
