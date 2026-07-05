from __future__ import annotations

from typing import Optional


def pe_cycle_ratio(pe_cycles: Optional[float], max_pe_cycles: Optional[float]) -> Optional[float]:
    """Fraction of PE cycle budget consumed. None if data is unavailable."""
    if pe_cycles is None or max_pe_cycles is None or max_pe_cycles <= 0:
        return None
    return round(pe_cycles / max_pe_cycles, 4)


def endurance_evidence_confidence(ratio: Optional[float], warn_ratio: float = 0.80) -> float:
    """Confidence that endurance degradation is evidenced (0.0 to 1.0)."""
    if ratio is None:
        return 0.0
    if ratio >= 0.95:
        return 0.88
    if ratio >= warn_ratio:
        slope = (ratio - warn_ratio) / max(0.95 - warn_ratio, 1e-6)
        return round(0.50 + slope * 0.38, 3)
    return 0.10
