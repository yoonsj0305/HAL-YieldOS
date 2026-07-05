from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from ..contracts import EvidencePack, OutcomeRecord


class ExperienceGraph:
    """
    Persistent ledger: state → action → outcome.
    Each record is a newline-delimited JSON entry in experiences.jsonl.
    """

    def __init__(self, store_path: str = "output/experiences.jsonl"):
        self._path = Path(store_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, outcome: OutcomeRecord, pack: Optional[EvidencePack] = None) -> None:
        entry = outcome.to_dict()
        if pack:
            entry["evidence_pack_hash"] = pack.checksum
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def load_all(self) -> List[dict]:
        if not self._path.exists():
            return []
        records = []
        with self._path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def load_by_asset(self, asset_id: str) -> List[dict]:
        return [r for r in self.load_all() if r.get("asset_id") == asset_id]

    def load_by_domain(self, domain: str) -> List[dict]:
        return [r for r in self.load_all() if r.get("domain") == domain]

    def summary(self) -> dict:
        records = self.load_all()
        by_domain: dict = {}
        for r in records:
            d = r.get("domain", "unknown")
            by_domain.setdefault(d, 0)
            by_domain[d] += 1
        return {"total": len(records), "by_domain": by_domain}
