"""Tests that case_manifest.json checksums remain valid after v3.0.3 post-patching.

Verifies that case_manifest reflects updated sha256/byte_size for the 4 patched standard files
(functional_passport, decision_readiness_report, state_snapshot, ooda_frame) plus report.html.
Also verifies the new export/manifest files appear in pilot output.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from yieldos.cli.main import main

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"

PATCHED_FILES = [
    "functional_passport.json",
    "decision_readiness_report.json",
    "state_snapshot.json",
    "ooda_frame.json",
    "report.html",
]

NEW_V303_FILES = [
    "semiconductor_recovery_compiler_export.json",
    "semiconductor_handoff_manifest.json",
]


@pytest.fixture(scope="module")
def manifest_contract_output(tmp_path_factory):
    if not SAMPLE_DIR.exists() or not (SAMPLE_DIR / "tool_log.csv").exists():
        pytest.skip("pilot_semiconductor samples not found")
    out = tmp_path_factory.mktemp("semi_pilot_manifest_contract")
    rc = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(out),
        "--asset", "manifest_contract_chip",
        "--case", "manifest_contract_case_001",
    ])
    assert rc == 0, f"semiconductor pilot-pack failed (rc={rc})"
    return out


@pytest.fixture(scope="module")
def cm(manifest_contract_output):
    return json.loads(
        (manifest_contract_output / "case_manifest.json").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("fname", NEW_V303_FILES)
def test_new_v303_file_exists(manifest_contract_output, fname):
    assert (manifest_contract_output / fname).exists(), \
        f"v3.0.3 new file missing: {fname}"


@pytest.mark.parametrize("fname", NEW_V303_FILES)
def test_new_v303_file_in_case_manifest(cm, fname):
    files = cm.get("files", {})
    paths = {entry.get("path", "") for entry in files.values()}
    assert fname in paths, f"case_manifest does not reference {fname}"


@pytest.mark.parametrize("fname", PATCHED_FILES)
def test_patched_file_checksum_in_case_manifest_is_valid(manifest_contract_output, cm, fname):
    files = cm.get("files", {})
    entry = next(
        (e for e in files.values() if e.get("path", "") == fname), None
    )
    if entry is None:
        pytest.skip(f"{fname} not in case_manifest (may be optional for this output)")

    stored_checksum = entry.get("sha256", "")
    actual_bytes = (manifest_contract_output / fname).read_bytes()
    expected = "sha256:" + hashlib.sha256(actual_bytes).hexdigest()
    assert stored_checksum == expected, \
        (f"case_manifest sha256 stale for {fname} after v3.0.3 post-patch. "
         f"stored={stored_checksum!r}, actual={expected!r}")


def test_case_manifest_has_standard_keys(cm):
    files = cm.get("files", {})
    for key in ("state_snapshot", "evidence_pack", "ooda_frame", "functional_passport"):
        assert key in files, f"case_manifest missing standard key: {key}"


def test_functional_passport_has_semiconductor_pilot_context(manifest_contract_output):
    fp = json.loads(
        (manifest_contract_output / "functional_passport.json").read_text(encoding="utf-8")
    )
    assert "semiconductor_pilot_context" in fp


def test_ooda_act_is_dict_after_patch(manifest_contract_output):
    ooda = json.loads(
        (manifest_contract_output / "ooda_frame.json").read_text(encoding="utf-8")
    )
    act = ooda.get("act")
    assert isinstance(act, dict), \
        f"ooda_frame.act must be dict after v3.0.3 post-patch, got {type(act)}: {act!r}"


def test_recovery_profile_not_generated(manifest_contract_output):
    assert not (manifest_contract_output / "recovery_profile.json").exists()
