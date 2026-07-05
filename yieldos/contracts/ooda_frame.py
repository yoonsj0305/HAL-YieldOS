from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

ACT_BOUNDARY = "recommendation_only_no_hardware_action"


@dataclass
class OODAFrame:
    schema: str = "yieldos.ooda_frame.v1"
    case_id: str = ""
    domain: str = ""
    observe: str = ""
    orient: str = ""
    decide: str = ""
    act: str = ACT_BOUNDARY
    evidence_pack_ref: str = ""
    created_at: str = ""

    SCHEMA = "yieldos.ooda_frame.v1"

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.act != ACT_BOUNDARY:
            raise ValueError(
                f"act must be '{ACT_BOUNDARY}'. "
                "YieldOS never issues hardware commands."
            )

    def to_dict(self) -> dict:
        from .meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by
        d = asdict(self)
        d["schema_version"] = SCHEMA_VERSION
        d["generated_by"] = generated_by()
        d["safety"] = SAFETY_BLOCK
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
