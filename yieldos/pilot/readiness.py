"""
yieldos/pilot/readiness.py

Implements `yieldos pilot check --domain <domain> --input <dir> --out <dir>`.

Canonical output files (v2.9.2):
  pilot_readiness_report.json   — strict canonical schema with readiness_status
  missing_data_request.json     — canonical missing arrays with functional-yield reasons
  data_sufficiency_preview.json — top-level sufficiency_status + functional_yield_gaps
  pilot_decision_boundary.json  — allowed_decisions + forbidden_decisions

Compatibility aliases (also generated):
  readiness_report.json         — alias for pilot_readiness_report.json (old schema)
  data_sufficiency.json         — alias for data_sufficiency_preview.json (old schema)
  blocking_issues.json          — blocking issues extracted from readiness report
  next_steps.json               — next steps extracted from readiness report

Status values (canonical):
  READY_FOR_FUNCTIONAL_YIELD_PILOT
  PARTIAL_FOR_FUNCTIONAL_YIELD_PILOT
  NOT_READY_FOR_FUNCTIONAL_YIELD_PILOT
  INVALID_INPUT
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from ..contracts.meta import generated_by
from .contracts import InputField, PilotContract
from .domain_contracts import DomainContracts
from .missing_data import check_missing_fields

# ── Status constants ───────────────────────────────────────────────────────────

STATUS_READY = "READY_FOR_FUNCTIONAL_YIELD_PILOT"
STATUS_PARTIAL = "PARTIAL_FOR_FUNCTIONAL_YIELD_PILOT"
STATUS_NOT_READY = "NOT_READY_FOR_FUNCTIONAL_YIELD_PILOT"
STATUS_INVALID = "INVALID_INPUT"

# ── Claim boundary constants ───────────────────────────────────────────────────

_NOT_SUFFICIENT_FOR = [
    "certified_root_cause",
    "safety_certification",
    "yield_guarantee",
    "automatic_recovery",
    "hardware_control",
]

_SUFFICIENT_FOR_READY = [
    "pilot_data_intake_review",
    "candidate_functional_yield_pilot",
]

_SUFFICIENT_FOR_PARTIAL = [
    "partial_data_intake_review",
    "missing_data_request_generation",
]

_SUFFICIENT_FOR_NOT_READY = [
    "missing_data_request_generation",
]

_FORBIDDEN_DECISIONS = [
    "execute_recovery",
    "control_hardware",
    "certify_safety",
    "claim_root_cause",
    "guarantee_yield",
    "modify_recipe",
    "send_robot_command",
    "uplink_satellite_command",
]

_ALLOWED_DECISIONS_READY = [
    "accept_for_offline_functional_yield_pilot",
    "request_missing_data",
    "reject_until_required_inputs_exist",
]

_ALLOWED_DECISIONS_NOT_READY = [
    "request_missing_data",
    "reject_until_required_inputs_exist",
]

# ── FY role → reason mapping (must reference functional yield concepts) ────────

_FY_ROLE_REASON = {
    "remaining_functions_inputs": (
        "identifies which operations remain viable under current conditions, "
        "enabling the remaining_functions candidate list"
    ),
    "blocked_functions_inputs": (
        "determines which functions must be blocked based on current evidence, "
        "enabling the blocked_functions candidate list"
    ),
    "valid_conditions_inputs": (
        "defines boundary conditions under which functional yield claims remain valid"
    ),
    "evidence_inputs": (
        "provides core evidence for functional yield scoring and candidate identification"
    ),
    "human_review_inputs": (
        "supplies context required for human review before any yield decision is made"
    ),
}

# ── I/O helpers ───────────────────────────────────────────────────────────────


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _load_json_safe(path: Path) -> tuple[dict | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, str(exc)


# ── Per-file checking ──────────────────────────────────────────────────────────


def _check_csv_columns(path: Path, expected_columns: list[str]) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            actual = list(reader.fieldnames or [])
            rows = sum(1 for _ in reader)
        missing_cols = [c for c in expected_columns if c not in actual]
        extra_cols = [c for c in actual if c not in expected_columns]
        return {
            "status": "ok" if not missing_cols else "columns_missing",
            "row_count": rows,
            "expected_columns": expected_columns,
            "actual_columns": actual,
            "missing_columns": missing_cols,
            "extra_columns": extra_cols,
        }
    except Exception as exc:
        return {"status": "read_error", "error": str(exc)}


def _check_json_keys(path: Path, expected_keys: list[str]) -> dict:
    data, err = _load_json_safe(path)
    if err:
        return {"status": "parse_error", "error": err}
    if isinstance(data, dict):
        actual = list(data.keys())
        # Count largest nested array (e.g. defect_map, roles, steps) as row_count
        list_counts = [len(v) for v in data.values() if isinstance(v, list)]
        row_count = max(list_counts) if list_counts else 1
    elif isinstance(data, list):
        actual = list(data[0].keys()) if data and isinstance(data[0], dict) else []
        row_count = len(data)
    else:
        actual = []
        row_count = 1
    missing = [k for k in expected_keys if k not in actual]
    return {
        "status": "ok" if not missing else "keys_missing",
        "row_count": row_count,
        "expected_keys": expected_keys,
        "actual_keys": actual,
        "missing_keys": missing,
    }


def _check_field(field: InputField, input_dir: Path) -> dict:
    file_path = input_dir / field.name
    result: dict[str, Any] = {
        "file": field.name,
        "required": field.required,
        "present": file_path.exists(),
        "minimum_viable_rows": field.minimum_viable_rows,
        "recommended_rows": field.recommended_rows,
        "functional_yield_role": field.functional_yield_role,
    }

    if not file_path.exists():
        result["status"] = "missing"
        result["blocking"] = field.required
        result["row_count"] = 0
        result["sufficiency_status"] = "MISSING"
        return result

    if field.format == "csv" and field.columns:
        check = _check_csv_columns(file_path, field.columns)
        result.update(check)
        result["blocking"] = check["status"] != "ok" and field.required
    elif field.format == "json" and field.json_keys:
        check = _check_json_keys(file_path, field.json_keys)
        result.update(check)
        result["blocking"] = check["status"] != "ok" and field.required
    elif field.format == "csv":
        # CSV without expected columns — count rows
        try:
            with open(file_path, encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                result["actual_columns"] = list(reader.fieldnames or [])
                rows = sum(1 for _ in reader)
            result["row_count"] = rows
            result["status"] = "ok" if rows > 0 else "empty"
            result["blocking"] = rows == 0 and field.required
        except Exception as exc:
            result["status"] = "read_error"
            result["error"] = str(exc)
            result["blocking"] = field.required
    elif field.format == "json":
        data, err = _load_json_safe(file_path)
        if err:
            result["status"] = "parse_error"
            result["error"] = err
            result["blocking"] = field.required
        else:
            rc = len(data) if isinstance(data, list) else 1
            result["row_count"] = rc
            result["status"] = "ok" if rc > 0 else "empty"
            result["blocking"] = rc == 0 and field.required
    else:
        try:
            size = file_path.stat().st_size
            result["status"] = "ok" if size > 0 else "empty"
            result["byte_size"] = size
            result["blocking"] = size == 0 and field.required
        except Exception as exc:
            result["status"] = "read_error"
            result["error"] = str(exc)
            result["blocking"] = field.required

    if "status" not in result:
        result["status"] = "ok"
        result["blocking"] = False

    # ── Row-count sufficiency (Option A: per-field minimum_viable_rows) ────────
    row_count = result.get("row_count", 0)
    if result["status"] in ("read_error", "parse_error"):
        result["sufficiency_status"] = "MISSING"
    elif row_count >= field.minimum_viable_rows:
        result["sufficiency_status"] = "SUFFICIENT"
    elif row_count > 0:
        result["sufficiency_status"] = "INSUFFICIENT"
        # Treat as blocking if field is required and below minimum
        if field.required:
            result["blocking"] = True
            result["sufficiency_note"] = (
                f"Has {row_count} row(s) but needs {field.minimum_viable_rows} "
                f"minimum viable rows for functional yield analysis."
            )
    else:
        result["sufficiency_status"] = "MISSING"
        if field.required:
            result["blocking"] = True

    # ── Column/key mismatch overrides SUFFICIENT ───────────────────────────────
    # A file with missing required columns or JSON keys cannot be SUFFICIENT
    # even if its row count is high enough.
    if result["status"] in ("columns_missing", "keys_missing") and field.required:
        if result.get("sufficiency_status") == "SUFFICIENT":
            result["sufficiency_status"] = "INSUFFICIENT"
        result["blocking"] = True

    return result


# ── Structured check summaries ─────────────────────────────────────────────────


def _build_required_optional_lists(
    field_checks: list[dict], contract: PilotContract
) -> tuple[list, list, list, list]:
    """Return (required_present, required_missing, optional_present, optional_missing)."""
    req_names = {f.name for f in contract.required_fields}
    opt_names = {f.name for f in contract.optional_fields}
    checks_by_file = {c["file"]: c for c in field_checks}

    required_present = [
        n for n in req_names
        if checks_by_file.get(n, {}).get("present", False)
    ]
    required_missing = [
        n for n in req_names
        if not checks_by_file.get(n, {}).get("present", False)
    ]
    optional_present = [
        n for n in opt_names
        if checks_by_file.get(n, {}).get("present", False)
    ]
    optional_missing = [
        n for n in opt_names
        if not checks_by_file.get(n, {}).get("present", False)
    ]
    return required_present, required_missing, optional_present, optional_missing


def _build_column_check(field_checks: list[dict]) -> dict:
    """Aggregate column check results across all checked files."""
    passed = []
    failed = []
    for c in field_checks:
        if "missing_columns" in c:
            fname = c["file"]
            missing = c["missing_columns"]
            if missing:
                failed.append({"file": fname, "missing_columns": missing})
            else:
                passed.append(fname)
        elif "missing_keys" in c:
            fname = c["file"]
            missing = c["missing_keys"]
            if missing:
                failed.append({"file": fname, "missing_keys": missing})
            else:
                passed.append(fname)
        elif c.get("present") and c.get("status") == "ok":
            passed.append(c["file"])
    return {"passed": passed, "failed": failed}


def _build_mvr_check(field_checks: list[dict]) -> dict:
    """Build minimum_viable_rows_check summary."""
    passed = []
    failed = []
    warnings = []
    for c in field_checks:
        suf = c.get("sufficiency_status", "MISSING")
        fname = c["file"]
        mvr = c.get("minimum_viable_rows", 0)
        rc = c.get("row_count", 0)
        if suf == "SUFFICIENT":
            passed.append({"file": fname, "row_count": rc, "minimum_viable_rows": mvr})
        elif suf == "INSUFFICIENT":
            entry = {"file": fname, "row_count": rc, "minimum_viable_rows": mvr}
            if c.get("required"):
                failed.append(entry)
            else:
                warnings.append(entry)
        elif suf == "MISSING" and c.get("present"):
            # Present but effectively empty
            failed.append({"file": fname, "row_count": rc, "minimum_viable_rows": mvr})
    return {"passed": passed, "failed": failed, "warnings": warnings}


def _compute_functional_yield_readiness(
    field_checks: list[dict], contract: PilotContract
) -> dict:
    """Compute per-role readiness booleans based on sufficiency status."""
    fy_map = contract.functional_yield_mapping()
    checks_by_file = {c["file"]: c for c in field_checks}

    roles = [
        "remaining_functions_inputs",
        "blocked_functions_inputs",
        "valid_conditions_inputs",
        "evidence_inputs",
        "human_review_inputs",
    ]

    result = {}
    for role in roles:
        files_in_role = fy_map.get(role, [])
        # Role is ready if all its required files are SUFFICIENT
        # (vacuously true if no files assigned to this role)
        role_ready = True
        for fname in files_in_role:
            c = checks_by_file.get(fname, {})
            field = next((f for f in contract.input_fields if f.name == fname), None)
            if field and field.required:
                if c.get("sufficiency_status") != "SUFFICIENT":
                    role_ready = False
                    break
        result[f"{role}_ready"] = role_ready
    return result


# ── Scoring ────────────────────────────────────────────────────────────────────


def _score_readiness(
    field_checks: list[dict], contract: PilotContract
) -> tuple[float, str]:
    """
    Returns (score_0_to_1, canonical_status).

    Scoring:
    - Required files are 80% of score; optional 20%.
    - A required file that is SUFFICIENT scores 1.0; INSUFFICIENT scores 0.5;
      MISSING scores 0.0.
    - Score capping: if any required field is MISSING → cap score at 0.4.
    - Status thresholds:
        all required SUFFICIENT              → READY_FOR_FUNCTIONAL_YIELD_PILOT
        some required INSUFFICIENT/MISSING   → PARTIAL or NOT_READY
        any required MISSING (blocking=True) → NOT_READY_FOR_FUNCTIONAL_YIELD_PILOT
    """
    required_fields = [f for f in contract.input_fields if f.required]
    optional_fields = [f for f in contract.input_fields if not f.required]
    checks_by_file = {c["file"]: c for c in field_checks}

    any_required_missing = False

    req_scores = []
    for f in required_fields:
        c = checks_by_file.get(f.name, {"sufficiency_status": "MISSING", "blocking": True})
        suf = c.get("sufficiency_status", "MISSING")
        if suf == "SUFFICIENT":
            req_scores.append(1.0)
        elif suf == "INSUFFICIENT":
            req_scores.append(0.5)
        else:
            req_scores.append(0.0)
            any_required_missing = True

    opt_scores = []
    for f in optional_fields:
        c = checks_by_file.get(f.name, {"sufficiency_status": "MISSING"})
        suf = c.get("sufficiency_status", "MISSING")
        opt_scores.append(1.0 if suf == "SUFFICIENT" else (0.5 if suf == "INSUFFICIENT" else 0.0))

    req_avg = (sum(req_scores) / len(req_scores)) if req_scores else 1.0
    opt_avg = (sum(opt_scores) / len(opt_scores)) if opt_scores else 1.0

    score = req_avg * 0.8 + opt_avg * 0.2

    # Cap score if any required file is missing
    if any_required_missing:
        score = min(score, 0.4)

    # Canonical status
    if req_avg == 1.0:
        status = STATUS_READY
    elif req_avg >= 0.5 and not any_required_missing:
        status = STATUS_PARTIAL
    else:
        status = STATUS_NOT_READY

    return round(score, 3), status


# ── Blocking issues ────────────────────────────────────────────────────────────


def _build_blocking_issues(field_checks: list[dict]) -> list[dict]:
    issues = []
    for c in field_checks:
        if not c.get("blocking"):
            continue
        status = c.get("status", "unknown")
        suf = c.get("sufficiency_status", "MISSING")
        if status == "missing" or suf == "MISSING":
            issues.append({
                "severity": "blocking",
                "file": c["file"],
                "functional_yield_role": c.get("functional_yield_role", "evidence_inputs"),
                "issue": f"Required file '{c['file']}' is missing from input directory.",
                "resolution": f"Provide '{c['file']}' in the --input directory.",
            })
        elif suf == "INSUFFICIENT":
            issues.append({
                "severity": "blocking",
                "file": c["file"],
                "functional_yield_role": c.get("functional_yield_role", "evidence_inputs"),
                "issue": c.get("sufficiency_note", (
                    f"File '{c['file']}' has too few rows for functional yield analysis "
                    f"(minimum_viable_rows: {c.get('minimum_viable_rows', '?')})."
                )),
                "resolution": (
                    f"Provide at least {c.get('minimum_viable_rows', '?')} rows "
                    f"in '{c['file']}'."
                ),
            })
        elif status == "columns_missing":
            issues.append({
                "severity": "blocking",
                "file": c["file"],
                "functional_yield_role": c.get("functional_yield_role", "evidence_inputs"),
                "issue": (
                    f"Required CSV columns missing in '{c['file']}': "
                    f"{c.get('missing_columns', [])}"
                ),
                "resolution": "Add the missing columns to the CSV file.",
            })
        elif status == "keys_missing":
            issues.append({
                "severity": "blocking",
                "file": c["file"],
                "functional_yield_role": c.get("functional_yield_role", "evidence_inputs"),
                "issue": (
                    f"Required JSON keys missing in '{c['file']}': "
                    f"{c.get('missing_keys', [])}"
                ),
                "resolution": "Add the missing keys to the JSON file.",
            })
        elif status in ("parse_error", "read_error"):
            issues.append({
                "severity": "blocking",
                "file": c["file"],
                "functional_yield_role": c.get("functional_yield_role", "evidence_inputs"),
                "issue": f"Cannot read '{c['file']}': {c.get('error', status)}",
                "resolution": "Check file encoding (UTF-8 required) and format.",
            })
        elif status == "empty":
            issues.append({
                "severity": "blocking",
                "file": c["file"],
                "functional_yield_role": c.get("functional_yield_role", "evidence_inputs"),
                "issue": f"File '{c['file']}' is empty.",
                "resolution": "Provide non-empty data file.",
            })
    return issues


# ── Missing data request (canonical v2.9.2) ───────────────────────────────────


def _build_missing_data_request(
    field_checks: list[dict], contract: PilotContract, meta: dict
) -> dict:
    """Build canonical missing_data_request.json for the check run."""
    fy_map = contract.functional_yield_mapping()
    file_to_role: dict[str, str] = {}
    for role, files in fy_map.items():
        for fname in files:
            file_to_role[fname] = role

    # Canonical arrays
    missing_required_files: list[str] = []
    missing_required_columns: list[dict] = []
    missing_units: list[dict] = []
    minimum_viable_rows_failures: list[dict] = []
    recommended_optional_files: list[str] = []
    why_needed: list[dict] = []

    # Legacy items list (kept for compat)
    items: list[dict] = []

    # First pass: collect column/key mismatches from ALL checks (independent of sufficiency)
    for c in field_checks:
        fname = c["file"]
        field = next((f for f in contract.input_fields if f.name == fname), None)
        if field is None or not field.required:
            continue
        missing_cols = c.get("missing_columns") or c.get("missing_keys")
        if missing_cols:
            missing_required_columns.append({
                "file": fname,
                "missing_columns": missing_cols,
            })

    for c in field_checks:
        suf = c.get("sufficiency_status", "MISSING")
        fname = c["file"]
        field = next((f for f in contract.input_fields if f.name == fname), None)
        if field is None:
            continue

        fy_role = file_to_role.get(fname, field.functional_yield_role)
        reason = _FY_ROLE_REASON.get(fy_role, "required for functional yield analysis")

        if suf == "SUFFICIENT":
            continue

        if suf == "MISSING":
            if field.required:
                missing_required_files.append(fname)
                why_needed.append({
                    "missing_item": fname,
                    "needed_for": fy_role,
                    "reason": reason,
                })
            else:
                recommended_optional_files.append(fname)
        elif suf == "INSUFFICIENT":
            minimum_viable_rows_failures.append({
                "file": fname,
                "row_count": c.get("row_count", 0),
                "minimum_viable_rows": field.minimum_viable_rows,
                "required": field.required,
            })
            if field.required:
                why_needed.append({
                    "missing_item": fname,
                    "needed_for": fy_role,
                    "reason": f"insufficient rows ({c.get('row_count', 0)} < {field.minimum_viable_rows}); {reason}",
                })

        # Legacy items list
        priority = "P0_blocking" if field.required else "P1_recommended"
        item: dict = {
            "file": fname,
            "required": field.required,
            "priority": priority,
            "sufficiency_status": suf,
            "row_count": c.get("row_count", 0),
            "minimum_viable_rows": field.minimum_viable_rows,
            "recommended_rows": field.recommended_rows,
            "functional_yield_role": fy_role,
            "why_needed_for_functional_yield": _FY_ROLE_REASON.get(fy_role, "Required for analysis."),
        }
        if suf == "MISSING":
            item["issue"] = f"File '{fname}' is missing from input directory."
        elif suf == "INSUFFICIENT":
            item["issue"] = (
                f"File '{fname}' has {c.get('row_count', 0)} row(s), "
                f"needs {field.minimum_viable_rows} minimum viable rows."
            )
        items.append(item)

    p0 = [i for i in items if i["priority"] == "P0_blocking"]
    p1 = [i for i in items if i["priority"] == "P1_recommended"]

    return {
        "schema": "hal.yieldos.pilot.missing_data_request.v1",
        "domain": contract.domain,
        # Canonical arrays (v2.9.2)
        "missing_required_files": missing_required_files,
        "missing_required_columns": missing_required_columns,
        "missing_units": missing_units,
        "minimum_viable_rows_failures": minimum_viable_rows_failures,
        "recommended_optional_files": recommended_optional_files,
        "why_needed_for_functional_yield": why_needed,
        "human_review_required": True,
        "claim_boundary": "missing_data_request_for_candidate_review_only",
        # Legacy (kept for compat)
        "status": "missing_data_identified_from_check",
        "blocking_count": len(p0),
        "recommended_count": len(p1),
        "items": items,
        "generated_by": meta,
    }


# ── Data sufficiency preview (canonical v2.9.2) ───────────────────────────────


def _sufficiency_status_from_readiness(readiness_status: str) -> str:
    mapping = {
        STATUS_READY: "SUFFICIENT_FOR_CANDIDATE_REVIEW",
        STATUS_PARTIAL: "PARTIAL_FOR_CANDIDATE_REVIEW",
        STATUS_NOT_READY: "INSUFFICIENT_FOR_CANDIDATE_REVIEW",
        STATUS_INVALID: "INVALID_INPUT",
    }
    return mapping.get(readiness_status, "INSUFFICIENT_FOR_CANDIDATE_REVIEW")


def _build_data_sufficiency_preview(
    field_checks: list[dict],
    contract: PilotContract,
    readiness_status: str,
    meta: dict,
) -> dict:
    fy_map = contract.functional_yield_mapping()
    file_to_role: dict[str, str] = {}
    for role, files in fy_map.items():
        for fname in files:
            file_to_role[fname] = role

    per_file = []
    for c in field_checks:
        fname = c["file"]
        field = next(
            (f for f in contract.input_fields if f.name == fname), None
        )
        mvr = field.minimum_viable_rows if field else 0
        fy_role = file_to_role.get(fname, c.get("functional_yield_role", "evidence_inputs"))
        per_file.append({
            "file": fname,
            "required": c.get("required", False),
            "functional_yield_role": fy_role,
            "present": c.get("present", False),
            "row_count": c.get("row_count", 0),
            "minimum_viable_rows": mvr,
            "recommended_rows": field.recommended_rows if field else 0,
            "sufficiency_status": c.get("sufficiency_status", "MISSING"),
            "status": c.get("status", "missing"),
        })

    sufficient = [p for p in per_file if p["sufficiency_status"] == "SUFFICIENT"]
    insufficient = [p for p in per_file if p["sufficiency_status"] == "INSUFFICIENT"]
    missing = [p for p in per_file if p["sufficiency_status"] == "MISSING"]

    # functional_yield_gaps: files in FY roles that are not SUFFICIENT
    checks_by_file = {c["file"]: c for c in field_checks}
    functional_yield_gaps = []
    for role, files in fy_map.items():
        for fname in files:
            c = checks_by_file.get(fname, {})
            suf = c.get("sufficiency_status", "MISSING")
            field = next((f for f in contract.input_fields if f.name == fname), None)
            if field and field.required and suf != "SUFFICIENT":
                functional_yield_gaps.append({
                    "file": fname,
                    "role": role,
                    "sufficiency_status": suf,
                })

    # Top-level sufficiency status (v2.9.2 canonical)
    top_sufficiency = _sufficiency_status_from_readiness(readiness_status)

    if readiness_status == STATUS_READY:
        sufficient_for = _SUFFICIENT_FOR_READY
    elif readiness_status == STATUS_PARTIAL:
        sufficient_for = _SUFFICIENT_FOR_PARTIAL
    else:
        sufficient_for = _SUFFICIENT_FOR_NOT_READY

    return {
        "schema": "hal.yieldos.pilot.data_sufficiency_preview.v1",
        "domain": contract.domain,
        # Canonical top-level (v2.9.2)
        "sufficiency_status": top_sufficiency,
        "sufficient_for": sufficient_for,
        "not_sufficient_for": _NOT_SUFFICIENT_FOR,
        "functional_yield_gaps": functional_yield_gaps,
        "claim_boundary": "data_sufficiency_preview_not_analysis_result",
        # Detailed breakdown
        "files_sufficient": len(sufficient),
        "files_insufficient": len(insufficient),
        "files_missing": len(missing),
        "per_file": per_file,
        "functional_yield_mapping": fy_map,
        "generated_by": meta,
    }


# ── Pilot decision boundary (canonical v2.9.2) ────────────────────────────────


def _build_pilot_decision_boundary(
    status: str, contract: PilotContract, blocking_issues: list[dict], meta: dict
) -> dict:
    allowed = _ALLOWED_DECISIONS_READY if status == STATUS_READY else _ALLOWED_DECISIONS_NOT_READY
    return {
        "schema": "hal.yieldos.pilot.decision_boundary.v1",
        "domain": contract.domain,
        "readiness_status": status,
        # Canonical v2.9.2: explicit allowed / forbidden decisions
        "allowed_decisions": allowed,
        "forbidden_decisions": _FORBIDDEN_DECISIONS,
        "pilot_can_proceed": status == STATUS_READY,
        "human_review_required": True,
        "automatic_decision_enabled": False,
        "read_only": True,
        "candidate_only": True,
        "hardware_control_enabled": False,
        "claim_boundary": "pilot_decision_boundary_not_operational_authority",
        "safety_note": (
            "YieldOS produces evidence candidates for human review. "
            "No operational decision should be taken without human approval. "
            "This check does not certify yield, safety, or root cause."
        ),
        "blocking_issues_count": len(blocking_issues),
        "evidence_claims_available_if_ready": (
            contract.evidence_claims if status == STATUS_READY else []
        ),
        "blocked_claims": contract.blocked_claims,
        "generated_by": meta,
    }


# ── Next steps (compatibility alias) ──────────────────────────────────────────


def _build_next_steps(
    status: str,
    blocking_issues: list[dict],
    field_checks: list[dict],
    contract: PilotContract,
) -> list[dict]:
    steps = []
    prio = 1

    for issue in blocking_issues:
        steps.append({
            "priority": prio,
            "action": issue["resolution"],
            "reason": issue["issue"],
            "category": "fix_blocking_issue",
        })
        prio += 1

    for c in field_checks:
        if not c.get("present") and not c.get("required"):
            steps.append({
                "priority": prio,
                "action": f"Provide optional file '{c['file']}' for deeper analysis.",
                "reason": "Optional files improve functional yield score accuracy.",
                "category": "provide_optional_data",
            })
            prio += 1

    if status == STATUS_READY:
        steps.append({
            "priority": prio,
            "action": (
                f"Run full YieldOS {contract.domain} analysis: "
                f"yieldos {contract.domain} analyze --input <dir> --out <out_dir>"
            ),
            "reason": "All required data is present and sufficient.",
            "category": "proceed_to_analysis",
        })
    elif status in (STATUS_PARTIAL, STATUS_NOT_READY):
        steps.append({
            "priority": prio,
            "action": "Resolve blocking issues above before running full analysis.",
            "reason": "Some required data is missing or below minimum viable rows.",
            "category": "resolve_before_proceeding",
        })

    return steps


# ── Public entry point ─────────────────────────────────────────────────────────


def run_pilot_check(*, domain: str, input_dir: Path, out_dir: Path) -> Path:
    """
    Check input data against domain contract. Write canonical + alias output files.
    Returns the output directory path.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    contract = DomainContracts.get(domain)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    meta = generated_by()

    present_files = [f.name for f in input_dir.iterdir() if f.is_file()]

    field_checks = [_check_field(field, input_dir) for field in contract.input_fields]
    score, status = _score_readiness(field_checks, contract)
    blocking_issues = _build_blocking_issues(field_checks)

    # Structured check helpers
    req_present, req_missing, opt_present, opt_missing = _build_required_optional_lists(
        field_checks, contract
    )
    col_check = _build_column_check(field_checks)
    mvr_check = _build_mvr_check(field_checks)
    fy_readiness = _compute_functional_yield_readiness(field_checks, contract)

    sufficient_for = (
        _SUFFICIENT_FOR_READY if status == STATUS_READY
        else _SUFFICIENT_FOR_PARTIAL if status == STATUS_PARTIAL
        else _SUFFICIENT_FOR_NOT_READY
    )

    # ── Canonical output files ─────────────────────────────────────────────────

    # 1. pilot_readiness_report.json (canonical schema v2.9.2)
    readiness_report = {
        "schema": "hal.yieldos.pilot.readiness_report.v1",
        "domain": domain,
        "display_name": contract.display_name,
        "input_path": str(input_dir),
        # Canonical status (v2.9.2): readiness_status is the primary field
        "readiness_status": status,
        # Compat: status kept as alias (same value as readiness_status)
        "status": status,
        "readiness_score": score,
        "readiness_score_percent": round(score * 100, 2),
        # File presence lists
        "required_files_present": sorted(req_present),
        "required_files_missing": sorted(req_missing),
        "optional_files_present": sorted(opt_present),
        "optional_files_missing": sorted(opt_missing),
        # Structured checks
        "column_check": col_check,
        "unit_check": {"passed": [], "warnings": []},
        "minimum_viable_rows_check": mvr_check,
        # Functional yield readiness (5 booleans)
        "functional_yield_readiness": fy_readiness,
        # Claim context
        "sufficient_for": sufficient_for,
        "not_sufficient_for": _NOT_SUFFICIENT_FOR,
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "pilot_readiness_only_not_certification",
        # Legacy fields kept for compat
        "blocking_issue_count": len(blocking_issues),
        "automatic_decision_enabled": False,
        "input_directory": str(input_dir),
        "files_found_in_input": present_files,
        "pilot_duration_hint": contract.pilot_duration_hint,
        "functional_yield_mapping": contract.functional_yield_mapping(),
        "generated_by": meta,
        "summary": (
            f"Pilot readiness for domain '{domain}': {status} "
            f"(score={score:.1%}). "
            f"{len(blocking_issues)} blocking issue(s) found."
        ),
    }
    _write_json(out / "pilot_readiness_report.json", readiness_report)

    # 2. missing_data_request.json (canonical schema v2.9.2)
    missing_req = _build_missing_data_request(field_checks, contract, meta)
    _write_json(out / "missing_data_request.json", missing_req)

    # 3. data_sufficiency_preview.json (canonical schema v2.9.2)
    dsp = _build_data_sufficiency_preview(field_checks, contract, status, meta)
    _write_json(out / "data_sufficiency_preview.json", dsp)

    # 4. pilot_decision_boundary.json (canonical schema v2.9.2)
    boundary = _build_pilot_decision_boundary(status, contract, blocking_issues, meta)
    _write_json(out / "pilot_decision_boundary.json", boundary)

    # ── Compatibility aliases ──────────────────────────────────────────────────

    # readiness_report.json
    compat_report = dict(readiness_report)
    compat_report["schema"] = "hal.yieldos.pilot_readiness_report.v1"
    _status_compat = {
        STATUS_READY: "READY",
        STATUS_PARTIAL: "PARTIAL",
        STATUS_NOT_READY: "NOT_READY",
        STATUS_INVALID: "NOT_READY",
    }
    compat_report["status"] = _status_compat.get(status, status)
    compat_report["status_v291"] = status
    _write_json(out / "readiness_report.json", compat_report)

    # data_sufficiency.json
    field_check_summary = check_missing_fields(contract, present_files)
    data_sufficiency_compat = {
        "schema": "hal.yieldos.pilot_data_sufficiency.v1",
        "domain": domain,
        "generated_by": meta,
        "field_checks": field_checks,
        "summary": field_check_summary,
        "min_records_required": contract.min_records,
        "recommended_records": contract.recommended_records,
        "row_counts": {
            c["file"]: c.get("row_count", "N/A")
            for c in field_checks
            if c.get("present") and "row_count" in c
        },
    }
    _write_json(out / "data_sufficiency.json", data_sufficiency_compat)

    # blocking_issues.json
    blocking_output = {
        "schema": "hal.yieldos.pilot_blocking_issues.v1",
        "domain": domain,
        "generated_by": meta,
        "blocking_count": len(blocking_issues),
        "pilot_can_proceed": len(blocking_issues) == 0,
        "issues": blocking_issues,
    }
    _write_json(out / "blocking_issues.json", blocking_output)

    # next_steps.json
    next_steps = _build_next_steps(status, blocking_issues, field_checks, contract)
    next_steps_output = {
        "schema": "hal.yieldos.pilot_next_steps.v1",
        "domain": domain,
        "generated_by": meta,
        "status": _status_compat.get(status, status),
        "status_v291": status,
        "next_steps": next_steps,
        "pilot_duration_hint": contract.pilot_duration_hint,
        "full_analysis_command": (
            f"yieldos {contract.domain} analyze --input <data_dir> --out <output_dir>"
        ),
    }
    _write_json(out / "next_steps.json", next_steps_output)

    return out
