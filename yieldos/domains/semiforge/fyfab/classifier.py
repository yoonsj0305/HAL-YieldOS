"""FYFab Seed cell classifier — assigns candidate use classes to each cell."""
from __future__ import annotations

from typing import Dict, List

from .schemas import _SAFETY_BLOCK, _SCHEMA_VERSION, CellRecord, DefectRecord

_HIGH_SEVERITY = frozenset({"critical", "high"})
_ALL_SEVERITY = frozenset({"critical", "high", "medium", "low"})

_LOGIC_COND_MIN = 0.78
_LOGIC_LEAK_MAX = 0.20
_LOGIC_STAB_MIN = 0.72

_ROUTING_COND_MIN = 0.72
_ROUTING_LEAK_MAX = 0.28
_ROUTING_STAB_MIN = 0.60

_MEMORY_COND_MIN = 0.62
_MEMORY_MOB_MIN = 0.72
_MEMORY_LEAK_MAX = 0.30

_BLOCK_COND_MAX = 0.25


def classify_cells(
    case_id: str,
    cells: List[CellRecord],
    defects: List[DefectRecord],
) -> dict:
    defect_by_cell: Dict[str, DefectRecord] = {}
    for d in defects:
        if d.cell_id not in defect_by_cell or \
                _severity_rank(d.severity) > _severity_rank(defect_by_cell[d.cell_id].severity):
            defect_by_cell[d.cell_id] = d

    classified = []
    class_counts: Dict[str, int] = {
        "usable_logic_candidate": 0,
        "usable_routing_candidate": 0,
        "usable_memory_candidate": 0,
        "low_confidence_candidate": 0,
        "blocked_defect_cell": 0,
        "discard_candidate": 0,
    }

    for cell in cells:
        d = defect_by_cell.get(cell.cell_id)
        cls, confidence, reasons = _classify_one(cell, d)
        class_counts[cls] = class_counts.get(cls, 0) + 1
        classified.append({
            "cell_id": cell.cell_id,
            "classification": cls,
            "confidence": confidence,
            "reason_codes": reasons,
        })

    return {
        "schema": "hal.yieldos.fyfab.usable_cell_classification.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "class_counts": class_counts,
        "cells": classified,
        "claim_boundary": "candidate_functional_classification_only",
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def _severity_rank(s: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(s, 0)


def _classify_one(cell: CellRecord, defect):
    c = cell.conductivity_score
    m = cell.mobility_score
    leak = cell.leakage_score
    s = cell.stability_score

    # Hard block: critical/high defect or extreme conductivity collapse
    if defect and defect.severity in _HIGH_SEVERITY:
        return "blocked_defect_cell", round(1.0 - defect.confidence * 0.3, 2), [
            f"defect_{defect.defect_type}", f"severity_{defect.severity}"
        ]
    if c < _BLOCK_COND_MAX:
        return "blocked_defect_cell", 0.15, ["extreme_low_conductivity", "below_block_threshold"]

    # Medium/low defect → low confidence
    if defect and defect.severity in ("medium", "low"):
        return "low_confidence_candidate", round(0.35 + (1.0 - defect.confidence) * 0.25, 2), [
            f"defect_{defect.defect_type}", f"severity_{defect.severity}", "requires_reinspection"
        ]

    # Logic: high conductivity, low leakage, stable
    if c >= _LOGIC_COND_MIN and leak <= _LOGIC_LEAK_MAX and s >= _LOGIC_STAB_MIN:
        reasons = []
        if c >= 0.85:
            reasons.append("high_conductivity")
        else:
            reasons.append("acceptable_conductivity")
        if leak <= 0.12:
            reasons.append("very_low_leakage")
        else:
            reasons.append("acceptable_leakage")
        if s >= 0.80:
            reasons.append("highly_stable_region")
        else:
            reasons.append("stable_region")
        conf = round((c + (1.0 - leak) + s) / 3.0, 2)
        return "usable_logic_candidate", conf, reasons

    # Routing: good conductivity, moderate leakage
    if c >= _ROUTING_COND_MIN and leak <= _ROUTING_LEAK_MAX and s >= _ROUTING_STAB_MIN:
        reasons = ["acceptable_conductivity", "acceptable_leakage", "suitable_for_routing"]
        conf = round((c + (1.0 - leak) + s) / 3.0, 2)
        return "usable_routing_candidate", conf, reasons

    # Memory: moderate conductivity, good mobility
    if c >= _MEMORY_COND_MIN and m >= _MEMORY_MOB_MIN and leak <= _MEMORY_LEAK_MAX:
        reasons = ["acceptable_mobility", "suitable_for_memory", "low_variation"]
        conf = round((c + m + (1.0 - leak)) / 3.0, 2)
        return "usable_memory_candidate", conf, reasons

    # Low confidence: near threshold but not quite
    if c >= 0.45:
        return "low_confidence_candidate", round(0.30 + c * 0.25, 2), [
            "marginal_conductivity", "borderline_scores"
        ]

    # Discard: very low scores, no specific defect
    return "discard_candidate", round(c * 0.4, 2), ["low_conductivity", "low_stability", "below_use_threshold"]
