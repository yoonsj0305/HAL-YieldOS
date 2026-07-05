"""
YieldOS-Orbit Demo — CubeSat Power Degradation Analysis (v2.2.0)

Runs a complete shadow analysis pass on the bundled CubeSat power degradation
sample and writes the Standard Output Bundle plus an orbit_mission_recommendation.json
to the specified output directory.

Safety invariant: no uplink commands, no hardware actions. Output is shadow analysis
recommendation_only — all findings require human review.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from ...contracts.meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by
from ..satellite.analyzer import SatGuardAnalyzer

ORBIT_SAMPLE_DIR = Path(__file__).parent.parent.parent.parent / "samples" / "yieldos_orbit"
TELEMETRY_FILE = "cubesat_power_degradation.csv"
MISSION_PROFILE_FILE = "mission_profile.json"


def _load_mission_profile(sample_dir: Path) -> dict:
    path = sample_dir / MISSION_PROFILE_FILE
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _build_orbit_recommendation(
    result: Dict[str, Any],
    mission_profile: dict,
    case_id: str,
    asset_id: str,
) -> dict:
    """
    Build orbit_mission_recommendation.json from analysis result and mission profile.
    All recommendations are candidate suggestions — no execution authority.
    """
    state = result.get("state")
    rcs = result.get("recovery_candidates", [])

    severity = state.severity.value if state else "info"
    confidence = state.confidence if state else 0.0
    state_kind = state.state.value if state else "unknown"
    snapshot_hash = state.snapshot_hash if state else ""

    mission_readiness = state.metrics.get("mission_readiness", 0.0) if state else 0.0
    health_scores = state.metrics.get("health_scores", {}) if state else {}

    orbit = mission_profile.get("orbit", "unknown")
    power_budget = mission_profile.get("power_budget", {})
    envelope = mission_profile.get("operating_envelope", {})

    # Derive mission orbit recommendation (candidate only)
    if severity in ("critical", "high") or mission_readiness < 0.5:
        orbit_mode = "safe_hold_candidate"
        payload_action = "recommend_payload_suspension_pending_review"
        priority = "critical"
    elif severity == "medium" or mission_readiness < 0.75:
        orbit_mode = "low_power_ops_candidate"
        payload_action = "recommend_payload_duty_cycle_reduction"
        priority = "high"
    else:
        orbit_mode = "nominal_ops"
        payload_action = "recommend_continue_monitoring"
        priority = "low"

    return {
        "schema": "hal.yieldos.orbit_mission_recommendation.v1",
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "orbit": orbit,
        "analysis_summary": {
            "state": state_kind,
            "severity": severity,
            "confidence": confidence,
            "mission_readiness": mission_readiness,
            "health_scores": health_scores,
        },
        "state_snapshot_hash": snapshot_hash,
        "orbit_mode_recommendation": orbit_mode,
        "payload_recommendation": payload_action,
        "priority": priority,
        "recovery_candidates": [
            rc.to_dict() if hasattr(rc, "to_dict") else rc for rc in rcs[:5]
        ],
        "power_budget_ref": power_budget,
        "operating_envelope_ref": envelope,
        "mission_profile_schema": mission_profile.get("schema", ""),
        "causal_claim_boundary": "candidate_only_not_certified_cause",
        "human_review_required": True,
        "hardware_execution_enabled": False,
        "uplink_commands_generated": False,
        "notes": (
            "This recommendation is a shadow analysis output. "
            "No uplink commands are generated. "
            "Human mission operations review is required before any action."
        ),
        "safety_boundary": SAFETY_BLOCK,
        "generated_by": generated_by(),
    }


def run_orbit_demo(
    out_dir: str,
    asset_id: str = "cubesat_demo_01",
    sample_dir: Optional[Path] = None,
    case_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the YieldOS-Orbit demo analysis and write Standard Output Bundle.

    Parameters
    ----------
    out_dir    : output directory for Standard Output Bundle
    asset_id   : asset identifier (default: cubesat_demo_01)
    sample_dir : override sample data directory (default: bundled samples/yieldos_orbit/)
    case_id    : override case ID (default: auto-generated)

    Returns
    -------
    dict with keys: paths (written files), state, evidence_pack, ooda_frame, orbit_recommendation
    """
    sample_dir = sample_dir or ORBIT_SAMPLE_DIR
    telemetry_path = str(sample_dir / TELEMETRY_FILE)
    case_id = case_id or f"orbit_demo_{uuid.uuid4().hex[:8]}"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    mission_profile = _load_mission_profile(sample_dir)

    analyzer = SatGuardAnalyzer()
    result = analyzer.analyze(
        telemetry_path=telemetry_path,
        case_id=case_id,
        asset_id=asset_id,
    )

    # Write Standard Output Bundle
    from ...core.report_writer import ReportWriter
    writer = ReportWriter()
    paths = writer.write_all(
        out_dir=str(out),
        state=result["state"],
        pack=result["evidence_pack"],
        ooda=result["ooda_frame"],
        recovery_candidates=result.get("recovery_candidates", []),
        remaining_roles=result.get("remaining_roles", []),
        blocked_roles=result.get("blocked_roles", []),
        bin_class=result.get("bin_class"),
        decision_readiness=result.get("decision_readiness"),
        domain_canonical="space",
    )

    # Write orbit mission recommendation
    orbit_rec = _build_orbit_recommendation(result, mission_profile, case_id, asset_id)
    orbit_path = out / "orbit_mission_recommendation.json"
    orbit_path.write_text(
        json.dumps(orbit_rec, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    paths["orbit_mission_recommendation"] = str(orbit_path)

    # Write mission profile copy
    if mission_profile:
        mp_path = out / "mission_profile.json"
        mp_path.write_text(
            json.dumps(mission_profile, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        paths["mission_profile"] = str(mp_path)

    return {
        "paths": paths,
        "state": result["state"],
        "evidence_pack": result["evidence_pack"],
        "ooda_frame": result["ooda_frame"],
        "recovery_candidates": result.get("recovery_candidates", []),
        "orbit_recommendation": orbit_rec,
        "case_id": case_id,
    }
