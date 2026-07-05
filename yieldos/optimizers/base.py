"""
YieldOS Optimizer Base — abstract interface for all optimizer backends.

All OptimizationResult objects must have hardware_execution_enabled=False.
Optimizers produce candidate rankings only. They do not execute anything.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class OptimizationResult:
    """
    Output of an optimizer backend.

    Invariant: hardware_execution_enabled is ALWAYS False.
    Optimizers rank candidates — they do not execute actions.
    """
    backend: str
    objective_value: float
    selected_indices: List[int]
    metadata: Dict[str, Any] = field(default_factory=dict)
    hardware_execution_enabled: bool = False
    fallback: bool = False
    fallback_reason: str = ""

    def __post_init__(self):
        if self.hardware_execution_enabled:
            raise ValueError(
                "OptimizationResult.hardware_execution_enabled must be False. "
                "Optimizers rank candidates only — they never execute hardware."
            )


class OptimizerBackend(ABC):
    """Abstract base class for all YieldOS optimizer backends."""

    name: str = "base"

    @abstractmethod
    def optimize(self, problem: Dict[str, Any]) -> OptimizationResult:
        """
        Solve the optimization problem and return a ranked candidate list.

        Parameters
        ----------
        problem : dict with keys:
            candidates   : List[dict] — each has {action, risk, benefit_score}
            max_select   : int (optional) — max candidates to select

        Returns
        -------
        OptimizationResult with hardware_execution_enabled=False
        """
        raise NotImplementedError

    def is_available(self) -> bool:
        """Return True if this backend is ready to use (dependencies met)."""
        return True
