from __future__ import annotations

import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from ..contracts import EvidencePack, OODAFrame, StateSnapshot
from ..contracts.meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by


def _esc(value: Any) -> str:
    """Escape all string values going into HTML output."""
    return html.escape(str(value), quote=True)


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class ReportWriter:
    """
    Renders domain objects to the Standard Output Bundle.
    JSON objects are the source of truth; reports are derived renderings.
    Generates all v2.1 required output files.
    """

    def write_all(
        self,
        out_dir: str,
        state: StateSnapshot,
        pack: EvidencePack,
        ooda: OODAFrame,
        recovery_candidates: Optional[List] = None,
        remaining_roles: Optional[List[str]] = None,
        blocked_roles: Optional[List[str]] = None,
        bin_class: Optional[str] = None,
        decision_readiness: Optional[str] = None,
        domain_canonical: Optional[str] = None,
        extra_outputs: Optional[dict] = None,
        input_validation_override: Optional[dict] = None,
        source_data_paths: Optional[List[str]] = None,
        policy_inputs: Optional[dict] = None,
        optimizer_info_override: Optional[dict] = None,
    ) -> dict:
        base = Path(out_dir)
        base.mkdir(parents=True, exist_ok=True)

        rec_list = recovery_candidates or []
        remaining_roles = remaining_roles or []
        blocked_roles = blocked_roles or []
        bin_class = bin_class or self._derive_bin_class(state)
        decision_readiness = decision_readiness or "ACTION_INELIGIBLE"
        canonical = domain_canonical or state.domain

        # --- Standard v2.0 core files ---
        paths = {}
        paths["state_snapshot"] = self._write_json(base / "state_snapshot.json", state.to_dict())
        paths["evidence_pack"] = self._write_json(base / "evidence_pack.json", pack.to_dict())

        # Enrich OODA frame with pipeline coherence fields (P0-5, P1-3)
        ooda_dict = ooda.to_dict()
        ooda_dict["ooda_mode"] = "read_only_evidence_frame"
        ooda_dict["control_loop"] = False
        ooda_dict["hardware_action_enabled"] = False
        ooda_dict["human_review_required"] = True
        ooda_dict["evidence_pack_ref"] = pack.checksum  # ensure cross-reference is set
        _fyv = (state.metrics or {}).get("functional_yield_vector")
        ooda_dict["functional_yield_ref"] = {
            "score": round(_fyv.get("functional_yield_score", 0.0), 4) if _fyv else 0.0,
            "source": "functional_yield_scorecard.json",
            "score_kind": _fyv.get("score_kind", "heuristic") if _fyv else "heuristic",
        }
        paths["ooda_frame"] = self._write_json(base / "ooda_frame.json", ooda_dict)

        # Enrich recovery candidates with route_membership (P1-4)
        if rec_list:
            _opt = optimizer_info_override or {}
            rc_dicts = []
            for _i, r in enumerate(rec_list):
                rd = r.to_dict() if hasattr(r, "to_dict") else dict(r)
                rd["route_membership"] = {
                    "included_in_recovery_route": True,
                    "route_rank": _i + 1,
                    "optimizer_used": _opt.get("used") or "none",
                    "optimizer_fallback": bool(_opt.get("fallback", False)),
                }
                rc_dicts.append(rd)
            paths["recovery_candidates"] = self._write_json(
                base / "recovery_candidates.json",
                rc_dicts,
            )
        paths["report_md"] = self._write_md(base / "report.md", state, pack, ooda, rec_list)
        paths["report_html"] = self._write_html(base / "report.html", state, pack, ooda, rec_list)

        # --- v2.1 Standard Output Bundle ---
        missing_items = pack.missing_evidence or []

        # Use domain-provided input_validation if available; else build heuristic version
        iv_payload = input_validation_override if input_validation_override else self._build_input_validation(state, pack, canonical)
        paths["input_validation"] = self._write_json(base / "input_validation.json", iv_payload)
        paths["decision_readiness_report"] = self._write_json(
            base / "decision_readiness_report.json",
            self._build_decision_readiness(state, pack, decision_readiness, missing_items, canonical),
        )
        paths["functional_yield_scorecard"] = self._write_json(
            base / "functional_yield_scorecard.json",
            self._build_fy_scorecard(state, pack, remaining_roles, canonical),
        )
        paths["functional_binning_result"] = self._write_json(
            base / "functional_binning_result.json",
            self._build_binning_result(state, pack, bin_class, remaining_roles, blocked_roles, canonical),
        )
        # Detect semiconductor-specific extra output refs before building passport/trace
        _semi_refs: dict = {}
        if extra_outputs:
            if "process_drift_report" in extra_outputs:
                _semi_refs["process_drift_report_ref"] = "process_drift_report.json"
            if "semiconductor_confidence_report" in extra_outputs:
                _semi_refs["semiconductor_confidence_report_ref"] = "semiconductor_confidence_report.json"

        fp_data = self._build_functional_passport(state, pack, bin_class, remaining_roles, blocked_roles,
                                                  decision_readiness, canonical, policy_inputs)
        if _semi_refs:
            fp_data.update(_semi_refs)
            fp_data["semiconductor_analysis_context"] = {
                "recent_trend_detection_present": "process_drift_report_ref" in _semi_refs,
                "confidence_report_present": "semiconductor_confidence_report_ref" in _semi_refs,
                "data_sufficiency_present": True,
                "confidence_kind": "analysis_confidence",
                "process_control_enabled": False,
                "recipe_change_enabled": False,
                "context_boundary": "candidate_functional_yield_evidence_not_process_control",
            }
            # v3.0.6: propagate confidence_explanation to functional_passport
            if extra_outputs and "semiconductor_confidence_report" in extra_outputs:
                _semi_conf_raw = (
                    extra_outputs["semiconductor_confidence_report"].get("confidence_report") or {}
                )
                if _semi_conf_raw:
                    _missing_m_fp = _semi_conf_raw.get("missing_metrics", [])
                    fp_data["confidence_explanation"] = {
                        "confidence_report_ref": "semiconductor_confidence_report.json",
                        "score": _semi_conf_raw.get("score", 0.0),
                        "data_status": _semi_conf_raw.get("data_status", "UNKNOWN"),
                        "signal_status": _semi_conf_raw.get("signal_status", "UNKNOWN"),
                        "reasons": _semi_conf_raw.get("reasons", []),
                        "missing_metrics": _missing_m_fp,
                        "missing_metric_messages": [f"{m}: no data" for m in _missing_m_fp],
                        "available_metrics_summary": _semi_conf_raw.get("available_metrics_summary", {}),
                        "claim_boundary": "confidence_explanation_not_root_cause_certification",
                    }
                    fp_data["semiconductor_analysis_context"]["confidence_explanation"] = {
                        "missing_metrics": _missing_m_fp,
                        "missing_metric_messages": [f"{m}: no data" for m in _missing_m_fp],
                        "available_metrics_summary": _semi_conf_raw.get("available_metrics_summary", {}),
                    }
        paths["functional_passport"] = self._write_json(base / "functional_passport.json", fp_data)

        paths["evidence_pack_md"] = self._write_evidence_md(base / "evidence_pack.md", state, pack)
        paths["recovery_route_report"] = self._write_json(
            base / "recovery_route_report.json",
            self._build_recovery_route_report(state, pack, rec_list, canonical, optimizer_info_override),
        )
        paths["failure_scenario_record"] = self._write_json(
            base / "failure_scenario_record.json",
            self._build_failure_scenario_record(state, pack, remaining_roles, blocked_roles,
                                                decision_readiness, canonical),
        )
        paths["next_data_request"] = self._write_json(
            base / "next_data_request.json",
            self._build_next_data_request(state, pack, decision_readiness, canonical),
        )
        at_data = self._build_analysis_trace(state, pack, rec_list, decision_readiness, canonical, iv_payload)
        if _semi_refs:
            at_data["semiconductor_calibration_outputs"] = list(_semi_refs.values())
        paths["analysis_trace"] = self._write_json(base / "analysis_trace.json", at_data)
        # --- v2.4 Standard Output Bundle additions ---
        paths["source_data_manifest"] = self._write_json(
            base / "source_data_manifest.json",
            self._build_source_data_manifest(state, pack, canonical, source_data_paths),
        )
        paths["data_quality_report"] = self._write_json(
            base / "data_quality_report.json",
            self._build_data_quality_report(state, pack, canonical),
        )
        paths["evidence_conflict_report"] = self._write_json(
            base / "evidence_conflict_report.json",
            self._build_evidence_conflict_report(state, pack, canonical),
        )
        paths["baseline_vs_yieldos"] = self._write_json(
            base / "baseline_vs_yieldos.json",
            self._build_baseline_comparison(state, pack, canonical, bin_class, remaining_roles, blocked_roles, extra_outputs),
        )
        paths["business_case_summary"] = self._write_json(
            base / "business_case_summary.json",
            self._build_business_case_summary(state, pack, canonical, bin_class),
        )
        # Extra outputs (domain-specific JSON files)
        extra_fnames: list = []
        if extra_outputs:
            for fname, payload in extra_outputs.items():
                if not fname.endswith(".json"):
                    fname = fname + ".json"
                paths[fname] = self._write_json(base / fname, payload)
                extra_fnames.append(fname)

        # v3.0.6: post-patch HTML/MD with semiconductor confidence section (before case_manifest)
        if extra_outputs and "semiconductor_confidence_report" in extra_outputs:
            _semi_conf_pw = extra_outputs["semiconductor_confidence_report"].get("confidence_report") or {}
            if _semi_conf_pw:
                from ..domains.semfab.analyzer import WATCHED_METRICS as _WATCHED_METRICS_PW
                _avail_sum_pw = _semi_conf_pw.get("available_metrics_summary", {})
                _avail_set_pw = set(_avail_sum_pw.get("available", []))
                _score_pw = _semi_conf_pw.get("score", 0.0)
                _kind_pw = _semi_conf_pw.get("confidence_kind", "")
                _ds_pw = _semi_conf_pw.get("data_status", "UNKNOWN")
                _ss_pw = _semi_conf_pw.get("signal_status", "UNKNOWN")
                _stxt_pw = _avail_sum_pw.get("summary_text", "")
                html_p = base / "report.html"
                if html_p.exists():
                    _html_pw = html_p.read_text(encoding="utf-8")
                    _metric_rows_pw = "".join(
                        f"<tr><td><code>{_esc(m)}</code></td>"
                        f"<td>{'<span style=\"color:#388e3c\">available</span>' if m in _avail_set_pw else '<span style=\"color:#b71c1c\">no data</span>'}</td></tr>"
                        for m in _WATCHED_METRICS_PW
                    )
                    _semi_conf_html = (
                        '<div class="semi-confidence-section" style="background:#e3f2fd;border:1px solid #90caf9;'
                        'padding:12px;border-radius:6px;margin:12px 0;">'
                        f"<h3 style='margin:0 0 8px'>Semiconductor Process Confidence</h3>"
                        f"<p><b>Score:</b> {_score_pw:.2f} &nbsp;|&nbsp; <b>Kind:</b> {_esc(_kind_pw)} &nbsp;|&nbsp; "
                        f"<b>Data Status:</b> {_esc(_ds_pw)} &nbsp;|&nbsp; <b>Signal Status:</b> {_esc(_ss_pw)}</p>"
                        f"<p>{_esc(_stxt_pw)}</p>"
                        f"<table><tr><th>Metric</th><th>Status</th></tr>{_metric_rows_pw}</table>"
                        "<p style='font-size:0.85em;color:#555;'>"
                        "Boundary: confidence_is_analysis_quality_not_safety_certification</p>"
                        "</div>"
                    )
                    if "</body>" in _html_pw:
                        _html_pw = _html_pw.replace("</body>", _semi_conf_html + "</body>")
                    else:
                        _html_pw += _semi_conf_html
                    html_p.write_text(_html_pw, encoding="utf-8")
                md_p = base / "report.md"
                if md_p.exists():
                    _md_pw = md_p.read_text(encoding="utf-8")
                    _avail_set_md = set(_avail_sum_pw.get("available", []))
                    _md_rows_pw = "\n".join(
                        f"| `{m}` | {'available' if m in _avail_set_md else 'no data'} |"
                        for m in _WATCHED_METRICS_PW
                    )
                    _md_conf_section = (
                        "\n\n---\n"
                        "## 8. Semiconductor Confidence\n"
                        f"**Score**: {_score_pw:.2f} ({_kind_pw})  \n"
                        f"**Data Status**: {_ds_pw} | **Signal Status**: {_ss_pw}  \n"
                        f"**Summary**: {_stxt_pw}  \n\n"
                        "| Metric | Status |\n"
                        "|--------|--------|\n"
                        f"{_md_rows_pw}\n\n"
                        "> Boundary: confidence_is_analysis_quality_not_safety_certification\n"
                    )
                    _md_pw += _md_conf_section
                    md_p.write_text(_md_pw, encoding="utf-8")

        # Case manifest is last — records checksums of ALL already-written files
        paths["case_manifest"] = self._write_json(
            base / "case_manifest.json",
            self._build_case_manifest_from_paths(state, canonical, paths),
        )

        return paths

    # ── Builders ──────────────────────────────────────────────────────────────

    def _derive_bin_class(self, state: StateSnapshot) -> str:
        from ..contracts import SeverityLevel
        if state.severity == SeverityLevel.HIGH:
            return "mission_survival_candidate"
        if state.severity == SeverityLevel.MEDIUM:
            return "degraded_role_candidate"
        return "full_operation"

    def _build_input_validation(self, state, pack, canonical: str) -> dict:
        m = state.metrics or {}
        missing_inputs = m.get("missing_inputs", [])
        domain = state.domain  # internal adapter name (e.g. "robotics", "satellite")

        # Domain-specific PASSED rules
        if domain == "memory_device" or canonical == "memory":
            total_blocks = m.get("total_blocks", 0) or 0
            raw_cap = m.get("raw_capacity_gb", 0) or 0
            passed = (total_blocks > 0) and (raw_cap > 0)
            blocking = []
            if total_blocks == 0:
                blocking.append("total_blocks == 0")
            if raw_cap == 0:
                blocking.append("raw_capacity_gb == 0")
        elif domain == "semiconductor_fab" or canonical == "semiconductor":
            tool_rows = m.get("total_tool_log_rows", 0) or 0
            wafer_dies = m.get("total_dies", 0) or 0
            metrology = m.get("metrology_rows", 0) or 0
            passed = (tool_rows > 0) or (wafer_dies > 0) or (metrology > 0)
            blocking = [] if passed else ["no tool_log_rows, wafer_dies, or metrology_rows present"]
        else:
            # robot, space, semiforge: telemetry_samples > 0
            telemetry = m.get("telemetry_samples", 0) or 0
            passed = telemetry > 0
            blocking = [] if passed else ["telemetry_samples == 0"]

        data_level = "MINIMUM_RUNNABLE" if (passed and not missing_inputs) else (
            "BELOW_MINIMUM" if passed else (
                "EMPTY" if not any(v for k, v in m.items() if k != "missing_inputs") else "BELOW_MINIMUM"
            )
        )
        found = [k for k, v in m.items() if v and k not in ("missing_inputs",)]
        return {
            "schema": "hal.yieldos.input_validation.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "domain_adapter": domain,
            "status": "PASSED" if passed else "FAILED",
            "data_level": data_level,
            "found_inputs": found,
            "missing_inputs": missing_inputs,
            "blocking_reasons": blocking,
            "warnings": [],
            "degraded_mode": m.get("degraded_mode", False),
            "safety_boundary": SAFETY_BLOCK,
            "generated_by": generated_by(),
        }

    def _build_decision_readiness(self, state, pack, category: str, missing_items: list, canonical: str) -> dict:
        n_missing = len(missing_items)
        readiness_score = max(0.1, min(0.9, state.confidence - n_missing * 0.05))
        limiting_factors = []
        if n_missing > 0:
            limiting_factors.append(f"{n_missing} missing evidence items")
        if not state.metrics.get("telemetry_samples", 0):
            limiting_factors.append("no_telemetry_data")
        limiting_factors.append("missing_action_authority_matrix")
        limiting_factors.append("missing_cvc_json")

        return {
            "schema": "hal.yieldos.decision_readiness.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "category": category,
            "readiness_score": round(readiness_score, 3),
            "confidence": state.confidence,
            "limiting_factors": limiting_factors,
            "missing_context": [
                "cvc.json — constraint and value priority",
                "action_authority_matrix.json — who can approve what",
                "operating_envelope.json — safe operating range",
            ],
            "confidence_policy": {
                "confidence_limited_by_missing_data": n_missing > 0,
                "limiting_factors": limiting_factors,
                "max_allowed_readiness_category": category,
                "note": "DECISION_READY requires action_authority_matrix.json and cvc.json",
            },
            "human_review_preparation": {
                "review_packet_ready": True,
                "required_human_decision": "accept_reject_request_more_data",
                "automatic_decision_enabled": False,
                "approval_gate_required": True,
                "claim_boundary": "human_review_preparation_not_approval_execution",
            },
            "shadow_analysis_notice": (
                "This report is a shadow analysis output. "
                "It does not command, control, or certify the target system. "
                "All recovery routes are candidate-only and require human review."
            ),
            "safety_boundary": SAFETY_BLOCK,
            "generated_by": generated_by(),
        }

    def _build_fy_scorecard(self, state, pack, remaining_roles: list, canonical: str) -> dict:
        ev_count = len(pack.evidence_objects or [])

        # Use FYV vector if pre-computed and stored in state.metrics
        fyv = state.metrics.get("functional_yield_vector") if state.metrics else None
        if fyv and isinstance(fyv, dict):
            functional_retention = fyv.get("functional_yield_score", 0.0)
            false_confidence_penalty = fyv.get("false_confidence_penalty", 0.0)
            score_kind = fyv.get("score_kind", "heuristic")
            component_scores = fyv.get("component_scores", {})
            role_scores = fyv.get("role_scores", {})
            missing_inputs = fyv.get("missing_inputs", [])
            model_limitations = fyv.get("model_limitations", [])
            calculation_basis = fyv.get("calculation_basis", "functional_yield_vector")
            cannot_certify = fyv.get("cannot_certify_safety", "")
            cannot_hw = fyv.get("cannot_authorize_hardware_action", "")
        else:
            functional_retention = round(
                1.0 - state.confidence * 0.4 if state.severity.value in ("high", "critical") else
                1.0 - state.confidence * 0.2 if state.severity.value == "medium" else
                1.0,
                3,
            )
            false_confidence_penalty = 0.0
            score_kind = "heuristic"
            component_scores = {}
            role_scores = {}
            missing_inputs = state.metrics.get("missing_inputs", []) if state.metrics else []
            model_limitations = ["heuristic_severity_mapping"]
            calculation_basis = "severity_based_heuristic"
            cannot_certify = (
                "This score is a candidate estimate. Cannot certify safety or authorize hardware action."
            )
            cannot_hw = "Human review required before any operational decision."

        return {
            "schema": "hal.yieldos.functional_yield_scorecard.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "functional_retention": round(functional_retention, 4),
            "degradation_score": round(1.0 - functional_retention, 4),
            "evidence_confidence": state.confidence,
            "evidence_signal_count": ev_count,
            "remaining_role_count": len(remaining_roles),
            "recovery_potential": round(min(0.9, functional_retention + 0.2), 3),
            "safety_boundary_compliance": True,
            "false_confidence_penalty": round(false_confidence_penalty, 4),
            "score_kind": score_kind,
            "component_scores": component_scores,
            "role_scores": role_scores,
            "missing_inputs": missing_inputs,
            "model_limitations": model_limitations,
            "calculation_basis": calculation_basis,
            "cannot_certify_safety": cannot_certify,
            "cannot_authorize_hardware_action": cannot_hw,
            "notes": "Software simulation / sample-based validation only.",
            "safety_boundary": SAFETY_BLOCK,
            "generated_by": generated_by(),
        }

    def _build_binning_result(self, state, pack, bin_class: str, remaining_roles: list,
                               blocked_roles: list, canonical: str) -> dict:
        bin_descriptions = {
            "full_operation": "All primary roles available. No degradation detected.",
            "monitored_operation": "All primary roles available with active monitoring.",
            "degraded_role_candidate": "Reduced role available. Primary roles require review.",
            "mission_survival_candidate": "Survival roles only. Primary roles blocked pending review.",
            "shadow_analysis_only": "Shadow analysis mode. No operational role claim.",
            "full_compute_silver": "Full compute eligible per simulation.",
            "reduced_inference_silver": "Reduced inference role eligible. Full roles blocked.",
            "survival_monitoring_only": "Survival monitoring only. Full compute roles blocked.",
        }
        return {
            "schema": "hal.yieldos.functional_binning.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "bin_class": bin_class,
            "bin_description": bin_descriptions.get(bin_class, "See evidence pack for details."),
            "remaining_roles": remaining_roles,
            "blocked_roles": blocked_roles,
            "state": state.state.value,
            "severity": state.severity.value,
            "confidence": state.confidence,
            "note": "Bin class is a candidate estimate based on sample/simulation data. Human review required.",
            "safety_boundary": SAFETY_BLOCK,
            "generated_by": generated_by(),
        }

    _VALID_CONDITIONS = {
        "memory": [
            "same device health snapshot",
            "no new uncorrectable error event",
            "same ECC policy assumption",
        ],
        "memory_device": [
            "same device health snapshot",
            "no new uncorrectable error event",
            "same ECC policy assumption",
        ],
        "robot": ["same robot configuration", "same payload class", "same operating envelope"],
        "robotics": ["same robot configuration", "same payload class", "same operating envelope"],
        "space": ["same mission profile", "same power budget assumption", "no new fault flag after analysis"],
        "satellite": ["same mission profile", "same power budget assumption", "no new fault flag after analysis"],
        "semiconductor": ["same lot context", "same tool log window", "no recipe change inferred or applied"],
        "semiconductor_fab": ["same lot context", "same tool log window", "no recipe change inferred or applied"],
        "semiforge": [
            "same simulation config (array geometry, defect rate)",
            "same defect distribution model",
            "no new measurement-based defect map",
        ],
        "semiforge_crossbar": [
            "same simulation config (array geometry, defect rate)",
            "same defect distribution model",
            "no new measurement-based defect map",
        ],
    }
    _REQUIRED_HUMAN_ROLES = {
        "memory": ["storage_engineer", "quality_manager"],
        "memory_device": ["storage_engineer", "quality_manager"],
        "robot": ["maintenance_engineer", "operations_manager"],
        "robotics": ["maintenance_engineer", "operations_manager"],
        "space": ["ground_operations_engineer", "mission_manager"],
        "satellite": ["ground_operations_engineer", "mission_manager"],
        "semiconductor": ["process_engineer", "quality_manager"],
        "semiconductor_fab": ["process_engineer", "quality_manager"],
        "semiforge": ["device_physicist", "yield_engineer"],
        "semiforge_crossbar": ["device_physicist", "yield_engineer"],
    }

    def _build_functional_passport(self, state, pack, bin_class: str, remaining_roles: list,
                                    blocked_roles: list, decision_readiness: str, canonical: str,
                                    policy_inputs: dict = None) -> dict:
        passport_type_map = {
            "robotics": "robot_functional_passport",
            "satellite": "space_relevant_fault_tolerance_record",
            "semiconductor_fab": "semiconductor_edge_ai_functional_passport",
            "semiforge": "dark_functional_cell_passport",
            "memory_device": "memory_functional_passport",
        }
        passport_type = passport_type_map.get(state.domain, "functional_passport")

        # Evidence strength
        m = state.metrics or {}
        missing_ev_count = len(pack.missing_evidence or [])
        ev_confs = [
            e.get("confidence", 0) if isinstance(e, dict) else getattr(e, "confidence", 0)
            for e in (pack.evidence_objects or [])
        ]
        data_completeness = round(max(0.0, 1.0 - missing_ev_count * 0.08), 2)
        if len(ev_confs) >= 2:
            signal_consistency = round(max(0.0, 1.0 - (max(ev_confs) - min(ev_confs))), 3)
        elif ev_confs:
            signal_consistency = round(ev_confs[0] * 0.8, 3)
        else:
            signal_consistency = 0.3
        fyv = m.get("functional_yield_vector")
        score_kind = fyv.get("score_kind", "heuristic") if fyv else "heuristic"
        evidence_strength = {
            "data_completeness": data_completeness,
            "signal_consistency": signal_consistency,
            "historical_support": 0.0,
            "model_calibration": 0.7 if score_kind == "simulation" else 0.5,
        }

        # Role confidence
        role_confidence = {}
        for role in remaining_roles:
            role_confidence[role] = round(state.confidence * 0.9, 3)
        for role in blocked_roles:
            role_confidence[role] = round(max(0.05, state.confidence * 0.15), 3)

        # Validity conditions (domain-specific)
        valid_conditions = (
            self._VALID_CONDITIONS.get(canonical) or
            self._VALID_CONDITIONS.get(state.domain) or []
        )
        required_human_roles = (
            self._REQUIRED_HUMAN_ROLES.get(canonical) or
            self._REQUIRED_HUMAN_ROLES.get(state.domain) or ["engineering_reviewer"]
        )
        authority_matrix_present = bool(policy_inputs and policy_inputs.get("authority_matrix"))

        return {
            "schema": "hal.yieldos.functional_passport.v2",
            "schema_version": SCHEMA_VERSION,
            "passport_id": f"fp_{state.case_id}",
            "component_id": state.asset_id,
            "asset_id": state.asset_id,
            "domain_pack": canonical,
            "passport_type": passport_type,
            "failure_scenario_id": f"fs_{state.case_id}",
            "mode_state": state.state.value,
            "degradation_signature": state.severity.value,
            "bin_class": bin_class,
            "remaining_roles": remaining_roles,
            "blocked_roles": blocked_roles,
            "confidence": state.confidence,
            "readiness_score": round(max(0.1, state.confidence - missing_ev_count * 0.05), 3),
            "decision_readiness": decision_readiness,
            "evidence_lineage": [
                e.get("evidence_id") if isinstance(e, dict) else getattr(e, "evidence_id", "")
                for e in (pack.evidence_objects or [])
            ],
            "missing_data": [
                m_item.get("item") if isinstance(m_item, dict) else str(m_item)
                for m_item in (pack.missing_evidence or [])
            ],
            # v2.4 additions
            "passport_validity": {
                "status": "candidate_only",
                "expires_after": "requires_new_data_after_context_change",
                "valid_conditions": valid_conditions,
            },
            "operating_constraints": [],
            "required_human_roles": required_human_roles,
            "approval_gate": {
                "required": True,
                "authority_matrix_present": authority_matrix_present,
                "approval_level": "engineering_review",
                "cvc_present": bool(policy_inputs and policy_inputs.get("cvc")),
                "risk_policy_present": bool(policy_inputs and policy_inputs.get("risk_policy")),
            },
            "evidence_strength": evidence_strength,
            "role_confidence": role_confidence,
            "case_id": state.case_id,
            "evidence_pack_ref": pack.checksum,
            "human_approval_required": True,
            "hardware_execution_enabled": False,
            "causal_claim_boundary": "candidate_only_not_certified_cause",
            "state_snapshot_hash": state.snapshot_hash,
            "evidence_pack_checksum": pack.checksum,
            "functional_yield_organizing_principle": {
                "core_question": "what_can_still_function_what_must_be_blocked_under_what_conditions_based_on_what_evidence",
                "remaining_functions_present": len(remaining_roles) > 0,
                "blocked_functions_present": len(blocked_roles) > 0,
                "valid_conditions_present": len(valid_conditions) > 0,
                "evidence_refs_present": len(pack.evidence_objects or []) > 0,
                "human_review_required": True,
                "claim_boundary": "functional_yield_evidence_not_certification",
            },
            "generated_by": generated_by(),
            "safety_boundary": SAFETY_BLOCK,
            "shadow_analysis_notice": (
                "This Functional Passport is produced by shadow analysis on sample/simulation data. "
                "It does not certify operational capability or authorize any hardware action. "
                "Human review is required before any operational decision."
            ),
        }

    def _build_evidence_md(self, path: Path, state: StateSnapshot, pack: EvidencePack) -> str:
        ev_lines = [f"# Evidence Pack — {pack.case_id}\n"]
        ev_lines.append(f"**Domain**: {pack.domain}  ")
        ev_lines.append(f"**Asset**: {pack.asset_id}  ")
        ev_lines.append(f"**Summary**: {pack.summary}\n")
        ev_lines.append("---\n## Evidence Objects\n")
        for ev in (pack.evidence_objects or []):
            ev_id = ev.get("evidence_id", "") if isinstance(ev, dict) else getattr(ev, "evidence_id", "")
            summary = ev.get("summary", "") if isinstance(ev, dict) else getattr(ev, "summary", "")
            conf = ev.get("confidence", 0) if isinstance(ev, dict) else getattr(ev, "confidence", 0)
            ev_lines.append(f"- **{ev_id}**: {summary} (confidence: {conf:.0%})")
        ev_lines.append("\n## Missing Evidence\n")
        for m in (pack.missing_evidence or []):
            item = m.get("item", str(m)) if isinstance(m, dict) else str(m)
            ev_lines.append(f"- {item}")
        ev_lines.append(
            "\n---\n> This report is a shadow analysis output. "
            "It does not command, control, or certify the target system. "
            "All recovery routes are candidate-only and require human review."
        )
        content = "\n".join(ev_lines)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def _write_evidence_md(self, path: Path, state: StateSnapshot, pack: EvidencePack) -> str:
        return self._build_evidence_md(path, state, pack)

    def _build_recovery_route_report(self, state, pack, rec_list: list, canonical: str,
                                      optimizer_info: Optional[dict] = None) -> dict:
        routes = []
        for r in rec_list:
            rd = r.to_dict() if hasattr(r, "to_dict") else r
            routes.append({
                "action": rd.get("action", ""),
                "status": "requires_approval",
                "human_review_required": True,
                "hardware_execution_enabled": False,
                "risk": rd.get("risk", ""),
                "expected_benefit": rd.get("expected_benefit", ""),
                "steps": rd.get("steps", []),
                "causal_claim_boundary": "candidate_only_not_certified_cause",
            })
        opt = optimizer_info or {
            "requested": "none",
            "used": "none",
            "fallback": False,
            "reason": "optimizer not requested",
            "ordered_actions": [],
        }
        return {
            "schema": "hal.yieldos.recovery_route_report.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "total_routes": len(routes),
            "routes_requiring_approval": len(routes),
            "routes_blocked": 0,
            "routes": routes,
            "optimizer_info": opt,
            "note": (
                "All recovery routes are candidate-only. "
                "None can be executed without human review and approval. "
                "Hardware execution is always disabled."
            ),
            "safety_boundary": SAFETY_BLOCK,
            "generated_by": generated_by(),
        }

    def _build_failure_scenario_record(self, state, pack, remaining_roles: list,
                                        blocked_roles: list, decision_readiness: str, canonical: str) -> dict:
        symptoms = [
            ev.get("summary", "") if isinstance(ev, dict) else getattr(ev, "summary", "")
            for ev in (pack.evidence_objects or [])
        ]
        rca_list = pack.root_cause_candidates or []
        affected = [r.get("candidate", "") if isinstance(r, dict) else getattr(r, "candidate", "")
                    for r in rca_list[:2]]
        missing = [
            m.get("item", str(m)) if isinstance(m, dict) else str(m)
            for m in (pack.missing_evidence or [])
        ]
        return {
            "schema": "hal.yieldos.failure_scenario_record.v1",
            "schema_version": SCHEMA_VERSION,
            "scenario_id": f"fs_{state.case_id}",
            "domain_pack": canonical,
            "asset_type": state.domain,
            "symptoms": symptoms[:5],
            "affected_functions": affected,
            "remaining_roles": remaining_roles,
            "blocked_roles": blocked_roles,
            "missing_evidence": missing,
            "decision_readiness_category": decision_readiness,
            "outcome_label": None,
            "human_review_required": True,
            "hardware_execution_enabled": False,
            "generated_by": generated_by(),
        }

    def _build_next_data_request(self, state, pack, decision_readiness: str, canonical: str) -> dict:
        required = [
            m.get("item", str(m)) if isinstance(m, dict) else str(m)
            for m in (pack.missing_evidence or [])
        ]
        to_improve = []
        if decision_readiness in ("ACTION_INELIGIBLE", "RUNNABLE_LOW_CONFIDENCE"):
            to_improve = [
                "cvc.json — constraint and value priority specification",
                "action_authority_matrix.json — who can approve what action",
                "operating_envelope.json — safe operating range per role",
            ]
        return {
            "schema": "hal.yieldos.next_data_request.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "current_readiness": decision_readiness,
            "required_evidence": required,
            "required_to_improve_readiness": to_improve,
            "note": (
                "Providing the listed evidence will enable more accurate Functional Passport generation. "
                "No data from this analysis is transmitted externally."
            ),
            "generated_by": generated_by(),
        }

    def _build_analysis_trace(self, state, pack, rec_list: list, decision_readiness: str,
                               canonical: str, iv_payload: Optional[dict] = None) -> dict:
        n_missing = len(pack.missing_evidence or [])
        m = state.metrics or {}
        domain = state.domain

        # Build domain-specific record_counts
        if domain == "memory_device" or canonical == "memory":
            record_counts = {
                "total_blocks": m.get("total_blocks", 0),
                "raw_capacity_gb": m.get("raw_capacity_gb", 0.0),
            }
        elif domain == "semiconductor_fab" or canonical == "semiconductor":
            record_counts = {
                "total_tool_log_rows": m.get("total_tool_log_rows", 0),
                "total_dies": m.get("total_dies", 0),
            }
        elif domain == "semiforge_crossbar" or canonical == "semiforge":
            record_counts = {
                "array_size": m.get("array_size", ""),
                "monte_carlo_runs": m.get("monte_carlo_runs", 0),
            }
        else:
            record_counts = {"telemetry_samples": m.get("telemetry_samples", 0)}

        # Use actual iv_payload (the written input_validation.json) if available
        if iv_payload:
            iv_status = iv_payload.get("status", "UNKNOWN")
            iv_data_level = iv_payload.get("data_level", "UNKNOWN")
            iv_missing = iv_payload.get("missing_inputs", [])
            iv_blocking = iv_payload.get("blocking_reasons", [])
        else:
            iv_status = "PASSED"
            iv_data_level = "MINIMUM_RUNNABLE"
            iv_missing = m.get("missing_inputs", [])
            iv_blocking = []

        iv_section = {
            "status": iv_status,
            "data_level": iv_data_level,
            "source": "input_validation.json",
            "record_counts": record_counts,
            "missing_inputs": iv_missing,
            "blocking_reasons": iv_blocking,
        }

        # Build minimal event summary from analysis steps
        representative_events = [
            {
                "event_id": "evt_001",
                "event_type": "input_validated",
                "source_ref": "input_validation.json",
                "impact_on_functional_yield": f"data_level_{iv_data_level.lower()}",
            },
            {
                "event_id": "evt_002",
                "event_type": "evidence_collected",
                "source_ref": "evidence_pack.json",
                "impact_on_functional_yield": f"{len(pack.evidence_objects or [])} evidence objects support functional assessment",
            },
            {
                "event_id": "evt_003",
                "event_type": "functional_binning_completed",
                "source_ref": "functional_binning_result.json",
                "impact_on_functional_yield": f"domain_state_{state.state.value}",
            },
        ]

        return {
            "schema": "hal.yieldos.analysis_trace.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "input_validation": iv_section,
            "functional_yield_event_summary": {
                "timeline_built": False,
                "event_summary_available": True,
                "event_basis": "domain_analyzer_events_and_output_artifacts",
                "representative_events": representative_events,
                "claim_boundary": "event_summary_not_real_time_monitoring",
            },
            "steps": [
                {
                    "step": "input_validation",
                    "result": iv_status,
                    "notes": [
                        f"data_level: {iv_data_level}",
                        f"record_counts: {record_counts}",
                        f"missing_inputs: {iv_missing}",
                    ],
                },
                {
                    "step": "evidence_collection",
                    "result": f"{len(pack.evidence_objects or [])} evidence objects collected",
                    "evidence_ids": [
                        ev.get("evidence_id", "") if isinstance(ev, dict) else getattr(ev, "evidence_id", "")
                        for ev in (pack.evidence_objects or [])
                    ],
                },
                {
                    "step": "decision_readiness",
                    "result": decision_readiness,
                    "limiting_factors": [
                        f"{n_missing} missing evidence items",
                        "missing_action_authority_matrix",
                        "missing_cvc_json",
                    ],
                },
                {
                    "step": "functional_binning",
                    "result": state.state.value,
                    "evidence_refs": [
                        ev.get("evidence_id", "") if isinstance(ev, dict) else getattr(ev, "evidence_id", "")
                        for ev in (pack.evidence_objects or [])
                    ],
                },
                {
                    "step": "recovery_route_generation",
                    "result": f"{len(rec_list)} candidate routes — all require_approval",
                    "blocked_terms_checked": True,
                    "safe_prefix_enforced": True,
                    "hardware_execution_enabled": False,
                },
            ],
            "generated_by": generated_by(),
        }

    def _build_source_data_manifest(self, state, pack, canonical: str,
                                     source_data_paths: Optional[List[str]] = None) -> dict:
        import csv as _csv
        import hashlib as _hl
        domain_adapter = state.domain
        input_files = []
        for p_str in (source_data_paths or []):
            p = Path(p_str)
            ext = p.suffix.lower()
            file_kind = "csv" if ext == ".csv" else ("json" if ext == ".json" else ext.lstrip(".") or "unknown")
            entry: dict = {
                "path": p.name,
                "file_kind": file_kind,
                "exists": p.exists(),
            }
            if p.exists():
                raw = p.read_bytes()
                entry["sha256"] = "sha256:" + _hl.sha256(raw).hexdigest()
                entry["byte_size"] = len(raw)
                if file_kind == "csv":
                    try:
                        text = raw.decode("utf-8", errors="replace")
                        reader = _csv.reader(text.splitlines())
                        header = next(reader, [])
                        rows = sum(1 for _ in reader)
                        entry["rows"] = rows
                        entry["columns"] = header
                    except Exception:
                        entry["rows"] = 0
                        entry["columns"] = []
            else:
                entry["sha256"] = None
                entry["byte_size"] = None
                entry["warning"] = f"File not found at analysis time: {p.name}"
            input_files.append(entry)
        return {
            "schema": "hal.yieldos.source_data_manifest.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "domain_adapter": domain_adapter,
            "input_files": input_files,
            "file_count": len(input_files),
            "claim_boundary": "input_hash_traceability_only",
            "note": (
                "This manifest records only file hashes and dimensions at analysis time. "
                "No raw data is embedded. Content is not transmitted externally."
            ),
            "generated_by": generated_by(),
        }

    def _build_data_quality_report(self, state, pack, canonical: str) -> dict:
        m = state.metrics or {}
        missing_ev = len(pack.missing_evidence or [])
        ev_count = len(pack.evidence_objects or [])
        total_signal = ev_count + missing_ev
        data_completeness = round(ev_count / total_signal, 3) if total_signal > 0 else 0.0
        fyv = m.get("functional_yield_vector")
        score_kind = fyv.get("score_kind", "heuristic") if fyv else "heuristic"

        domain = state.domain
        signal_coverage: dict = {}
        if domain == "memory_device" or canonical == "memory":
            signal_coverage = {
                "total_blocks": "present" if m.get("total_blocks", 0) > 0 else "absent",
                "raw_capacity_gb": "present" if m.get("raw_capacity_gb", 0) > 0 else "absent",
                "bad_block_count": "present" if "bad_block_count" in m else "absent",
                "ecc_error_count": "present" if "ecc_error_count" in m else "absent",
            }
        elif domain == "semiconductor_fab" or canonical == "semiconductor":
            signal_coverage = {
                "tool_log_rows": "present" if m.get("total_tool_log_rows", 0) > 0 else "absent",
                "wafer_dies": "present" if m.get("total_dies", 0) > 0 else "absent",
                "metrology_rows": "present" if m.get("metrology_rows", 0) > 0 else "absent",
            }
        elif domain == "robotics" or canonical == "robot":
            signal_coverage = {
                "telemetry_samples": "present" if m.get("telemetry_samples", 0) > 0 else "absent",
                "joint_error_rate": "present" if "joint_error_rate" in m else "absent",
            }
        elif domain == "satellite" or canonical == "space":
            signal_coverage = {
                "telemetry_samples": "present" if m.get("telemetry_samples", 0) > 0 else "absent",
                "power_budget_w": "present" if "power_budget_w" in m else "absent",
            }
        elif domain == "semiforge_crossbar" or canonical == "semiforge":
            signal_coverage = {
                "array_size": "present" if m.get("array_size") else "absent",
                "defect_rate": "present" if "defect_rate" in m else "absent",
            }

        # Determine sufficiency_status based on completeness and missing evidence
        if data_completeness >= 0.8 and missing_ev == 0:
            sufficiency_status = "SUFFICIENT_FOR_CANDIDATE_REVIEW"
        elif data_completeness >= 0.5 or ev_count > 0:
            sufficiency_status = "PARTIAL_FOR_CANDIDATE_REVIEW"
        elif ev_count == 0:
            sufficiency_status = "INSUFFICIENT_FOR_CANDIDATE_REVIEW"
        else:
            sufficiency_status = "UNKNOWN"

        return {
            "schema": "hal.yieldos.data_quality_report.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "data_completeness": data_completeness,
            "evidence_count": ev_count,
            "missing_evidence_count": missing_ev,
            "signal_coverage": signal_coverage,
            "score_basis": score_kind,
            "model_calibration_note": (
                "Simulation-calibrated" if score_kind == "simulation"
                else "Heuristic estimate — not calibrated against historical ground truth"
            ),
            "data_sufficiency": {
                "sufficiency_status": sufficiency_status,
                "sufficient_for": [
                    "candidate_functional_yield_assessment",
                    "human_review_preparation",
                ],
                "not_sufficient_for": [
                    "root_cause_certification",
                    "safety_certification",
                    "yield_certification",
                    "automatic_recovery",
                ],
                "missing_inputs": m.get("missing_inputs", []),
                "claim_boundary": "data_sufficiency_for_candidate_review_only",
            },
            "generated_by": generated_by(),
        }

    def _build_evidence_conflict_report(self, state, pack, canonical: str) -> dict:
        ev_list = pack.evidence_objects or []
        confs = [
            float(e.get("confidence", 0) if isinstance(e, dict) else getattr(e, "confidence", 0))
            for e in ev_list
        ]
        conflicts = []
        for i in range(len(confs)):
            for j in range(i + 1, len(confs)):
                delta = abs(confs[i] - confs[j])
                if delta > 0.3:
                    ev_i = ev_list[i]
                    ev_j = ev_list[j]
                    id_i = ev_i.get("evidence_id", f"ev_{i}") if isinstance(ev_i, dict) else getattr(ev_i, "evidence_id", f"ev_{i}")
                    id_j = ev_j.get("evidence_id", f"ev_{j}") if isinstance(ev_j, dict) else getattr(ev_j, "evidence_id", f"ev_{j}")
                    conflicts.append({
                        "evidence_a": id_i,
                        "evidence_b": id_j,
                        "confidence_delta": round(delta, 3),
                        "flag": "confidence_divergence",
                    })
        return {
            "schema": "hal.yieldos.evidence_conflict_report.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "note": (
                "Conflicts are confidence-divergence flags only. "
                "They do not invalidate the analysis but indicate areas needing additional data."
            ),
            "generated_by": generated_by(),
        }

    def _build_baseline_comparison(self, state, pack, canonical: str, bin_class: str,
                                    remaining_roles: Optional[List[str]],
                                    blocked_roles: Optional[List[str]],
                                    extra_outputs: Optional[dict] = None) -> dict:
        remaining_roles = remaining_roles or []
        blocked_roles = blocked_roles or []
        binary_verdict = "PASS" if state.severity.value in ("low", "info") else "FAIL"
        yieldos_verdict = bin_class or "degraded_role_candidate"
        reclassified = binary_verdict == "FAIL" and bool(remaining_roles)
        m = state.metrics or {}
        fyv = m.get("functional_yield_vector")
        fy_score = fyv.get("functional_yield_score", 0.0) if fyv else 0.0
        result = {
            "schema": "hal.yieldos.baseline_vs_yieldos.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "binary_policy_verdict": binary_verdict,
            "binary_policy_basis": "severity_threshold_only",
            "yieldos_functional_verdict": yieldos_verdict,
            "yieldos_functional_yield_score": round(fy_score, 4),
            "remaining_roles_identified": remaining_roles,
            "blocked_roles_identified": blocked_roles,
            "reclassification_occurred": reclassified,
            "reclassification_note": (
                "YieldOS identified remaining functional roles despite binary FAIL classification. "
                "Human review required to determine if reclassification is operationally valid."
                if reclassified else
                "No reclassification: binary verdict and YieldOS verdict aligned."
            ),
            "human_decision_required": True,
            "generated_by": generated_by(),
        }
        # Memory domain: embed capacity breakdown from memory_functional_capacity extra output
        if (canonical == "memory" or state.domain == "memory_device") and extra_outputs:
            cap = extra_outputs.get("memory_functional_capacity") or {}
            if cap:
                result["capacity_breakdown_gb"] = {
                    "raw_capacity_gb": cap.get("raw_capacity_gb", m.get("raw_capacity_gb", 0.0)),
                    "safe_capacity_gb": cap.get("safe_capacity_gb", 0.0),
                    "approximate_cache_capacity_gb": cap.get("approximate_cache_capacity_gb", 0.0),
                    "read_only_archive_capacity_gb": cap.get("read_only_archive_capacity_gb", 0.0),
                    "discarded_capacity_gb": cap.get("discarded_capacity_gb", 0.0),
                }
        return result

    def _build_business_case_summary(self, state, pack, canonical: str, bin_class: str) -> dict:
        domain_value_prop = {
            "memory": (
                "YieldOS identifies partially-functional memory blocks that binary policy would discard. "
                "Rebinning candidates reduce waste and extend component lifecycle under human-reviewed conditions."
            ),
            "robot": (
                "YieldOS identifies reduced-capability robot operating modes (e.g., low-speed inspection) "
                "that allow continued use pending maintenance, rather than full shutdown."
            ),
            "space": (
                "YieldOS identifies mission-salvage operating modes (e.g., safe-hold, minimal comms) "
                "that preserve asset value when primary mission roles are blocked."
            ),
            "semiconductor": (
                "YieldOS identifies process drift evidence and wafer-level functional impact, "
                "enabling targeted lot disposition rather than blanket scrapping."
            ),
            "semiforge": (
                "YieldOS reclassifies dark functional cells in crossbar arrays, "
                "identifying which inference or sensing roles remain viable under defect conditions."
            ),
        }
        value_prop = domain_value_prop.get(canonical, "YieldOS reclassifies remaining functional roles for human review.")
        reclassified = bin_class not in ("shadow_analysis_only",) and state.severity.value not in ("low", "info")
        return {
            "schema": "hal.yieldos.business_case_summary.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "value_proposition": value_prop,
            "reclassification_candidate": reclassified,
            "overclaiming_boundary": (
                "YieldOS does not certify that reclassified roles are operationally safe. "
                "It provides evidence lineage for human engineers to make that determination."
            ),
            "decision_authority": "human_only",
            "generated_by": generated_by(),
        }

    def _build_case_manifest_from_paths(self, state, canonical: str, paths: dict) -> dict:
        """Build case manifest from the full paths dict — includes ALL written files."""
        files = {}
        optional_outputs = {}
        for key, path_str in sorted(paths.items()):
            if key == "case_manifest" or not path_str:
                continue
            p = Path(path_str)
            if not p.exists() or not p.is_file():
                continue
            entry = {
                "path": p.name,
                "sha256": _sha256_file(p),
                "byte_size": p.stat().st_size,
            }
            # Extra output keys have .json in the key name; standard keys do not
            if key.endswith(".json"):
                stem = key[:-5]
                optional_outputs[stem] = entry
            files[key] = entry
        # Cross-references: key pipeline artifacts for navigation
        CROSS_REF_KEYS = [
            "state_snapshot", "input_validation", "evidence_pack", "ooda_frame",
            "functional_yield_scorecard", "functional_passport",
            "recovery_candidates", "recovery_route_report", "analysis_trace",
        ]
        cross_references = {k: files[k]["path"] for k in CROSS_REF_KEYS if k in files}
        # Include optimizer_info if present (optional output)
        if "optimizer_info.json" in files:
            cross_references["optimizer_info"] = files["optimizer_info.json"]["path"]
        return {
            "schema": "hal.yieldos.case_manifest.v1",
            "schema_version": SCHEMA_VERSION,
            "case_id": state.case_id,
            "domain_pack": canonical,
            "yieldos_version": SCHEMA_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mode": "shadow_only",
            "file_count": len(files),
            "safety_boundary": SAFETY_BLOCK,
            "cross_references": cross_references,
            "functional_yield_lineage_summary": {
                "lineage_graph_generated": False,
                "source_manifest_ref": "source_data_manifest.json",
                "evidence_pack_ref": "evidence_pack.json",
                "functional_passport_ref": "functional_passport.json",
                "decision_readiness_ref": "decision_readiness_report.json",
                "artifact_hashes_present": len(files) > 0,
                "claim_boundary": "lineage_summary_not_legal_chain_of_custody",
            },
            "files": files,
            "optional_outputs": optional_outputs,
            "generated_by": generated_by(),
        }

    # ── File writers ───────────────────────────────────────────────────────────

    def _write_json(self, path: Path, data) -> str:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def _write_md(
        self, path: Path, state: StateSnapshot, pack: EvidencePack, ooda: OODAFrame,
        recovery_candidates: List,
    ) -> str:
        rcc = pack.root_cause_candidates
        ev = pack.evidence_objects
        recovery = [r.to_dict() if hasattr(r, "to_dict") else r for r in recovery_candidates]

        lines = [
            f"# YieldOS Report -- {pack.case_id}",
            f"**Generated**: {datetime.now(timezone.utc).isoformat()}  ",
            f"**Domain**: {pack.domain}  ",
            f"**Asset**: {pack.asset_id}  ",
            f"**Mode**: {state.mode}  ",
            "",
            "---",
            "## 1. Case Summary",
            f"> {pack.summary}",
            "",
            f"**State**: `{state.state.value}`  ",
            f"**Severity**: `{state.severity.value}`  ",
            f"**Confidence**: `{state.confidence:.0%}`  ",
            "",
            "---",
            "## 2. OODA Frame",
            f"**Observe**: {ooda.observe}  ",
            f"**Orient**: {ooda.orient}  ",
            f"**Decide**: {ooda.decide}  ",
            f"**Act**: `{ooda.act}`  ",
            "",
            "---",
            "## 3. Evidence Objects",
        ]
        for i, e in enumerate(ev, 1):
            e_dict = e if isinstance(e, dict) else e.to_dict() if hasattr(e, "to_dict") else {}
            lines.append(f"### EV-{i:02d} `{e_dict.get('evidence_id', '')}`")
            lines.append(f"- **Type**: {e_dict.get('type')}  ")
            lines.append(f"- **Source**: {e_dict.get('source')}  ")
            lines.append(f"- **Summary**: {e_dict.get('summary')}  ")
            lines.append(f"- **Confidence**: {e_dict.get('confidence', 0):.0%}  ")
            lines.append("")

        lines += ["---", "## 4. Root Cause Candidates"]
        lines.append(f"> WARNING: {pack.causal_claim_boundary}")
        lines.append("")
        for i, rc in enumerate(rcc, 1):
            cand = rc.get("candidate", "") if isinstance(rc, dict) else getattr(rc, "candidate", "")
            conf = rc.get("confidence", 0) if isinstance(rc, dict) else getattr(rc, "confidence", 0)
            lines.append(f"{i}. **{cand}** (confidence: {conf:.0%})")
        lines.append("")

        if recovery:
            lines += ["---", "## 5. Recovery Candidates"]
            for i, r in enumerate(recovery, 1):
                lines.append(
                    f"{i}. **{r.get('action')}** -- "
                    f"risk: {r.get('risk')} -- {r.get('expected_benefit')}"
                )
            lines.append("")

        if pack.missing_evidence:
            lines += ["---", "## 6. Missing Evidence Request"]
            for m in pack.missing_evidence:
                if isinstance(m, dict):
                    item = m.get("item", m.get("name", str(m)))
                    reason = m.get("reason", "")
                    priority = m.get("priority", "")
                    lines.append(f"- **{item}** [{priority}]: {reason}" if reason else f"- {item}")
                else:
                    lines.append(f"- {m}")
            lines.append("")

        lines += [
            "---",
            "## 7. Safety Boundary",
            "```",
            "read_only_shadow: true",
            "hardware_execution_enabled: false",
            "causal_claim: candidate_only_not_certified_cause",
            "act: recommendation_only_no_hardware_action",
            "```",
            "",
            "> This report is a shadow analysis output. It does not command, control, or certify "
            "the target system. All recovery routes are candidate-only and require human review.",
            "",
            f"**Checksum**: `{pack.checksum}`",
        ]

        content = "\n".join(lines)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def _write_html(
        self, path: Path, state: StateSnapshot, pack: EvidencePack, ooda: OODAFrame,
        recovery_candidates: List,
    ) -> str:
        sev_color = {
            "critical": "#d32f2f", "high": "#f57c00",
            "medium": "#fbc02d", "low": "#388e3c", "info": "#1976d2",
        }.get(state.severity.value, "#555")

        ev_rows = "".join(
            f"<tr><td><code>{_esc(e.get('evidence_id', '') if isinstance(e, dict) else getattr(e, 'evidence_id', ''))}</code></td>"
            f"<td>{_esc(e.get('type', '') if isinstance(e, dict) else getattr(e, 'type', ''))}</td>"
            f"<td>{_esc(e.get('summary', '') if isinstance(e, dict) else getattr(e, 'summary', ''))}</td>"
            f"<td>{float(e.get('confidence', 0) if isinstance(e, dict) else getattr(e, 'confidence', 0)):.0%}</td></tr>"
            for e in (pack.evidence_objects or [])
        )
        rca_rows = "".join(
            f"<tr><td>{_esc(r.get('candidate', '') if isinstance(r, dict) else getattr(r, 'candidate', ''))}</td>"
            f"<td>{float(r.get('confidence', 0) if isinstance(r, dict) else getattr(r, 'confidence', 0)):.0%}</td>"
            f"<td>{_esc(r.get('claim_boundary', '') if isinstance(r, dict) else getattr(r, 'claim_boundary', ''))}</td></tr>"
            for r in (pack.root_cause_candidates or [])
        )

        def _missing_html(m):
            if isinstance(m, dict):
                item = _esc(m.get("item", m.get("name", str(m))))
                reason = _esc(m.get("reason", ""))
                priority = _esc(m.get("priority", ""))
                return f"<li><b>{item}</b> [{priority}] {reason}</li>"
            return f"<li>{_esc(m)}</li>"

        missing = "".join(_missing_html(m) for m in (pack.missing_evidence or []))

        recovery = [r.to_dict() if hasattr(r, "to_dict") else r for r in recovery_candidates]
        rec_rows = "".join(
            f"<tr><td><b>{_esc(r.get('action', ''))}</b></td>"
            f"<td>{_esc(r.get('risk', ''))}</td>"
            f"<td>{_esc(r.get('expected_benefit', ''))}</td></tr>"
            for r in recovery
        )

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>YieldOS Report -- {_esc(pack.case_id)}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 40px; color: #222; background:#f9f9f9; }}
  h1 {{ color: #1a237e; }} h2 {{ border-bottom: 2px solid #eee; padding-bottom:4px; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:12px; color:#fff; font-weight:bold;
            background:{sev_color}; }}
  .safety {{ background:#e8f5e9; border:1px solid #a5d6a7; padding:12px; border-radius:6px; font-family:monospace; }}
  .shadow-notice {{ background:#fff3e0; border:1px solid #ffcc80; padding:10px; border-radius:6px; margin:12px 0; font-size:0.9em; }}
  table {{ border-collapse:collapse; width:100%; margin:12px 0; }}
  th {{ background:#e3f2fd; text-align:left; padding:8px; }}
  td {{ padding:8px; border-bottom:1px solid #eee; vertical-align:top; }}
  .meta {{ background:#fff; border:1px solid #ddd; padding:16px; border-radius:6px; margin:16px 0; }}
  code {{ background:#f5f5f5; padding:2px 6px; border-radius:3px; }}
  .warn {{ color:#b71c1c; font-weight:bold; }}
</style>
</head>
<body>
<div class="shadow-notice">
  <b>Shadow Analysis Notice:</b> This report does not command, control, or certify the target system.
  All recovery routes are candidate-only and require human review before any action.
</div>
<h1>YieldOS Report -- {_esc(pack.case_id)}</h1>
<div class="meta">
  <b>Domain:</b> {_esc(pack.domain)} &nbsp;|&nbsp;
  <b>Asset:</b> {_esc(pack.asset_id)} &nbsp;|&nbsp;
  <b>State:</b> <code>{_esc(state.state.value)}</code> &nbsp;|&nbsp;
  <b>Severity:</b> <span class="badge">{_esc(state.severity.value)}</span> &nbsp;|&nbsp;
  <b>Confidence:</b> {state.confidence:.0%} &nbsp;|&nbsp;
  <b>Mode:</b> <code>{_esc(state.mode)}</code>
</div>

<h2>1. Summary</h2>
<p>{_esc(pack.summary)}</p>

<h2>2. OODA Frame</h2>
<table><tr><th>Phase</th><th>Content</th></tr>
<tr><td><b>Observe</b></td><td>{_esc(ooda.observe)}</td></tr>
<tr><td><b>Orient</b></td><td>{_esc(ooda.orient)}</td></tr>
<tr><td><b>Decide</b></td><td>{_esc(ooda.decide)}</td></tr>
<tr><td><b>Act</b></td><td><code>{_esc(ooda.act)}</code></td></tr>
</table>

<h2>3. Evidence Objects</h2>
<table><tr><th>ID</th><th>Type</th><th>Summary</th><th>Conf.</th></tr>
{ev_rows or "<tr><td colspan='4'>No evidence objects</td></tr>"}
</table>

<h2>4. Root Cause Candidates</h2>
<p class="warn">WARNING: {_esc(pack.causal_claim_boundary)}</p>
<table><tr><th>Candidate</th><th>Confidence</th><th>Boundary</th></tr>
{rca_rows or "<tr><td colspan='3'>No candidates</td></tr>"}
</table>

{f'<h2>5. Recovery Candidates</h2><table><tr><th>Action</th><th>Risk</th><th>Expected Benefit</th></tr>{rec_rows}</table>' if rec_rows else ''}

{f'<h2>6. Missing Evidence Request</h2><ul>{missing}</ul>' if missing else ''}

<h2>Safety Boundary</h2>
<div class="safety">
read_only_shadow: true<br>
hardware_execution_enabled: false<br>
causal_claim: candidate_only_not_certified_cause<br>
act: recommendation_only_no_hardware_action
</div>

<p style="margin-top:32px;color:#888;font-size:0.85em;">
  Checksum: <code>{_esc(pack.checksum)}</code>
</p>
</body></html>"""
        path.write_text(html_content, encoding="utf-8")
        return str(path)
