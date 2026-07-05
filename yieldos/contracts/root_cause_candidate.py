from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import List

CLAIM_BOUNDARY = "candidate_only"


@dataclass
class RootCauseCandidate:
    candidate: str
    confidence: float
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    claim_boundary: str = CLAIM_BOUNDARY
    requires_engineer_review: bool = True
    investigation_hints: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be 0.0–1.0, got {self.confidence}")
        if self.claim_boundary != CLAIM_BOUNDARY:
            raise ValueError(f"claim_boundary must be '{CLAIM_BOUNDARY}'")

    def to_dict(self) -> dict:
        from .meta import SCHEMA_VERSION
        d = asdict(self)
        d["schema"] = "yieldos.root_cause_candidate.v1"
        d["schema_version"] = SCHEMA_VERSION
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
