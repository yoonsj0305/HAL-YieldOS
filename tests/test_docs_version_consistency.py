"""
tests/test_docs_version_consistency.py

Verifies that all documentation and metadata files are consistent
with the current version (read from VERSION file) and do not reference
stale versions in current-version contexts.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"

CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

DOCS_REQUIRING_CURRENT_VERSION = [
    "README.md",
    "docs/KNOWN_LIMITATIONS.md",
    "docs/DELIVERY_GUIDE.md",
    "docs/TECHNICAL_SPEC.md",
    "docs/VALIDATION_METHOD.md",
    "docs/ANONYMIZATION_GUIDE.md",
    "docs/PILOT_PROPOSAL_TEMPLATE.md",
    "docs/ROBOT_DATA_SCHEMA.md",
    "docs/ARCHITECTURE.md",
]

FORBIDDEN_CURRENT_PHRASES = [
    "Current version: v2.5.1",
    "Current version: v2.7.0",
    "Current version: v2.8.0",
    "Current version: v2.8.1",
    "Current version: v2.8.2",
    "HAL YieldOS v2.5.1 Technical Specification",
    "HAL YieldOS v2.7.0 is a sample-validated",
    "HAL YieldOS v2.8.0 is a sample-validated",
    "does not exist in v2.8.1",
    "does not exist in v2.8.2",
]


# ── Version metadata consistency ─────────────────────────────────────────────

def test_version_file_is_current():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert version == CURRENT_VERSION


def test_pyproject_version_matches():
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{CURRENT_VERSION}"' in content, \
        f"pyproject.toml must have version = \"{CURRENT_VERSION}\""


def test_manifest_version_matches():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["version"] == CURRENT_VERSION, \
        f"MANIFEST.json version must be '{CURRENT_VERSION}', got '{manifest.get('version')}'"


def test_yieldos_version_file_matches():
    ver = (ROOT / "yieldos" / "VERSION").read_text(encoding="utf-8").strip()
    assert ver == CURRENT_VERSION, \
        f"yieldos/VERSION must be '{CURRENT_VERSION}', got '{ver}'"


def test_yieldos_manifest_version_matches():
    manifest = json.loads((ROOT / "yieldos" / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["version"] == CURRENT_VERSION, \
        f"yieldos/MANIFEST.json version must be '{CURRENT_VERSION}', got '{manifest.get('version')}'"


def test_all_five_version_files_consistent():
    root_ver = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    pkg_ver = (ROOT / "yieldos" / "VERSION").read_text(encoding="utf-8").strip()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    root_manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    pkg_manifest = json.loads((ROOT / "yieldos" / "MANIFEST.json").read_text(encoding="utf-8"))

    assert root_ver == pkg_ver, f"VERSION ({root_ver}) != yieldos/VERSION ({pkg_ver})"
    assert f'version = "{root_ver}"' in pyproject, \
        f"pyproject.toml version must match VERSION ({root_ver})"
    assert root_manifest["version"] == root_ver, \
        f"MANIFEST.json ({root_manifest['version']}) != VERSION ({root_ver})"
    assert pkg_manifest["version"] == root_ver, \
        f"yieldos/MANIFEST.json ({pkg_manifest['version']}) != VERSION ({root_ver})"


# ── Current docs must reference the current version ──────────────────────────

def test_docs_current_version_is_current():
    """Docs in DOCS_REQUIRING_CURRENT_VERSION must contain the current version or 'v2.8.x'."""
    for path_str in DOCS_REQUIRING_CURRENT_VERSION:
        path = ROOT / path_str
        assert path.exists(), f"{path_str} must exist"
        text = path.read_text(encoding="utf-8")
        assert CURRENT_VERSION in text or "v2.8.x" in text, \
            f"{path_str} must contain current version '{CURRENT_VERSION}' or 'v2.8.x'"


# ── Stale current-version phrases must not appear ────────────────────────────

def test_docs_do_not_use_old_versions_as_current():
    """
    FORBIDDEN_CURRENT_PHRASES that indicate stale current-version context
    must not appear in any doc file (RELEASE_NOTES.md is exempt as historical archive).
    """
    checked_paths = [
        p for p in DOCS.glob("**/*.md")
        if p.name != "RELEASE_NOTES.md"
    ] + [ROOT / "README.md"]

    bad = []
    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        for phrase in FORBIDDEN_CURRENT_PHRASES:
            if phrase in text:
                bad.append(f"{path.name}: {phrase!r}")
    assert not bad, "Stale current-version phrases found:\n" + "\n".join(bad)


# ── docs/DELIVERY_GUIDE.md ───────────────────────────────────────────────────

def test_delivery_guide_zip_name_is_current():
    content = (DOCS / "DELIVERY_GUIDE.md").read_text(encoding="utf-8")
    assert f"v{CURRENT_VERSION}-poc-release.zip" in content, \
        f"DELIVERY_GUIDE.md must reference v{CURRENT_VERSION}-poc-release.zip"


def test_delivery_guide_no_old_zip_names():
    content = (DOCS / "DELIVERY_GUIDE.md").read_text(encoding="utf-8")
    for stale in ("v2.1.0-poc-release.zip", "v2.5.1-poc-release.zip",
                  "v2.7.0-poc-release.zip", "v2.8.0-poc-release.zip",
                  "v2.8.1-poc-release.zip", "v2.8.2-poc-release.zip", "v2.8.3-poc-release.zip"):
        assert stale not in content, \
            f"DELIVERY_GUIDE.md must not reference stale {stale}"


def test_delivery_guide_no_v210_zip():
    content = (DOCS / "DELIVERY_GUIDE.md").read_text(encoding="utf-8")
    assert "v2.1.0-poc-release.zip" not in content


def test_delivery_guide_no_4_domain_demos():
    content = (DOCS / "DELIVERY_GUIDE.md").read_text(encoding="utf-8").lower()
    assert "all 4 domain" not in content


def test_delivery_guide_has_memory_in_demo_structure():
    content = (DOCS / "DELIVERY_GUIDE.md").read_text(encoding="utf-8")
    assert "memory" in content.lower()


def test_delivery_guide_cli_uses_simulate_not_run():
    content = (DOCS / "DELIVERY_GUIDE.md").read_text(encoding="utf-8")
    assert "semiforge simulate" in content
    assert "semiforge run" not in content


# ── docs/VALIDATION_METHOD.md ────────────────────────────────────────────────

def test_validation_method_version_is_current():
    content = (DOCS / "VALIDATION_METHOD.md").read_text(encoding="utf-8")
    assert CURRENT_VERSION in content or "v2.8.x" in content, \
        "VALIDATION_METHOD.md must reference current version"


def test_validation_method_no_stale_version_as_current():
    content = (DOCS / "VALIDATION_METHOD.md").read_text(encoding="utf-8")
    for stale in ("v2.5.1 is validated", "HAL YieldOS v2.5.1 is"):
        assert stale not in content


def test_validation_method_no_v210():
    content = (DOCS / "VALIDATION_METHOD.md").read_text(encoding="utf-8")
    assert "v2.1.0" not in content


def test_validation_method_no_4_domain_demos():
    content = (DOCS / "VALIDATION_METHOD.md").read_text(encoding="utf-8").lower()
    assert "all 4 domain" not in content


def test_validation_method_has_memory_in_table():
    content = (DOCS / "VALIDATION_METHOD.md").read_text(encoding="utf-8")
    assert "memory" in content.lower()


def test_validation_method_has_5_domains():
    content = (DOCS / "VALIDATION_METHOD.md").read_text(encoding="utf-8")
    assert "5 domain" in content.lower() or "5-domain" in content.lower() or \
           "all 5" in content.lower()


def test_validation_method_cli_uses_simulate():
    content = (DOCS / "VALIDATION_METHOD.md").read_text(encoding="utf-8")
    assert "semiforge simulate" in content


# ── README.md ────────────────────────────────────────────────────────────────

def test_readme_no_v210_zip_reference():
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "v2.1.0-poc-release.zip" not in content


def test_readme_no_4_domain_demos():
    content = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "all 4 domain demos" not in content


def test_readme_has_stable_baseline_statement():
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    assert CURRENT_VERSION in content or "v2.8.x" in content, \
        "README must mention the current stable baseline version"


# ── No stale v2.1.0 zip reference across all docs ───────────────────────────

def test_all_docs_no_v210_zip():
    bad_files = []
    for doc in DOCS.glob("*.md"):
        if "v2.1.0-poc-release.zip" in doc.read_text(encoding="utf-8"):
            bad_files.append(doc.name)
    assert not bad_files, \
        f"These docs still reference v2.1.0-poc-release.zip: {bad_files}"


# ── RELEASE_NOTES.md ─────────────────────────────────────────────────────────

def test_release_notes_has_current_version_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert f"## v{CURRENT_VERSION}" in content, \
        f"RELEASE_NOTES.md must have a v{CURRENT_VERSION} section"


def test_release_notes_has_v282_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.8.2" in content


def test_release_notes_has_v281_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.8.1" in content


def test_release_notes_has_v280_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.8.0" in content


def test_release_notes_has_v271_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.7.1" in content


def test_release_notes_has_v270_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.7.0" in content


def test_release_notes_has_v262_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.6.2" in content


def test_release_notes_has_v261_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.6.1" in content


def test_release_notes_has_v260_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.6.0" in content


def test_release_notes_has_v253_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.5.3" in content


def test_release_notes_has_v252_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.5.2" in content


def test_release_notes_has_v251_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.5.1" in content


def test_release_notes_has_v250_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.5.0" in content


def test_release_notes_has_v241_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.4.1" in content


def test_release_notes_has_v240_section():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "## v2.4.0" in content


def test_release_notes_no_v240_roadmap_label():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "v2.4 roadmap" not in content.lower()


def test_release_notes_schedule_not_in_safe_prefixes():
    content = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    lines = content.splitlines()
    in_safe_section = False
    for line in lines:
        if "safe_action_prefix" in line.lower() or "safe prefix" in line.lower():
            in_safe_section = True
        if in_safe_section and "schedule_" in line and "FORBIDDEN" not in line and "moved" not in line.lower():
            if line.strip().startswith("`schedule_`") or line.strip() == "`schedule_`":
                assert False, "RELEASE_NOTES.md must not list 'schedule_' as a safe prefix"


# ── MANIFEST.json standard output bundle ────────────────────────────────────

def test_manifest_has_22_standard_output_files():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    bundle = manifest.get("standard_output_bundle", [])
    assert len(bundle) == 22, \
        f"MANIFEST.json standard_output_bundle must have 22 files, got {len(bundle)}"


def test_manifest_includes_v24_new_files():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    bundle = manifest.get("standard_output_bundle", [])
    v24_files = {
        "source_data_manifest.json",
        "data_quality_report.json",
        "evidence_conflict_report.json",
        "baseline_vs_yieldos.json",
        "business_case_summary.json",
    }
    for f in v24_files:
        assert f in bundle, f"MANIFEST.json must include {f} in standard_output_bundle"
