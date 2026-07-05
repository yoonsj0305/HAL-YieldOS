from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import List

CAUSAL_CLAIM_BOUNDARY = "candidate_only_not_certified_cause"


@dataclass
class EvidencePack:
    schema: str = "yieldos.evidence_pack.v1"
    case_id: str = ""
    domain: str = ""
    asset_id: str = ""
    summary: str = ""
    causal_claim_boundary: str = CAUSAL_CLAIM_BOUNDARY
    evidence_objects: List[dict] = field(default_factory=list)
    root_cause_candidates: List[dict] = field(default_factory=list)
    missing_evidence: List = field(default_factory=list)
    state_snapshot_ref: str = ""
    state_snapshot_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    checksum: str = ""

    SCHEMA = "yieldos.evidence_pack.v1"

    def __post_init__(self):
        if self.causal_claim_boundary != CAUSAL_CLAIM_BOUNDARY:
            raise ValueError(
                f"causal_claim_boundary must be '{CAUSAL_CLAIM_BOUNDARY}'. "
                "YieldOS never certifies root cause."
            )

    def seal(self) -> "EvidencePack":
        """Compute checksum over all content fields (call after all fields are set)."""
        payload = {
            "schema": self.schema,
            "case_id": self.case_id,
            "domain": self.domain,
            "asset_id": self.asset_id,
            "summary": self.summary,
            "causal_claim_boundary": self.causal_claim_boundary,
            "evidence_objects": self.evidence_objects,
            "root_cause_candidates": self.root_cause_candidates,
            "missing_evidence": self.missing_evidence,
            "state_snapshot_ref": self.state_snapshot_ref,
            "state_snapshot_hash": self.state_snapshot_hash,
            "created_at": self.created_at,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.checksum = "sha256:" + hashlib.sha256(blob).hexdigest()
        return self

    def to_dict(self) -> dict:
        from .meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by
        d = asdict(self)
        d["schema_version"] = SCHEMA_VERSION
        d["generated_by"] = generated_by()
        d["safety"] = SAFETY_BLOCK
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "EvidencePack":
        d = dict(d)
        for key in ("schema_version", "generated_by", "safety"):
            d.pop(key, None)
        return cls(**d)
