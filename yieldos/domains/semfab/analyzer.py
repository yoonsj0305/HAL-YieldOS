from __future__ import annotations

import math
import uuid
from typing import Any, Optional

from ...contracts import (
    EvidenceObject,
    EvidenceType,
    RecoveryCandidate,
    RootCauseCandidate,
    SeverityLevel,
    StateKind,
    StateSnapshot,
)
from ...core.evidence_engine import EvidenceEngine
from .adapter import load_all
from .cross_step_rca import build_cross_step_graph
from .drift_detector import detect_metric_drift, find_affected_lots, find_affected_wafers

DOMAIN = "semiconductor_fab"
WATCHED_METRICS = ["rf_power_W", "pressure_mTorr", "gas_flow_sccm", "temperature_C", "endpoint_signal"]

SEMICONDUCTOR_RECENT_TREND_FRACTION = 0.30
SEMICONDUCTOR_RECENT_TREND_THRESHOLD = 0.08
SEMICONDUCTOR_MIN_TREND_SAMPLES = 8


def _detect_recent_trend(
    rows: list[dict[str, Any]],
    column: str,
    *,
    recent_fraction: float = SEMICONDUCTOR_RECENT_TREND_FRACTION,
    threshold: float = SEMICONDUCTOR_RECENT_TREND_THRESHOLD,
    min_samples: int = SEMICONDUCTOR_MIN_TREND_SAMPLES,
) -> dict[str, Any]:
    """
    Compare the recent tail (last recent_fraction of rows) vs the early body.
    Returns status DRIFT_CANDIDATE / STABLE_NORMAL / INSUFFICIENT_DATA plus numeric detail.
    """
    values: list[float] = []
    for row in rows:
        raw = row.get(column)
        if raw is None or raw == "":
            continue
        try:
            values.append(float(raw))
        except (TypeError, ValueError):
            continue

    if len(values) < min_samples:
        return {
            "metric": column,
            "status": "INSUFFICIENT_DATA",
            "sample_count": len(values),
            "min_samples_required": min_samples,
            "relative_delta": None,
            "early_mean": None,
            "recent_mean": None,
        }

    recent_count = max(1, math.ceil(len(values) * recent_fraction))
    recent_vals = values[-recent_count:]
    early_vals = values[:-recent_count] or values

    recent_mean = sum(recent_vals) / len(recent_vals)
    early_mean = sum(early_vals) / len(early_vals)
    relative_delta = (recent_mean - early_mean) / max(abs(early_mean), 1e-9)

    status = "DRIFT_CANDIDATE" if abs(relative_delta) >= threshold else "STABLE_NORMAL"

    return {
        "metric": column,
        "status": status,
        "sample_count": len(values),
        "recent_fraction": recent_fraction,
        "threshold": threshold,
        "relative_delta": round(relative_delta, 4),
        "early_mean": round(early_mean, 4),
        "recent_mean": round(recent_mean, 4),
    }


def _build_confidence_report(
    *,
    tool_log_rows: int,
    metrology_rows: int,
    trend_statuses: list[dict[str, Any]],
    watched_metrics: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Compute a structured confidence report for semiconductor analysis.
    Confidence reflects analysis confidence (not severity).

    Score table:
      INSUFFICIENT_DATA              -> 0.30
      PARTIAL_DATA                   -> 0.45
      SUFFICIENT + DRIFT_CANDIDATE   -> 0.65
      SUFFICIENT + STABLE_NORMAL     -> 0.70
      SUFFICIENT + CONFLICTING_SIGNALS -> 0.50
    """
    if watched_metrics is None:
        watched_metrics = WATCHED_METRICS

    # Determine data_status
    has_any_data = (tool_log_rows > 0) or (metrology_rows > 0)
    has_sufficient = (tool_log_rows >= 8) or (metrology_rows >= 4)

    if not has_any_data:
        data_status = "INSUFFICIENT_DATA"
    elif not has_sufficient:
        data_status = "PARTIAL_DATA"
    else:
        data_status = "SUFFICIENT"

    # Determine signal_status from trend report
    drift_count = sum(1 for t in trend_statuses if t.get("status") == "DRIFT_CANDIDATE")
    stable_count = sum(1 for t in trend_statuses if t.get("status") == "STABLE_NORMAL")
    insufficient_count = sum(1 for t in trend_statuses if t.get("status") == "INSUFFICIENT_DATA")

    if data_status == "INSUFFICIENT_DATA":
        signal_status = "UNKNOWN"
    elif drift_count > 0 and stable_count > 0 and drift_count < stable_count:
        signal_status = "CONFLICTING_SIGNALS"
    elif drift_count > 0:
        signal_status = "DRIFT_CANDIDATE"
    elif stable_count > 0:
        signal_status = "STABLE_NORMAL"
    else:
        signal_status = "UNKNOWN"

    # Score
    if data_status == "INSUFFICIENT_DATA":
        score = 0.30
        confidence_kind = "low_data_quality"
    elif data_status == "PARTIAL_DATA":
        score = 0.45
        confidence_kind = "partial_data_quality"
    elif signal_status == "DRIFT_CANDIDATE":
        score = 0.65
        confidence_kind = "drift_detected_sufficient_data"
    elif signal_status == "CONFLICTING_SIGNALS":
        score = 0.50
        confidence_kind = "conflicting_signals_sufficient_data"
    else:
        score = 0.70
        confidence_kind = "stable_normal_sufficient_data"

    reasons: list[str] = []
    if tool_log_rows == 0:
        reasons.append("no tool_log rows")
    elif tool_log_rows < 8:
        reasons.append(f"only {tool_log_rows} tool_log rows (below 8-row threshold)")
    if metrology_rows == 0:
        reasons.append("no metrology rows")
    elif metrology_rows < 4:
        reasons.append(f"only {metrology_rows} metrology rows (below 4-row threshold)")
    if drift_count > 0:
        metrics = [t["metric"] for t in trend_statuses if t.get("status") == "DRIFT_CANDIDATE"]
        reasons.append(f"recent trend drift detected on: {metrics}")
    if insufficient_count > 0:
        metrics = [t["metric"] for t in trend_statuses if t.get("status") == "INSUFFICIENT_DATA"]
        reasons.append(f"insufficient samples for trend on: {metrics}")
    if not reasons:
        reasons.append("all metrics stable, data sufficient")

    # Compute missing/available metrics from watched list
    metric_status_map = {t["metric"]: t.get("status") for t in trend_statuses}
    missing_metrics = [
        m for m in watched_metrics
        if metric_status_map.get(m) == "INSUFFICIENT_DATA"
    ]
    available_metrics = [m for m in watched_metrics if m not in missing_metrics]
    total_watched = len(watched_metrics)
    available_count = len(available_metrics)
    missing_count = len(missing_metrics)

    # Per-watched-metric drift/stable breakdown (only among available metrics)
    drift_candidate_metrics = [
        m for m in available_metrics if metric_status_map.get(m) == "DRIFT_CANDIDATE"
    ]
    stable_metrics_list = [
        m for m in available_metrics if metric_status_map.get(m) == "STABLE_NORMAL"
    ]
    drift_candidate_count_watched = len(drift_candidate_metrics)
    stable_count_watched = len(stable_metrics_list)

    # summary_text (v3.0.5 format)
    if missing_count == total_watched:
        summary_text = "0 available metrics; all watched metrics have insufficient data"
    elif missing_count == 0 and drift_candidate_count_watched == 0:
        summary_text = (
            f"0/{available_count} available metrics show drift;"
            f" all watched metrics have usable data"
        )
    else:
        _drift_part = f"{drift_candidate_count_watched}/{available_count} available metrics show drift"
        if drift_candidate_metrics:
            _drift_part += f" ({', '.join(drift_candidate_metrics)})"
        if missing_count > 0:
            _no_data_part = (
                f"{missing_count} watched metrics have no data ({', '.join(missing_metrics)})"
            )
            summary_text = f"{_drift_part}; {_no_data_part}"
        else:
            summary_text = _drift_part

    available_metrics_summary = {
        # v3.0.5 exact fields
        "available_metric_count": available_count,
        "watched_metric_count": total_watched,
        "drift_candidate_count": drift_candidate_count_watched,
        "stable_count": stable_count_watched,
        "insufficient_data_count": missing_count,
        "drift_candidate_metrics": drift_candidate_metrics,
        "stable_metrics": stable_metrics_list,
        "insufficient_data_metrics": missing_metrics,
        "summary_text": summary_text,
        # v3.0.4 compatibility fields
        "total_watched": total_watched,
        "available_count": available_count,
        "missing_count": missing_count,
        "available": available_metrics,
        "missing": missing_metrics,
    }

    return {
        "confidence_kind": confidence_kind,
        "score": round(score, 3),
        "data_status": data_status,
        "signal_status": signal_status,
        "reasons": reasons,
        "claim_boundary": "confidence_in_analysis_quality_not_severity",
        "missing_metrics": missing_metrics,
        "available_metrics_summary": available_metrics_summary,
    }


def _choose_top_signal(evidence_objects) -> str:
    """Pick the most informative signal name from the highest-confidence evidence."""
    if not evidence_objects:
        return "no_signal"
    top = max(evidence_objects, key=lambda e: getattr(e, "confidence", 0.0))
    metric = getattr(top, "metric", None)
    source = getattr(top, "source", None)
    ev_type = getattr(top, "type", None)
    if metric and metric not in ("unknown", ""):
        return metric
    if source and source not in ("unknown", ""):
        return source
    if ev_type:
        return ev_type.value if hasattr(ev_type, "value") else str(ev_type)
    return "evidence_signal"


class SemFabAnalyzer:
    """
    Read-only shadow analysis for semiconductor fab data.
    Produces StateSnapshot + EvidencePack + OODAFrame from tool log + wafer data.
    """

    def __init__(self):
        self._engine = EvidenceEngine()

    def analyze(self, data_dir: str, case_id: Optional[str] = None, asset_id: str = "ETCH_01.CH_A") -> dict:
        if not case_id:
            case_id = f"case_semfab_{uuid.uuid4().hex[:8]}"

        data = load_all(data_dir)
        tool_log = data["tool_log"]
        wafer_map = data["wafer_map"]
        metrology = data["metrology"]
        test_result = data["test_result"]

        # --- Drift detection across all watched metrics ---
        all_drifts = []
        for metric in WATCHED_METRICS:
            drifts = detect_metric_drift(tool_log, metric_col=metric)
            for d in drifts:
                d["metric"] = metric
            all_drifts.extend(drifts)

        all_drifts.sort(key=lambda x: x["confidence"], reverse=True)

        # --- Build EvidenceObjects ---
        evidence_objects = []
        ev_counter = 1

        for drift in all_drifts[:5]:
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.TREND_SHIFT,
                source="tool_log",
                summary=(
                    f"{drift['metric']} baseline shifted at step {drift['step']}: "
                    f"step_mean={drift['step_mean']}, global_mean={drift['global_mean']}, "
                    f"sigma={drift['sigma_count']}"
                ),
                metric=drift["metric"],
                value=drift["step_mean"],
                baseline=drift["global_mean"],
                confidence=drift["confidence"],
                extra={"sigma_count": drift["sigma_count"], "shift_ratio": drift["shift_ratio"]},
            )
            evidence_objects.append(ev)
            ev_counter += 1

        # --- Wafer map: check fail rate ---
        total_dies = len(wafer_map)
        fail_dies = sum(1 for w in wafer_map if w.get("bin_result", "").upper() in ("FAIL", "F", "1"))
        if total_dies > 0:
            fail_rate = fail_dies / total_dies
            if fail_rate > 0.05:
                ev = EvidenceObject(
                    evidence_id=f"ev_{ev_counter:03d}",
                    type=EvidenceType.YIELD_DROP,
                    source="wafer_map",
                    summary=f"Wafer map shows {fail_rate:.1%} fail rate ({fail_dies}/{total_dies} dies)",
                    metric="fail_rate",
                    value=round(fail_rate, 4),
                    baseline=0.02,
                    unit="ratio",
                    confidence=min(0.95, 0.5 + fail_rate * 3),
                )
                evidence_objects.append(ev)
                ev_counter += 1

        # --- Metrology: CD shift ---
        cd_vals = []
        for row in metrology:
            try:
                cd_vals.append(float(row.get("cd_nm", 0) or 0))
            except ValueError:
                pass
        if len(cd_vals) >= 4:
            import statistics
            cd_mean = statistics.mean(cd_vals)
            cd_std = statistics.stdev(cd_vals)
            target_cd = float(metrology[0].get("target_cd_nm", cd_mean) or cd_mean)
            cd_offset = abs(cd_mean - target_cd)
            if cd_offset > cd_std:
                ev = EvidenceObject(
                    evidence_id=f"ev_{ev_counter:03d}",
                    type=EvidenceType.STATISTICAL_OUTLIER,
                    source="metrology",
                    summary=f"CD mean={cd_mean:.1f}nm deviates from target={target_cd:.1f}nm by {cd_offset:.1f}nm",
                    metric="cd_nm",
                    value=round(cd_mean, 2),
                    baseline=round(target_cd, 2),
                    unit="nm",
                    confidence=min(0.9, 0.4 + cd_offset / max(cd_std, 1) * 0.1),
                )
                evidence_objects.append(ev)
                ev_counter += 1

        # --- Cross-step RCA ---
        # Find which lots/wafers were affected by top drift event
        affected_wafers = []
        affected_lots_list = []
        if all_drifts:
            top_drift_step = all_drifts[0]["step"]
            affected_wafers = find_affected_wafers(tool_log, top_drift_step)
            affected_lots_list = find_affected_lots(tool_log, affected_wafers)

        cross_graph = build_cross_step_graph(all_drifts, affected_lots_list, metrology, wafer_map)

        # Add cross-step evidence objects
        for cd_hit in cross_graph["cd_shift"]:
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.CORRELATION_BREAK,
                source="cross_step_rca",
                summary=cd_hit["interpretation"],
                metric="cd_nm_cross_step",
                confidence=cd_hit["confidence"],
                extra=cd_hit,
            )
            evidence_objects.append(ev)
            ev_counter += 1

        for yl_hit in cross_graph["yield_loss"]:
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.YIELD_DROP,
                source="cross_step_rca",
                summary=yl_hit["interpretation"],
                metric="fail_rate_cross_step",
                confidence=yl_hit["confidence"],
                extra=yl_hit,
            )
            evidence_objects.append(ev)
            ev_counter += 1

        # --- Sort evidence by confidence descending ---
        evidence_objects.sort(key=lambda e: getattr(e, "confidence", 0.0), reverse=True)

        # --- Recent trend detection (independent of sigma-based drift) ---
        recent_trend_statuses = [
            _detect_recent_trend(tool_log, metric) for metric in WATCHED_METRICS
        ]
        cd_trend = _detect_recent_trend(
            metrology,
            "cd_nm",
            min_samples=SEMICONDUCTOR_MIN_TREND_SAMPLES // 2,
        )
        recent_trend_statuses.append(cd_trend)

        process_drift_report = {
            "schema": "yieldos.semfab.process_drift_report.v1",
            "asset_id": asset_id,
            "metric_trends": recent_trend_statuses,
            "drift_candidate_count": sum(
                1 for t in recent_trend_statuses if t.get("status") == "DRIFT_CANDIDATE"
            ),
            "stable_count": sum(
                1 for t in recent_trend_statuses if t.get("status") == "STABLE_NORMAL"
            ),
            "insufficient_count": sum(
                1 for t in recent_trend_statuses if t.get("status") == "INSUFFICIENT_DATA"
            ),
        }

        # --- Build confidence report (always present) ---
        confidence_report = _build_confidence_report(
            tool_log_rows=len(tool_log),
            metrology_rows=len(metrology),
            trend_statuses=recent_trend_statuses,
        )

        # --- Determine severity & confidence ---
        if not evidence_objects:
            # Use data-driven confidence instead of hardcoded 0.3
            top_conf = confidence_report["score"]
            state_kind = StateKind.NOMINAL
            severity = SeverityLevel.INFO
        else:
            top_conf = evidence_objects[0].confidence
            if top_conf >= 0.80:
                state_kind = StateKind.FAULT_CANDIDATE
                severity = SeverityLevel.HIGH
            elif top_conf >= 0.60:
                state_kind = StateKind.PROCESS_DRIFT_CANDIDATE
                severity = SeverityLevel.MEDIUM
            else:
                state_kind = StateKind.ANOMALY_CANDIDATE
                severity = SeverityLevel.LOW

        # --- StateSnapshot ---
        state = StateSnapshot(
            case_id=case_id,
            domain=DOMAIN,
            asset_id=asset_id,
            state=state_kind,
            severity=severity,
            confidence=top_conf,
            evidence_refs=[e.evidence_id for e in evidence_objects],
            metrics={
                "total_tool_log_rows": len(tool_log),
                "drift_events_detected": len(all_drifts),
                "fail_dies": fail_dies if total_dies > 0 else 0,
                "total_dies": total_dies,
                "affected_lots": affected_lots_list,
                "cross_step_chain_confidence": cross_graph["chain_confidence"],
                "cross_step_interpretation": cross_graph["chain_interpretation"],
            },
        )

        # --- Root cause candidates ---
        rca_list = []
        cross_ev_ids = [e.evidence_id for e in evidence_objects if "cross_step" in e.source]
        tool_ev_ids = [e.evidence_id for e in evidence_objects if "tool_log" in e.source]

        if all_drifts:
            chain_hint = cross_graph["chain_interpretation"]
            rca_list.append(RootCauseCandidate(
                candidate="chamber condition drift",
                confidence=round(max(top_conf, cross_graph["chain_confidence"]) * 0.90, 3),
                supporting_evidence=tool_ev_ids + cross_ev_ids,
                investigation_hints=[
                    "check chamber clean log",
                    "compare recipe revision history",
                    f"cross-step chain: {chain_hint}",
                ],
            ))
        if fail_dies > 0 or cross_graph["yield_loss"]:
            rca_list.append(RootCauseCandidate(
                candidate="recipe-step instability causing downstream yield loss",
                confidence=round(top_conf * 0.72, 3),
                supporting_evidence=[e.evidence_id for e in evidence_objects if "wafer_map" in e.source or "cross_step" in e.source],
                investigation_hints=["cross-reference with lot genealogy", "check incoming wafer specs"],
            ))
        rca_list.append(RootCauseCandidate(
            candidate="incoming wafer variation",
            confidence=round(top_conf * 0.45, 3),
            investigation_hints=["request pre-etch metrology", "check supplier lot trace"],
        ))

        # --- Missing evidence (structured) ---
        missing = [
            {
                "item": "pre-etch metrology",
                "reason": "Cannot confirm CD shift origin without pre-etch baseline",
                "priority": "high",
                "related_candidates": ["chamber condition drift", "incoming wafer variation"],
                "expected_value": "CD measurements before etching step for affected lots",
            },
            {
                "item": "chamber clean history",
                "reason": "PM log needed to correlate drift with maintenance window",
                "priority": "high",
                "related_candidates": ["chamber condition drift"],
                "expected_value": "cleaning event timestamps and chamber IDs from MES",
            },
            {
                "item": "incoming wafer inspection report",
                "reason": "Rules out substrate variation as root cause",
                "priority": "medium",
                "related_candidates": ["incoming wafer variation"],
                "expected_value": "wafer flatness, bow, resistivity from supplier lot trace",
            },
        ]
        if not metrology:
            missing.insert(0, {
                "item": "post-etch CD metrology",
                "reason": "Required for cross-step correlation",
                "priority": "high",
                "related_candidates": ["chamber condition drift", "recipe-step instability causing downstream yield loss"],
                "expected_value": "CD measurement data per lot/wafer/site",
            })

        # --- EvidencePack ---
        top_signal = _choose_top_signal(evidence_objects)
        pack = self._engine.build_pack(
            case_id=case_id,
            domain=DOMAIN,
            asset_id=asset_id,
            summary=(
                f"Possible process drift detected in {asset_id}. "
                f"Top signal: {top_signal}. "
                f"{len(evidence_objects)} evidence objects found."
            ),
            evidence_objects=evidence_objects,
            root_cause_candidates=rca_list,
            missing_evidence=missing,
            state_snapshot_ref=case_id,
            state_snapshot_hash=state.snapshot_hash,
        )

        # --- OODAFrame ---
        ooda = self._engine.build_ooda(
            case_id=case_id,
            domain=DOMAIN,
            observe=(
                f"{len(evidence_objects)} anomaly signals detected in {asset_id}. "
                f"Top: {top_signal}."
            ),
            orient=(
                f"Possible chamber drift in {asset_id}. "
                f"Top confidence: {top_conf:.0%}. "
                f"Affected metrics: {[d['metric'] for d in all_drifts[:3]]}."
            ),
            decide=(
                f"Recommend engineer review of {asset_id} before next production batch. "
                f"Request missing evidence: {missing[:2]}."
            ),
            evidence_pack_ref=pack.checksum,
        )

        # Remaining / blocked roles (semiconductor is always shadow analysis layer)
        remaining_roles = [
            "shadow_monitoring",
            "evidence_generation",
            "yield_investigation_support",
            "drift_investigation_support",
            "yield_loss_triage",
            "cross_step_correlation_review",
        ]
        blocked_roles = [
            "certified_root_cause",
            "recipe_change",
            "automatic_lot_hold",
            "equipment_control",
            "process_parameter_update",
            "production_disposition",
        ]
        bin_class = "shadow_analysis_only"
        decision_readiness = "ACTION_INELIGIBLE"

        from ...contracts.input_validation import build_input_validation
        from ...core.functional_yield import build_functional_yield_vector

        tool_log_rows = len(tool_log)
        fail_rate_score = round(1.0 - (fail_dies / max(total_dies, 1)), 3) if total_dies > 0 else 0.5
        drift_health = round(max(0.0, 1.0 - top_conf * 0.8), 3)
        semfab_components = {
            "tool_log_health": drift_health,
            "wafer_yield_health": fail_rate_score,
            "metrology_stability": 0.8 if cd_vals else 0.5,
        }
        fyv = build_functional_yield_vector(
            domain="semiconductor",
            case_id=case_id,
            asset_id=asset_id,
            component_scores=semfab_components,
            role_scores={r: 1.0 for r in remaining_roles},
            evidence_confidence=top_conf,
            missing_inputs=[],
            score_kind="heuristic",
            model_limitations=["shadow_analysis_only", "no_process_control_authority"],
            domain_adapter="semiconductor_fab",
        )
        state.metrics["functional_yield_vector"] = fyv

        semfab_passed = (tool_log_rows > 0) or (total_dies > 0) or (len(metrology) > 0)
        input_validation = build_input_validation(
            case_id=case_id,
            domain_pack="semiconductor",
            domain_adapter="semiconductor_fab",
            status="PASSED" if semfab_passed else "FAILED",
            data_level="MINIMUM_RUNNABLE" if semfab_passed else "EMPTY",
            found_inputs=(
                (["tool_log"] if tool_log_rows > 0 else []) +
                (["wafer_map"] if total_dies > 0 else []) +
                (["metrology"] if len(metrology) > 0 else [])
            ),
            missing_inputs=[],
            record_counts={
                "tool_log_rows": tool_log_rows,
                "wafer_dies": total_dies,
                "metrology_rows": len(metrology),
            },
            blocking_reasons=[] if semfab_passed else [
                "no tool_log_rows, wafer_dies, or metrology_rows present"
            ],
        )

        # --- Recovery candidates ---
        recovery = [
            RecoveryCandidate(
                action="recommend_chamber_inspection",
                expected_benefit="identify and correct chamber condition drift — review for process engineer",
                risk="low",
                steps=[
                    "prepare chamber inspection review request",
                    "schedule PM window review with maintenance team",
                    "flag seasoning wafer run as pending engineer review",
                ],
            ),
            RecoveryCandidate(
                action="request_chamber_clean_log",
                expected_benefit="correlate drift timeline with maintenance history",
                risk="low",
                steps=[
                    "request chamber clean log from MES for review",
                    "prepare drift timeline comparison for process engineer",
                ],
            ),
            RecoveryCandidate(
                action="recommend_lot_hold_review",
                expected_benefit="prevent further affected wafers from proceeding — hold for engineer review",
                risk="medium",
                steps=[
                    "prepare lot hold review request",
                    "flag lot in MES for process engineer notification",
                ],
            ),
        ]

        # --- Time alignment report ---
        time_alignment = self._build_time_alignment(tool_log, metrology, test_result)

        # --- Evidence graph ---
        evidence_graph = self._build_evidence_graph(evidence_objects, rca_list, recovery)

        return {
            "case_id": case_id,
            "domain": DOMAIN,
            "state": state,
            "evidence_pack": pack,
            "ooda_frame": ooda,
            "recovery_candidates": recovery,
            "time_alignment_report": time_alignment,
            "evidence_graph": evidence_graph,
            "remaining_roles": remaining_roles,
            "blocked_roles": blocked_roles,
            "bin_class": bin_class,
            "decision_readiness": decision_readiness,
            "input_validation": input_validation,
            "confidence_report": confidence_report,
            "process_drift_report": process_drift_report,
        }

    def _build_time_alignment(self, tool_log: list, metrology: list, test_result: list) -> dict:
        """Build a time alignment quality report across data sources."""
        def _ts_range(rows, key="timestamp"):
            vals = [r.get(key, "") for r in rows if r.get(key)]
            if not vals:
                return None, None
            return min(vals), max(vals)

        tl_start, tl_end = _ts_range(tool_log)
        me_start, me_end = _ts_range(metrology)
        tr_start, tr_end = _ts_range(test_result)

        warnings = []
        if not tl_start:
            warnings.append("tool_log has no timestamp data")
        if not me_start:
            warnings.append("metrology has no timestamp data — cross-step correlation limited")
        if not tr_start:
            warnings.append("test_result has no timestamp data")

        alignment = "good"
        if not me_start or not tl_start:
            alignment = "poor"
        elif not tr_start:
            alignment = "medium"

        return {
            "schema": "yieldos.semfab.time_alignment.v1",
            "tool_log_range": f"{tl_start} to {tl_end}" if tl_start else None,
            "metrology_range": f"{me_start} to {me_end}" if me_start else None,
            "test_result_range": f"{tr_start} to {tr_end}" if tr_start else None,
            "alignment_quality": alignment,
            "warnings": warnings,
        }

    def _build_evidence_graph(self, evidence_objects, rca_list, recovery_candidates) -> dict:
        """Build a simple JSON evidence relationship graph."""
        nodes = []
        edges = []

        # Tool node
        nodes.append({"id": "source:tool_log", "type": "source"})
        nodes.append({"id": "source:wafer_map", "type": "source"})
        nodes.append({"id": "source:metrology", "type": "source"})

        for ev in evidence_objects:
            ev_id = ev.evidence_id if hasattr(ev, "evidence_id") else ev.get("evidence_id", "")
            source = ev.source if hasattr(ev, "source") else ev.get("source", "unknown")
            ev_node_id = f"evidence:{ev_id}"
            nodes.append({"id": ev_node_id, "type": "evidence"})
            edges.append({"from": f"source:{source}", "to": ev_node_id, "relation": "produced"})

        for rca in rca_list:
            cand = rca.candidate if hasattr(rca, "candidate") else rca.get("candidate", "unknown")
            rca_node_id = f"rca:{cand[:40].replace(' ', '_')}"
            nodes.append({"id": rca_node_id, "type": "root_cause_candidate"})
            for ev_id in (rca.supporting_evidence if hasattr(rca, "supporting_evidence") else rca.get("supporting_evidence", [])):
                edges.append({"from": f"evidence:{ev_id}", "to": rca_node_id, "relation": "supports"})

        for rec in recovery_candidates:
            action = rec.action if hasattr(rec, "action") else rec.get("action", "unknown")
            rec_node_id = f"recovery:{action}"
            nodes.append({"id": rec_node_id, "type": "recovery_candidate"})

        return {
            "schema": "yieldos.evidence_graph.v1",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
        }
