"""
yieldos/pilot/missing_data.py

Generates the missing_data_request.json for `yieldos pilot init`.
Lists all required (and recommended optional) input files with
collection guidance for the customer's data team.
"""
from __future__ import annotations

from .contracts import PilotContract


def build_missing_data_request(contract: PilotContract) -> dict:
    """
    Returns a missing_data_request dict for all input fields.
    Used when no --input directory is provided (pre-collection state).
    """
    items = []
    for f in contract.input_fields:
        item: dict = {
            "file": f.name,
            "description": f.description,
            "format": f.format,
            "required": f.required,
            "priority": "P0_blocking" if f.required else "P1_recommended",
            "sensitivity": f.sensitivity,
        }
        if f.columns:
            item["required_columns"] = f.columns
        if f.json_keys:
            item["required_json_keys"] = f.json_keys
        if f.sanitization_notes:
            item["sanitization_notes"] = f.sanitization_notes
        if f.example_value:
            item["example_value"] = f.example_value
        items.append(item)

    p0 = [i for i in items if i["priority"] == "P0_blocking"]
    p1 = [i for i in items if i["priority"] == "P1_recommended"]

    return {
        "schema": "hal.yieldos.pilot_missing_data_request.v1",
        "domain": contract.domain,
        "status": "awaiting_input_data",
        "summary": (
            f"{len(p0)} required file(s) must be provided before pilot analysis can run. "
            f"{len(p1)} optional file(s) improve analysis depth."
        ),
        "blocking_count": len(p0),
        "recommended_count": len(p1),
        "items": items,
        "collection_guidance": {
            "minimum_records_for_valid_analysis": contract.min_records,
            "recommended_records": contract.recommended_records,
            "pilot_duration_hint": contract.pilot_duration_hint,
            "data_export_instructions": (
                "Export data to CSV/JSON using standard tooling. "
                "Apply sanitization_notes before sharing. "
                "Do not include PII, credentials, or IP addresses."
            ),
            "contact_for_questions": (
                "Share sanitized data with your YieldOS pilot contact. "
                "Questions about data format: refer to pilot_contract.json."
            ),
        },
    }


def build_missing_data_request_template(contract: PilotContract) -> dict:
    """
    Returns a template dict for missing_data_request_template.json (v2.9.1 canonical).
    Includes why_needed_for_functional_yield per item.
    """
    fy_map = contract.functional_yield_mapping()
    file_to_role: dict[str, str] = {}
    for role, files in fy_map.items():
        for fname in files:
            file_to_role[fname] = role

    template_items = []
    for f in contract.input_fields:
        fy_role = file_to_role.get(f.name, f.functional_yield_role)
        why = {
            "remaining_functions_inputs": (
                "Provides evidence for what functions remain viable under current conditions."
            ),
            "blocked_functions_inputs": (
                "Identifies which operations must be blocked based on current device/system state."
            ),
            "valid_conditions_inputs": (
                "Defines the boundary conditions under which functional yield claims are valid."
            ),
            "evidence_inputs": (
                "Core evidence source for functional yield scoring and candidate identification."
            ),
            "human_review_inputs": (
                "Provides human judgment context required before any yield decision can be made."
            ),
        }.get(fy_role, "Required for functional yield analysis.")

        item: dict = {
            "file": f.name,
            "description": f.description,
            "format": f.format,
            "required": f.required,
            "priority": "P0_blocking" if f.required else "P1_recommended",
            "sensitivity": f.sensitivity,
            "minimum_viable_rows": f.minimum_viable_rows,
            "recommended_rows": f.recommended_rows,
            "functional_yield_role": fy_role,
            "why_needed_for_functional_yield": why,
        }
        if f.columns:
            item["required_columns"] = f.columns
        if f.json_keys:
            item["required_json_keys"] = f.json_keys
        if f.sanitization_notes:
            item["sanitization_notes"] = f.sanitization_notes
        template_items.append(item)

    p0 = [i for i in template_items if i["priority"] == "P0_blocking"]
    p1 = [i for i in template_items if i["priority"] == "P1_recommended"]

    return {
        "schema": "hal.yieldos.pilot.missing_data_request_template.v1",
        "domain": contract.domain,
        "status": "template_for_data_collection",
        "purpose": "functional_yield_pilot_readiness",
        "summary": (
            f"{len(p0)} required file(s) must be provided before pilot analysis can run. "
            f"{len(p1)} optional file(s) improve analysis depth."
        ),
        "blocking_count": len(p0),
        "recommended_count": len(p1),
        "template_items": template_items,
        "collection_guidance": {
            "minimum_viable_rows_per_file": {
                i["file"]: i["minimum_viable_rows"] for i in p0
            },
            "minimum_records_for_valid_analysis": contract.min_records,
            "recommended_records": contract.recommended_records,
            "pilot_duration_hint": contract.pilot_duration_hint,
            "data_export_instructions": (
                "Export data to CSV/JSON. Apply sanitization_notes before sharing. "
                "Do not include PII, credentials, or IP addresses."
            ),
        },
        "claim_boundary": "template_only_not_readiness_assessment",
    }


def check_missing_fields(
    contract: PilotContract, input_dir_files: list[str]
) -> dict:
    """
    Compare contract required files against files present in input directory.
    Returns a dict with present/missing breakdown and blocking status.
    """
    present = set(input_dir_files)
    missing_required = []
    missing_optional = []
    found = []

    for f in contract.input_fields:
        if f.name in present:
            found.append({"file": f.name, "required": f.required, "status": "present"})
        elif f.required:
            missing_required.append({"file": f.name, "description": f.description})
        else:
            missing_optional.append({"file": f.name, "description": f.description})

    is_blocked = len(missing_required) > 0

    return {
        "schema": "hal.yieldos.pilot_field_check.v1",
        "domain": contract.domain,
        "blocked": is_blocked,
        "found": found,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "summary": (
            f"{len(found)} file(s) present, "
            f"{len(missing_required)} required missing, "
            f"{len(missing_optional)} optional missing."
        ),
    }
