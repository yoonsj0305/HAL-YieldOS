"""
tests/test_cli_unified_memory.py

Verifies that `yieldos analyze --domain memory` works identically
to `yieldos memory analyze` and that the output passes strict validation.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"
MEMORY_SAMPLE = SAMPLES_ROOT / "memory_device"


def _has_memory_sample() -> bool:
    return MEMORY_SAMPLE.exists() and (MEMORY_SAMPLE / "block_health.csv").exists()


# ── Domain alias / resolver ──────────────────────────────────────────────────

def test_memory_is_in_domain_aliases():
    from yieldos.cli.main import DOMAIN_ALIASES
    assert "memory" in DOMAIN_ALIASES
    assert DOMAIN_ALIASES["memory"] == "memory"


def test_memory_device_alias_resolves_to_memory():
    from yieldos.cli.main import DOMAIN_ALIASES
    assert DOMAIN_ALIASES.get("memory_device") == "memory"


def test_nand_alias_resolves_to_memory():
    from yieldos.cli.main import DOMAIN_ALIASES
    assert DOMAIN_ALIASES.get("nand") == "memory"


def test_memory_is_in_canonical_to_analyzer():
    from yieldos.cli.main import CANONICAL_TO_ANALYZER
    assert "memory" in CANONICAL_TO_ANALYZER
    assert CANONICAL_TO_ANALYZER["memory"] == "memory"


def test_resolve_domain_memory():
    from yieldos.cli.main import _resolve_domain
    canonical, analyzer = _resolve_domain("memory")
    assert canonical == "memory"
    assert analyzer == "memory"


def test_resolve_domain_memory_device():
    from yieldos.cli.main import _resolve_domain
    canonical, analyzer = _resolve_domain("memory_device")
    assert canonical == "memory"
    assert analyzer == "memory"


# ── Unified analyze --domain memory ─────────────────────────────────────────

@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_unified_analyze_memory_runs():
    """yieldos analyze --domain memory --input <dir> --out <dir> must not fail."""
    import argparse

    from yieldos.cli.main import cmd_analyze

    with tempfile.TemporaryDirectory() as tmp:
        args = argparse.Namespace(
            domain="memory",
            input=str(MEMORY_SAMPLE),
            out=tmp,
            asset="memdev_01",
            case=None,
            mc=30,
            optimizer="greedy",
            cvc=None,
            authority=None,
            envelope=None,
            risk_policy=None,
        )
        ret = cmd_analyze(args)
        assert ret == 0, "cmd_analyze --domain memory must return 0"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_unified_analyze_memory_produces_standard_bundle():
    """All 22 standard output files must be present."""
    import argparse

    from yieldos.cli.main import cmd_analyze

    REQUIRED_FILES = [
        "state_snapshot.json", "evidence_pack.json", "ooda_frame.json",
        "recovery_candidates.json", "report.md", "report.html",
        "input_validation.json", "decision_readiness_report.json",
        "functional_yield_scorecard.json", "functional_binning_result.json",
        "functional_passport.json", "evidence_pack.md",
        "recovery_route_report.json", "failure_scenario_record.json",
        "next_data_request.json", "analysis_trace.json",
        "source_data_manifest.json", "data_quality_report.json",
        "evidence_conflict_report.json", "baseline_vs_yieldos.json",
        "business_case_summary.json", "case_manifest.json",
    ]

    with tempfile.TemporaryDirectory() as tmp:
        args = argparse.Namespace(
            domain="memory",
            input=str(MEMORY_SAMPLE),
            out=tmp,
            asset="memdev_01",
            case=None,
            mc=30,
            optimizer="greedy",
            cvc=None,
            authority=None,
            envelope=None,
            risk_policy=None,
        )
        ret = cmd_analyze(args)
        assert ret == 0

        out = Path(tmp)
        for fname in REQUIRED_FILES:
            assert (out / fname).exists(), f"Missing {fname} in unified memory output"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_unified_analyze_memory_passes_strict_validation():
    """Output from unified analyze --domain memory must pass strict validation."""
    import argparse

    from yieldos.cli.main import cmd_analyze, cmd_validate

    with tempfile.TemporaryDirectory() as tmp:
        analyze_args = argparse.Namespace(
            domain="memory",
            input=str(MEMORY_SAMPLE),
            out=tmp,
            asset="memdev_01",
            case=None,
            mc=30,
            optimizer="greedy",
            cvc=None,
            authority=None,
            envelope=None,
            risk_policy=None,
        )
        ret = cmd_analyze(analyze_args)
        assert ret == 0

        val_args = argparse.Namespace(case=tmp, strict=True)
        result = cmd_validate(val_args)
        assert result == 0, "Unified memory output must pass strict validation"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_unified_analyze_memory_produces_passport_validity():
    """functional_passport.json must have passport_validity with candidate_only status."""
    import argparse

    from yieldos.cli.main import cmd_analyze

    with tempfile.TemporaryDirectory() as tmp:
        args = argparse.Namespace(
            domain="memory",
            input=str(MEMORY_SAMPLE),
            out=tmp,
            asset="memdev_01",
            case=None,
            mc=30,
            optimizer="greedy",
            cvc=None,
            authority=None,
            envelope=None,
            risk_policy=None,
        )
        cmd_analyze(args)
        fp = json.loads((Path(tmp) / "functional_passport.json").read_text(encoding="utf-8"))
        pv = fp.get("passport_validity")
        assert pv is not None
        assert pv["status"] == "candidate_only"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_unified_analyze_memory_extra_outputs():
    """Memory-specific extra outputs must be present."""
    import argparse

    from yieldos.cli.main import cmd_analyze

    with tempfile.TemporaryDirectory() as tmp:
        args = argparse.Namespace(
            domain="memory",
            input=str(MEMORY_SAMPLE),
            out=tmp,
            asset="memdev_01",
            case=None,
            mc=30,
            optimizer="greedy",
            cvc=None,
            authority=None,
            envelope=None,
            risk_policy=None,
        )
        cmd_analyze(args)
        out = Path(tmp)
        # At least one memory-specific file should exist
        memory_extras = [
            "memory_functional_capacity.json",
            "memory_data_placement_recommendation.json",
            "memory_bad_block_evidence_map.json",
        ]
        found = [f for f in memory_extras if (out / f).exists()]
        assert len(found) > 0, f"No memory extra outputs found. Expected one of: {memory_extras}"


@pytest.mark.skipif(not _has_memory_sample(), reason="memory_device sample not available")
def test_unified_analyze_memory_source_data_manifest_has_files():
    """source_data_manifest.json must record the input CSV path."""
    import argparse

    from yieldos.cli.main import cmd_analyze

    with tempfile.TemporaryDirectory() as tmp:
        args = argparse.Namespace(
            domain="memory",
            input=str(MEMORY_SAMPLE),
            out=tmp,
            asset="memdev_01",
            case=None,
            mc=30,
            optimizer="greedy",
            cvc=None,
            authority=None,
            envelope=None,
            risk_policy=None,
        )
        cmd_analyze(args)
        sdm = json.loads((Path(tmp) / "source_data_manifest.json").read_text(encoding="utf-8"))
        assert len(sdm["input_files"]) > 0, "source_data_manifest must list at least one input file"
        existing_files = [f for f in sdm["input_files"] if f.get("exists")]
        assert len(existing_files) > 0, "At least one listed input file must be exists=True"
