"""
yieldos/pilot/init_pack.py

Generates all outputs for `yieldos pilot init --domain <domain> --out <dir>`.

Canonical output files (v2.9.1):
  pilot_input_contract.json        — domain contract with functional-yield mapping
  sample_file_manifest.json        — file-by-file requirements with minimum viable rows
  missing_data_request_template.json — collection guidance template (pre-data state)
  sanitization_checklist.md        — Markdown data-prep checklist
  pilot_boundary_statement.md      — Markdown: what YieldOS is and is not
  README.md                        — human-readable pilot launch guide

Compatibility aliases (also generated):
  pilot_contract.json              — alias for pilot_input_contract.json
  input_requirements.json          — alias for sample_file_manifest.json
  missing_data_request.json        — alias for missing_data_request_template.json
  sanitization_checklist.json      — JSON form of sanitization checklist
  boundary_statement.json          — JSON form of boundary statement
  pilot_readme.md                  — alias for README.md
"""
from __future__ import annotations

import json
from pathlib import Path

from ..contracts.meta import generated_by
from .boundary import build_boundary_statement, build_boundary_statement_md
from .domain_contracts import DomainContracts
from .missing_data import build_missing_data_request_template
from .sanitization import build_sanitization_checklist, build_sanitization_checklist_md


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _build_pilot_input_contract(contract, meta: dict) -> dict:
    fy_map = contract.functional_yield_mapping()
    return {
        "schema": "hal.yieldos.pilot.input_contract.v1",
        "domain": contract.domain,
        "display_name": contract.display_name,
        "purpose": "functional_yield_pilot_readiness",
        "core_question": (
            "what_can_still_function_what_must_be_blocked_"
            "under_what_conditions_based_on_what_evidence"
        ),
        "organizing_question": contract.organizing_question,
        "required_files": [f.to_dict() for f in contract.required_fields],
        "optional_files": [f.to_dict() for f in contract.optional_fields],
        "required_identifiers": _derive_identifiers(contract),
        "required_time_fields": _derive_time_fields(contract),
        "minimum_viable_rows": {
            f.name: f.minimum_viable_rows for f in contract.input_fields if f.required
        },
        "recommended_rows": {
            f.name: f.recommended_rows for f in contract.input_fields if f.required
        },
        "functional_yield_mapping": {
            "remaining_functions_inputs": fy_map["remaining_functions_inputs"],
            "blocked_functions_inputs": fy_map["blocked_functions_inputs"],
            "valid_conditions_inputs": fy_map["valid_conditions_inputs"],
            "evidence_inputs": fy_map["evidence_inputs"],
            "human_review_inputs": fy_map["human_review_inputs"],
        },
        "not_sufficient_for": [
            "certified_root_cause",
            "safety_certification",
            "yield_guarantee",
            "automatic_recovery",
            "hardware_control",
        ],
        "safety_boundary": {
            "hardware_control_enabled": False,
            "human_review_required": True,
            "candidate_only": True,
            "claim_boundary": "pilot_readiness_only_not_certification",
        },
        "pilot_duration_hint": contract.pilot_duration_hint,
        "notes": contract.notes,
        "generated_by": meta,
    }


def _build_sample_file_manifest(contract, meta: dict) -> dict:
    required_items = []
    for f in contract.required_fields:
        item: dict = {
            "path": f.name,
            "format": f.format,
            "purpose": f.description,
            "functional_yield_role": f.functional_yield_role,
            "minimum_viable_rows": f.minimum_viable_rows,
            "recommended_rows": f.recommended_rows,
            "sensitivity": f.sensitivity,
        }
        if f.columns:
            item["required_columns"] = f.columns
        if f.json_keys:
            item["required_json_keys"] = f.json_keys
        required_items.append(item)

    optional_items = []
    for f in contract.optional_fields:
        item = {
            "path": f.name,
            "format": f.format,
            "purpose": f.description,
            "functional_yield_role": f.functional_yield_role,
            "minimum_viable_rows": f.minimum_viable_rows,
            "sensitivity": f.sensitivity,
        }
        optional_items.append(item)

    return {
        "schema": "hal.yieldos.pilot.sample_file_manifest.v1",
        "domain": contract.domain,
        "required_sample_files": required_items,
        "optional_sample_files": optional_items,
        "claim_boundary": "sample_manifest_for_pilot_preparation_only",
        "generated_by": meta,
    }


def _write_readme(path: Path, domain: str, contract) -> Path:
    fy_map = contract.functional_yield_mapping()
    lines = [
        f"# HAL YieldOS Pilot — {contract.display_name}",
        "",
        "## Purpose",
        "",
        "This folder contains your **Pilot Readiness Pack** for the "
        f"`{domain}` domain.",
        "",
        "## Core Question",
        "",
        f"> {contract.organizing_question}",
        "",
        "## Files in This Pack",
        "",
        "| File | Purpose |",
        "|------|---------|",
        "| `pilot_input_contract.json` | Domain contract with functional-yield mapping |",
        "| `sample_file_manifest.json` | Required/optional files with minimum viable rows |",
        "| `missing_data_request_template.json` | Data collection template for your data team |",
        "| `sanitization_checklist.md` | Data sanitization steps before sharing |",
        "| `pilot_boundary_statement.md` | What YieldOS is and is not for this pilot |",
        "| `README.md` | This file |",
        "",
        "## Required Input Files",
        "",
    ]
    for f in contract.required_fields:
        lines.append(f"- **`{f.name}`** — {f.description}")
        lines.append(f"  - Minimum viable rows: {f.minimum_viable_rows}")
        lines.append(f"  - Functional yield role: {f.functional_yield_role}")
    lines += [
        "",
        "## Functional Yield Mapping",
        "",
        "| Purpose | Files |",
        "|---------|-------|",
    ]
    for purpose, files in fy_map.items():
        if files:
            lines.append(f"| {purpose} | {', '.join(f'`{x}`' for x in files)} |")
    lines += [
        "",
        "## Next Steps",
        "",
        "1. Share `missing_data_request_template.json` with your data engineering team.",
        "2. Complete `sanitization_checklist.md` before exporting any data.",
        "3. Once data is collected, run:",
        "   ```",
        f"   yieldos pilot check --domain {domain} --input <your_data_dir> --out <output_dir>",
        "   ```",
        "4. Review `pilot_readiness_report.json` in the check output.",
        "5. If READY_FOR_FUNCTIONAL_YIELD_PILOT, proceed to full YieldOS domain analysis.",
        "",
        "## What YieldOS Will NOT Do",
        "",
    ]
    for claim in contract.blocked_claims:
        lines.append(f"- {claim}")
    lines += [
        "",
        "## What YieldOS WILL Produce",
        "",
    ]
    for claim in contract.evidence_claims:
        lines.append(f"- {claim}")
    lines += [
        "",
        "## Safety Boundary",
        "",
        "```",
        "hardware_control_enabled: false",
        "human_review_required: true",
        "automatic_decision_enabled: false",
        "claim_boundary: pilot_readiness_only_not_certification",
        "```",
        "",
        "---",
        "",
        "_Generated by HAL YieldOS — read-only Functional Yield Evidence Layer._",
        "_Human review required before any operational decision._",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _derive_identifiers(contract) -> list[str]:
    ids = []
    for f in contract.required_fields:
        if f.columns:
            ids.extend(
                c for c in f.columns
                if any(k in c for k in ("_id", "wafer_id", "spacecraft_id", "block_id"))
            )
    return list(dict.fromkeys(ids))


def _derive_time_fields(contract) -> list[str]:
    times = []
    for f in contract.required_fields:
        if f.columns:
            times.extend(c for c in f.columns if "timestamp" in c or c == "date")
    return list(dict.fromkeys(times))


def generate_init_pack(*, domain: str, out_dir: Path) -> Path:
    """
    Generate the canonical Pilot Init Pack for the given domain.
    Returns the output directory path.
    """
    contract = DomainContracts.get(domain)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    meta = generated_by()

    # ── Canonical files ───────────────────────────────────────────────────────

    # 1. pilot_input_contract.json
    pilot_input_contract = _build_pilot_input_contract(contract, meta)
    _write_json(out / "pilot_input_contract.json", pilot_input_contract)

    # 2. sample_file_manifest.json
    sfm = _build_sample_file_manifest(contract, meta)
    _write_json(out / "sample_file_manifest.json", sfm)

    # 3. missing_data_request_template.json
    mdr_template = build_missing_data_request_template(contract)
    mdr_template["generated_by"] = meta
    _write_json(out / "missing_data_request_template.json", mdr_template)

    # 4. sanitization_checklist.md
    sanit_md = build_sanitization_checklist_md(contract)
    _write_text(out / "sanitization_checklist.md", sanit_md)

    # 5. pilot_boundary_statement.md
    boundary_md = build_boundary_statement_md(contract)
    _write_text(out / "pilot_boundary_statement.md", boundary_md)

    # 6. README.md
    _write_readme(out / "README.md", domain, contract)

    # ── Compatibility aliases ──────────────────────────────────────────────────

    # pilot_contract.json (alias for pilot_input_contract.json, old schema)
    contract_data = contract.to_dict()
    contract_data["generated_by"] = meta
    _write_json(out / "pilot_contract.json", contract_data)

    # input_requirements.json
    input_req = {
        "schema": "hal.yieldos.pilot_input_requirements.v1",
        "domain": domain,
        "generated_by": meta,
        "required_files": [f.to_dict() for f in contract.required_fields],
        "optional_files": [f.to_dict() for f in contract.optional_fields],
        "min_records": contract.min_records,
        "recommended_records": contract.recommended_records,
        "pilot_duration_hint": contract.pilot_duration_hint,
        "notes": contract.notes,
    }
    _write_json(out / "input_requirements.json", input_req)

    # missing_data_request.json
    from .missing_data import build_missing_data_request  # noqa: PLC0415
    missing_req = build_missing_data_request(contract)
    missing_req["generated_by"] = meta
    _write_json(out / "missing_data_request.json", missing_req)

    # sanitization_checklist.json
    sanit_json = build_sanitization_checklist(contract)
    sanit_json["generated_by"] = meta
    _write_json(out / "sanitization_checklist.json", sanit_json)

    # boundary_statement.json
    boundary_json = build_boundary_statement(contract)
    boundary_json["generated_by"] = meta
    _write_json(out / "boundary_statement.json", boundary_json)

    # pilot_readme.md
    _write_text(out / "pilot_readme.md", (out / "README.md").read_text(encoding="utf-8"))

    return out
