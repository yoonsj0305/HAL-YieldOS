"""FYFab Seed — Functional Yield Chip Passport generator."""
from __future__ import annotations

from .schemas import _SAFETY_BLOCK, _SCHEMA_VERSION


def build_chip_passport(
    case_id: str,
    classification: dict,
    candidate_regions: dict,
    reconfig_map: dict,
) -> dict:
    class_counts = classification.get("class_counts", {})
    mappings = reconfig_map.get("candidate_mappings", [])

    usable_logic = class_counts.get("usable_logic_candidate", 0)
    usable_routing = class_counts.get("usable_routing_candidate", 0)
    usable_memory = class_counts.get("usable_memory_candidate", 0)
    total_usable = usable_logic + usable_routing + usable_memory
    total_cells = sum(class_counts.values())

    fy_score = round(total_usable / max(total_cells, 1), 2)

    remaining = []
    if usable_logic >= 10:
        remaining.append("low_power_logic_candidate")
    if usable_routing >= 10:
        remaining.append("limited_routing_candidate")
    if usable_memory >= 5:
        remaining.append("monitoring_sensor_candidate")

    blocked = []
    if usable_logic < 50:
        blocked.append("high_performance_logic")
    blocked.append("safety_critical_compute")
    if usable_memory < 30:
        blocked.append("high_reliability_memory")

    # Determine bin
    if fy_score >= 0.80:
        bin_candidate = "fyfab_gold_full_function_candidate"
    elif fy_score >= 0.60:
        bin_candidate = "fyfab_bronze_logic_routing_candidate"
    elif fy_score >= 0.40:
        bin_candidate = "fyfab_silver_partial_function_candidate"
    else:
        bin_candidate = "fyfab_iron_monitor_only_candidate"

    mapping_refs = [m["mapping_id"] for m in mappings]
    evidence_refs = [
        "fabricated_structure_map.json",
        "defect_map_summary.json",
        "usable_cell_classification.json",
        "reconfiguration_candidate_map.json",
    ]

    return {
        "schema": "hal.yieldos.fyfab.functional_yield_chip_passport.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "chip_bin_candidate": bin_candidate,
        "functional_yield_score": fy_score,
        "remaining_functions": remaining,
        "blocked_functions": blocked,
        "candidate_reconfiguration_refs": mapping_refs,
        "evidence_refs": evidence_refs,
        **_SAFETY_BLOCK,
        "claim_boundary": "simulation_only_functional_yield_chip_passport",
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }


def build_case_study(case_id: str, chip_passport: dict) -> dict:
    return {
        "schema": "hal.yieldos.fyfab.case_study.v1",
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "title": "Functional Yield Fab Seed Demo",
        "case_summary": {
            "baseline_view": "imperfect fabricated structure contains defects and regions of varying quality",
            "yieldos_view": "usable cells and candidate regions can be classified into remaining and blocked functions",
            "one_sentence_summary": (
                "YieldOS does not fabricate the chip; it interprets a simulated imperfect "
                "fabricated structure and generates candidate functional yield evidence."
            ),
        },
        "pipeline_steps": [
            "load simulated fabricated structure",
            "load observed defect map",
            "load material regions",
            "classify usable cells",
            "group candidate functional regions",
            "generate candidate reconfiguration map",
            "issue functional yield chip passport",
        ],
        "not_claimed": [
            "real fabrication control",
            "lithography replacement",
            "process recipe execution",
            "physical design signoff",
            "timing closure",
            "yield guarantee",
        ],
        "safety_boundary": _SAFETY_BLOCK,
        "chip_passport_summary": {
            "functional_yield_score": chip_passport.get("functional_yield_score", 0.0),
            "chip_bin_candidate": chip_passport.get("chip_bin_candidate", "unknown"),
            "remaining_functions": chip_passport.get("remaining_functions", []),
            "blocked_functions": chip_passport.get("blocked_functions", []),
        },
        "claim_boundary": "simulation_only_case_study_not_manufacturing_evidence",
        "generated_by": f"HAL YieldOS v{_SCHEMA_VERSION}",
    }
