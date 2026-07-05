"""
DomainPack Protocol — v2.2.0

Defines the structural interface all domain analyzers/simulators must satisfy.
Not a base class — uses duck typing. Register implementations via domain_registry.
"""
from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class DomainPack(Protocol):
    """
    Protocol that every YieldOS domain analyzer must satisfy.

    A domain_pack is registered in DomainRegistry under its canonical name
    (robot | space | semiconductor | semiforge).
    """

    @property
    def domain(self) -> str:
        """Canonical domain name."""
        ...

    def domain_name(self) -> str:
        """Canonical domain name (method form for backward compat)."""
        ...

    def analyze(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Run analysis on domain data.
        Must return a dict with keys: state, evidence_pack, ooda_frame, recovery_candidates.
        Hardware execution is never enabled. Output is always recommendation_only.
        """
        ...
