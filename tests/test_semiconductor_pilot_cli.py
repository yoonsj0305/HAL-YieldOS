"""CLI integration tests for `yieldos semiconductor pilot-pack` (v3.0.1)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.cli.main import build_parser, main

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


def test_parser_has_semiconductor_command():
    parser = build_parser()
    # Should not raise
    args = parser.parse_args([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", "/tmp/test_out",
    ])
    assert args.command == "semiconductor"
    assert args.action == "pilot-pack"


def test_parser_input_argument():
    parser = build_parser()
    args = parser.parse_args([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", "/tmp/out",
    ])
    assert args.input == str(SAMPLE_DIR)


def test_parser_out_argument():
    parser = build_parser()
    args = parser.parse_args([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", "/tmp/out",
    ])
    assert args.out == "/tmp/out"


def test_parser_asset_default():
    parser = build_parser()
    args = parser.parse_args([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", "/tmp/out",
    ])
    assert args.asset == "chip_demo_001"


def test_parser_asset_override():
    parser = build_parser()
    args = parser.parse_args([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", "/tmp/out",
        "--asset", "my_chip_v2",
    ])
    assert args.asset == "my_chip_v2"


def test_parser_case_default_none():
    parser = build_parser()
    args = parser.parse_args([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", "/tmp/out",
    ])
    assert args.case is None


def test_parser_case_override():
    parser = build_parser()
    args = parser.parse_args([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", "/tmp/out",
        "--case", "lot_ABCDEF",
    ])
    assert args.case == "lot_ABCDEF"


def test_main_semiconductor_pilot_pack_creates_output(tmp_path):
    ret = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(tmp_path),
        "--asset", "cli_test_chip",
        "--case", "cli_test_case",
    ])
    assert ret == 0
    output_files = list(tmp_path.glob("*.json"))
    assert len(output_files) >= 11


def test_main_semiconductor_pilot_pack_creates_md(tmp_path):
    main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(tmp_path),
    ])
    md_files = list(tmp_path.glob("*.md"))
    assert len(md_files) >= 1


def test_main_semiconductor_pilot_pack_readiness_report(tmp_path):
    main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(tmp_path),
    ])
    rr_path = tmp_path / "semiconductor_pilot_readiness_report.json"
    assert rr_path.exists()
    rr = json.loads(rr_path.read_text(encoding="utf-8"))
    assert "readiness_status" in rr
    assert rr["hardware_control_enabled"] is False
    assert rr["human_review_required"] is True


def test_main_semiconductor_pilot_pack_intake_preview(tmp_path):
    main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(tmp_path),
    ])
    ip_path = tmp_path / "semiconductor_recovery_compiler_intake_preview.json"
    assert ip_path.exists()
    ip = json.loads(ip_path.read_text(encoding="utf-8"))
    assert "handoff_status" in ip
    # Full sample has all 3 inputs → READY
    assert ip["handoff_status"] == "READY_FOR_OFFLINE_COMPILER_TEST"


def test_main_semiconductor_pilot_pack_no_recovery_profile_json(tmp_path):
    main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(tmp_path),
    ])
    rp_path = tmp_path / "recovery_profile.json"
    assert not rp_path.exists(), "YieldOS must never generate recovery_profile.json"


def test_main_semiconductor_pilot_pack_handoff_boundary(tmp_path):
    main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(tmp_path),
    ])
    hb_path = tmp_path / "semiconductor_recovery_compiler_handoff_boundary.json"
    assert hb_path.exists()
    hb = json.loads(hb_path.read_text(encoding="utf-8"))
    assert hb["hardware_control_enabled"] is False
    assert isinstance(hb["forbidden_handoff"], list)
    assert len(hb["forbidden_handoff"]) > 0
