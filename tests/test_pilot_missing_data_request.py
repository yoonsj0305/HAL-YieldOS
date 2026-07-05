"""
tests/test_pilot_missing_data_request.py

Tests for yieldos.pilot.missing_data module:
  - build_missing_data_request()
  - check_missing_fields()
"""
from __future__ import annotations

import pytest

from yieldos.pilot.domain_contracts import DomainContracts
from yieldos.pilot.missing_data import build_missing_data_request, check_missing_fields

DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]


@pytest.fixture(params=DOMAINS)
def contract(request):
    return DomainContracts.get(request.param)


# ── build_missing_data_request ────────────────────────────────────────────────

def test_missing_data_request_schema(contract):
    data = build_missing_data_request(contract)
    assert data["schema"] == "hal.yieldos.pilot_missing_data_request.v1"


def test_missing_data_request_has_blocking_items(contract):
    data = build_missing_data_request(contract)
    p0_items = [i for i in data["items"] if i["priority"] == "P0_blocking"]
    assert len(p0_items) >= 2, f"{contract.domain}: must have at least 2 P0_blocking items"


def test_missing_data_request_status(contract):
    data = build_missing_data_request(contract)
    assert data["status"] == "awaiting_input_data"


def test_missing_data_request_collection_guidance(contract):
    data = build_missing_data_request(contract)
    guidance = data["collection_guidance"]
    assert "minimum_records_for_valid_analysis" in guidance
    assert guidance["minimum_records_for_valid_analysis"] == contract.min_records


def test_missing_data_request_p0_items_have_required_fields(contract):
    data = build_missing_data_request(contract)
    for item in data["items"]:
        assert "file" in item
        assert "description" in item
        assert "format" in item
        assert "sensitivity" in item


def test_missing_data_request_csv_items_have_columns(contract):
    data = build_missing_data_request(contract)
    for item in data["items"]:
        if item["format"] == "csv":
            assert "required_columns" in item, (
                f"{contract.domain}: CSV item '{item['file']}' must list required_columns"
            )


def test_missing_data_request_json_items_have_keys(contract):
    data = build_missing_data_request(contract)
    for item in data["items"]:
        if item["format"] == "json":
            assert "required_json_keys" in item, (
                f"{contract.domain}: JSON item '{item['file']}' must list required_json_keys"
            )


# ── check_missing_fields ──────────────────────────────────────────────────────

def test_check_missing_fields_all_present(contract):
    all_files = [f.name for f in contract.input_fields]
    result = check_missing_fields(contract, all_files)
    assert not result["blocked"]
    assert len(result["missing_required"]) == 0
    assert len(result["found"]) == len(all_files)


def test_check_missing_fields_none_present(contract):
    result = check_missing_fields(contract, [])
    assert result["blocked"] is True
    assert len(result["missing_required"]) >= 2


def test_check_missing_fields_partial(contract):
    required = [f.name for f in contract.required_fields]
    optional = [f.name for f in contract.optional_fields]
    if not optional:
        return  # skip if no optional fields
    # Provide all required but no optional
    result = check_missing_fields(contract, required)
    assert not result["blocked"]
    assert len(result["missing_optional"]) == len(optional)


def test_check_missing_fields_schema(contract):
    result = check_missing_fields(contract, [])
    assert result["schema"] == "hal.yieldos.pilot_field_check.v1"
    assert result["domain"] == contract.domain
