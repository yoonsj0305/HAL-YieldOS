from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class StateKind(str, Enum):
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    ANOMALY_CANDIDATE = "anomaly_candidate"
    FAULT_CANDIDATE = "fault_candidate"
    PROCESS_DRIFT_CANDIDATE = "process_drift_candidate"
    JOINT_PRECISION_DEGRADATION_CANDIDATE = "joint_precision_degradation_candidate"
    POWER_MARGIN_DEGRADED = "power_margin_degraded"
    MISSION_READINESS_DEGRADED = "mission_readiness_degraded"
    FUNCTIONAL_YIELD_ESTIMATED = "functional_yield_estimated"
    UNKNOWN = "unknown"


@dataclass
class StateSnapshot:
    schema: str = "yieldos.state_snapshot.v1"
    case_id: str = ""
    domain: str = ""          # semiconductor_fab | robotics | satellite | semiforge
    asset_id: str = ""
    state: StateKind = StateKind.UNKNOWN
    severity: SeverityLevel = SeverityLevel.INFO
    confidence: float = 0.0   # 0.0 ~ 1.0
    mode: str = "read_only_shadow"
    evidence_refs: List[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""
    snapshot_hash: str = ""

    SCHEMA = "yieldos.state_snapshot.v1"
    MODE = "read_only_shadow"

    def __post_init__(self):
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be 0.0–1.0, got {self.confidence}")
        if self.mode != self.MODE:
            raise ValueError(f"mode must be '{self.MODE}'")
        if not self.snapshot_hash:
            self.snapshot_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """SHA-256 of canonical content fields (excludes generated_by/safety/schema_version)."""
        payload = {
            "schema": self.schema,
            "case_id": self.case_id,
            "domain": self.domain,
            "asset_id": self.asset_id,
            "state": self.state.value if hasattr(self.state, "value") else str(self.state),
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "confidence": self.confidence,
            "mode": self.mode,
            "evidence_refs": self.evidence_refs,
            "metrics": self.metrics,
            "tags": self.tags,
            "created_at": self.created_at,
            "notes": self.notes,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "sha256:" + hashlib.sha256(blob).hexdigest()

    def to_dict(self) -> dict:
        from .meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by
        d = asdict(self)
        d["state"] = self.state.value
        d["severity"] = self.severity.value
        d["schema_version"] = SCHEMA_VERSION
        d["generated_by"] = generated_by()
        d["safety"] = SAFETY_BLOCK
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "StateSnapshot":
        d = dict(d)
        d["state"] = StateKind(d.get("state", "unknown"))
        d["severity"] = SeverityLevel(d.get("severity", "info"))
        # Strip generated keys not in dataclass
        for key in ("schema_version", "generated_by", "safety"):
            d.pop(key, None)
        return cls(**d)
