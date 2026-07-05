"""FYFab Seed data schemas."""
from __future__ import annotations

from dataclasses import dataclass

_SCHEMA_VERSION = "2.8.0"  # matches package version

_SAFETY_BLOCK = {
    "hardware_execution_enabled": False,
    "human_review_required": True,
    "candidate_only": True,
}

_FORBIDDEN_TERMS = frozenset({
    "execute_recipe", "modify_recipe", "control_deposition",
    "control_etch", "control_lithography",
    "physical_design_signoff_certified", "timing_closure_certified",
    "yield_guarantee", "certified_root_cause", "confirmed_root_cause",
})


@dataclass
class CellRecord:
    cell_id: str
    x: int
    y: int
    region_id: str
    material_type: str
    conductivity_score: float
    mobility_score: float
    leakage_score: float
    stability_score: float
    measured_variation_score: float


@dataclass
class DefectRecord:
    defect_id: str
    cell_id: str
    defect_type: str
    severity: str
    confidence: float
    measurement_method: str


@dataclass
class MaterialRegion:
    region_id: str
    material_type: str
    growth_method: str
    selective_deposition_candidate: bool
    region_area_um2: float
    average_conductivity_score: float
    average_stability_score: float
    candidate_use: str


@dataclass
class TargetBlock:
    block_id: str
    required_cell_count: int
    minimum_average_conductivity: float
    maximum_average_leakage: float
    minimum_stability: float
    role: str
