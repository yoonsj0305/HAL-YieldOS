from __future__ import annotations

from typing import Optional


def retention_shortfall(retention_hours: Optional[float],
                        min_retention_hours: float) -> Optional[float]:
    """Hours below minimum retention spec. None if data unavailable. 0.0 means spec met."""
    if retention_hours is None:
        return None
    return max(0.0, min_retention_hours - retention_hours)


def retention_evidence_confidence(shortfall: Optional[float],
                                  min_retention_hours: float) -> float:
    """Confidence that a retention failure is evidenced (0.0 to 1.0)."""
    if shortfall is None or shortfall <= 0:
        return 0.0
    return min(0.88, 0.40 + (shortfall / max(min_retention_hours, 1.0)) * 0.48)
