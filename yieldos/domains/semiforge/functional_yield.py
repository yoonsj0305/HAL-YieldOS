from __future__ import annotations

import math


def compute_r_conn(routing_success: float) -> float:
    """r_conn: fraction of routing paths that succeed (from percolation sim)."""
    return round(max(0.0, min(1.0, routing_success)), 4)


def compute_r_alg(
    baseline_accuracy: float,
    damaged_accuracy: float,
    recovered_accuracy: float,
) -> float:
    """
    r_alg: algorithmic recovery ratio after remapping/retraining.
    ratio = recovered_accuracy / baseline_accuracy (no r_conn factor here —
    r_conn is applied separately in compute_y_func to avoid double-counting).
    """
    if baseline_accuracy <= 0:
        return 0.0
    raw = recovered_accuracy / baseline_accuracy
    return round(max(0.0, min(1.0, raw)), 4)


def compute_y_func(
    r_conn: float,
    r_alg: float,
    y_phys: float = 1.0,
    analog_factor: float = 1.0,
) -> float:
    """
    Y_func = y_phys * r_conn * r_alg * analog_factor.
    Functional yield: fraction of nominal compute capacity recoverable.
    r_conn is applied once here; compute_r_alg must NOT pre-multiply by r_conn.
    """
    raw = y_phys * r_conn * r_alg * analog_factor
    return round(max(0.0, min(1.0, raw)), 4)


def compute_c_eff(
    c_fab: float,
    c_ctrl: float,
    c_rec: float,
    y_func: float,
) -> float:
    """
    C_eff = (C_fab + C_ctrl + C_rec) / Y_func.
    Effective cost per unit of functional compute.
    Returns inf if Y_func = 0.
    """
    if y_func <= 0:
        return float("inf")
    return round((c_fab + c_ctrl + c_rec) / y_func, 4)


def compute_physical_yield(defect_rate: float, dies_per_wafer: int = 1000, defects_per_cm2: float = 0.0) -> float:
    """
    Simplified Poisson yield model: Y_phys = exp(-D0 * A).
    Uses defect_rate as proxy for D0*A.
    """
    return round(math.exp(-defect_rate * dies_per_wafer / max(dies_per_wafer, 1) * dies_per_wafer / 100), 4)
