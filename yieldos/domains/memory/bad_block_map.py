from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BlockClassification:
    block_id: str
    block_size_gb: float
    classification: str  # safe | at_risk | approximate_cache | read_only_archive | discard
    reasons: List[str] = field(default_factory=list)

    @property
    def is_discard(self) -> bool:
        return self.classification == "discard"

    @property
    def is_at_risk(self) -> bool:
        return self.classification in ("at_risk", "approximate_cache", "read_only_archive")


def _opt_float(row: dict, key: str) -> Optional[float]:
    v = row.get(key)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def classify_block(row: dict, policy: dict) -> BlockClassification:
    """
    Classify a single block into: safe | read_only_archive | approximate_cache | at_risk | discard.

    Priority: discard > read_only_archive | approximate_cache > at_risk > safe
    """
    block_id = row.get("block_id", "unknown")
    block_size_gb = float(_opt_float(row, "block_size_gb") or 1.0)
    reasons: List[str] = []

    is_factory_bad = str(row.get("is_factory_bad", "false")).lower() in ("true", "1", "yes")
    is_runtime_bad = str(row.get("is_runtime_bad", "false")).lower() in ("true", "1", "yes")
    uncorrectable = int(_opt_float(row, "uncorrectable_error_count") or 0)
    corrected = int(_opt_float(row, "corrected_error_count") or 0)
    pe_cycles = _opt_float(row, "pe_cycles")
    max_pe_cycles = _opt_float(row, "max_pe_cycles")
    retention_hours = _opt_float(row, "retention_hours")
    temp_c = _opt_float(row, "temperature_C")

    ecc_policy = policy.get("ecc_policy", {})
    endurance_policy = policy.get("endurance_policy", {})
    retention_policy = policy.get("retention_policy", {})

    corrected_warn = float(ecc_policy.get("corrected_error_warning_threshold", 100))
    uncorrectable_fail = int(ecc_policy.get("uncorrectable_error_fail_threshold", 1))
    pe_warn_ratio = float(endurance_policy.get("pe_cycle_warning_ratio", 0.80))
    min_retention = float(retention_policy.get("min_retention_hours", 72))

    # --- Discard conditions (hard failures) ---
    if is_factory_bad:
        reasons.append("is_factory_bad=true")
    if is_runtime_bad:
        reasons.append("is_runtime_bad=true")
    if uncorrectable >= uncorrectable_fail:
        reasons.append(f"uncorrectable_error_count={uncorrectable}")

    if is_factory_bad or is_runtime_bad or uncorrectable >= uncorrectable_fail:
        return BlockClassification(block_id=block_id, block_size_gb=block_size_gb,
                                   classification="discard", reasons=reasons)

    # --- At-risk signals ---
    at_risk_reasons: List[str] = []
    has_high_corrected = corrected >= corrected_warn
    has_low_retention = retention_hours is not None and retention_hours < min_retention
    has_high_temp = temp_c is not None and temp_c > 85.0

    pe_ratio: Optional[float] = None
    has_high_pe = False
    if pe_cycles is not None and max_pe_cycles is not None and max_pe_cycles > 0:
        pe_ratio = pe_cycles / max_pe_cycles
        has_high_pe = pe_ratio >= pe_warn_ratio

    if has_high_corrected:
        at_risk_reasons.append(f"corrected_errors={corrected} >= warn_threshold={int(corrected_warn)}")
    if has_high_pe:
        at_risk_reasons.append(f"pe_ratio={pe_ratio:.3f} >= warn_ratio={pe_warn_ratio}")
    if has_low_retention:
        at_risk_reasons.append(f"retention_hours={retention_hours} < min={min_retention}")
    if has_high_temp:
        at_risk_reasons.append(f"temperature_C={temp_c} > 85.0")

    if not at_risk_reasons:
        return BlockClassification(block_id=block_id, block_size_gb=block_size_gb,
                                   classification="safe", reasons=[])

    # --- Classify at-risk subtypes ---
    # read_only_archive: write endurance degraded, but ECC/retention still acceptable
    if has_high_pe and not has_high_corrected and not has_low_retention and uncorrectable == 0:
        return BlockClassification(block_id=block_id, block_size_gb=block_size_gb,
                                   classification="read_only_archive", reasons=at_risk_reasons)

    # approximate_cache: elevated corrected errors or poor retention (recomputable data only)
    if has_high_corrected or has_low_retention:
        return BlockClassification(block_id=block_id, block_size_gb=block_size_gb,
                                   classification="approximate_cache", reasons=at_risk_reasons)

    # Generic at_risk (e.g. temperature only)
    return BlockClassification(block_id=block_id, block_size_gb=block_size_gb,
                               classification="at_risk", reasons=at_risk_reasons)


def classify_all_blocks(rows: List[dict], policy: dict) -> List[BlockClassification]:
    return [classify_block(row, policy) for row in rows]
