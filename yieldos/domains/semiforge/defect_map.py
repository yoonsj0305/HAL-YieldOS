from __future__ import annotations

import random
from typing import List


def generate_iid_defects(rows: int, cols: int, defect_rate: float, seed: int = 42) -> List[List[int]]:
    """Uniformly random (i.i.d.) defect map: 1 = defective cell."""
    rng = random.Random(seed)
    return [
        [1 if rng.random() < defect_rate else 0 for _ in range(cols)]
        for _ in range(rows)
    ]


def generate_clustered_defects(
    rows: int,
    cols: int,
    defect_rate: float,
    clustering_factor: float = 3.0,
    seed: int = 42,
) -> List[List[int]]:
    """
    Clustered defect model using negative-binomial-inspired spreading.
    clustering_factor > 1 increases spatial correlation.
    """
    rng = random.Random(seed)
    grid = [[0] * cols for _ in range(rows)]
    total_cells = rows * cols
    target_defects = int(total_cells * defect_rate)

    # Place cluster seeds
    n_seeds = max(1, int(target_defects / max(clustering_factor, 1)))
    defects_placed = 0

    for _ in range(n_seeds):
        if defects_placed >= target_defects:
            break
        r0 = rng.randint(0, rows - 1)
        c0 = rng.randint(0, cols - 1)
        # Spread defects around seed
        cluster_size = max(1, int(rng.gauss(clustering_factor, clustering_factor * 0.3)))
        for _ in range(cluster_size):
            if defects_placed >= target_defects:
                break
            dr = int(rng.gauss(0, max(1, clustering_factor * 0.5)))
            dc = int(rng.gauss(0, max(1, clustering_factor * 0.5)))
            r = max(0, min(rows - 1, r0 + dr))
            c = max(0, min(cols - 1, c0 + dc))
            if grid[r][c] == 0:
                grid[r][c] = 1
                defects_placed += 1

    return grid


def defect_count(grid: List[List[int]]) -> int:
    return sum(cell for row in grid for cell in row)


def actual_defect_rate(grid: List[List[int]]) -> float:
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    if rows * cols == 0:
        return 0.0
    return defect_count(grid) / (rows * cols)
