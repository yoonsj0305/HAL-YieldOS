"""FYFab Seed orchestrator — runs the full FYFab demo pipeline."""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Optional

from .analyzer import (
    build_defect_summary,
    build_structure_map,
    load_defects,
    load_grid,
    load_regions,
    load_target_blocks,
)
from .classifier import classify_cells
from .passport import build_case_study, build_chip_passport
from .reconfiguration import build_candidate_regions, build_reconfiguration_map

_SAMPLE_DIR = Path(__file__).parent.parent.parent.parent / "sample_data" / "fyfab_seed"

_FYFAB_CONFIG = {
    "asset_id": "fyfab_seed_substrate",
    "array_rows": 8,
    "array_cols": 16,
    "defect_rate": 0.14,
    "defect_distribution": "clustered",
    "clustering_factor": 2.5,
    "baseline_accuracy": 0.88,
    "c_fab": 0.95,
    "c_ctrl": 0.18,
    "c_rec": 0.12,
    "notes": "FYFab seed demo: simulated fabricated substrate 128 cells, functional yield evidence pipeline",
}


def run_fyfab_demo(
    out_dir: str,
    input_dir: Optional[str] = None,
    case_id: Optional[str] = None,
) -> dict:
    """
    Run FYFab seed demo: load simulated structure, classify cells,
    generate candidate regions, reconfiguration map, chip passport.
    Writes standard 22-file output bundle plus 7 FYFab-specific outputs.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    sd = Path(input_dir) if input_dir else _SAMPLE_DIR
    case_id = case_id or f"fyfab_{uuid.uuid4().hex[:8]}"

    # Input paths
    grid_path = str(sd / "fabricated_structure_grid.csv")
    defect_path = str(sd / "defect_map.csv")
    region_path = str(sd / "material_regions.csv")
    target_path = str(sd / "target_function_blocks.json")

    # 1. Load inputs
    cells = load_grid(grid_path)
    defects = load_defects(defect_path)
    regions = load_regions(region_path)
    target_blocks = load_target_blocks(target_path)

    # 2. Build FYFab-specific outputs
    structure_map = build_structure_map(case_id, cells, regions)
    defect_summary = build_defect_summary(case_id, defects)
    classification = classify_cells(case_id, cells, defects)
    candidate_regions = build_candidate_regions(case_id, cells, classification)
    reconfig_map = build_reconfiguration_map(case_id, candidate_regions, target_blocks)
    chip_passport = build_chip_passport(case_id, classification, candidate_regions, reconfig_map)
    case_study = build_case_study(case_id, chip_passport)

    # 3. Write FYFab-specific outputs
    _write_json(out_path / "fabricated_structure_map.json", structure_map)
    _write_json(out_path / "defect_map_summary.json", defect_summary)
    _write_json(out_path / "usable_cell_classification.json", classification)
    _write_json(out_path / "candidate_functional_regions.json", candidate_regions)
    _write_json(out_path / "reconfiguration_candidate_map.json", reconfig_map)
    _write_json(out_path / "functional_yield_chip_passport.json", chip_passport)
    _write_json(out_path / "fyfab_case_study.json", case_study)

    # 4. Build standard bundle result via SemiForgeSimulator with FYFab config
    import os
    import tempfile

    from ..simulator import SemiForgeSimulator

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump(_FYFAB_CONFIG, tf)
        tmp_cfg = tf.name

    try:
        result = SemiForgeSimulator().simulate(
            config_path=tmp_cfg,
            case_id=case_id,
            monte_carlo_runs=20,
        )
    finally:
        try:
            os.unlink(tmp_cfg)
        except OSError:
            pass

    # Inject FYFab classification into standard result
    result["remaining_roles"] = chip_passport.get("remaining_functions", [])
    result["blocked_roles"] = chip_passport.get("blocked_functions", [])
    result["bin_class"] = chip_passport.get("chip_bin_candidate", "fyfab_bronze_logic_routing_candidate")

    # 5. Write standard 22-file bundle
    from ....cli.main import _run_and_write
    _run_and_write(
        result,
        out_dir,
        "semiforge",
        source_data_paths=[grid_path, defect_path, region_path, target_path],
    )

    # 6. Enrich functional_passport.json with FYFab chip passport reference
    _enrich_functional_passport(
        out_path / "functional_passport.json",
        chip_passport,
    )

    # 7. Enrich ooda_frame.json with FYFab case study reference
    _enrich_ooda_frame(out_path / "ooda_frame.json")

    # 8. Refresh case_manifest with FYFab optional outputs
    _refresh_case_manifest(out_path)

    return {
        "case_id": case_id,
        "structure_map": structure_map,
        "defect_summary": defect_summary,
        "classification": classification,
        "candidate_regions": candidate_regions,
        "reconfig_map": reconfig_map,
        "chip_passport": chip_passport,
        "case_study": case_study,
    }


def _enrich_functional_passport(fp_path: Path, chip_passport: dict) -> None:
    if not fp_path.exists():
        return
    fp = json.loads(fp_path.read_text(encoding="utf-8"))
    fp["fyfab_chip_passport_ref"] = "functional_yield_chip_passport.json"
    fp["reconfiguration_candidate_map_ref"] = "reconfiguration_candidate_map.json"
    fp["fabrication_context"] = {
        "simulated_bottom_up_structure": True,
        "defect_map_present": True,
        "usable_cell_classification_present": True,
        "candidate_reconfiguration_present": True,
        "context_boundary": "simulation_only_not_fab_control",
    }
    _write_json(fp_path, fp)


def _enrich_ooda_frame(ooda_path: Path) -> None:
    if not ooda_path.exists():
        return
    ooda = json.loads(ooda_path.read_text(encoding="utf-8"))
    ooda["ooda_mode"] = "read_only_evidence_frame"
    ooda["control_loop"] = False
    ooda["hardware_action_enabled"] = False
    ooda["human_review_required"] = True
    ooda["fyfab_case_study_ref"] = "fyfab_case_study.json"
    _write_json(ooda_path, ooda)


def _refresh_case_manifest(out_path: Path) -> None:
    manifest_path = out_path / "case_manifest.json"
    if not manifest_path.exists():
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files", {})

    # Refresh checksums for all existing files
    for entry in files.values():
        p = out_path / entry.get("path", "")
        if p.exists():
            raw = p.read_bytes()
            entry["sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
            entry["byte_size"] = p.stat().st_size

    manifest["files"] = files
    manifest["file_count"] = len(files)

    # Add FYFab optional outputs
    optional_outputs: dict = manifest.get("optional_outputs", {})
    fyfab_files = [
        ("fabricated_structure_map.json", "fabricated_structure_map"),
        ("defect_map_summary.json", "defect_map_summary"),
        ("usable_cell_classification.json", "usable_cell_classification"),
        ("candidate_functional_regions.json", "candidate_functional_regions"),
        ("reconfiguration_candidate_map.json", "reconfiguration_candidate_map"),
        ("functional_yield_chip_passport.json", "functional_yield_chip_passport"),
        ("fyfab_case_study.json", "fyfab_case_study"),
    ]
    for fname, key in fyfab_files:
        p = out_path / fname
        if p.exists():
            raw = p.read_bytes()
            optional_outputs[key] = {
                "path": fname,
                "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "byte_size": p.stat().st_size,
            }

    if optional_outputs:
        manifest["optional_outputs"] = optional_outputs

    _write_json(manifest_path, manifest)


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
