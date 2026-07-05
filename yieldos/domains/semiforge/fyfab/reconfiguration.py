"""FYFab Seed reconfiguration — groups usable cells into candidate regions and maps to target blocks."""
from __future__ import annotations

from typing import Dict, List

from .schemas import _SAFETY_BLOCK, _SCHEMA_VERSION, CellRecord, TargetBlock

_USABLE_CLASSES = frozenset({
    "usable_logic_candidate", "usable_routing_candidate", "usable_memory_candidate",
})

_ROLE_TO_REGION_TYPE = {
    "usable_logic_candidate": "logic",
    "usable_routing_candidate": "routing",
    "usable_memory_candidate": "memory",
}


def build_candidate_regions(
    case_id: str,
    cells: List[CellRecord],
    classification: dict,
) -> dict:
    cell_by_id: Dict[str, CellRecord] = {c.cell_id: c for c in cells}
    classified_cells = classification.get("cells", [])

    # Group usable cells by their classification role
    groups: Dict[str, list] = {}
    for entry in classified_cells:
        cls = entry["classification"]
        if cls in _USABLE_CLASSES:
            region_type = _ROLE_TO_REGION_TYPE[cls]
            groups.setdefault(region_type, []).append(entry)

    regions = []
    region_idx = 1

    for region_type, cell_entries in sorted(groups.items()):
        cell_ids = [e["cell_id"] for e in cell_entries]
        cell_objs = [cell_by_id[cid] for cid in cell_ids if cid in cell_by_id]

        if not cell_objs:
            continue

        avg_cond = round(sum(c.conductivity_score for c in cell_objs) / len(cell_objs), 3)
        avg_leak = round(sum(c.leakage_score for c in cell_objs) / len(cell_objs), 3)
        avg_stab = round(sum(c.stability_score for c in cell_objs) / len(cell_objs), 3)
        avg_conf = round(sum(e["confidence"] for e in cell_entries) / len(cell_entries), 2)

        role_map = {
            "logic": "low_power_logic_candidate",
            "routing": "routing_candidate",
            "memory": "memory_candidate",
        }

        regions.append({
            "candidate_region_id": f"cand_{region_type}_region_{region_idx:03d}",
            "role": role_map.get(region_type, f"{region_type}_candidate"),
            "cell_ids": cell_ids[:50],
            "cell_count": len(cell_ids),
            "average_conductivity_score": avg_cond,
            "average_leakage_score": avg_leak,
            "average_stability_score": avg_stab,
            "confidence": avg_conf,
            "claim_boundary": "candidate_region_not_physical_design_signoff",
        })
        region_idx += 1

    return {
        "schema": "hal.yieldos.fyfab.candidate_functional_regions.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "regions": regions,
        "claim_boundary": "candidate_functional_regions_not_physical_design",
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def build_reconfiguration_map(
    case_id: str,
    candidate_regions: dict,
    target_blocks: List[TargetBlock],
) -> dict:
    regions = candidate_regions.get("regions", [])
    region_by_role: Dict[str, dict] = {}
    for r in regions:
        role = r.get("role", "")
        region_by_role[role] = r

    mappings = []
    mapping_idx = 1

    for block in target_blocks:
        block_role = block.role
        cand_region = region_by_role.get(block_role)

        if cand_region is None:
            continue

        usable_count = cand_region.get("cell_count", 0)
        avg_cond = cand_region.get("average_conductivity_score", 0.0)
        avg_leak = cand_region.get("average_leakage_score", 1.0)
        avg_stab = cand_region.get("average_stability_score", 0.0)

        meets_leak = avg_leak <= block.maximum_average_leakage
        enough_cells = usable_count >= block.required_cell_count

        blocked_count = max(0, int(usable_count * 0.08))

        fit = round(
            (avg_cond / max(block.minimum_average_conductivity, 0.01)) * 0.4 +
            (1.0 - avg_leak / max(block.maximum_average_leakage, 0.01)) * 0.3 +
            (avg_stab / max(block.minimum_stability, 0.01)) * 0.3,
            2,
        )
        fit = min(fit, 1.0)

        reasons = []
        if enough_cells:
            reasons.append("enough_candidate_cells")
        else:
            reasons.append("insufficient_candidate_cells")
        if meets_leak:
            reasons.append("acceptable_average_leakage")
        else:
            reasons.append("high_leakage_concern")
        if blocked_count > 0:
            reasons.append("some_neighbor_defects_present")

        risk = "low" if fit >= 0.80 else "medium" if fit >= 0.60 else "high"

        mappings.append({
            "mapping_id": f"reconf_{mapping_idx:03d}",
            "target_block_id": block.block_id,
            "candidate_region_id": cand_region["candidate_region_id"],
            "usable_cell_count": usable_count,
            "blocked_cell_count": blocked_count,
            "estimated_functional_fit": fit,
            "estimated_risk": risk,
            "reason_codes": reasons,
            "claim_boundary": "candidate_mapping_not_routing_signoff",
        })
        mapping_idx += 1

    return {
        "schema": "hal.yieldos.fyfab.reconfiguration_candidate_map.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "reconfiguration_mode": "simulation_candidate_only",
        "candidate_mappings": mappings,
        "forbidden_claims": [
            "physical design signoff",
            "timing closure",
            "manufacturing certification",
            "yield guarantee",
        ],
        "safety_boundary": _SAFETY_BLOCK,
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }
