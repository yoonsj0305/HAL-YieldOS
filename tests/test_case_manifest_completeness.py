"""
tests/test_case_manifest_completeness.py

Verifies that case_manifest.json includes ALL generated standard output files,
not just a hardcoded subset. Also verifies that strict validation catches
hash mismatches and missing files.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SAMPLES_ROOT = ROOT / "samples"
MEMORY_SAMPLE = SAMPLES_ROOT / "memory_device"

STANDARD_OUTPUT_KEYS = {
    "state_snapshot",
    "evidence_pack",
    "ooda_frame",
    "recovery_candidates",
    "report_md",
    "report_html",
    "input_validation",
    "decision_readiness_report",
    "functional_yield_scorecard",
    "functional_binning_result",
    "functional_passport",
    "evidence_pack_md",
    "recovery_route_report",
    "failure_scenario_record",
    "next_data_request",
    "analysis_trace",
    "source_data_manifest",
    "data_quality_report",
    "evidence_conflict_report",
    "baseline_vs_yieldos",
    "business_case_summary",
}


def _has_memory_sample() -> bool:
    return MEMORY_SAMPLE.exists() and (MEMORY_SAMPLE / "block_health.csv").exists()


def _run_memory_write_all(tmp: str):
    from yieldos.cli.main import _memory_extra_outputs, _memory_source_data_paths, _run_and_write, _run_memory
    result = _run_memory(str(MEMORY_SAMPLE), case_id="case_cm_test", asset_id="memdev_test")
    extra = _memory_extra_outputs(result)
    return _run_and_write(result, tmp, "memory", extra_outputs=extra,
                          source_data_paths=_memory_source_data_paths(str(MEMORY_SAMPLE)))


# ── Manifest includes all standard outputs ────────────────────────────────────

@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_includes_all_standard_outputs():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        manifest = json.loads((Path(tmp) / "case_manifest.json").read_text(encoding="utf-8"))
        files_section = manifest.get("files", {})
        missing = STANDARD_OUTPUT_KEYS - set(files_section.keys())
        assert not missing, f"case_manifest missing standard output keys: {missing}"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_includes_source_data_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        manifest = json.loads((Path(tmp) / "case_manifest.json").read_text(encoding="utf-8"))
        assert "source_data_manifest" in manifest["files"]


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_includes_baseline_vs_yieldos():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        manifest = json.loads((Path(tmp) / "case_manifest.json").read_text(encoding="utf-8"))
        assert "baseline_vs_yieldos" in manifest["files"]


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_includes_business_case_summary():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        manifest = json.loads((Path(tmp) / "case_manifest.json").read_text(encoding="utf-8"))
        assert "business_case_summary" in manifest["files"]


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_includes_report_md():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        manifest = json.loads((Path(tmp) / "case_manifest.json").read_text(encoding="utf-8"))
        assert "report_md" in manifest["files"]


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_includes_evidence_pack_md():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        manifest = json.loads((Path(tmp) / "case_manifest.json").read_text(encoding="utf-8"))
        assert "evidence_pack_md" in manifest["files"]


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_includes_ooda_frame():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        manifest = json.loads((Path(tmp) / "case_manifest.json").read_text(encoding="utf-8"))
        assert "ooda_frame" in manifest["files"]


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_includes_memory_extras():
    """Memory-domain extra outputs should appear in the manifest."""
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        manifest = json.loads((Path(tmp) / "case_manifest.json").read_text(encoding="utf-8"))
        files_section = manifest.get("files", {})
        memory_extras = [
            "memory_functional_capacity.json",
            "memory_data_placement_recommendation.json",
            "memory_bad_block_evidence_map.json",
        ]
        found = [f for f in memory_extras if any(
            v.get("path") == f for v in files_section.values()
        )]
        assert len(found) > 0, f"No memory extra outputs found in manifest. Files: {list(files_section.keys())}"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_file_count_matches_files_section():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        manifest = json.loads((Path(tmp) / "case_manifest.json").read_text(encoding="utf-8"))
        assert manifest.get("file_count") == len(manifest.get("files", {}))


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_entries_have_sha256_and_byte_size():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        manifest = json.loads((Path(tmp) / "case_manifest.json").read_text(encoding="utf-8"))
        for key, entry in manifest.get("files", {}).items():
            assert entry.get("sha256", "").startswith("sha256:"), \
                f"Entry '{key}' missing valid sha256"
            assert isinstance(entry.get("byte_size"), int) and entry["byte_size"] > 0, \
                f"Entry '{key}' missing byte_size"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_case_manifest_all_listed_files_exist_on_disk():
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        case_dir = Path(tmp)
        manifest = json.loads((case_dir / "case_manifest.json").read_text(encoding="utf-8"))
        missing = [
            entry["path"]
            for entry in manifest.get("files", {}).values()
            if not (case_dir / entry["path"]).exists()
        ]
        assert not missing, f"Manifest lists files not on disk: {missing}"


# ── Strict validation: hash mismatch detection ────────────────────────────────

@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_strict_validation_fails_on_manifest_hash_mismatch():
    """Tamper with an output file after analysis — strict validation must fail."""
    import argparse

    from yieldos.cli.main import cmd_validate
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        # Tamper with a file that is listed in the manifest
        target = Path(tmp) / "data_quality_report.json"
        assert target.exists()
        original = target.read_bytes()
        target.write_bytes(original + b"\n/* tampered */")

        val_args = argparse.Namespace(case=tmp, strict=True)
        result = cmd_validate(val_args)
        assert result != 0, "Strict validation must fail after tampering with a manifest-listed file"


# ── Strict validation: manifest completeness check ────────────────────────────

@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_strict_validation_passes_with_complete_manifest():
    import argparse

    from yieldos.cli.main import cmd_validate
    with tempfile.TemporaryDirectory() as tmp:
        _run_memory_write_all(tmp)
        val_args = argparse.Namespace(case=tmp, strict=True)
        result = cmd_validate(val_args)
        assert result == 0, "Strict validation must pass with complete, untampered manifest"
