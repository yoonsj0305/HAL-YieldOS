from __future__ import annotations

from typing import List, Optional

from ..contracts import (
    EvidenceObject,
    EvidencePack,
    OODAFrame,
    RootCauseCandidate,
)
from ..contracts.evidence_pack import CAUSAL_CLAIM_BOUNDARY
from ..contracts.ooda_frame import ACT_BOUNDARY


class EvidenceEngine:
    """
    Assembles domain analysis results into sealed EvidencePack + OODAFrame.
    Domain packs call build_pack(); this engine enforces safety invariants.
    """

    def build_pack(
        self,
        case_id: str,
        domain: str,
        asset_id: str,
        summary: str,
        evidence_objects: List[EvidenceObject],
        root_cause_candidates: List[RootCauseCandidate],
        missing_evidence: Optional[List[str]] = None,
        state_snapshot_ref: str = "",
        state_snapshot_hash: str = "",
    ) -> EvidencePack:
        pack = EvidencePack(
            case_id=case_id,
            domain=domain,
            asset_id=asset_id,
            summary=summary,
            causal_claim_boundary=CAUSAL_CLAIM_BOUNDARY,
            evidence_objects=[e.to_dict() for e in evidence_objects],
            root_cause_candidates=[r.to_dict() for r in root_cause_candidates],
            missing_evidence=missing_evidence or [],
            state_snapshot_ref=state_snapshot_ref,
            state_snapshot_hash=state_snapshot_hash,
        )
        return pack.seal()

    def build_ooda(
        self,
        case_id: str,
        domain: str,
        observe: str,
        orient: str,
        decide: str,
        evidence_pack_ref: str = "",
    ) -> OODAFrame:
        return OODAFrame(
            case_id=case_id,
            domain=domain,
            observe=observe,
            orient=orient,
            decide=decide,
            act=ACT_BOUNDARY,
            evidence_pack_ref=evidence_pack_ref,
        )
