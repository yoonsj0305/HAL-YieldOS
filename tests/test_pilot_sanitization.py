"""
tests/test_pilot_sanitization.py

Tests for yieldos.pilot.sanitization.build_sanitization_checklist().
"""
from __future__ import annotations

import pytest

from yieldos.pilot.domain_contracts import DomainContracts
from yieldos.pilot.sanitization import build_sanitization_checklist

DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]


@pytest.fixture(params=DOMAINS)
def checklist(request):
    contract = DomainContracts.get(request.param)
    return request.param, build_sanitization_checklist(contract)


def test_sanitization_schema(checklist):
    domain, data = checklist
    assert data["schema"] == "hal.yieldos.pilot_sanitization_checklist.v1"
    assert data["domain"] == domain


def test_sanitization_has_steps(checklist):
    domain, data = checklist
    assert data["total_steps"] >= 6, f"{domain}: must have at least 6 checklist steps"


def test_sanitization_has_pii_step(checklist):
    domain, data = checklist
    categories = [s["category"] for s in data["steps"]]
    assert "PII_removal" in categories, f"{domain}: must include PII_removal step"


def test_sanitization_has_credentials_step(checklist):
    domain, data = checklist
    categories = [s["category"] for s in data["steps"]]
    assert "credentials" in categories, f"{domain}: must include credentials step"


def test_sanitization_has_format_validation(checklist):
    domain, data = checklist
    categories = [s["category"] for s in data["steps"]]
    assert "format_validation" in categories, f"{domain}: must include format_validation step"


def test_sanitization_has_domain_specific_step(checklist):
    domain, data = checklist
    categories = [s["category"] for s in data["steps"]]
    assert "domain_specific" in categories, f"{domain}: must include at least one domain_specific step"


def test_sanitization_steps_have_required_fields(checklist):
    domain, data = checklist
    for step in data["steps"]:
        assert "step" in step
        assert "action" in step
        assert "details" in step
        assert "required" in step
        assert "verification" in step


def test_sanitization_steps_numbered_sequentially(checklist):
    domain, data = checklist
    for i, step in enumerate(data["steps"], start=1):
        assert step["step"] == i, f"{domain}: step {i} has step number {step['step']}"


def test_sanitization_has_sign_off_prompt(checklist):
    domain, data = checklist
    assert "sign_off_prompt" in data
    assert len(data["sign_off_prompt"]) > 50


def test_sanitization_required_count(checklist):
    domain, data = checklist
    assert data["required_steps_count"] >= 4, f"{domain}: at least 4 required steps"
