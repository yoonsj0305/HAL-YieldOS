"""
tests/test_pilot_contracts.py

Tests for PilotContract and InputField data classes, and DomainContracts registry.
"""
from __future__ import annotations

import pytest

from yieldos.pilot.contracts import InputField, PilotContract
from yieldos.pilot.domain_contracts import DomainContracts

DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]


# ── DomainContracts registry ─────────────────────────────────────────────────

def test_all_domains_registered():
    contracts = DomainContracts.all()
    for domain in DOMAINS:
        assert domain in contracts, f"Domain '{domain}' missing from registry"


def test_get_returns_pilot_contract():
    for domain in DOMAINS:
        c = DomainContracts.get(domain)
        assert isinstance(c, PilotContract)
        assert c.domain == domain


def test_get_unknown_domain_raises():
    with pytest.raises(ValueError, match="Unknown domain"):
        DomainContracts.get("not_a_domain")


def test_each_contract_has_display_name():
    for domain in DOMAINS:
        c = DomainContracts.get(domain)
        assert c.display_name, f"{domain} missing display_name"


def test_each_contract_has_organizing_question():
    for domain in DOMAINS:
        c = DomainContracts.get(domain)
        assert "function" in c.organizing_question.lower(), (
            f"{domain}: organizing_question must reference functional yield"
        )


def test_each_contract_has_required_fields():
    for domain in DOMAINS:
        c = DomainContracts.get(domain)
        assert len(c.required_fields) >= 2, (
            f"{domain}: must have at least 2 required input fields"
        )


def test_each_contract_has_blocked_claims():
    for domain in DOMAINS:
        c = DomainContracts.get(domain)
        assert len(c.blocked_claims) >= 5, f"{domain}: must block at least 5 claim types"
        assert "certified_root_cause" in c.blocked_claims, (
            f"{domain}: must block 'certified_root_cause'"
        )
        assert "hardware_control_commands" in c.blocked_claims, (
            f"{domain}: must block 'hardware_control_commands'"
        )
        assert "automatic_recovery_execution" in c.blocked_claims, (
            f"{domain}: must block 'automatic_recovery_execution'"
        )


def test_each_contract_has_evidence_claims():
    for domain in DOMAINS:
        c = DomainContracts.get(domain)
        assert len(c.evidence_claims) >= 4, f"{domain}: must have at least 4 evidence claims"
        assert any("functional_yield" in e for e in c.evidence_claims), (
            f"{domain}: evidence_claims must include functional_yield score"
        )
        assert any("decision_readiness" in e for e in c.evidence_claims), (
            f"{domain}: evidence_claims must include decision_readiness"
        )


def test_min_records_positive():
    for domain in DOMAINS:
        c = DomainContracts.get(domain)
        assert c.min_records > 0, f"{domain}: min_records must be > 0"
        assert c.recommended_records >= c.min_records, (
            f"{domain}: recommended_records must be >= min_records"
        )


# ── InputField data class ────────────────────────────────────────────────────

def test_input_field_to_dict_required():
    f = InputField(name="test.csv", description="desc", format="csv", required=True)
    d = f.to_dict()
    assert d["name"] == "test.csv"
    assert d["required"] is True
    assert d["format"] == "csv"


def test_input_field_optional_columns_in_dict():
    f = InputField(
        name="data.csv",
        description="d",
        format="csv",
        columns=["a", "b"],
    )
    d = f.to_dict()
    assert d["columns"] == ["a", "b"]


def test_input_field_json_keys_in_dict():
    f = InputField(name="cfg.json", description="d", format="json", json_keys=["key1"])
    d = f.to_dict()
    assert d["json_keys"] == ["key1"]


def test_input_field_sanitization_notes_in_dict():
    f = InputField(name="x.csv", description="d", format="csv", sanitization_notes="Remove PII")
    d = f.to_dict()
    assert "sanitization_notes" in d


# ── PilotContract to_dict ────────────────────────────────────────────────────

def test_pilot_contract_to_dict_schema():
    for domain in DOMAINS:
        c = DomainContracts.get(domain)
        d = c.to_dict()
        assert d["schema"] == "hal.yieldos.pilot_contract.v1"
        assert d["domain"] == domain
        assert "input_fields" in d
        assert "blocked_claims" in d
        assert "evidence_claims" in d


def test_robot_contract_csv_columns():
    c = DomainContracts.get("robot")
    telem = next(f for f in c.input_fields if f.name == "robot_telemetry.csv")
    assert "joint_id" in (telem.columns or [])
    assert "position_error_mm" in (telem.columns or [])
    assert "imu_vibration_g" in (telem.columns or [])


def test_semiconductor_contract_tool_log_columns():
    c = DomainContracts.get("semiconductor")
    tl = next(f for f in c.input_fields if f.name == "tool_log.csv")
    assert "alarm_code" in (tl.columns or [])
    assert "pressure_mTorr" in (tl.columns or [])


def test_space_contract_mission_config_optional():
    c = DomainContracts.get("space")
    mc = next(f for f in c.input_fields if f.name == "mission_config.json")
    assert not mc.required


def test_memory_contract_bad_block_map_required():
    c = DomainContracts.get("memory")
    bbm = next(f for f in c.input_fields if f.name == "bad_block_map.csv")
    assert bbm.required
    assert "block_id" in (bbm.columns or [])


def test_semiforge_contract_defect_map_json():
    c = DomainContracts.get("semiforge")
    dm = next(f for f in c.input_fields if f.name == "synthetic_defect_map.json")
    assert dm.format == "json"
    assert dm.required
