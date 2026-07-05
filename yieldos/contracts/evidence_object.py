from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class EvidenceType(str, Enum):
    TREND_SHIFT = "trend_shift"
    THRESHOLD_BREACH = "threshold_breach"
    PATTERN_ANOMALY = "pattern_anomaly"
    CORRELATION_BREAK = "correlation_break"
    MISSING_DATA = "missing_data"
    STATISTICAL_OUTLIER = "statistical_outlier"
    SPATIAL_PATTERN = "spatial_pattern"
    TEMPORAL_CLUSTER = "temporal_cluster"
    SENSOR_FAULT = "sensor_fault"
    YIELD_DROP = "yield_drop"


@dataclass
class TimeWindow:
    start: str
    end: str


@dataclass
class EvidenceObject:
    evidence_id: str
    type: EvidenceType
    source: str           # tool_log | wafer_map | telemetry | test_result | csv_file
    summary: str
    confidence: float
    metric: str = ""
    value: Optional[float] = None
    baseline: Optional[float] = None
    unit: str = ""
    time_window: Optional[TimeWindow] = None
    raw_refs: list = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be 0.0–1.0, got {self.confidence}")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
