"""
Tests for yieldos.core.persistence — Failure Scenario Library (v2.2.0)
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAppendFailureScenario:
    def test_appends_record(self, monkeypatch):
        import yieldos.core.persistence as pers
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr(pers, "STATE_DIR", Path(tmpdir) / "yieldos_state")
            record = {"domain_pack": "robot", "case_id": "test_001", "severity": "medium"}
            result_path = pers.append_failure_scenario(record)
            assert result_path is not None
            assert result_path.exists()
            loaded = pers.load_failure_scenarios("robot")
            assert len(loaded) == 1
            assert loaded[0]["case_id"] == "test_001"

    def test_appends_multiple_records(self, monkeypatch):
        import yieldos.core.persistence as pers
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr(pers, "STATE_DIR", Path(tmpdir) / "yieldos_state")
            for i in range(3):
                pers.append_failure_scenario({"domain_pack": "semfab", "case_id": f"case_{i}"})
            loaded = pers.load_failure_scenarios("semfab")
            assert len(loaded) == 3

    def test_returns_none_gracefully_on_bad_dir(self, monkeypatch):
        import yieldos.core.persistence as pers
        # Simulate _ensure_dir returning None (unwritable dir)
        monkeypatch.setattr(pers, "_ensure_dir", lambda: None)
        result = pers.append_failure_scenario({"domain_pack": "robot", "case_id": "x"})
        assert result is None

    def test_domain_from_domain_key(self, monkeypatch):
        import yieldos.core.persistence as pers
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr(pers, "STATE_DIR", Path(tmpdir) / "yieldos_state")
            pers.append_failure_scenario({"domain": "satellite", "case_id": "sat_01"})
            # domain_pack not set, falls back to "domain" key -> "satellite"
            loaded = pers.load_failure_scenarios("satellite")
            assert len(loaded) == 1

    def test_jsonl_format(self, monkeypatch):
        import yieldos.core.persistence as pers
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "yieldos_state"
            monkeypatch.setattr(pers, "STATE_DIR", state_dir)
            pers.append_failure_scenario({"domain_pack": "space", "case_id": "jsonl_test"})
            jsonl_path = state_dir / "space.jsonl"
            lines = [line for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            assert len(lines) == 1
            record = json.loads(lines[0])
            assert record["case_id"] == "jsonl_test"


class TestLoadFailureScenarios:
    def test_load_all_domains(self, monkeypatch):
        import yieldos.core.persistence as pers
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr(pers, "STATE_DIR", Path(tmpdir) / "yieldos_state")
            pers.append_failure_scenario({"domain_pack": "robot", "case_id": "r01"})
            pers.append_failure_scenario({"domain_pack": "space", "case_id": "s01"})
            all_records = pers.load_failure_scenarios()
            assert len(all_records) == 2

    def test_load_specific_domain(self, monkeypatch):
        import yieldos.core.persistence as pers
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr(pers, "STATE_DIR", Path(tmpdir) / "yieldos_state")
            pers.append_failure_scenario({"domain_pack": "robot", "case_id": "r01"})
            pers.append_failure_scenario({"domain_pack": "space", "case_id": "s01"})
            robot_only = pers.load_failure_scenarios("robot")
            assert len(robot_only) == 1
            assert robot_only[0]["case_id"] == "r01"

    def test_load_empty_dir(self, monkeypatch):
        import yieldos.core.persistence as pers
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "yieldos_state"
            state_dir.mkdir()
            monkeypatch.setattr(pers, "STATE_DIR", state_dir)
            assert pers.load_failure_scenarios() == []

    def test_load_missing_dir(self, monkeypatch):
        import yieldos.core.persistence as pers
        monkeypatch.setattr(pers, "STATE_DIR", Path("C:/totally_nonexistent_path_v220"))
        assert pers.load_failure_scenarios() == []
