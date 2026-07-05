from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass
class OutcomeRecord:
    schema: str = "yieldos.outcome_record.v1"
    case_id: str = ""
    domain: str = ""
    asset_id: str = ""
    selected_action: str = ""
    outcome: str = ""           # confirmed_X | refuted_X | inconclusive | pending
    before_score: float = 0.0   # functional or health score before action
    after_score: float = 0.0    # functional or health score after action
    notes: str = ""
    evidence_pack_hash: str = ""
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    recorded_by: str = "engineer"   # engineer | ai_agent | auto

    SCHEMA = "yieldos.outcome_record.v1"

    def delta(self) -> float:
        return round(self.after_score - self.before_score, 4)

    def to_dict(self) -> dict:
        from .meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by
        d = asdict(self)
        d["delta"] = self.delta()
        d["schema_version"] = SCHEMA_VERSION
        d["generated_by"] = generated_by()
        d["safety"] = SAFETY_BLOCK
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
