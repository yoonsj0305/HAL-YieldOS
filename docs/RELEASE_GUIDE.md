# HAL YieldOS Release Guide

This guide describes the official release packaging procedure for HAL YieldOS.

---

## Official Release Artifact

The official release artifact must be generated only through:

```bash
python scripts/build_release.py
```

The official release zip is placed in `dist/`:

```
dist/HAL-YieldOS-v<version>-poc-release.zip
```

The internal top-level folder inside the zip is:

```
HAL-YieldOS-v<version>-poc-release/
```

Both the zip filename and the internal root folder are derived dynamically from
the `VERSION` file. They are never hardcoded.

---

## Excluded Artifacts

The release zip must not include:

| Category | Patterns |
|----------|----------|
| Build artifacts | `build/`, `dist/` |
| Demo outputs | `output/`, `outputs/`, `artifacts/` |
| Test cache | `.pytest_tmp/`, `.pytest_cache/`, `.ruff_cache/` |
| Compiled Python | `__pycache__/`, `*.pyc`, `*.pyo` |
| Old dist dirs | `dist_v*/` (e.g., `dist_v287/`, `dist_v289/`) |
| Wheels / tarballs | `*.whl`, `*.tar.gz` |
| Nested zip files | `*.zip` (no inner zips) |
| Package metadata | `*.egg-info/`, `*.dist-info/` |
| Virtual environments | `.venv/`, `venv/`, `env/` |

---

## Pre-Release Validation Checklist

Run these commands before building the release zip:

```bash
# 1. Default test suite
python -m pytest -q

# 2. Lint
python -m ruff check .

# 3. Build wheel (optional, for installed_wheel validation)
python -m build

# 4. Doctor deep check
yieldos doctor --deep

# 5. Marker-specific suites
python -m pytest -q -m cli_e2e
python -m pytest -q -m release_heavy
python -m pytest -q -m installed_wheel
python -m pytest -q -m packaging
```

---

## Building the Release

```bash
# Standard build
python scripts/build_release.py

# Build with pre-cleanup (removes build/, dist/, output/, caches)
python scripts/build_release.py --clean

# Verify an existing zip
python scripts/build_release.py --verify dist/HAL-YieldOS-v<version>-poc-release.zip
```

The builder automatically runs a final hygiene scan after creating the zip.
It fails with a non-zero exit code if any violations are detected.

---

## What the Hygiene Scan Checks

After building, `build_release.py` scans every zip entry for:

1. **Root folder name** — must be `HAL-YieldOS-v<version>-poc-release/` (not `halyieldos/`)
2. **No forbidden path components** — `/build/`, `/dist/`, `/output/`, `/__pycache__/`, etc.
3. **No forbidden extensions** — `.pyc`, `.pyo`, `.whl`, `.tar.gz`
4. **No nested zip files** — no `.zip` files inside the archive
5. **No `dist_v*` directories** — old versioned dist folders excluded

---

## MANIFEST.json and CHECKSUMS.sha256

The release zip contains two generated files at the root:

- `HAL-YieldOS-v<version>-poc-release/MANIFEST.json` — release manifest with:
  - `version` — current version
  - `release_name` — `HAL-YieldOS-v<version>-poc-release`
  - `checksummed_file_count` — number of source files checksummed
  - `zip_entry_count` — total zip entries (source + generated)
  - `excluded_artifact_patterns` — list of excluded patterns
  - `generated_release_files` — `["MANIFEST.json", "CHECKSUMS.sha256"]`

- `HAL-YieldOS-v<version>-poc-release/CHECKSUMS.sha256` — SHA-256 hashes for all source files, using `HAL-YieldOS-v<version>-poc-release/` path prefix.

---

## Release Marker Tests

The `release_heavy` test suite validates the release zip:

```bash
python -m pytest -q -m release_heavy
```

These tests:
- Verify the root folder is correctly named
- Verify no nested artifacts (old zips, dist_v*, output, .pytest_tmp)
- Verify CHECKSUMS.sha256 excludes artifact paths
- Verify MANIFEST.json has required fields
- Unit-test the `scan_release_zip()` function directly

## Release-Heavy Test Runtime

Release-heavy tests build the release archive **once per pytest session** using
a shared `release_zip_path` session fixture in `tests/conftest.py`. All
archive-inspection tests reuse that one zip.

**Correct usage:**

```bash
python -m pytest -q -m release_heavy
```

**Incorrect usage (do not do this):**

```
# Running scripts/build_release.py separately inside every release test
```

The fixture is session-scoped. A single `python -m pytest -q -m release_heavy`
invocation triggers exactly one build, then all inspection tests reuse the
result.

---

## Version Bump Procedure

When releasing a new version:

1. Update `VERSION` (BOM-free UTF-8)
2. Update `pyproject.toml` → `version = "<new_version>"`
3. Update `MANIFEST.json` and `yieldos/MANIFEST.json` → `"version": "<new_version>"`
4. Update `yieldos/VERSION`
5. Update `docs/*.md`, `README.md`, `RELEASE_NOTES.md`
6. Run ruff: `python -m ruff check .`
7. Run tests: `python -m pytest -q`
8. Build: `python scripts/build_release.py`
9. Verify: `python scripts/build_release.py --verify dist/HAL-YieldOS-v<new_version>-poc-release.zip`

---

*HAL YieldOS — read-only Functional Yield Evidence Layer.*
*Human review required before any operational decision.*
