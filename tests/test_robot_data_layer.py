"""
Tests for Robot Industrial Data Layer — incident_memory module (v2.2.0)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

ROBOT_INDUSTRIAL_DIR = Path(__file__).parent.parent / "samples" / "robot_industrial"


class TestIncidentMemorySampleData:
    def test_sample_files_exist(self):
        for fname in ["robot_telemetry.csv", "maintenance_log.csv",
                      "operation_log.csv", "environment_log.csv", "README.md"]:
            assert (ROBOT_INDUSTRIAL_DIR / fname).exists(), f"Missing: {fname}"

    def test_telemetry_csv_has_expected_columns(self):
        import csv
        with open(ROBOT_INDUSTRIAL_DIR / "robot_telemetry.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
        for col in ["timestamp", "motor_current_A", "joint_temp_C", "imu_vibration_g",
                    "position_error_mm", "latency_ms", "fault_code"]:
            assert col in fieldnames, f"Missing column: {col}"

    def test_maintenance_log_has_expected_columns(self):
        import csv
        with open(ROBOT_INDUSTRIAL_DIR / "maintenance_log.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
        for col in ["timestamp", "event_type", "component", "action_taken", "outcome"]:
            assert col in fieldnames, f"Missing column: {col}"


class TestLoadIndustrialData:
    def test_load_all_sources(self):
        from yieldos.domains.robot.incident_memory import load_industrial_data
        data = load_industrial_data(
            telemetry_path=str(ROBOT_INDUSTRIAL_DIR / "robot_telemetry.csv"),
            maintenance_log_path=str(ROBOT_INDUSTRIAL_DIR / "maintenance_log.csv"),
            operation_log_path=str(ROBOT_INDUSTRIAL_DIR / "operation_log.csv"),
            environment_log_path=str(ROBOT_INDUSTRIAL_DIR / "environment_log.csv"),
        )
        assert len(data["telemetry"]) > 0
        assert len(data["maintenance_log"]) > 0
        assert len(data["operation_log"]) > 0
        assert len(data["environment_log"]) > 0

    def test_load_missing_optional_files(self):
        from yieldos.domains.robot.incident_memory import load_industrial_data
        data = load_industrial_data(
            telemetry_path=str(ROBOT_INDUSTRIAL_DIR / "robot_telemetry.csv"),
        )
        assert len(data["telemetry"]) > 0
        assert data["maintenance_log"] == []
        assert data["operation_log"] == []
        assert data["environment_log"] == []


class TestBuildIncidentTimeline:
    def _load(self):
        from yieldos.domains.robot.incident_memory import load_industrial_data
        return load_industrial_data(
            telemetry_path=str(ROBOT_INDUSTRIAL_DIR / "robot_telemetry.csv"),
            maintenance_log_path=str(ROBOT_INDUSTRIAL_DIR / "maintenance_log.csv"),
            operation_log_path=str(ROBOT_INDUSTRIAL_DIR / "operation_log.csv"),
        )

    def test_timeline_schema(self):
        from yieldos.domains.robot.incident_memory import build_incident_timeline
        data = self._load()
        tl = build_incident_timeline(
            data["telemetry"], data["maintenance_log"], data["operation_log"],
            case_id="tl_test", asset_id="arm_01",
        )
        assert tl["schema"] == "hal.yieldos.robot.incident_timeline.v1"

    def test_timeline_has_events(self):
        from yieldos.domains.robot.incident_memory import build_incident_timeline
        data = self._load()
        tl = build_incident_timeline(
            data["telemetry"], data["maintenance_log"], data["operation_log"],
            case_id="tl_test", asset_id="arm_01",
        )
        assert tl["total_events"] > 0

    def test_timeline_safety_fields(self):
        from yieldos.domains.robot.incident_memory import build_incident_timeline
        data = self._load()
        tl = build_incident_timeline(
            data["telemetry"], data["maintenance_log"], data["operation_log"],
        )
        assert tl["hardware_execution_enabled"] is False
        assert tl["human_review_required"] is True

    def test_timeline_chronological(self):
        from yieldos.domains.robot.incident_memory import build_incident_timeline
        data = self._load()
        tl = build_incident_timeline(
            data["telemetry"], data["maintenance_log"], data["operation_log"],
        )
        timestamps = [e["timestamp"] for e in tl["timeline"] if e.get("timestamp")]
        assert timestamps == sorted(timestamps)


class TestBuildIndustrialDataRecord:
    def test_record_schema(self):
        from yieldos.domains.robot.incident_memory import build_industrial_data_record, load_industrial_data
        data = load_industrial_data(
            str(ROBOT_INDUSTRIAL_DIR / "robot_telemetry.csv"),
            str(ROBOT_INDUSTRIAL_DIR / "maintenance_log.csv"),
            str(ROBOT_INDUSTRIAL_DIR / "operation_log.csv"),
            str(ROBOT_INDUSTRIAL_DIR / "environment_log.csv"),
        )
        rec = build_industrial_data_record(
            data["telemetry"], data["maintenance_log"], data["operation_log"],
            data["environment_log"], case_id="idr_test", asset_id="arm_01",
        )
        assert rec["schema"] == "hal.yieldos.robot.industrial_data_record.v1"
        assert rec["hardware_execution_enabled"] is False
        assert rec["human_review_required"] is True

    def test_record_data_sources_nonzero(self):
        from yieldos.domains.robot.incident_memory import build_industrial_data_record, load_industrial_data
        data = load_industrial_data(
            str(ROBOT_INDUSTRIAL_DIR / "robot_telemetry.csv"),
            str(ROBOT_INDUSTRIAL_DIR / "maintenance_log.csv"),
            str(ROBOT_INDUSTRIAL_DIR / "operation_log.csv"),
            str(ROBOT_INDUSTRIAL_DIR / "environment_log.csv"),
        )
        rec = build_industrial_data_record(
            data["telemetry"], data["maintenance_log"], data["operation_log"],
            data["environment_log"],
        )
        assert rec["data_sources"]["telemetry_samples"] > 0
        assert rec["data_sources"]["maintenance_events"] > 0


class TestBuildFleetFailureMemory:
    def test_fleet_memory_schema(self):
        from yieldos.domains.robot.incident_memory import (
            build_fleet_failure_memory,
            build_incident_timeline,
            build_industrial_data_record,
            load_industrial_data,
        )
        data = load_industrial_data(
            str(ROBOT_INDUSTRIAL_DIR / "robot_telemetry.csv"),
            str(ROBOT_INDUSTRIAL_DIR / "maintenance_log.csv"),
            str(ROBOT_INDUSTRIAL_DIR / "operation_log.csv"),
        )
        tl = build_incident_timeline(
            data["telemetry"], data["maintenance_log"], data["operation_log"],
        )
        idr = build_industrial_data_record(
            data["telemetry"], data["maintenance_log"],
            data["operation_log"], data["environment_log"],
        )
        fm = build_fleet_failure_memory(idr, tl, case_id="fm_test", asset_id="arm_01")
        assert fm["schema"] == "hal.yieldos.robot.fleet_failure_memory.v1"
        assert fm["hardware_execution_enabled"] is False
        assert fm["pattern_hash"].startswith("sha256:")

    def test_fleet_memory_causal_boundary(self):
        from yieldos.domains.robot.incident_memory import (
            build_fleet_failure_memory,
            build_incident_timeline,
            build_industrial_data_record,
            load_industrial_data,
        )
        data = load_industrial_data(str(ROBOT_INDUSTRIAL_DIR / "robot_telemetry.csv"))
        tl = build_incident_timeline(data["telemetry"], [], [])
        idr = build_industrial_data_record(data["telemetry"], [], [], [])
        fm = build_fleet_failure_memory(idr, tl)
        assert fm["causal_claim_boundary"] == "candidate_only_not_certified_cause"
