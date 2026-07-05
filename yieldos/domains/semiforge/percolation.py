from __future__ import annotations

from typing import List, Tuple


def _find(parent: List[int], i: int) -> int:
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def _union(parent: List[int], rank: List[int], a: int, b: int) -> None:
    ra, rb = _find(parent, a), _find(parent, b)
    if ra == rb:
        return
    if rank[ra] < rank[rb]:
        ra, rb = rb, ra
    parent[rb] = ra
    if rank[ra] == rank[rb]:
        rank[ra] += 1


def percolation_connectivity(grid: List[List[int]]) -> float:
    """
    Fraction of non-defective (healthy) cells that belong to the largest
    connected component (4-connectivity). Proxy for routing success r_conn.
    """
    rows = len(grid)
    if rows == 0:
        return 0.0
    cols = len(grid[0])
    total = rows * cols
    healthy = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 0]
    if not healthy:
        return 0.0

    parent = list(range(total))
    rank = [0] * total

    for r, c in healthy:
        cell_idx = r * cols + c
        for dr, dc in [(0, 1), (1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                _union(parent, rank, cell_idx, nr * cols + nc)

    comp_counts: dict = {}
    for r, c in healthy:
        root = _find(parent, r * cols + c)
        comp_counts[root] = comp_counts.get(root, 0) + 1

    largest = max(comp_counts.values()) if comp_counts else 0
    return largest / max(len(healthy), 1)


def routing_success_rate(
    grid: List[List[int]],
    n_routes: int = 200,
    seed: int = 42,
) -> float:
    """
    Monte Carlo: sample random source→sink pairs, check path exists
    using BFS on healthy cells. Returns fraction of routable pairs.
    """
    import random
    from collections import deque

    rows = len(grid)
    if rows == 0:
        return 0.0
    cols = len(grid[0])
    rng = random.Random(seed)
    healthy = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 0]
    if len(healthy) < 2:
        return 0.0

    def bfs_path_exists(src: Tuple[int, int], dst: Tuple[int, int]) -> bool:
        if src == dst:
            return True
        visited = {src}
        queue = deque([src])
        while queue:
            r, c = queue.popleft()
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) == dst:
                    return True
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0 and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return False

    successes = 0
    trials = min(n_routes, len(healthy) * (len(healthy) - 1))
    for _ in range(trials):
        src, dst = rng.sample(healthy, 2)
        if bfs_path_exists(src, dst):
            successes += 1
    return successes / max(trials, 1)
