"""
tests/test_pilot_boundaries.py

Tests for yieldos.pilot.boundary.build_boundary_statement().
Verifies YieldOS safety invariants in pilot boundary statements.
"""
from __future__ import annotations

import pytest

from yieldos.pilot.boundary import build_boundary_statement
from yieldos.pilot.domain_contracts import DomainContracts

DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]


@pytest.fixture(params=DOMAINS)
def boundary(request):
    contract = DomainContracts.get(request.param)
    return request.param, build_boundary_statement(contract)


def test_boundary_schema(boundary):
    domain, data = boundary
    assert data["schema"] == "hal.yieldos.pilot_boundary_statement.v1"
    assert data["domain"] == domain


def test_boundary_read_only(boundary):
    domain, data = boundary
    assert data["read_only"] is True


def test_boundary_shadow_only(boundary):
    domain, data = boundary
    assert data["shadow_only"] is True


def test_boundary_no_hardware_execution(boundary):
    domain, data = boundary
    assert data.get("hardware_execution_enabled") is not True
    assert "hardware" in data.get("what_yieldos_is_not", [None])[0].lower() or \
           any("hardware" in s.lower() for s in data.get("what_yieldos_is_not", []))


def test_boundary_human_review_required(boundary):
    domain, data = boundary
    assert data["human_review_required"] is True


def test_boundary_no_auto_decision(boundary):
    domain, data = boundary
    assert data["automatic_decision_enabled"] is False


def test_boundary_approval_gate(boundary):
    domain, data = boundary
    assert data["approval_gate_required"] is True


def test_boundary_causal_claim_boundary(boundary):
    domain, data = boundary
    assert data["causal_claim_boundary"] == "candidate_only_not_certified_cause"


def test_boundary_blocks_root_cause_certification(boundary):
    domain, data = boundary
    blocked = data["blocked_claims"]
    assert "certified_root_cause" in blocked


def test_boundary_has_evidence_claims(boundary):
    domain, data = boundary
    assert len(data["evidence_claims"]) >= 4


def test_boundary_pilot_scope_mentions_domain(boundary):
    domain, data = boundary
    assert domain in data["pilot_scope"]


def test_boundary_what_yieldos_is_not_list(boundary):
    domain, data = boundary
    not_list = data["what_yieldos_is_not"]
    assert len(not_list) >= 5
    assert any("root-cause" in item.lower() or "root cause" in item.lower() for item in not_list)
    assert any("hardware" in item.lower() for item in not_list)
    assert any("autonomous" in item.lower() or "automatic" in item.lower() for item in not_list)
