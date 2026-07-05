from __future__ import annotations

import statistics
from typing import Dict, List


def _safe_float(v: str, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def detect_metric_drift(
    rows: List[dict],
    metric_col: str,
    step_col: str = "process_step",
    threshold_sigma: float = 2.0,
) -> List[dict]:
    """
    Scan each process step for baseline shift in a metric column.
    Returns list of drift events: {step, metric, mean, baseline, sigma, shift_ratio, confidence}.
    """
    by_step: Dict[str, List[float]] = {}
    for row in rows:
        step = row.get(step_col, "UNKNOWN")
        val = _safe_float(row.get(metric_col, ""))
        if val != 0.0:
            by_step.setdefault(step, []).append(val)

    if not by_step:
        return []

    all_vals = [v for vals in by_step.values() for v in vals]
    if len(all_vals) < 4:
        return []

    global_mean = statistics.mean(all_vals)
    global_std = statistics.stdev(all_vals) if len(all_vals) > 1 else 1e-9

    events = []
    for step, vals in by_step.items():
        if len(vals) < 2:
            continue
        step_mean = statistics.mean(vals)
        deviation = abs(step_mean - global_mean)
        sigma_count = deviation / max(global_std, 1e-9)
        if sigma_count >= threshold_sigma:
            shift_ratio = deviation / max(abs(global_mean), 1e-9)
            confidence = min(0.99, 0.5 + sigma_count * 0.12)
            events.append({
                "step": step,
                "metric": metric_col,
                "step_mean": round(step_mean, 4),
                "global_mean": round(global_mean, 4),
                "sigma_count": round(sigma_count, 2),
                "shift_ratio": round(shift_ratio, 4),
                "confidence": round(confidence, 3),
            })
    return sorted(events, key=lambda x: x["confidence"], reverse=True)


def find_affected_wafers(
    rows: List[dict],
    step: str,
    step_col: str = "process_step",
    wafer_col: str = "wafer_id",
) -> List[str]:
    return list({
        row[wafer_col] for row in rows
        if row.get(step_col) == step and row.get(wafer_col)
    })


def find_affected_lots(
    rows: List[dict],
    wafer_ids: List[str],
    wafer_col: str = "wafer_id",
    lot_col: str = "lot_id",
) -> List[str]:
    wset = set(wafer_ids)
    return list({
        row[lot_col] for row in rows
        if row.get(wafer_col) in wset and row.get(lot_col)
    })
