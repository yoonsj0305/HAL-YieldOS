#!/usr/bin/env python3
"""
HAL YieldOS release builder.

Creates:
  dist/HAL-YieldOS-v<VERSION>-poc-release.zip  (POSIX paths, versioned root folder)
  dist/MANIFEST.json
  dist/CHECKSUMS.sha256

Usage:
  python scripts/build_release.py                              # build release zip
  python scripts/build_release.py --clean                      # clean artifacts, then build
  python scripts/build_release.py --verify <path-to-zip>       # verify existing zip
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SRC_ROOT = Path(__file__).parent.parent
DIST_DIR = SRC_ROOT / "dist"
VERSION = (SRC_ROOT / "VERSION").read_text(encoding="utf-8").strip() if (SRC_ROOT / "VERSION").exists() else "1.0.0"
RELEASE_NAME = f"HAL-YieldOS-v{VERSION}-poc-release"
ZIP_NAME = f"{RELEASE_NAME}.zip"

EXCLUDE_DIRS = {
    "output", "outputs", "artifacts",
    "__pycache__", ".pytest_cache", ".pytest_tmp", ".ruff_cache",
    ".git", "_sqbm_inspect", "dist", "build",
    ".venv", ".env", ".mypy_cache", "htmlcov",
    "release_tmp", "tmp", "temp", "old_dist", "old_build",
}
EXCLUDE_DIR_PREFIXES = ("dist_v",)
EXCLUDE_EXTS = {".pyc", ".pyo", ".zip", ".whl", ".tar.gz", ".coverage"}
EXCLUDE_SUFFIXES = {".egg-info", ".dist-info"}
ROOT_EXCLUDE_NAMES = {"MANIFEST.json", "CHECKSUMS.sha256"}

EXCLUDED_ARTIFACT_PATTERNS = [
    "build/", "dist/", "output/", "outputs/", "artifacts/",
    ".pytest_tmp/", ".pytest_cache/", ".ruff_cache/",
    "__pycache__/", ".mypy_cache/", "*.pyc", "*.whl",
    "*.tar.gz", "*.zip", "dist_v*/", "*.egg-info/",
]

_SCAN_FORBIDDEN_PATH_PARTS = [
    "/build/", "/dist/", "/output/", "/outputs/", "/artifacts/",
    "/.pytest_tmp/", "/.pytest_cache/", "/.ruff_cache/", "/__pycache__/",
    "/.mypy_cache/", "/dist_v",
]
_SCAN_FORBIDDEN_EXTS = (".pyc", ".pyo", ".whl", ".tar.gz")

STANDARD_OUTPUT_BUNDLE = [
    "state_snapshot.json",
    "evidence_pack.json",
    "ooda_frame.json",
    "recovery_candidates.json",
    "report.md",
    "report.html",
    "input_validation.json",
    "decision_readiness_report.json",
    "functional_yield_scorecard.json",
    "functional_binning_result.json",
    "functional_passport.json",
    "evidence_pack.md",
    "recovery_route_report.json",
    "failure_scenario_record.json",
    "next_data_request.json",
    "analysis_trace.json",
    "source_data_manifest.json",
    "data_quality_report.json",
    "evidence_conflict_report.json",
    "baseline_vs_yieldos.json",
    "business_case_summary.json",
    "case_manifest.json",
]


def should_exclude(rel: Path) -> bool:
    for part in rel.parts:
        if part in EXCLUDE_DIRS:
            return True
        if any(part.endswith(s) for s in EXCLUDE_SUFFIXES):
            return True
        if any(part.startswith(p) for p in EXCLUDE_DIR_PREFIXES):
            return True
    return False


def scan_release_zip(zip_path: Path, release_name: str | None = None) -> list[str]:
    """
    Inspect every entry in the release zip for hygiene violations.
    Returns a list of violation strings. Empty list = clean.

    This function is importable for direct use in tests.
    """
    if release_name is None:
        release_name = RELEASE_NAME

    violations: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            # Root folder must be exactly release_name/
            if not name.startswith(f"{release_name}/"):
                violations.append(f"WRONG_ROOT: {name!r} (expected prefix '{release_name}/')")
                continue
            # No forbidden path components (check using prefixed slash to avoid false positives)
            prefixed = f"/{name}"
            for part in _SCAN_FORBIDDEN_PATH_PARTS:
                if part in prefixed:
                    violations.append(f"FORBIDDEN_PATH ({part!r}): {name!r}")
                    break
            else:
                for ext in _SCAN_FORBIDDEN_EXTS:
                    if name.endswith(ext):
                        violations.append(f"FORBIDDEN_EXT ({ext!r}): {name!r}")
                        break
                else:
                    if name.endswith(".zip"):
                        violations.append(f"NESTED_ZIP: {name!r}")
    return violations


def collect_files() -> list[tuple[Path, Path]]:
    files = []
    for f in SRC_ROOT.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix in EXCLUDE_EXTS:
            continue
        rel = f.relative_to(SRC_ROOT)
        if len(rel.parts) == 1 and rel.name in ROOT_EXCLUDE_NAMES:
            continue
        if should_exclude(rel):
            continue
        files.append((f, rel))
    return sorted(files, key=lambda x: str(x[1]))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_manifest(files: list[tuple[Path, Path]]) -> dict:
    checksummed = len(files)
    zip_entries = checksummed + 2  # +MANIFEST.json +CHECKSUMS.sha256
    return {
        "name": "hal-yieldos",
        "version": VERSION,
        "release_name": RELEASE_NAME,
        "release_type": "poc-mvp",
        "checksummed_file_count": checksummed,
        "zip_entry_count": zip_entries,
        "file_count_kind": "checksummed_source_files",
        "generated_release_files": ["MANIFEST.json", "CHECKSUMS.sha256"],
        "excluded_artifact_patterns": EXCLUDED_ARTIFACT_PATTERNS,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "python_requires": ">=3.10",
        "entrypoint": "yieldos",
        "safety": {
            "read_only": True,
            "hardware_execution_enabled": False,
            "candidate_only_rca": True,
            "shadow_only": True,
            "human_review_required": True,
        },
        "domains": ["robot", "space", "semiconductor", "semiforge", "memory"],
        "canonical_domains": ["robot", "space", "semiconductor", "semiforge", "memory"],
        "domain_adapters": {
            "robot": "robotics",
            "space": "satellite",
            "semiconductor": "semiconductor_fab",
            "semiforge": "semiforge_crossbar",
            "memory": "memory_device",
        },
        "domain_aliases": {
            "satellite": "space", "satguard": "space", "sat": "space",
            "semfab": "semiconductor", "edge_ai": "semiconductor",
            "dark_cell": "semiforge",
        },
        "domain_extra_outputs": {
            "memory": [
                "memory_functional_capacity.json",
                "memory_data_placement_recommendation.json",
                "memory_bad_block_evidence_map.json",
            ],
        },
        "optional_layers": ["sqbm", "scheduler"],
        "standard_output_bundle": STANDARD_OUTPUT_BUNDLE,
        "causal_claim_boundary": "candidate_only_not_certified_cause",
        "note": "sample-validated PoC/MVP - not certified for real production systems",
    }


def build_checksums(files: list[tuple[Path, Path]]) -> str:
    lines = []
    for f, rel in files:
        digest = sha256_file(f)
        posix_path = RELEASE_NAME + "/" + "/".join(rel.parts)
        lines.append(f"{digest}  {posix_path}")
    return "\n".join(lines) + "\n"


def build_zip(files: list[tuple[Path, Path]], manifest: dict, checksums: str, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f, rel in files:
            arcname = RELEASE_NAME + "/" + "/".join(rel.parts)
            zf.write(f, arcname)
        zf.writestr(f"{RELEASE_NAME}/MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr(f"{RELEASE_NAME}/CHECKSUMS.sha256", checksums)


def sync_bundled_files() -> None:
    """Sync root MANIFEST.json and VERSION into yieldos/ as bundled package data."""
    root_manifest = SRC_ROOT / "MANIFEST.json"
    bundled_manifest = SRC_ROOT / "yieldos" / "MANIFEST.json"
    root_version = SRC_ROOT / "VERSION"
    bundled_version = SRC_ROOT / "yieldos" / "VERSION"

    if root_manifest.exists():
        manifest_data = json.loads(root_manifest.read_text(encoding="utf-8"))
        manifest_data["version"] = VERSION
        bundled_manifest.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")
        bundle = manifest_data.get("standard_output_bundle", [])
        assert len(bundle) == 22, f"standard_output_bundle must have 22 files, got {len(bundle)}"
        assert manifest_data["version"] == VERSION, f"MANIFEST version must be {VERSION}"
        print(f"[build_release] Synced yieldos/MANIFEST.json (version={VERSION}, bundle={len(bundle)} files)")
    else:
        print("[build_release] WARNING: root MANIFEST.json not found, skipping bundled sync")

    if root_version.exists():
        bundled_version.write_text(VERSION + "\n", encoding="utf-8")
        print(f"[build_release] Synced yieldos/VERSION ({VERSION})")


def clean_artifacts() -> None:
    """Remove generated build/cache/output artifacts from source tree."""
    targets = [
        SRC_ROOT / "build",
        SRC_ROOT / "dist",
        SRC_ROOT / "output",
        SRC_ROOT / ".pytest_tmp",
        SRC_ROOT / ".pytest_cache",
        SRC_ROOT / ".ruff_cache",
    ]
    for t in targets:
        if t.exists():
            shutil.rmtree(t, ignore_errors=True)
            print(f"[build_release] Cleaned: {t.name}/")

    for pycache in SRC_ROOT.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache, ignore_errors=True)
    print("[build_release] Cleaned: __pycache__/ (all)")


def cmd_verify(zip_path_str: str) -> int:
    zip_path = Path(zip_path_str)
    if not zip_path.exists():
        print(f"[build_release] ERROR: zip not found: {zip_path}")
        return 1
    print(f"[build_release] Verifying: {zip_path}")
    violations = scan_release_zip(zip_path)
    if violations:
        print(f"[build_release] FAIL: {len(violations)} violation(s):")
        for v in violations:
            print(f"  {v}")
        return 1
    with zipfile.ZipFile(zip_path) as zf:
        try:
            manifest_data = json.loads(zf.read(f"{RELEASE_NAME}/MANIFEST.json"))
        except KeyError:
            print(f"[build_release] FAIL: {RELEASE_NAME}/MANIFEST.json not found in zip")
            return 1
    if manifest_data.get("version") != VERSION:
        print(f"[build_release] FAIL: MANIFEST.json version={manifest_data.get('version')!r} != {VERSION!r}")
        return 1
    if manifest_data.get("release_name") != RELEASE_NAME:
        print(f"[build_release] FAIL: MANIFEST.json release_name={manifest_data.get('release_name')!r} != {RELEASE_NAME!r}")
        return 1
    print(f"[build_release] PASS: {zip_path.name}")
    print(f"  version={manifest_data['version']}")
    print(f"  release_name={manifest_data['release_name']}")
    print(f"  entries={len(zf.namelist()) if False else '(reopen to count)'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="HAL YieldOS release builder")
    parser.add_argument("--clean", action="store_true",
                        help="Remove generated artifacts before building")
    parser.add_argument("--verify", metavar="ZIP",
                        help="Verify an existing release zip and exit")
    args = parser.parse_args()

    if args.verify:
        return cmd_verify(args.verify)

    if args.clean:
        clean_artifacts()

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    sync_bundled_files()

    # Remove stale artifacts from dist/
    for stale in (
        list(DIST_DIR.glob("*.whl"))
        + list(DIST_DIR.glob("*.tar.gz"))
        + list(DIST_DIR.glob("*.zip"))
        + list(DIST_DIR.glob("MANIFEST.json"))
        + list(DIST_DIR.glob("CHECKSUMS.sha256"))
    ):
        stale.unlink()
        print(f"[build_release] Removed stale: {stale.name}")

    zip_path = DIST_DIR / ZIP_NAME

    print(f"[build_release] HAL YieldOS v{VERSION} - building release...")
    print(f"[build_release] Release name: {RELEASE_NAME}")
    print(f"[build_release] Source: {SRC_ROOT}")
    print(f"[build_release] Output: {zip_path}")

    files = collect_files()
    print(f"[build_release] Collecting {len(files)} files...")

    manifest = build_manifest(files)
    checksums = build_checksums(files)

    manifest_path = DIST_DIR / "MANIFEST.json"
    checksums_path = DIST_DIR / "CHECKSUMS.sha256"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    checksums_path.write_text(checksums, encoding="utf-8")
    print(f"[build_release] MANIFEST.json -> {manifest_path}")
    print(f"[build_release] CHECKSUMS.sha256 -> {checksums_path}")

    build_zip(files, manifest, checksums, zip_path)

    size_kb = zip_path.stat().st_size / 1024
    with zipfile.ZipFile(zip_path) as zf:
        entry_count = len(zf.namelist())

    print(f"\n[build_release] Created: {zip_path}")
    print(f"[build_release] Size:    {size_kb:.1f} KB")
    print(f"[build_release] Entries: {entry_count}")
    print(f"[build_release] Root folder: {RELEASE_NAME}/")

    # Final hygiene scan using check_release_artifact.py
    print("[build_release] Running final hygiene scan...")
    _checker = Path(__file__).parent / "check_release_artifact.py"
    if _checker.exists():
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("check_release_artifact", _checker)
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        violations = _mod.validate_release_artifact(zip_path, expected_version=VERSION)
    else:
        violations = scan_release_zip(zip_path)
    if violations:
        print(f"[build_release] ERROR: {len(violations)} hygiene violation(s):")
        for v in violations:
            print(f"  {v}")
        return 1

    print("[build_release] Release artifact hygiene: PASS")
    print("\n[build_release] Release complete!")
    print(f"  ZIP:      {zip_path}")
    print(f"  MANIFEST: {manifest_path}")
    print(f"  SHA256:   {checksums_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
