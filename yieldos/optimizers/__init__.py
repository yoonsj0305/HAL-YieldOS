"""
YieldOS Optimizer Layer — optional, recommendation-only.

Optimizers rank and select recovery candidates.
They do NOT produce hardware commands.

Available backends:
  greedy      — pure Python, always available (default)
  sqbm        — Simulated Bifurcation Machine (requires hal-yieldos[sqbm])

Usage:
  from yieldos.optimizers import get_optimizer
  opt = get_optimizer("greedy")
  result = opt.optimize(problem)
"""

from .base import OptimizationResult, OptimizerBackend
from .greedy import GreedyOptimizer


def get_optimizer(name: str, fallback: bool = True) -> OptimizerBackend:
    """
    Return an optimizer backend by name.

    Parameters
    ----------
    name     : 'greedy' | 'sqbm'
    fallback : if True and sqbm is unavailable, silently use greedy

    Returns
    -------
    OptimizerBackend instance

    Raises
    ------
    ImportError  — if sqbm requested, not installed, and fallback=False
    ValueError   — if name is unknown
    """
    if name == "greedy":
        return GreedyOptimizer()
    if name == "sqbm":
        from .sqbm_optional import SQBMOptimizer
        opt = SQBMOptimizer()
        if not opt.is_available():
            if fallback:
                return GreedyOptimizer()
            raise ImportError(
                "SQBM backend is not installed. "
                "Install with: pip install hal-yieldos[sqbm]\n"
                "Or use optimizer='greedy' (no extra dependencies)."
            )
        return opt
    raise ValueError(f"Unknown optimizer '{name}'. Choose: greedy, sqbm")


__all__ = [
    "OptimizationResult",
    "OptimizerBackend",
    "GreedyOptimizer",
    "get_optimizer",
]
