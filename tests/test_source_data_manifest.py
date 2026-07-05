"""
tests/test_source_data_manifest.py

Verifies source_data_manifest.json contains real input file metadata:
sha256, byte_size, rows, columns, file_kind, exists, claim_boundary.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SAMPLES_ROOT = ROOT / "samples"
MEMORY_SAMPLE = SAMPLES_ROOT / "memory_device"


def _has_memory_sample() -> bool:
    return MEMORY_SAMPLE.exists() and (MEMORY_SAMPLE / "block_health.csv").exists()


def _make_memory_result():
    from yieldos.domains.memory import MemoryAnalyzer
    return MemoryAnalyzer().analyze(str(MEMORY_SAMPLE), case_id="case_sdm_test", asset_id="memdev_test")


# ── Schema and claim_boundary ─────────────────────────────────────────────────

@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_source_data_manifest_has_schema():
    from yieldos.cli.main import _memory_source_data_paths
    from yieldos.core.report_writer import ReportWriter
    result = _make_memory_result()
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(
            tmp, result["state"], result["evidence_pack"], result["ooda_frame"],
            domain_canonical="memory",
            source_data_paths=_memory_source_data_paths(str(MEMORY_SAMPLE)),
        )
        sdm = json.loads((Path(tmp) / "source_data_manifest.json").read_text(encoding="utf-8"))
        assert sdm["schema"] == "hal.yieldos.source_data_manifest.v1"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_source_data_manifest_has_claim_boundary():
    from yieldos.cli.main import _memory_source_data_paths
    from yieldos.core.report_writer import ReportWriter
    result = _make_memory_result()
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(
            tmp, result["state"], result["evidence_pack"], result["ooda_frame"],
            domain_canonical="memory",
            source_data_paths=_memory_source_data_paths(str(MEMORY_SAMPLE)),
        )
        sdm = json.loads((Path(tmp) / "source_data_manifest.json").read_text(encoding="utf-8"))
        assert sdm.get("claim_boundary") == "input_hash_traceability_only"


# ── Memory: block_health.csv and device_info.json ────────────────────────────

@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_memory_manifest_includes_block_health_csv():
    from yieldos.cli.main import _memory_source_data_paths
    from yieldos.core.report_writer import ReportWriter
    result = _make_memory_result()
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(
            tmp, result["state"], result["evidence_pack"], result["ooda_frame"],
            domain_canonical="memory",
            source_data_paths=_memory_source_data_paths(str(MEMORY_SAMPLE)),
        )
        sdm = json.loads((Path(tmp) / "source_data_manifest.json").read_text(encoding="utf-8"))
        names = [f["path"] for f in sdm["input_files"]]
        assert "block_health.csv" in names, f"block_health.csv not in manifest: {names}"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_memory_manifest_includes_device_info_json():
    from yieldos.cli.main import _memory_source_data_paths
    from yieldos.core.report_writer import ReportWriter
    result = _make_memory_result()
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(
            tmp, result["state"], result["evidence_pack"], result["ooda_frame"],
            domain_canonical="memory",
            source_data_paths=_memory_source_data_paths(str(MEMORY_SAMPLE)),
        )
        sdm = json.loads((Path(tmp) / "source_data_manifest.json").read_text(encoding="utf-8"))
        names = [f["path"] for f in sdm["input_files"]]
        assert "device_info.json" in names, f"device_info.json not in manifest: {names}"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_memory_manifest_sha256_for_existing_files():
    from yieldos.cli.main import _memory_source_data_paths
    from yieldos.core.report_writer import ReportWriter
    result = _make_memory_result()
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(
            tmp, result["state"], result["evidence_pack"], result["ooda_frame"],
            domain_canonical="memory",
            source_data_paths=_memory_source_data_paths(str(MEMORY_SAMPLE)),
        )
        sdm = json.loads((Path(tmp) / "source_data_manifest.json").read_text(encoding="utf-8"))
        for f in sdm["input_files"]:
            if f.get("exists"):
                assert f.get("sha256", "").startswith("sha256:"), \
                    f"File {f['path']} exists but no sha256"
                assert isinstance(f.get("byte_size"), int) and f["byte_size"] > 0


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_memory_manifest_csv_has_rows_and_columns():
    from yieldos.cli.main import _memory_source_data_paths
    from yieldos.core.report_writer import ReportWriter
    result = _make_memory_result()
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(
            tmp, result["state"], result["evidence_pack"], result["ooda_frame"],
            domain_canonical="memory",
            source_data_paths=_memory_source_data_paths(str(MEMORY_SAMPLE)),
        )
        sdm = json.loads((Path(tmp) / "source_data_manifest.json").read_text(encoding="utf-8"))
        csv_files = [f for f in sdm["input_files"] if f.get("file_kind") == "csv" and f.get("exists")]
        assert len(csv_files) > 0, "No CSV file entries found in manifest"
        for f in csv_files:
            assert "rows" in f, f"{f['path']} missing 'rows'"
            assert isinstance(f["rows"], int) and f["rows"] > 0
            assert "columns" in f, f"{f['path']} missing 'columns'"
            assert isinstance(f["columns"], list) and len(f["columns"]) > 0, \
                f"{f['path']} columns should be a non-empty list"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_memory_manifest_missing_file_has_exists_false():
    """A non-existent input file should be listed with exists=False and a warning."""
    from yieldos.core.report_writer import ReportWriter
    result = _make_memory_result()
    ghost_path = str(MEMORY_SAMPLE / "nonexistent_telemetry.csv")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(
            tmp, result["state"], result["evidence_pack"], result["ooda_frame"],
            domain_canonical="memory",
            source_data_paths=[ghost_path],
        )
        sdm = json.loads((Path(tmp) / "source_data_manifest.json").read_text(encoding="utf-8"))
        assert len(sdm["input_files"]) == 1
        entry = sdm["input_files"][0]
        assert entry["exists"] is False
        assert entry.get("sha256") is None
        assert "warning" in entry


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_memory_source_data_paths_returns_all_expected():
    """_memory_source_data_paths returns both CSV and JSON paths regardless of existence."""
    from yieldos.cli.main import _memory_source_data_paths
    paths = _memory_source_data_paths(str(MEMORY_SAMPLE))
    names = [Path(p).name for p in paths]
    assert "block_health.csv" in names
    assert "device_info.json" in names
    assert len(paths) == 2


# ── Robot source data paths ──────────────────────────────────────────────────

def _find_robot_telemetry() -> Path | None:
    for candidate in [
        SAMPLES_ROOT / "robot_ooda" / "robot_telemetry.csv",
        SAMPLES_ROOT / "robot" / "robot_telemetry.csv",
    ]:
        if candidate.exists():
            return candidate
    return None


def test_robot_manifest_includes_telemetry_file():
    tp = _find_robot_telemetry()
    if tp is None:
        pytest.skip("robot telemetry sample not available")
    from yieldos.cli.main import _robot_source_data_paths
    from yieldos.core.report_writer import ReportWriter
    from yieldos.domains.robot import RobotAnalyzer
    result = RobotAnalyzer().analyze(telemetry_path=str(tp), case_id="case_robot_sdm")
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(
            tmp, result["state"], result["evidence_pack"], result["ooda_frame"],
            domain_canonical="robot",
            source_data_paths=_robot_source_data_paths(str(tp)),
        )
        sdm = json.loads((Path(tmp) / "source_data_manifest.json").read_text(encoding="utf-8"))
        assert sdm["file_count"] > 0
        names = [f["path"] for f in sdm["input_files"]]
        assert tp.name in names, f"Telemetry file {tp.name} not listed in manifest: {names}"
        # The telemetry CSV must be marked as existing
        csv_entry = next((f for f in sdm["input_files"] if f["path"] == tp.name), None)
        assert csv_entry is not None
        assert csv_entry["exists"] is True


# ── SemiForge source data paths ──────────────────────────────────────────────

def _find_semiforge_config() -> Path | None:
    for candidate in [
        SAMPLES_ROOT / "semiforge_crossbar" / "config.json",
        SAMPLES_ROOT / "semiforge" / "config.json",
    ]:
        if candidate.exists():
            return candidate
    return None


def test_semiforge_manifest_includes_config_file():
    cp = _find_semiforge_config()
    if cp is None:
        pytest.skip("semiforge config sample not available")
    from yieldos.cli.main import _semiforge_source_data_paths
    from yieldos.core.report_writer import ReportWriter
    from yieldos.domains.semiforge import SemiForgeSimulator
    result = SemiForgeSimulator().simulate(config_path=str(cp), case_id="case_sf_sdm", monte_carlo_runs=10)
    with tempfile.TemporaryDirectory() as tmp:
        ReportWriter().write_all(
            tmp, result["state"], result["evidence_pack"], result["ooda_frame"],
            domain_canonical="semiforge",
            source_data_paths=_semiforge_source_data_paths(str(cp)),
        )
        sdm = json.loads((Path(tmp) / "source_data_manifest.json").read_text(encoding="utf-8"))
        assert sdm["file_count"] > 0
        names = [f["path"] for f in sdm["input_files"]]
        assert "config.json" in names
        config_entry = next(f for f in sdm["input_files"] if f["path"] == "config.json")
        assert config_entry["exists"] is True
        assert config_entry.get("sha256", "").startswith("sha256:")
