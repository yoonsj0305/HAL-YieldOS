"""
SemiForge sweep: Y_func / C_eff vs defect_rate curve.
Runs Monte Carlo at each defect_rate point and emits CSV + ASCII plot.
"""
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import List

from .defect_map import generate_clustered_defects, generate_iid_defects
from .functional_yield import compute_c_eff, compute_r_alg, compute_r_conn, compute_y_func
from .percolation import percolation_connectivity


def run_sweep(
    array_rows: int = 64,
    array_cols: int = 64,
    defect_rates: List[float] | None = None,
    distribution: str = "iid",
    clustering_factor: float = 3.0,
    baseline_accuracy: float = 0.92,
    c_fab: float = 1.0,
    c_ctrl: float = 0.15,
    c_rec: float = 0.10,
    monte_carlo_runs: int = 30,
    seed: int | None = None,
) -> List[dict]:
    if defect_rates is None:
        defect_rates = [round(i * 0.04, 2) for i in range(11)]  # 0.00 ~ 0.40

    base_seed = seed if seed is not None else 0
    results = []
    for dr in defect_rates:
        r_conn_samples = []
        for run in range(monte_carlo_runs):
            seed = base_seed + run * 13 + int(dr * 1000)
            if distribution == "clustered":
                grid = generate_clustered_defects(array_rows, array_cols, dr, clustering_factor, seed)
            else:
                grid = generate_iid_defects(array_rows, array_cols, dr, seed)
            r_conn_samples.append(percolation_connectivity(grid))

        r_conn_mean = statistics.mean(r_conn_samples)
        r_conn_std = statistics.stdev(r_conn_samples) if len(r_conn_samples) > 1 else 0.0

        damaged_acc = max(0.0, baseline_accuracy * (1 - dr * 2.5))
        defect_loss = baseline_accuracy - damaged_acc
        recovery_ratio = min(0.85, r_conn_mean * 0.9)
        recovered_acc = min(baseline_accuracy, damaged_acc + defect_loss * recovery_ratio)

        r_conn = compute_r_conn(r_conn_mean)
        r_alg = compute_r_alg(baseline_accuracy, damaged_acc, recovered_acc)
        y_func = compute_y_func(r_conn, r_alg)
        c_eff = compute_c_eff(c_fab, c_ctrl, c_rec, y_func)

        results.append({
            "defect_rate": dr,
            "distribution": distribution,
            "r_conn": r_conn,
            "r_conn_std": round(r_conn_std, 4),
            "r_alg": r_alg,
            "y_func": y_func,
            "damaged_accuracy": round(damaged_acc, 4),
            "recovered_accuracy": round(recovered_acc, 4),
            "c_eff": round(c_eff, 4) if c_eff != float("inf") else None,
            "mc_runs": monte_carlo_runs,
        })
    return results


def write_sweep_csv(results: List[dict], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)


def write_sweep_json(results: List[dict], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps({"schema": "yieldos.semiforge.sweep.v1", "points": results},
                   ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def ascii_plot(results: List[dict], metric: str = "y_func", width: int = 50) -> str:
    vals = [r[metric] for r in results if r[metric] is not None]
    if not vals:
        return ""
    vmin, vmax = 0.0, 1.0
    lines = [f"\n  {metric} vs defect_rate  ({results[0]['distribution']})\n"]
    lines.append(f"  {'dr':>5}  {'bar':<{width}}  {metric}")
    lines.append("  " + "-" * (width + 20))
    for r in results:
        v = r.get(metric)
        if v is None:
            lines.append(f"  {r['defect_rate']:>5.2f}  inf")
            continue
        filled = int((v - vmin) / max(vmax - vmin, 1e-9) * width)
        bar = "#" * filled + "-" * (width - filled)
        lines.append(f"  {r['defect_rate']:>5.2f}  {bar}  {v:.4f}")
    lines.append("")
    return "\n".join(lines)
