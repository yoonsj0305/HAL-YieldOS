#!/usr/bin/env python3
"""
HAL YieldOS -- Release Artifact Hygiene Checker

Validates a release zip before GitHub upload.
Rejects dirty archives containing build folders, cache folders, output folders,
nested zips, wheels, tarballs, pyc files, or old dist_v* folders.

Usage:
    python scripts/check_release_artifact.py dist/HAL-YieldOS-v3.0.11-poc-release.zip

No external dependencies. No hardware control. No Recovery Compiler execution.
No recovery_profile.json generated.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

FORBIDDEN_PATH_FRAGMENTS = [
    "/build/",
    "/dist/",
    "/output/",
    "/outputs/",
    "/artifacts/",
    "/.ruff_cache/",
    "/.pytest_cache/",
    "/.pytest_tmp/",
    "/__pycache__/",
    "/htmlcov/",
    "/.mypy_cache/",
    "/.venv/",
    "/venv/",
    "/dist_v",
    ".egg-info/",
]

FORBIDDEN_SUFFIXES = [
    ".pyc",
    ".pyo",
    ".whl",
    ".tar.gz",
    ".zip",
]

_REQUIRED_ENTRIES = [
    "MANIFEST.json",
    "VERSION",
    "pyproject.toml",
    "README.md",
    "RELEASE_NOTES.md",
    "scripts/check_launch_guard.py",
    "scripts/run_public_demo.py",
    "docs/PUBLIC_SAFETY_BOUNDARY.md",
    ".github/workflows/tests.yml",
    ".github/workflows/public-demo.yml",
]


def validate_release_artifact(
    zip_path: Path, expected_version: str | None = None
) -> list[str]:
    """
    Validate a release zip artifact for hygiene.
    Returns a list of error strings. Empty list = PASS.

    Importable from build_release.py and tests.
    """
    errors: list[str] = []

    if not zip_path.exists():
        errors.append(f"FILE_NOT_FOUND: {zip_path}")
        return errors

    if zip_path.suffix != ".zip":
        errors.append(f"NOT_A_ZIP: {zip_path}")
        return errors

    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
    except zipfile.BadZipFile as e:
        errors.append(f"BAD_ZIP: {e}")
        return errors

    if not names:
        errors.append("EMPTY_ZIP: no entries")
        return errors

    zip_stem = zip_path.stem
    expected_root = zip_stem + "/"

    if expected_version is not None and f"v{expected_version}" not in zip_stem:
        errors.append(
            f"VERSION_MISMATCH: zip name {zip_stem!r} does not contain v{expected_version}"
        )

    wrong_root = [n for n in names if not n.startswith(expected_root)]
    for name in wrong_root:
        errors.append(f"WRONG_ROOT: {name!r} (expected prefix {expected_root!r})")

    present = {n[len(expected_root):] for n in names if n.startswith(expected_root)}
    for req in _REQUIRED_ENTRIES:
        if req not in present:
            errors.append(f"MISSING_REQUIRED: {req}")

    for name in names:
        prefixed = "/" + name
        for frag in FORBIDDEN_PATH_FRAGMENTS:
            if frag in prefixed:
                errors.append(f"FORBIDDEN_PATH ({frag!r}): {name!r}")
                break
        else:
            for suf in FORBIDDEN_SUFFIXES:
                if name.endswith(suf):
                    if suf == ".zip":
                        errors.append(f"NESTED_ZIP: {name!r}")
                    else:
                        errors.append(f"FORBIDDEN_SUFFIX ({suf!r}): {name!r}")
                    break

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_release_artifact.py <path-to-release.zip>")
        return 1

    zip_path = Path(sys.argv[1])
    print(f"HAL YieldOS release artifact hygiene check: {zip_path}")

    errors = validate_release_artifact(zip_path)

    if errors:
        print(f"HAL YieldOS release artifact hygiene: FAIL ({len(errors)} issue(s))")
        for e in errors:
            print(f"  FAIL: {e}")
        return 1

    print("HAL YieldOS release artifact hygiene: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
