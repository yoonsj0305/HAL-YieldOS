"""
Cross-step RCA: correlate tool drift signals with downstream metrology and yield.
Returns a ranked evidence graph linking etch drift → CD shift → bin fails.

Guard limits (v2.2.0):
  MAX_STEPS     = 50   — max drift_events processed
  MAX_FEATURES  = 100  — max metrology / wafer_map rows processed
  TOP_K         = 10   — max correlation hits returned
  MIN_SUPPORT   = 3    — minimum rows required for correlation
"""
from __future__ import annotations

import statistics
from typing import List, Tuple

MAX_STEPS = 50
MAX_FEATURES = 100
TOP_K = 10
MIN_SUPPORT = 3


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def correlate_drift_to_metrology(
    drift_events: List[dict],
    metrology: List[dict],
    affected_lots: List[str],
    _truncation_warnings: List[str] | None = None,
) -> List[dict]:
    """
    Check if lots affected by tool drift show CD shift in metrology.
    Returns list of correlation hits (at most TOP_K).
    Guard limits: MAX_STEPS drift_events, MAX_FEATURES metrology rows, MIN_SUPPORT minimum rows.
    """
    if not drift_events or not metrology:
        return []

    # Apply guard limits
    if len(drift_events) > MAX_STEPS:
        if _truncation_warnings is not None:
            _truncation_warnings.append(
                f"drift_events truncated from {len(drift_events)} to {MAX_STEPS} (MAX_STEPS guard)"
            )
        drift_events = drift_events[:MAX_STEPS]
    if len(metrology) > MAX_FEATURES:
        if _truncation_warnings is not None:
            _truncation_warnings.append(
                f"metrology truncated from {len(metrology)} to {MAX_FEATURES} (MAX_FEATURES guard)"
            )
        metrology = metrology[:MAX_FEATURES]

    affected_set = set(affected_lots)
    affected_cd = [_safe_float(r.get("cd_nm")) for r in metrology if r.get("lot_id") in affected_set]
    clean_cd = [_safe_float(r.get("cd_nm")) for r in metrology if r.get("lot_id") not in affected_set]

    if len(affected_cd) < MIN_SUPPORT or len(clean_cd) < MIN_SUPPORT:
        return []

    aff_mean = statistics.mean(affected_cd)
    clean_mean = statistics.mean(clean_cd)
    cd_delta = abs(aff_mean - clean_mean)
    target = _safe_float(metrology[0].get("target_cd_nm", clean_mean))
    offset_from_target = abs(aff_mean - target)

    if cd_delta < 0.5:
        return []

    confidence = min(0.92, 0.5 + cd_delta * 0.12)
    return [{
        "correlation": "drift_to_cd_shift",
        "cd_clean_mean": round(clean_mean, 2),
        "cd_affected_mean": round(aff_mean, 2),
        "cd_delta_nm": round(cd_delta, 2),
        "offset_from_target_nm": round(offset_from_target, 2),
        "affected_lots": list(affected_set),
        "confidence": round(confidence, 3),
        "interpretation": (
            f"CD in drift-affected lots shifted {cd_delta:.1f}nm vs clean lots "
            f"(target offset: {offset_from_target:.1f}nm)"
        ),
    }][:TOP_K]


def correlate_drift_to_yield(
    drift_events: List[dict],
    wafer_map: List[dict],
    affected_lots: List[str],
    _truncation_warnings: List[str] | None = None,
) -> List[dict]:
    """
    Check if lots affected by drift show higher bin fail rate.
    Returns correlation dict if significant (at most TOP_K).
    Guard limits: MAX_STEPS drift_events, MAX_FEATURES wafer_map rows, MIN_SUPPORT minimum rows.
    """
    if not drift_events or not wafer_map:
        return []

    # Apply guard limits
    if len(drift_events) > MAX_STEPS:
        if _truncation_warnings is not None:
            _truncation_warnings.append(
                f"drift_events truncated from {len(drift_events)} to {MAX_STEPS} (MAX_STEPS guard)"
            )
        drift_events = drift_events[:MAX_STEPS]
    if len(wafer_map) > MAX_FEATURES:
        if _truncation_warnings is not None:
            _truncation_warnings.append(
                f"wafer_map truncated from {len(wafer_map)} to {MAX_FEATURES} (MAX_FEATURES guard)"
            )
        wafer_map = wafer_map[:MAX_FEATURES]

    affected_set = set(affected_lots)

    def fail_rate(rows: List[dict]) -> Tuple[int, int, float]:
        total = len(rows)
        fails = sum(1 for r in rows if r.get("bin_result", "").upper() in ("FAIL", "F"))
        return fails, total, fails / max(total, 1)

    aff_rows = [r for r in wafer_map if r.get("lot_id") in affected_set]
    clean_rows = [r for r in wafer_map if r.get("lot_id") not in affected_set]

    if len(aff_rows) < MIN_SUPPORT or not clean_rows:
        return []

    aff_fails, aff_total, aff_rate = fail_rate(aff_rows)
    clean_fails, clean_total, clean_rate = fail_rate(clean_rows)
    relative_increase = (aff_rate - clean_rate) / max(clean_rate, 0.001)

    if relative_increase < 0.3:
        return []

    confidence = min(0.93, 0.45 + relative_increase * 0.4)
    return [{
        "correlation": "drift_to_yield_loss",
        "clean_fail_rate": round(clean_rate, 4),
        "affected_fail_rate": round(aff_rate, 4),
        "relative_increase": round(relative_increase, 3),
        "affected_dies": aff_fails,
        "total_affected_dies": aff_total,
        "confidence": round(confidence, 3),
        "interpretation": (
            f"Fail rate in drift-affected lots {aff_rate:.1%} vs {clean_rate:.1%} clean "
            f"(+{relative_increase:.0%} relative increase)"
        ),
    }][:TOP_K]


def build_cross_step_graph(
    drift_events: List[dict],
    affected_lots: List[str],
    metrology: List[dict],
    wafer_map: List[dict],
) -> dict:
    """
    Returns a cross-step evidence graph:
    tool_drift -> cd_shift -> yield_loss

    Guard limits (MAX_STEPS=50, MAX_FEATURES=100, TOP_K=10, MIN_SUPPORT=3) are
    enforced inside correlate_* functions. Truncation warnings are surfaced here.
    """
    truncation_warnings: List[str] = []
    cd_corr = correlate_drift_to_metrology(
        drift_events, metrology, affected_lots, _truncation_warnings=truncation_warnings
    )
    yield_corr = correlate_drift_to_yield(
        drift_events, wafer_map, affected_lots, _truncation_warnings=truncation_warnings
    )

    chain_confidence = 0.0
    if drift_events:
        chain_confidence = drift_events[0].get("confidence", 0.0)
        if cd_corr:
            chain_confidence = (chain_confidence + cd_corr[0]["confidence"]) / 2
        if yield_corr:
            chain_confidence = (chain_confidence + yield_corr[0]["confidence"]) / 2

    result = {
        "tool_drift": drift_events[:3],
        "cd_shift": cd_corr,
        "yield_loss": yield_corr,
        "chain_confidence": round(chain_confidence, 3),
        "chain_interpretation": _build_interpretation(drift_events, cd_corr, yield_corr),
    }
    if truncation_warnings:
        result["truncation_warnings"] = truncation_warnings
    return result


def _build_interpretation(drift_events, cd_corr, yield_corr) -> str:
    parts = []
    if drift_events:
        top = drift_events[0]
        parts.append(f"Tool drift at {top.get('step')} ({top.get('metric')})")
    if cd_corr:
        parts.append(f"→ CD shift {cd_corr[0].get('cd_delta_nm'):.1f}nm in affected lots")
    if yield_corr:
        parts.append(f"→ Yield loss +{yield_corr[0].get('relative_increase', 0):.0%}")
    if not parts:
        return "No cross-step correlation detected"
    return " ".join(parts) + "."
