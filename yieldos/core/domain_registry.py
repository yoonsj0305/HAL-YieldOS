"""
DomainRegistry — v2.2.0

Central registry for DomainPack implementations.
Decouples callers from import paths; enables runtime plugin-style extension.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .domain_pack import DomainPack

_REGISTRY: Dict[str, DomainPack] = {}


def register(domain_name: str, pack: DomainPack) -> None:
    """Register a DomainPack under a canonical domain name."""
    if not domain_name:
        raise ValueError("domain_name must be non-empty")
    _REGISTRY[domain_name] = pack


def get(domain_name: str) -> Optional[DomainPack]:
    """Return the registered DomainPack for domain_name, or None."""
    return _REGISTRY.get(domain_name)


def list_domains() -> List[str]:
    """Return all registered canonical domain names."""
    return list(_REGISTRY.keys())


def clear() -> None:
    """Clear all registrations (for test isolation only)."""
    _REGISTRY.clear()
