from __future__ import annotations


def ecc_evidence_confidence(corrected_count: int, uncorrectable_count: int,
                             corrected_warn_threshold: float = 100.0) -> float:
    """
    Confidence that ECC evidence indicates a real problem (0.0 to 1.0).
    uncorrectable errors are near-certain failures.
    """
    if uncorrectable_count >= 1:
        return 0.97
    if corrected_count == 0:
        return 0.05
    ratio = min(corrected_count / max(corrected_warn_threshold, 1.0), 2.0)
    return min(0.88, 0.30 + ratio * 0.29)


def ecc_summary(rows: list) -> dict:
    """Aggregate ECC metrics across block rows."""
    total_corrected = 0
    total_uncorrectable = 0
    max_corrected_single = 0
    for row in rows:
        c = int(float(row.get("corrected_error_count", 0) or 0))
        u = int(float(row.get("uncorrectable_error_count", 0) or 0))
        total_corrected += c
        total_uncorrectable += u
        max_corrected_single = max(max_corrected_single, c)
    return {
        "total_corrected_errors": total_corrected,
        "total_uncorrectable_errors": total_uncorrectable,
        "max_corrected_single_block": max_corrected_single,
    }
