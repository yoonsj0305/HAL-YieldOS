"""FYFab Seed analyzer — loads and summarizes simulated fabricated structure."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

from .schemas import (
    _SAFETY_BLOCK,
    _SCHEMA_VERSION,
    CellRecord,
    DefectRecord,
    MaterialRegion,
    TargetBlock,
)


def load_grid(csv_path: str) -> List[CellRecord]:
    cells = []
    p = Path(csv_path)
    if not p.exists():
        return cells
    with p.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                cells.append(CellRecord(
                    cell_id=row["cell_id"],
                    x=int(row["x"]),
                    y=int(row["y"]),
                    region_id=row["region_id"],
                    material_type=row["material_type"],
                    conductivity_score=float(row["conductivity_score"]),
                    mobility_score=float(row["mobility_score"]),
                    leakage_score=float(row["leakage_score"]),
                    stability_score=float(row["stability_score"]),
                    measured_variation_score=float(row["measured_variation_score"]),
                ))
            except (KeyError, ValueError):
                pass
    return cells


def load_defects(csv_path: str) -> List[DefectRecord]:
    defects = []
    p = Path(csv_path)
    if not p.exists():
        return defects
    with p.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                defects.append(DefectRecord(
                    defect_id=row["defect_id"],
                    cell_id=row["cell_id"],
                    defect_type=row["defect_type"],
                    severity=row["severity"],
                    confidence=float(row["confidence"]),
                    measurement_method=row["measurement_method"],
                ))
            except (KeyError, ValueError):
                pass
    return defects


def load_regions(csv_path: str) -> List[MaterialRegion]:
    regions = []
    p = Path(csv_path)
    if not p.exists():
        return regions
    with p.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                regions.append(MaterialRegion(
                    region_id=row["region_id"],
                    material_type=row["material_type"],
                    growth_method=row["growth_method"],
                    selective_deposition_candidate=row.get("selective_deposition_candidate", "false").lower() == "true",
                    region_area_um2=float(row["region_area_um2"]),
                    average_conductivity_score=float(row["average_conductivity_score"]),
                    average_stability_score=float(row["average_stability_score"]),
                    candidate_use=row["candidate_use"],
                ))
            except (KeyError, ValueError):
                pass
    return regions


def load_target_blocks(json_path: str) -> List[TargetBlock]:
    p = Path(json_path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    blocks = []
    for b in data.get("target_blocks", []):
        try:
            blocks.append(TargetBlock(
                block_id=b["block_id"],
                required_cell_count=int(b["required_cell_count"]),
                minimum_average_conductivity=float(b["minimum_average_conductivity"]),
                maximum_average_leakage=float(b["maximum_average_leakage"]),
                minimum_stability=float(b["minimum_stability"]),
                role=b["role"],
            ))
        except (KeyError, ValueError):
            pass
    return blocks


def build_structure_map(
    case_id: str,
    cells: List[CellRecord],
    regions: List[MaterialRegion],
) -> dict:
    material_types = sorted({c.material_type for c in cells})
    region_ids = sorted({c.region_id for c in cells})

    def _avg(vals):
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    cond_scores = [c.conductivity_score for c in cells]
    mob_scores = [c.mobility_score for c in cells]
    leak_scores = [c.leakage_score for c in cells]
    stab_scores = [c.stability_score for c in cells]

    return {
        "schema": "hal.yieldos.fyfab.fabricated_structure_map.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "grid_summary": {
            "total_cells": len(cells),
            "regions": len(region_ids),
            "region_ids": region_ids,
            "material_types": material_types,
        },
        "score_summary": {
            "average_conductivity_score": _avg(cond_scores),
            "average_mobility_score": _avg(mob_scores),
            "average_leakage_score": _avg(leak_scores),
            "average_stability_score": _avg(stab_scores),
        },
        "claim_boundary": "simulation_only",
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def build_defect_summary(
    case_id: str,
    defects: List[DefectRecord],
) -> dict:
    type_counts: dict = {}
    sev_counts: dict = {}
    blocked: list = []

    for d in defects:
        type_counts[d.defect_type] = type_counts.get(d.defect_type, 0) + 1
        sev_counts[d.severity] = sev_counts.get(d.severity, 0) + 1
        if d.severity == "critical":
            blocked.append(d.cell_id)

    return {
        "schema": "hal.yieldos.fyfab.defect_map_summary.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "total_defects": len(defects),
        "defect_type_counts": type_counts,
        "severity_counts": sev_counts,
        "blocked_cells": blocked,
        "claim_boundary": "observed_defect_map_not_root_cause_certification",
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }
