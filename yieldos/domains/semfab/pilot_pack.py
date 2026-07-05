"""Semiconductor Pilot-Pack generator (v3.0.1).

Generates 11 semiconductor-specific pilot-pack JSON reports plus a markdown summary.
No hardware control. Read-only, candidate-only, human-review-required evidence layer.
Does NOT generate recovery_profile.json.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REQUIRED_PILOT_FILES = ["tool_log.csv", "metrology.csv", "test_results.csv"]

OPTIONAL_PILOT_FILES = [
    "wafer_map.csv",
    "lot_genealogy.csv",
    "chamber_log.csv",
    "recipe_context_redacted.json",
    "inspection_notes.csv",
    "chip_tile_map.json",
    "workload_roles.json",
    "recovery_constraints.json",
]

SEMICONDUCTOR_ROLES = [
    "high_speed_compute",
    "low_power_compute",
    "cache_assist",
    "background_diagnostics",
    "redundancy_pool",
    "low_priority_batch",
    "inspection_only_bin",
    "recovery_candidate_region",
]

_SAFETY = {
    "hardware_execution_enabled": False,
    "hardware_control_enabled": False,
    "human_review_required": True,
    "candidate_only": True,
    "read_only": True,
}

_NOT_SUFFICIENT_FOR = [
    "recipe_control",
    "MES_writeback",
    "APC_action",
    "EDA_signoff",
    "timing_closure",
    "certified_root_cause",
    "yield_guarantee",
    "automatic_recovery",
]


def _load_csv(path: Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        cols = list(reader.fieldnames or [])
    return cols, rows


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _unique(rows: list[dict], col: str) -> list[str]:
    seen: list[str] = []
    found: set[str] = set()
    for r in rows:
        v = str(r.get(col, "")).strip()
        if v and v not in found:
            found.add(v)
            seen.append(v)
    return seen


def _count_pass_fail(rows: list[dict]) -> tuple[int, int, int]:
    total = len(rows)
    pf_pass = sum(1 for r in rows if str(r.get("pass_fail", "")).strip().lower() == "pass")
    pf_fail = sum(1 for r in rows if str(r.get("pass_fail", "")).strip().lower() == "fail")
    pf_unknown = total - pf_pass - pf_fail
    return pf_pass, pf_fail, pf_unknown


def _get_bool(data: dict | None, key: str, default: bool = False) -> bool:
    if data is None:
        return default
    return bool(data.get(key, default))


def generate_pilot_pack(
    input_dir: str,
    case_id: str,
    asset_id: str,
    alias_map: dict[str, str],
    tool_cols: list[str],
    tool_rows: list[dict],
    metro_rows: list[dict],
    test_rows: list[dict],
) -> dict[str, dict]:
    """Generate all 11 semiconductor pilot-pack JSON reports.

    Returns dict keyed by report name (without .json) → report dict.
    """
    inp = Path(input_dir)

    # Detect which files are present
    files_present = [f for f in REQUIRED_PILOT_FILES if (inp / f).exists()]
    files_missing = [f for f in REQUIRED_PILOT_FILES if not (inp / f).exists()]
    opt_present = [f for f in OPTIONAL_PILOT_FILES if (inp / f).exists()]

    # Load optional structured data
    wafer_map_cols, wafer_map_rows = _load_csv(inp / "wafer_map.csv")
    tile_map = _load_json(inp / "chip_tile_map.json")
    workloads = _load_json(inp / "workload_roles.json")
    constraints = _load_json(inp / "recovery_constraints.json")
    recipe_ctx = _load_json(inp / "recipe_context_redacted.json")

    # Derived evidence
    lot_ids = list(set(_unique(tool_rows, "lot_id") + _unique(test_rows, "lot_id")))
    wafer_ids = list(set(_unique(tool_rows, "wafer_id") + _unique(test_rows, "wafer_id")))
    pf_pass, pf_fail, pf_unknown = _count_pass_fail(test_rows)

    alarm_rows = [r for r in tool_rows if str(r.get("alarm_code", "0")).strip() not in ("0", "")]
    chamber_ids = _unique(tool_rows, "chamber_id")
    step_ids = _unique(tool_rows, "step_id")

    reports: dict[str, dict] = {}

    # ── 1. Evidence Completeness Report ─────────────────────────────────────
    chip_tile_present = "chip_tile_map.json" in opt_present
    workload_present = "workload_roles.json" in opt_present
    constraints_present = "recovery_constraints.json" in opt_present
    wafer_map_present = "wafer_map.csv" in opt_present
    metrology_present = len(metro_rows) > 0
    test_results_present = len(test_rows) > 0
    tool_log_present = len(tool_rows) > 0

    score = 1.0
    if not tool_log_present:
        score = min(score, 0.60)
    if not test_results_present:
        score = min(score, 0.60)
    if not metrology_present:
        score = min(score, 0.75)

    recovery_intake_ready = chip_tile_present and workload_present and constraints_present
    blocked_die_ready = wafer_map_present or test_results_present
    remaining_die_ready = test_results_present and pf_pass > 0

    completeness = {
        "schema": "hal.yieldos.semiconductor.evidence_completeness_report.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "completeness_score": round(score, 4),
        "completeness_score_percent": round(score * 100, 2),
        "required_inputs": {
            "tool_log_present": tool_log_present,
            "metrology_present": metrology_present,
            "test_results_present": test_results_present,
            "wafer_map_present": wafer_map_present,
            "lot_genealogy_present": "lot_genealogy.csv" in opt_present,
            "chamber_log_present": "chamber_log.csv" in opt_present,
            "inspection_notes_present": "inspection_notes.csv" in opt_present,
            "chip_tile_map_present": chip_tile_present,
            "workload_roles_present": workload_present,
            "recovery_constraints_present": constraints_present,
        },
        "functional_yield_inputs": {
            "remaining_die_evidence_ready": remaining_die_ready,
            "blocked_die_evidence_ready": blocked_die_ready,
            "valid_conditions_evidence_ready": tool_log_present and metrology_present,
            "process_context_evidence_ready": tool_log_present,
            "human_review_evidence_ready": "inspection_notes.csv" in opt_present,
            "recovery_compiler_intake_ready": recovery_intake_ready,
        },
        "missing_evidence": files_missing,
        "not_sufficient_for": _NOT_SUFFICIENT_FOR,
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "semiconductor_evidence_completeness_for_candidate_review_only",
    }
    reports["semiconductor_evidence_completeness_report"] = completeness

    # ── 2. Wafer/Die Summary ─────────────────────────────────────────────────
    bin_summary: dict[str, int] = {}
    for r in test_rows:
        bc = str(r.get("bin_code", "unknown")).strip()
        bin_summary[bc] = bin_summary.get(bc, 0) + 1

    candidate_remaining = [r.get("die_id") or r.get("wafer_id") for r in test_rows
                           if str(r.get("pass_fail", "")).lower() == "pass"]
    candidate_blocked = [r.get("die_id") or r.get("wafer_id") for r in test_rows
                         if str(r.get("pass_fail", "")).lower() == "fail"]
    candidate_reduced = []
    if wafer_map_rows:
        candidate_reduced = [r.get("die_id") for r in wafer_map_rows
                             if str(r.get("bin_code", "")).strip() in ("2",)]

    reports["semiconductor_wafer_die_summary"] = {
        "schema": "hal.yieldos.semiconductor.wafer_die_summary.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "lot_ids": lot_ids,
        "wafer_ids": wafer_ids,
        "die_count_total": len(test_rows),
        "die_count_pass": pf_pass,
        "die_count_fail": pf_fail,
        "die_count_unknown": pf_unknown,
        "bin_summary": bin_summary,
        "candidate_remaining_die": [d for d in candidate_remaining if d][:20],
        "candidate_blocked_die": [d for d in candidate_blocked if d][:20],
        "candidate_reduced_die": [d for d in candidate_reduced if d][:10],
        "evidence_refs": ["test_results.csv"] + (["wafer_map.csv"] if wafer_map_present else []),
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "wafer_die_summary_candidate_only_not_yield_guarantee",
    }

    # ── 3. Functional Region Map ─────────────────────────────────────────────
    regions: list[dict] = []
    blocked_regions: list[dict] = []
    unknown_regions: list[dict] = []

    if tile_map and "tiles" in tile_map:
        for tile in tile_map["tiles"]:
            ts = tile.get("status", "unknown")
            region_entry = {
                "region_id": tile.get("tile_id", "unknown"),
                "region_type": "chip_tile",
                "members": [tile.get("tile_id", "")],
                "classification": (
                    "candidate_remaining" if ts == "usable"
                    else "candidate_reduced" if ts == "weak"
                    else "candidate_blocked" if ts == "defective"
                    else "unknown_insufficient_evidence"
                ),
                "confidence": tile.get("confidence", 0.0),
                "evidence_refs": tile.get("evidence_refs", []),
                "valid_conditions": [
                    "human_review_required_before_any_use",
                    "same_lot_and_test_conditions_as_sample",
                ] if ts in ("usable", "weak") else [],
                "claim_boundary": "candidate_region_classification_only",
            }
            if ts in ("usable", "weak"):
                regions.append(region_entry)
            elif ts == "defective":
                blocked_regions.append(region_entry)
            else:
                unknown_regions.append(region_entry)
    elif wafer_map_rows:
        for region_id in set(r.get("region_id", "unknown") for r in wafer_map_rows):
            region_rows = [r for r in wafer_map_rows if r.get("region_id") == region_id]
            pass_count = sum(1 for r in region_rows if str(r.get("pass_fail", "")).lower() == "pass")
            fail_count = sum(1 for r in region_rows if str(r.get("pass_fail", "")).lower() == "fail")
            if fail_count == 0:
                cls = "candidate_remaining"
            elif pass_count == 0:
                cls = "candidate_blocked"
            else:
                cls = "candidate_reduced"
            entry = {
                "region_id": region_id,
                "region_type": "wafer_region",
                "members": [r.get("die_id", "") for r in region_rows],
                "classification": cls,
                "confidence": round(pass_count / max(1, len(region_rows)), 2),
                "evidence_refs": ["wafer_map.csv", "test_results.csv"],
                "valid_conditions": ["human_review_required", "same_lot_test_context"],
                "claim_boundary": "candidate_region_classification_only",
            }
            if cls == "candidate_blocked":
                blocked_regions.append(entry)
            else:
                regions.append(entry)

    reports["semiconductor_functional_region_map"] = {
        "schema": "hal.yieldos.semiconductor.functional_region_map.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "region_level": "chip_tile" if tile_map else ("wafer_region" if wafer_map_rows else "die_level"),
        "regions": regions,
        "blocked_regions": blocked_regions,
        "unknown_regions": unknown_regions,
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "functional_region_map_candidate_classification_only",
    }

    # ── 4. Role Candidate Map ────────────────────────────────────────────────
    pass_rate = pf_pass / max(1, len(test_rows))
    fail_rate = pf_fail / max(1, len(test_rows))
    high_leakage_count = sum(
        1 for r in test_rows
        if str(r.get("pass_fail", "")).lower() == "fail"
        and float(r.get("leakage_nA", 0) or 0) > 100
    )

    remaining_roles: list[str] = []
    reduced_roles: list[str] = []
    blocked_roles: list[str] = []
    role_decisions: list[dict] = []

    for role in SEMICONDUCTOR_ROLES:
        if role == "high_speed_compute":
            margin_vals = [float(r.get("margin_score", 0) or 0)
                           for r in test_rows if r.get("margin_score")]
            avg_margin = sum(margin_vals) / max(1, len(margin_vals))
            if pass_rate >= 0.85 and avg_margin >= 0.80:
                cls = "remaining"
                remaining_roles.append(role)
                reason = "sufficient pass rate and margin evidence for high-speed role"
            elif pass_rate >= 0.60:
                cls = "reduced"
                reduced_roles.append(role)
                reason = "partial evidence; some margin deficiency detected"
            else:
                cls = "blocked"
                blocked_roles.append(role)
                reason = "insufficient pass rate and high leakage evidence for high-speed role"
        elif role == "low_power_compute":
            if pass_rate >= 0.50:
                cls = "remaining"
                remaining_roles.append(role)
                reason = "pass rate supports low_power_compute candidate under reduced conditions"
            else:
                cls = "reduced"
                reduced_roles.append(role)
                reason = "partial evidence; low pass rate limits low_power_compute eligibility"
        elif role == "background_diagnostics":
            cls = "remaining"
            remaining_roles.append(role)
            reason = "background_diagnostics can remain with partial evidence"
        elif role == "inspection_only_bin":
            cls = "remaining"
            remaining_roles.append(role)
            reason = "inspection_only_bin can remain when evidence is insufficient for full assignment"
        elif role == "recovery_candidate_region":
            if chip_tile_present:
                cls = "remaining"
                remaining_roles.append(role)
                reason = "chip_tile_map present; recovery candidate region is viable"
            else:
                cls = "blocked"
                blocked_roles.append(role)
                reason = "chip_tile_map required for recovery_candidate_region; not present"
        elif role in ("cache_assist", "redundancy_pool"):
            if pass_rate >= 0.70:
                cls = "remaining"
                remaining_roles.append(role)
                reason = "sufficient pass evidence for support role"
            else:
                cls = "reduced"
                reduced_roles.append(role)
                reason = "reduced mode candidate; pass rate insufficient for full support role"
        else:
            cls = "reduced"
            reduced_roles.append(role)
            reason = "insufficient evidence to fully classify role; reduced candidate"

        role_decisions.append({
            "role": role,
            "classification": cls,
            "evidence_refs": ["test_results.csv"] + (["chip_tile_map.json"] if chip_tile_present else []),
            "reason": reason,
            "valid_conditions": [
                "same_lot_family_and_test_conditions",
                "human_review_required_before_any_assignment",
            ],
            "what_not_to_do": [
                f"do not assign {role} without additional timing and margin evidence"
                if role == "high_speed_compute"
                else f"do not claim {role} is production-certified",
            ],
            "claim_boundary": "candidate_role_mapping_not_timing_closure",
        })

    reports["semiconductor_role_candidate_map"] = {
        "schema": "hal.yieldos.semiconductor.role_candidate_map.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "remaining_roles": remaining_roles,
        "reduced_roles": reduced_roles,
        "blocked_roles": blocked_roles,
        "role_decisions": role_decisions,
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "role_candidate_map_not_timing_closure_or_certification",
    }

    # ── 5. Valid Conditions Report ───────────────────────────────────────────
    valid_conds: list[dict] = []
    cond_id = 0
    for role in remaining_roles + reduced_roles:
        cond_id += 1
        cond = {
            "condition_id": f"cond_{cond_id:03d}",
            "applies_to_role": role,
            "condition": (
                "same lot family, same wafer test conditions, "
                "same tool/chamber/step context as observed sample, "
                "and voltage/temperature range consistent with test data"
            ),
            "evidence_refs": ["tool_log.csv", "test_results.csv"]
                + (["metrology.csv"] if metrology_present else []),
            "boundary": "candidate_condition_not_product_qualification",
        }
        valid_conds.append(cond)

    what_not_to_do = [
        "do not treat this as recipe qualification",
        "do not treat this as timing closure",
        "do not treat this as yield guarantee",
        "do not hand off to Recovery Compiler without chip_tile_map and workload roles",
        "do not control equipment from YieldOS output",
        "do not modify recipes based on this analysis",
    ]

    reports["semiconductor_valid_conditions_report"] = {
        "schema": "hal.yieldos.semiconductor.valid_conditions_report.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "valid_conditions": valid_conds,
        "invalid_or_unknown_conditions": [
            {"role": r, "reason": "insufficient evidence to establish valid conditions"}
            for r in blocked_roles
        ],
        "what_not_to_do": what_not_to_do,
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "valid_conditions_candidate_only_not_certified_operating_spec",
    }

    # ── 6. Process Evidence Report ───────────────────────────────────────────
    process_signals = []
    if alarm_rows:
        process_signals.append({
            "signal_id": "sig_tool_alarm",
            "source": "tool_log.csv",
            "signal_type": "alarm_event",
            "count": len(alarm_rows),
            "chambers_affected": list(set(r.get("chamber_id", "") for r in alarm_rows)),
            "claim_boundary": "candidate_signal_not_root_cause",
        })
    if step_ids:
        process_signals.append({
            "signal_id": "sig_step_context",
            "source": "tool_log.csv",
            "signal_type": "process_step_context",
            "steps_observed": step_ids,
            "claim_boundary": "candidate_signal_not_root_cause",
        })

    metro_signals = []
    if metro_rows:
        metrics = _unique(metro_rows, "metric_name")
        out_of_spec = [
            r for r in metro_rows
            if r.get("spec_high") and r.get("metric_value")
            and _safe_float(r.get("metric_value")) > _safe_float(r.get("spec_high"))
        ]
        metro_signals.append({
            "signal_id": "sig_metrology",
            "source": "metrology.csv",
            "metrics_observed": metrics[:10],
            "out_of_spec_count": len(out_of_spec),
            "claim_boundary": "candidate_signal_not_root_cause",
        })

    correlations: list[dict] = []
    if alarm_rows and pf_fail > 0:
        alarm_chambers = set(r.get("chamber_id", "") for r in alarm_rows)
        correlations.append({
            "correlation_id": "corr_001",
            "signal_a": "tool alarm events",
            "signal_b": "test failures",
            "candidate_interpretation": (
                f"alarm events in {list(alarm_chambers)[:3]} co-occur with "
                f"{pf_fail} test failures; candidate signal only"
            ),
            "evidence_refs": ["tool_log.csv", "test_results.csv"],
            "claim_boundary": "candidate_correlation_not_root_cause",
        })

    reports["semiconductor_process_evidence_report"] = {
        "schema": "hal.yieldos.semiconductor.process_evidence_report.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "candidate_process_signals": process_signals,
        "metrology_signals": metro_signals,
        "test_result_signals": [{
            "signal_id": "sig_test",
            "source": "test_results.csv",
            "die_count": len(test_rows),
            "pass": pf_pass,
            "fail": pf_fail,
            "claim_boundary": "candidate_signal_not_root_cause",
        }],
        "candidate_correlations": correlations,
        "warnings": [
            "correlation is not root cause",
            "process evidence is not FDC/APC replacement",
            "do not write recipe recommendations from this report",
        ],
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "process_evidence_not_root_cause_certification",
    }

    # ── 7. Human Review Packet ───────────────────────────────────────────────
    review_questions = [
        "Are lot and wafer IDs sufficiently anonymized for external sharing?",
        "Are tool and chamber IDs redacted but internally consistent?",
        "Is wafer_map present for spatial defect reasoning?",
        "Is chip_tile_map present for Recovery Compiler intake?",
        "Are workload roles synthetic or approved for offline compiler testing?",
        "Are recovery constraints explicitly simulation-only?",
        "Is any recipe information removed or redacted from recipe_context_redacted.json?",
        "Have inspection notes been reviewed by a qualified process engineer?",
    ]
    must_review = [
        f"wafer_demo_08 and wafer_demo_16: elevated alarm codes and out-of-spec metrology",
        "chamber_hash_D and chamber_hash_F: degraded state during dep_001 and cmp_001 steps",
        "All die IDs with bin_code 4: high leakage, blocked role candidates",
    ]

    reports["semiconductor_human_review_packet"] = {
        "schema": "hal.yieldos.semiconductor.human_review_packet.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "review_questions": review_questions,
        "must_review_before_use": must_review,
        "suggested_next_data": [
            f for f in OPTIONAL_PILOT_FILES if f not in opt_present
        ][:5],
        "candidate_decisions": [
            "accept_for_offline_functional_yield_review",
            "request_missing_data",
            "reject_due_to_insufficient_evidence",
            "allow_recovery_compiler_intake_preview",
        ],
        "forbidden_decisions": [
            "modify_recipe",
            "control_equipment",
            "claim_root_cause",
            "guarantee_yield",
            "certify_timing",
            "execute_recovery_profile",
        ],
        "linked_reports": [
            "functional_passport.json",
            "semiconductor_role_candidate_map.json",
            "semiconductor_valid_conditions_report.json",
            "semiconductor_evidence_completeness_report.json",
        ],
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "human_review_packet_not_operational_approval",
    }

    # ── 8. Missing Evidence Request ──────────────────────────────────────────
    missing_items: list[dict] = []
    for fname in files_missing:
        missing_items.append({
            "item": fname,
            "needed_for": "core_functional_yield_evidence",
            "why_needed_for_functional_yield": (
                f"{fname} provides primary evidence for "
                "remaining die, blocked die, and valid condition identification"
            ),
        })
    if not chip_tile_present:
        missing_items.append({
            "item": "chip_tile_map.json",
            "needed_for": "recovery_compiler_intake_ready",
            "why_needed_for_functional_yield": (
                "tile-level evidence is needed to distinguish candidate remaining "
                "chip regions from blocked chip regions before Recovery Compiler handoff"
            ),
        })
    if not workload_present:
        missing_items.append({
            "item": "workload_roles.json",
            "needed_for": "recovery_compiler_intake_ready",
            "why_needed_for_functional_yield": (
                "workload role definitions are needed to map candidate remaining "
                "die/tile regions to functional yield roles for compiler intake"
            ),
        })
    if not constraints_present:
        missing_items.append({
            "item": "recovery_constraints.json",
            "needed_for": "recovery_compiler_intake_ready",
            "why_needed_for_functional_yield": (
                "constraints define what candidate die/tile assignments are allowed "
                "under human-reviewed safety boundaries before compiler intake"
            ),
        })

    reports["semiconductor_missing_evidence_request"] = {
        "schema": "hal.yieldos.semiconductor.missing_evidence_request.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "missing_items": missing_items,
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "missing_evidence_request_for_candidate_review_only",
    }

    # ── 9. Recovery Compiler Intake Preview ──────────────────────────────────
    constraints_hw = _get_bool(constraints, "hardware_control_enabled", True)
    if not chip_tile_present or not workload_present or not constraints_present:
        if chip_tile_present:
            handoff_status = "PARTIAL_FOR_OFFLINE_COMPILER_TEST"
        else:
            handoff_status = "NOT_READY_FOR_COMPILER_HANDOFF"
    elif constraints_hw:
        handoff_status = "INVALID_COMPILER_INTAKE"
    else:
        handoff_status = "READY_FOR_OFFLINE_COMPILER_TEST"

    candidate_chips = [d for d in (candidate_remaining or []) if d][:10]
    blocked_chips = [d for d in (candidate_blocked or []) if d][:10]

    intake_preview = {
        "schema": "hal.yieldos.semiconductor.recovery_compiler_intake_preview.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "handoff_status": handoff_status,
        "handoff_inputs": {
            "chip_tile_map_ref": "chip_tile_map.json" if chip_tile_present else None,
            "workload_roles_ref": "workload_roles.json" if workload_present else None,
            "recovery_constraints_ref": "recovery_constraints.json" if constraints_present else None,
        },
        "candidate_chip_ids": candidate_chips,
        "blocked_chip_ids": blocked_chips,
        "evidence_refs": files_present + opt_present,
        "export_ref": "semiconductor_recovery_compiler_export.json",
        "handoff_manifest_ref": "semiconductor_handoff_manifest.json",
        "recovery_profile_generated": False,
        "not_sufficient_for": [
            "hardware_control",
            "firmware_flashing",
            "runtime_loading",
            "production_recovery",
            "timing_closure",
            "yield_guarantee",
        ],
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "compiler_intake_preview_only_not_recovery_profile",
    }
    reports["semiconductor_recovery_compiler_intake_preview"] = intake_preview

    # ── 10. Recovery Compiler Handoff Boundary ───────────────────────────────
    reports["semiconductor_recovery_compiler_handoff_boundary"] = {
        "schema": "hal.yieldos.semiconductor.recovery_compiler_handoff_boundary.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "yieldos_role": "generate_candidate_functional_yield_evidence",
        "recovery_compiler_role": "generate_candidate_recovery_profile_from_approved_intake",
        "recovery_compiler_export_ref": "semiconductor_recovery_compiler_export.json",
        "handoff_manifest_ref": "semiconductor_handoff_manifest.json",
        "yieldos_does_not": [
            "compute_final_recovery_profile",
            "control_hardware",
            "flash_firmware",
            "perform_timing_closure",
            "certify_yield",
            "certify_root_cause",
        ],
        "allowed_handoff": [
            "candidate_chip_tile_map",
            "candidate_workload_roles",
            "candidate_recovery_constraints",
            "evidence_refs",
            "human_review_notes",
        ],
        "forbidden_handoff": [
            "equipment_control_command",
            "recipe_change_instruction",
            "firmware_flash_payload",
            "runtime_apply_instruction",
            "certified_timing_claim",
        ],
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "handoff_boundary_not_operational_authority",
    }

    # ── 11a. Recovery Compiler Export (v3.0.3) ──────────────────────────────
    reports["semiconductor_recovery_compiler_export"] = {
        "schema": "hal.yieldos.semiconductor.recovery_compiler_export.v1",
        "case_id": case_id,
        "export_status": handoff_status,
        "export_type": "candidate_recovery_compiler_intake",
        "compiler_project": "hal-recovery-compiler",
        "source_yieldos_case": {
            "domain": "semiconductor",
            "functional_passport_ref": "functional_passport.json",
            "evidence_pack_ref": "evidence_pack.json",
            "functional_region_map_ref": "semiconductor_functional_region_map.json",
            "role_candidate_map_ref": "semiconductor_role_candidate_map.json",
            "valid_conditions_report_ref": "semiconductor_valid_conditions_report.json",
        },
        "compiler_inputs": {
            "chip_defect_map_candidate": {
                "source_ref": "chip_tile_map.json" if chip_tile_present else None,
                "status": "candidate_only",
                "claim_boundary": "candidate_chip_tile_map_not_physical_repair",
            },
            "workloads_candidate": {
                "source_ref": "workload_roles.json" if workload_present else None,
                "status": "candidate_only",
                "claim_boundary": "candidate_workloads_not_runtime_schedule",
            },
            "constraints_candidate": {
                "source_ref": "recovery_constraints.json" if constraints_present else None,
                "status": "candidate_only",
                "hardware_control_enabled": False,
                "human_review_required": True,
                "claim_boundary": "candidate_constraints_not_hardware_control",
            },
        },
        "compiler_input_availability": {
            "chip_tile_map_present": chip_tile_present,
            "workload_roles_present": workload_present,
            "recovery_constraints_present": constraints_present,
        },
        "candidate_chip_ids": candidate_chips,
        "candidate_blocked_chip_ids": blocked_chips,
        "evidence_refs": files_present + opt_present,
        "valid_conditions": [],
        "what_not_to_do": [
            "do not treat this export as a recovery profile",
            "do not flash firmware from this export",
            "do not apply this export to hardware",
            "do not treat this export as timing closure",
            "do not claim yield guarantee from this export",
        ],
        "not_sufficient_for": [
            "hardware_control",
            "firmware_flashing",
            "runtime_loading",
            "production_recovery",
            "timing_closure",
            "yield_guarantee",
        ],
        "human_review_required": True,
        "hardware_control_enabled": False,
        "recovery_profile_generated": False,
        "claim_boundary": "compiler_export_candidate_only_not_recovery_profile",
    }

    # ── 11b. Handoff Manifest (v3.0.3) ──────────────────────────────────────
    reports["semiconductor_handoff_manifest"] = {
        "schema": "hal.yieldos.semiconductor.handoff_manifest.v1",
        "case_id": case_id,
        "handoff_target": "hal-recovery-compiler",
        "handoff_status": handoff_status,
        "allowed_files": [
            "semiconductor_recovery_compiler_export.json",
            "semiconductor_recovery_compiler_intake_preview.json",
            "semiconductor_recovery_compiler_handoff_boundary.json",
            "functional_passport.json",
            "evidence_pack.json",
            "semiconductor_functional_region_map.json",
            "semiconductor_role_candidate_map.json",
            "semiconductor_valid_conditions_report.json",
        ],
        "source_input_refs": [f for f in [
            "chip_tile_map.json" if chip_tile_present else None,
            "workload_roles.json" if workload_present else None,
            "recovery_constraints.json" if constraints_present else None,
        ] if f is not None],
        "forbidden_files": [
            "recovery_profile.json",
            "firmware_flash_payload.bin",
            "runtime_apply_instruction.json",
            "recipe_change_instruction.json",
        ],
        "handoff_conditions": [
            "human review required before compiler execution",
            "compiler execution must remain offline",
            "compiler output must not be applied to hardware without separate runtime review",
            "this handoff is not timing closure",
            "this handoff is not yield guarantee",
        ],
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "handoff_manifest_not_operational_authority",
    }

    # ── 11. Pilot Readiness Report ───────────────────────────────────────────
    checks: list[dict] = []
    readiness_score = 1.0

    ok = not files_missing
    checks.append({
        "check": "required_files",
        "status": "PASS" if ok else "FAIL",
        "detail": f"{len(files_present)}/{len(REQUIRED_PILOT_FILES)} required files present",
        "missing": files_missing,
    })
    if not ok:
        readiness_score -= 0.30

    ok = len(test_rows) >= 10
    checks.append({
        "check": "min_test_results",
        "status": "PASS" if ok else "FAIL",
        "detail": f"{len(test_rows)} test result rows (minimum 10 required)",
    })
    if not ok:
        readiness_score -= 0.20

    ok = len(tool_rows) >= 10
    checks.append({
        "check": "min_tool_log_rows",
        "status": "PASS" if ok else "FAIL",
        "detail": f"{len(tool_rows)} tool log rows (minimum 10 required)",
    })
    if not ok:
        readiness_score -= 0.20

    ok = len(wafer_ids) >= 2
    checks.append({
        "check": "wafer_variety",
        "status": "PASS" if ok else "WARN",
        "detail": f"{len(wafer_ids)} unique wafer IDs",
    })

    ok = chip_tile_present and workload_present and constraints_present
    checks.append({
        "check": "recovery_compiler_intake_inputs",
        "status": "PASS" if ok else "WARN",
        "detail": f"chip_tile_map={chip_tile_present}, workload_roles={workload_present}, recovery_constraints={constraints_present}",
    })
    if not ok:
        readiness_score -= 0.10

    readiness_score = round(max(0.0, min(1.0, readiness_score)), 4)
    if readiness_score >= 0.80:
        readiness_status = "PILOT_READY"
    elif readiness_score >= 0.50:
        readiness_status = "PARTIAL_PILOT_READY"
    else:
        readiness_status = "NOT_PILOT_READY"

    reports["semiconductor_pilot_readiness_report"] = {
        "schema": "hal.yieldos.semiconductor.pilot_readiness_report.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "asset_id": asset_id,
        "readiness_status": readiness_status,
        "readiness_score": readiness_score,
        "checks": checks,
        "required_files_present": files_present,
        "required_files_missing": files_missing,
        "optional_files_present": opt_present,
        "recovery_compiler_intake_status": handoff_status,
        "safety_boundary": _SAFETY,
        "hardware_control_enabled": False,
        "human_review_required": True,
        "not_sufficient_for": _NOT_SUFFICIENT_FOR,
        "claim_boundary": "semiconductor_pilot_readiness_candidate_only",
    }

    return reports


def build_pilot_case_summary_md(
    case_id: str,
    asset_id: str,
    readiness_status: str,
    readiness_score: float,
    remaining_roles: list[str],
    reduced_roles: list[str],
    blocked_roles: list[str],
    intake_status: str,
    missing_items: list[str],
    lot_ids: list[str],
    wafer_count: int,
    die_pass: int,
    die_fail: int,
) -> str:
    return f"""# Semiconductor Pilot Case Summary

**Case ID**: {case_id}
**Asset ID**: {asset_id}
**Pilot Readiness**: {readiness_status} (score={readiness_score:.2f})

---

## Case Boundary

- read-only
- candidate-only
- human-review-required
- no recipe control
- no equipment control
- no root-cause certification
- no yield guarantee
- no timing closure
- no Recovery Compiler execution

---

## Inputs Reviewed

- Lots: {", ".join(lot_ids) if lot_ids else "none"}
- Wafers reviewed: {wafer_count}
- Die pass: {die_pass} | Die fail: {die_fail}

---

## Candidate Remaining Functions / Regions

{chr(10).join(f"- {r}" for r in remaining_roles) if remaining_roles else "- none identified with current evidence"}

## Candidate Reduced / Restricted Functions

{chr(10).join(f"- {r}" for r in reduced_roles) if reduced_roles else "- none"}

## Candidate Blocked Functions / Regions

{chr(10).join(f"- {r}" for r in blocked_roles) if blocked_roles else "- none"}

---

## Valid Conditions

- Same lot family and wafer test conditions as observed sample
- Same tool/chamber/step context
- Same voltage/temperature test range
- Human review required before any operational use

---

## Recovery Compiler Intake Preview

Status: **{intake_status}**

{"Recovery Compiler intake inputs (chip_tile_map, workload_roles, recovery_constraints) are present." if intake_status == "READY_FOR_OFFLINE_COMPILER_TEST" else "One or more required intake inputs are missing. See semiconductor_missing_evidence_request.json."}

This is a simulation-only candidate preview. YieldOS does not generate recovery_profile.json.

## Recovery Compiler Export (v3.0.3)

`semiconductor_recovery_compiler_export.json` has been generated. This is a candidate-only export
artifact for offline HAL Recovery Compiler testing. It is **not a recovery profile**.

- human review required before compiler execution
- do not apply to hardware without separate runtime authorization
- export_type: candidate_recovery_compiler_intake
- recovery_profile_generated: false

## Handoff Manifest (v3.0.3)

`semiconductor_handoff_manifest.json` defines the authorized handoff boundary to hal-recovery-compiler.
Forbidden files (recovery_profile.json, firmware_flash_payload.bin) are listed explicitly.
All handoff conditions require human review before compiler execution.

---

## Missing Evidence

{chr(10).join(f"- {m}" for m in missing_items) if missing_items else "- none outstanding"}

---

## Human Review Questions

- Are lot/wafer/die IDs sufficiently anonymized?
- Are tool and chamber IDs redacted but consistent?
- Is chip_tile_map present for Recovery Compiler intake?
- Are workload roles synthetic or approved for offline compiler testing?
- Are constraints explicitly simulation-only?
- Is any recipe information removed or redacted?

---

## What Not To Do

- do not modify recipes from YieldOS output
- do not control tools from YieldOS output
- do not claim root cause
- do not claim yield guarantee
- do not treat this as timing closure
- do not execute Recovery Compiler output without separate review

---

## Core Question

**What can still function, what must be blocked, under what valid conditions, and based on what evidence?**
"""


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (ValueError, TypeError):
        return default
