"""
Memory Functional Yield Analyzer

Read-only shadow analysis of NAND/NOR flash and general memory devices.
Classifies blocks into functional capacity zones based on supplied health data.

Safety invariant:
  - Never modifies firmware, controller settings, or block mapping.
  - Never moves, stores, or certifies user data.
  - Never executes TRIM or secure erase.
  - All outputs are candidate estimates requiring human review.
"""
from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path
from typing import List, Optional

from ...contracts import (
    EvidenceObject,
    EvidenceType,
    RecoveryCandidate,
    RootCauseCandidate,
    SeverityLevel,
    StateKind,
    StateSnapshot,
)
from ...contracts.meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by
from ...core.evidence_engine import EvidenceEngine
from .bad_block_map import BlockClassification, classify_all_blocks
from .ecc_model import ecc_evidence_confidence, ecc_summary

DOMAIN = "memory"

SCHEMA_FUNCTIONAL_CAPACITY = "hal.yieldos.memory.functional_capacity.v1"
SCHEMA_PLACEMENT_REC = "hal.yieldos.memory.data_placement_recommendation.v1"
SCHEMA_BAD_BLOCK_MAP = "hal.yieldos.memory.bad_block_evidence_map.v1"


def _load_csv(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _functional_yield(safe_gb: float, raw_gb: float) -> float:
    """Conservative functional yield: safe capacity fraction of raw capacity."""
    if raw_gb <= 0:
        return 0.0
    return round(max(0.0, min(1.0, safe_gb / raw_gb)), 4)


def _build_functional_capacity(
    blocks: List[BlockClassification],
    raw_capacity_gb: float,
    device_info: dict,
    case_id: str,
    asset_id: str,
) -> dict:
    safe_gb = sum(b.block_size_gb for b in blocks if b.classification == "safe")
    approx_gb = sum(b.block_size_gb for b in blocks
                    if b.classification in ("approximate_cache", "at_risk"))
    read_only_gb = sum(b.block_size_gb for b in blocks if b.classification == "read_only_archive")
    discard_gb = sum(b.block_size_gb for b in blocks if b.classification == "discard")

    fy = _functional_yield(safe_gb, raw_capacity_gb)
    memory_type = device_info.get("memory_type", "unknown")

    return {
        "schema": SCHEMA_FUNCTIONAL_CAPACITY,
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "memory_type": memory_type,
        "raw_capacity_gb": round(raw_capacity_gb, 2),
        "safe_capacity_gb": round(safe_gb, 2),
        "approximate_cache_capacity_gb": round(approx_gb, 2),
        "read_only_archive_capacity_gb": round(read_only_gb, 2),
        "discarded_capacity_gb": round(discard_gb, 2),
        "functional_yield": fy,
        "capacity_breakdown": {
            "safe": round(safe_gb, 2),
            "approximate_cache": round(approx_gb, 2),
            "read_only_archive": round(read_only_gb, 2),
            "discard": round(discard_gb, 2),
        },
        "model_status": "heuristic_shadow_metric",
        "cannot_certify_data_integrity": True,
        "hardware_execution_enabled": False,
        "human_review_required": True,
        "causal_claim_boundary": "candidate_only_not_certified_cause",
        "generated_by": generated_by(),
        "safety_boundary": SAFETY_BLOCK,
    }


def _build_placement_recommendation(
    blocks: List[BlockClassification],
    case_id: str,
    asset_id: str,
) -> dict:
    safe_gb = round(sum(b.block_size_gb for b in blocks if b.classification == "safe"), 2)
    approx_gb = round(sum(b.block_size_gb for b in blocks
                          if b.classification in ("approximate_cache", "at_risk")), 2)
    read_only_gb = round(sum(b.block_size_gb for b in blocks
                             if b.classification == "read_only_archive"), 2)

    zones = []
    if safe_gb > 0:
        zones.append({
            "zone": "high_reliability_zone",
            "capacity_gb": safe_gb,
            "recommended_data": ["metadata_copy", "standard_storage_candidate"],
            "blocked_data": ["safety_critical_control", "encryption_key_primary"],
            "note": "Candidate only. Not certified for safety-critical use.",
        })
    if approx_gb > 0:
        zones.append({
            "zone": "approximate_ai_cache_zone",
            "capacity_gb": approx_gb,
            "recommended_data": [
                "ai_inference_cache",
                "temporary_tensor_buffer",
                "recomputable_data",
            ],
            "blocked_data": [
                "financial_records",
                "medical_records",
                "filesystem_metadata_primary",
            ],
            "note": "Elevated ECC or retention risk. Suitable only for recomputable or expendable data.",
        })
    if read_only_gb > 0:
        zones.append({
            "zone": "read_only_archive_zone",
            "capacity_gb": read_only_gb,
            "recommended_data": ["read_mostly_archive_candidate"],
            "blocked_data": ["write_intensive_workload"],
            "note": "Write endurance degraded. Read access only; no new writes recommended.",
        })

    return {
        "schema": SCHEMA_PLACEMENT_REC,
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "zones": zones,
        "note": (
            "Recommendation only. Does not modify device mapping, firmware, or controller settings. "
            "Human review required before any data placement decision."
        ),
        "hardware_execution_enabled": False,
        "human_review_required": True,
        "generated_by": generated_by(),
        "safety_boundary": SAFETY_BLOCK,
    }


def _build_bad_block_evidence_map(
    blocks: List[BlockClassification],
    case_id: str,
    asset_id: str,
) -> dict:
    bad_blocks = [b.block_id for b in blocks if b.classification == "discard"]
    at_risk_blocks = [b.block_id for b in blocks
                      if b.classification in ("at_risk", "approximate_cache", "read_only_archive")]
    safe_count = sum(1 for b in blocks if b.classification == "safe")

    return {
        "schema": SCHEMA_BAD_BLOCK_MAP,
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "asset_id": asset_id,
        "bad_blocks": bad_blocks,
        "at_risk_blocks": at_risk_blocks,
        "safe_blocks_count": safe_count,
        "classification_basis": [
            "factory/runtime bad flags",
            "ECC corrected/uncorrectable counts",
            "endurance proxy (PE cycle ratio)",
            "retention proxy (retention_hours vs min)",
        ],
        "cannot_certify_block_map_accuracy": True,
        "hardware_execution_enabled": False,
        "human_review_required": True,
        "generated_by": generated_by(),
        "safety_boundary": SAFETY_BLOCK,
    }


def _passport_roles(functional_yield: float) -> tuple:
    """Return (remaining_roles, blocked_roles, bin_class, decision_readiness)."""
    if functional_yield >= 0.90:
        return (
            ["high_reliability_storage_candidate", "standard_storage_candidate",
             "ai_cache_candidate"],
            ["safety_certified_storage"],
            "memory_gold_candidate",
            "PASSPORT_ELIGIBLE",
        )
    if functional_yield >= 0.70:
        return (
            ["standard_storage_candidate", "ai_cache_candidate",
             "read_only_archive_candidate"],
            ["safety_critical_storage", "encryption_key_primary_storage"],
            "memory_silver_candidate",
            "PASSPORT_ELIGIBLE",
        )
    if functional_yield >= 0.45:
        return (
            ["approximate_ai_cache_candidate", "temporary_buffer_candidate",
             "read_only_archive_candidate"],
            ["primary_filesystem_metadata", "financial_record_storage",
             "safety_critical_storage"],
            "memory_bronze_cache_only",
            "ACTION_INELIGIBLE",
        )
    return (
        ["lab_analysis_only", "discard_review_candidate"],
        ["production_storage", "ai_cache_candidate", "primary_data_storage"],
        "memory_discard_review",
        "ACTION_INELIGIBLE",
    )


class MemoryAnalyzer:
    """
    Read-only shadow analysis for memory device health data.
    Never modifies device firmware, mapping, or controller settings.
    """

    def __init__(self):
        self._engine = EvidenceEngine()

    def analyze(
        self,
        input_dir: str,
        case_id: Optional[str] = None,
        asset_id: str = "memdev_01",
    ) -> dict:
        if not case_id:
            case_id = f"case_memory_{uuid.uuid4().hex[:8]}"

        inp = Path(input_dir)
        block_health_path = inp / "block_health.csv"
        device_info_path = inp / "device_info.json"

        rows = _load_csv(block_health_path)
        device_info = _load_json(device_info_path)

        raw_capacity_gb = float(device_info.get("raw_capacity_gb", len(rows)))
        if not asset_id or asset_id == "memdev_01":
            asset_id = device_info.get("device_id", asset_id)

        # Classify all blocks
        blocks = classify_all_blocks(rows, device_info)
        n_total = len(blocks)
        n_discard = sum(1 for b in blocks if b.classification == "discard")
        n_safe = sum(1 for b in blocks if b.classification == "safe")
        n_approx = sum(1 for b in blocks
                       if b.classification in ("approximate_cache", "at_risk"))
        n_read_only = sum(1 for b in blocks if b.classification == "read_only_archive")

        safe_gb = sum(b.block_size_gb for b in blocks if b.classification == "safe")
        fy = _functional_yield(safe_gb, raw_capacity_gb)

        # ECC aggregate
        ecc_policy = device_info.get("ecc_policy", {})
        corrected_warn = float(ecc_policy.get("corrected_error_warning_threshold", 100))
        ecc_stats = ecc_summary(rows)

        # Evidence objects
        evidence_objects: List[EvidenceObject] = []
        ev_counter = 1
        missing_inputs: List[str] = []

        # Check for required columns
        if rows:
            available = set(rows[0].keys())
            for col in ("pe_cycles", "max_pe_cycles"):
                if col not in available:
                    missing_inputs.append(col)

        # EvidenceObject: uncorrectable errors
        if ecc_stats["total_uncorrectable_errors"] > 0:
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.SENSOR_FAULT,
                source="block_health_data",
                summary=(
                    f"{ecc_stats['total_uncorrectable_errors']} uncorrectable ECC error(s) "
                    f"across {n_discard} discard block(s)"
                ),
                metric="uncorrectable_error_count",
                value=float(ecc_stats["total_uncorrectable_errors"]),
                baseline=0.0,
                confidence=0.97,
            )
            evidence_objects.append(ev)
            ev_counter += 1

        # EvidenceObject: high corrected error rate
        if ecc_stats["total_corrected_errors"] > 0:
            conf = ecc_evidence_confidence(
                ecc_stats["total_corrected_errors"],
                ecc_stats["total_uncorrectable_errors"],
                corrected_warn,
            )
            if conf >= 0.25:
                ev = EvidenceObject(
                    evidence_id=f"ev_{ev_counter:03d}",
                    type=EvidenceType.THRESHOLD_BREACH,
                    source="block_health_data",
                    summary=(
                        f"Total corrected ECC errors: {ecc_stats['total_corrected_errors']} "
                        f"(max single block: {ecc_stats['max_corrected_single_block']})"
                    ),
                    metric="corrected_error_count",
                    value=float(ecc_stats["total_corrected_errors"]),
                    confidence=conf,
                )
                evidence_objects.append(ev)
                ev_counter += 1

        # EvidenceObject: bad block rate
        bad_rate = n_discard / max(n_total, 1)
        if n_discard > 0:
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.YIELD_DROP,
                source="block_health_data",
                summary=(
                    f"{n_discard}/{n_total} blocks classified as discard "
                    f"({bad_rate:.1%} discard rate)"
                ),
                metric="discard_block_rate",
                value=round(bad_rate, 4),
                baseline=0.02,
                confidence=min(0.95, 0.5 + bad_rate * 2.0),
            )
            evidence_objects.append(ev)
            ev_counter += 1

        # EvidenceObject: endurance degradation
        high_pe_blocks = [b for b in blocks
                          if b.classification in ("read_only_archive", "at_risk")
                          and any("pe_ratio" in r for r in b.reasons)]
        if high_pe_blocks or n_read_only > 0:
            endurance_conf = 0.65 + min(n_read_only / max(n_total, 1) * 2.0, 0.25)
            ev = EvidenceObject(
                evidence_id=f"ev_{ev_counter:03d}",
                type=EvidenceType.PATTERN_ANOMALY,
                source="block_health_data",
                summary=f"{n_read_only} block(s) show high PE cycle ratio (endurance degradation candidate)",
                metric="high_pe_cycle_block_count",
                value=float(n_read_only),
                confidence=round(endurance_conf, 3),
            )
            evidence_objects.append(ev)
            ev_counter += 1

        # State classification
        top_conf = max((e.confidence for e in evidence_objects), default=0.20)
        if fy < 0.45 or bad_rate > 0.20:
            state_kind = StateKind.FAULT_CANDIDATE
            severity = SeverityLevel.HIGH
        elif fy < 0.70 or bad_rate > 0.08:
            state_kind = StateKind.FUNCTIONAL_YIELD_ESTIMATED
            severity = SeverityLevel.MEDIUM
        elif evidence_objects:
            state_kind = StateKind.DEGRADED
            severity = SeverityLevel.LOW
        else:
            state_kind = StateKind.NOMINAL
            severity = SeverityLevel.INFO

        state = StateSnapshot(
            case_id=case_id,
            domain=DOMAIN,
            asset_id=asset_id,
            state=state_kind,
            severity=severity,
            confidence=round(top_conf, 3),
            evidence_refs=[e.evidence_id for e in evidence_objects],
            metrics={
                "total_blocks": n_total,
                "raw_capacity_gb": raw_capacity_gb,
                "safe_blocks": n_safe,
                "safe_gb": round(safe_gb, 2),
                "approximate_cache_blocks": n_approx,
                "read_only_archive_blocks": n_read_only,
                "discard_blocks": n_discard,
                "discard_rate": round(bad_rate, 4),
                "functional_yield": fy,
                "total_corrected_errors": ecc_stats["total_corrected_errors"],
                "total_uncorrectable_errors": ecc_stats["total_uncorrectable_errors"],
                "missing_inputs": missing_inputs,
            },
        )

        remaining_roles, blocked_roles, bin_class, decision_readiness = _passport_roles(fy)

        rca_list: List[RootCauseCandidate] = []
        if n_discard > 0 or ecc_stats["total_uncorrectable_errors"] > 0:
            rca_list.append(RootCauseCandidate(
                candidate="block-level wear-out or manufacturing defect",
                confidence=round(min(0.90, 0.50 + bad_rate * 2.0), 3),
                supporting_evidence=[e.evidence_id for e in evidence_objects],
                investigation_hints=[
                    "review factory bad block table from manufacturer",
                    "compare runtime bad block growth rate over time",
                    "request SMART/vendor health log",
                ],
            ))
        if ecc_stats["total_corrected_errors"] > 0:
            rca_list.append(RootCauseCandidate(
                candidate="accumulated ECC stress — potential read disturb or charge leakage",
                confidence=round(min(0.80, top_conf * 0.75), 3),
                investigation_hints=[
                    "request ECC error history per block",
                    "evaluate read disturb mitigation (scrub interval)",
                ],
            ))

        pack = self._engine.build_pack(
            case_id=case_id,
            domain=DOMAIN,
            asset_id=asset_id,
            summary=(
                f"Memory {asset_id}: {n_total} blocks, "
                f"functional yield {fy:.1%} "
                f"({n_safe} safe / {n_approx} approx / {n_read_only} read-only / {n_discard} discard). "
                f"State: {state_kind.value}."
            ),
            evidence_objects=evidence_objects,
            root_cause_candidates=rca_list,
            missing_evidence=[
                "block-level SMART log from device firmware",
                "historical PE cycle count per block",
                "vendor factory bad block certificate",
                "device operating temperature history",
            ],
            state_snapshot_hash=state.snapshot_hash,
        )

        ooda = self._engine.build_ooda(
            case_id=case_id,
            domain=DOMAIN,
            observe=(
                f"Memory {asset_id}: {n_discard}/{n_total} discard blocks detected. "
                f"Functional yield estimate: {fy:.1%}."
            ),
            orient=(
                f"Block classification: {n_safe} safe, {n_approx} approx cache, "
                f"{n_read_only} read-only archive, {n_discard} discard. "
                f"ECC corrected total: {ecc_stats['total_corrected_errors']}. "
                f"Passport bin: {bin_class}."
            ),
            decide=(
                "Recommend data migration review for degraded blocks and retirement review "
                "for discard blocks. No firmware or mapping changes are to be made. "
                "Human review required before any storage placement decision."
            ),
            evidence_pack_ref=pack.checksum,
        )

        recovery = [
            RecoveryCandidate(
                action="recommend_data_migration_review",
                expected_benefit=(
                    f"Identify and migrate data from {n_discard + n_approx} degraded blocks "
                    "to safe storage — for operator review"
                ),
                risk="low",
                steps=[
                    "generate candidate block list for migration review",
                    "flag approximate_cache blocks for data freshness review",
                    "prepare migration proposal for storage engineer",
                ],
            ),
            RecoveryCandidate(
                action="recommend_read_only_archive_review",
                expected_benefit=(
                    f"Review {n_read_only} read-only archive candidate blocks "
                    "before further write operations — for engineer review"
                ),
                risk="low",
                steps=[
                    "flag read_only_archive blocks for no-write policy review",
                    "prepare archival placement recommendation for operator",
                ],
            ),
            RecoveryCandidate(
                action="request_vendor_smart_log",
                expected_benefit="Obtain device-level health log from vendor for root cause investigation",
                risk="low",
                steps=[
                    "prepare vendor SMART log request",
                    "compare factory bad block table with runtime classification",
                ],
            ),
        ]

        # Extra output files
        functional_capacity = _build_functional_capacity(
            blocks, raw_capacity_gb, device_info, case_id, asset_id
        )
        placement_rec = _build_placement_recommendation(blocks, case_id, asset_id)
        bad_block_map = _build_bad_block_evidence_map(blocks, case_id, asset_id)

        from ...contracts.input_validation import build_input_validation
        from ...core.functional_yield import build_functional_yield_vector

        role_scores_fyv = {r: 1.0 for r in remaining_roles}
        role_scores_fyv.update({r: 0.0 for r in blocked_roles})
        safe_ratio = round(n_safe / max(n_total, 1), 4)
        ecc_health = round(max(0.0, 1.0 - ecc_stats["total_uncorrectable_errors"] * 0.1), 3)
        endurance_health = round(1.0 - n_read_only / max(n_total, 1), 3)
        fyv = build_functional_yield_vector(
            domain="memory",
            case_id=case_id,
            asset_id=asset_id,
            component_scores={
                "safe_block_ratio": safe_ratio,
                "ecc_health": ecc_health,
                "endurance_health": endurance_health,
                "bad_block_headroom": round(1.0 - bad_rate, 3),
            },
            role_scores=role_scores_fyv,
            evidence_confidence=top_conf,
            missing_inputs=missing_inputs,
            score_kind="heuristic",
            model_limitations=["sample_block_health_only", "no_firmware_level_data"],
            domain_adapter="memory_device",
            override_yield_score=fy,
        )
        state.metrics["functional_yield_vector"] = fyv

        mem_passed = (n_total > 0) and (raw_capacity_gb > 0)
        input_validation = build_input_validation(
            case_id=case_id,
            domain_pack="memory",
            domain_adapter="memory_device",
            status="PASSED" if mem_passed else "FAILED",
            data_level="MINIMUM_RUNNABLE" if mem_passed and not missing_inputs else (
                "BELOW_MINIMUM" if mem_passed else "EMPTY"
            ),
            found_inputs=(["block_health.csv"] if rows else []) + (["device_info.json"] if device_info else []),
            missing_inputs=missing_inputs,
            record_counts={
                "total_blocks": n_total,
                "raw_capacity_gb": raw_capacity_gb,
            },
            blocking_reasons=(
                (["total_blocks == 0"] if n_total == 0 else []) +
                (["raw_capacity_gb == 0"] if raw_capacity_gb == 0 else [])
            ),
        )

        return {
            "case_id": case_id,
            "domain": DOMAIN,
            "state": state,
            "evidence_pack": pack,
            "ooda_frame": ooda,
            "recovery_candidates": recovery,
            "remaining_roles": remaining_roles,
            "blocked_roles": blocked_roles,
            "bin_class": bin_class,
            "decision_readiness": decision_readiness,
            "functional_capacity": functional_capacity,
            "placement_recommendation": placement_rec,
            "bad_block_evidence_map": bad_block_map,
            "input_validation": input_validation,
        }
