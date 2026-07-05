"""
Functional Yield Vector Core — v2.2.0

Provides deterministic, penalty-aware functional yield scoring for all
YieldOS domains. All scores are 0.0–1.0 (higher = healthier).

Safety invariant: this module never enables hardware execution and never
certifies a root cause. It produces candidate estimates for human review.
"""
from __future__ import annotations

from typing import Dict, List

SCHEMA = "hal.yieldos.functional_yield_vector.v1"
CANNOT_CERTIFY_SAFETY = "This score is a candidate estimate. Cannot certify safety or authorize hardware action."
CANNOT_AUTHORIZE_HW = "Human review required before any operational decision."


def clamp01(value: float) -> float:
    """Clamp value to [0.0, 1.0]."""
    return max(0.0, min(1.0, float(value)))


def weighted_mean(values: List[float], weights: List[float]) -> float:
    """Weighted mean of values. Falls back to simple mean if weights sum to 0."""
    if not values:
        return 0.0
    total_w = sum(weights)
    if total_w <= 0:
        return sum(values) / len(values)
    return sum(v * w for v, w in zip(values, weights)) / total_w


def missing_data_penalty(missing_inputs: List[str], max_penalty: float = 0.3) -> float:
    """
    Returns a penalty in [0.0, max_penalty] proportional to number of missing inputs.
    Each missing input contributes max_penalty/5 up to max_penalty.
    """
    if not missing_inputs:
        return 0.0
    per_item = max_penalty / 5.0
    return clamp01(min(len(missing_inputs) * per_item, max_penalty))


def build_functional_yield_vector(
    *,
    domain: str,
    case_id: str,
    asset_id: str,
    component_scores: Dict[str, float],
    role_scores: Dict[str, float],
    evidence_confidence: float,
    missing_inputs: List[str],
    score_kind: str,
    recovery_bonus: float = 0.0,
    model_limitations: List[str],
    domain_adapter: str = "",
    override_yield_score: float = -1.0,
) -> dict:
    """
    Build a Functional Yield Vector dict for inclusion in StateSnapshot.metrics
    and the functional_yield_scorecard output.

    Parameters
    ----------
    domain             : canonical domain name (robot/space/semiconductor/semiforge)
    case_id            : unique case identifier
    asset_id           : asset being analyzed
    component_scores   : per-component health scores (0.0–1.0)
    role_scores        : per-role availability scores (0.0–1.0)
    evidence_confidence: overall evidence confidence (0.0–1.0)
    missing_inputs     : list of missing input signals/files
    score_kind         : 'heuristic' | 'simulation' | 'partial'
    recovery_bonus     : optional positive adjustment for available recovery paths
    model_limitations  : list of model limitation strings

    Returns
    -------
    dict — structured FYV ready to store in state.metrics["functional_yield_vector"]
    """
    evidence_confidence = clamp01(evidence_confidence)
    recovery_bonus = clamp01(recovery_bonus)

    # Clamp all component and role scores
    comp_clamped = {k: clamp01(v) for k, v in component_scores.items()}
    role_clamped = {k: clamp01(v) for k, v in role_scores.items()}

    # Compute base composite score
    all_scores = list(comp_clamped.values()) + list(role_clamped.values())
    weights = [1.0] * len(all_scores)
    base_score = weighted_mean(all_scores, weights) if all_scores else evidence_confidence

    # Apply missing data penalty
    penalty = missing_data_penalty(missing_inputs)

    # Compute final score — use override if provided (e.g., domain has exact FY value)
    if override_yield_score >= 0.0:
        raw = clamp01(override_yield_score)
        calculation = "domain_specific_functional_yield_override"
    else:
        raw = clamp01(base_score * evidence_confidence - penalty + recovery_bonus * 0.1)
        calculation = (
            "weighted_mean(component_scores + role_scores) * evidence_confidence "
            "- missing_data_penalty + recovery_bonus*0.1"
        )
    false_confidence_penalty = penalty

    remaining_roles = [k for k, v in role_clamped.items() if v >= 0.5]
    blocked_roles = [k for k, v in role_clamped.items() if v < 0.5]

    return {
        "schema": SCHEMA,
        "case_id": case_id,
        "domain": domain,
        "domain_pack": domain,
        "domain_adapter": domain_adapter or domain,
        "asset_id": asset_id,
        "score_kind": score_kind,
        "functional_yield_score": round(raw, 4),
        "functional_retention": round(raw, 4),
        "degradation_score": round(1.0 - raw, 4),
        "recovery_potential": round(min(0.9, raw + 0.2), 3),
        "base_composite_score": round(base_score, 4),
        "evidence_confidence": round(evidence_confidence, 4),
        "missing_data_penalty": round(false_confidence_penalty, 4),
        "false_confidence_penalty": round(false_confidence_penalty, 4),
        "recovery_bonus": round(recovery_bonus, 4),
        "component_scores": comp_clamped,
        "role_scores": role_clamped,
        "remaining_roles": remaining_roles,
        "blocked_roles": blocked_roles,
        "missing_inputs": missing_inputs,
        "model_limitations": model_limitations,
        "calculation_basis": calculation,
        "cannot_certify_safety": CANNOT_CERTIFY_SAFETY,
        "cannot_authorize_hardware_action": CANNOT_AUTHORIZE_HW,
    }
