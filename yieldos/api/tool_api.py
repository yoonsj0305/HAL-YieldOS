from __future__ import annotations

import json
from pathlib import Path


class YieldOSToolAPI:
    """
    AI Tool API: lets an AI agent query YieldOS output objects
    without reading raw logs. Token-efficient by design.

    Token Idiot Index goal: raw_log_tokens / api_response_tokens >= 10
    """

    def __init__(self, case_dir: str):
        self._base = Path(case_dir)

    def _load(self, filename: str) -> dict:
        p = self._base / filename
        if not p.exists():
            return {"error": f"Not found: {filename}. Run analysis first."}
        return json.loads(p.read_text(encoding="utf-8"))

    def get_state_snapshot(self) -> dict:
        """Returns compressed StateSnapshot. ~50 tokens vs thousands for raw log."""
        data = self._load("state_snapshot.json")
        if "error" in data:
            return data
        return {
            "case_id": data.get("case_id"),
            "domain": data.get("domain"),
            "asset_id": data.get("asset_id"),
            "state": data.get("state"),
            "severity": data.get("severity"),
            "confidence": data.get("confidence"),
            "mode": data.get("mode"),
            "metrics": data.get("metrics", {}),
            "created_at": data.get("created_at"),
        }

    @staticmethod
    def _token_estimate(obj) -> dict:
        """Rough token estimate (character-based, not tokenizer-based)."""
        text = json.dumps(obj, ensure_ascii=False)
        # ~4 chars per token is a common rough estimate
        est = max(1, len(text) // 4)
        return {
            "yieldos_response_estimate": est,
            "label": "estimate",
            "note": "character-based estimate only, not tokenizer-based",
        }

    def get_evidence_pack(self, include_objects: bool = True, max_evidence: int = 0) -> dict:
        """Returns EvidencePack. max_evidence=0 means no limit."""
        data = self._load("evidence_pack.json")
        if "error" in data:
            return data
        ev_all = data.get("evidence_objects", [])
        ev_slice = ev_all if max_evidence <= 0 else ev_all[:max_evidence]
        result = {
            "case_id": data.get("case_id"),
            "domain": data.get("domain"),
            "summary": data.get("summary"),
            "causal_claim_boundary": data.get("causal_claim_boundary"),
            "root_cause_candidates": data.get("root_cause_candidates", []),
            "missing_evidence": data.get("missing_evidence", []),
            "checksum": data.get("checksum"),
        }
        if include_objects:
            result["evidence_objects"] = [
                {"id": e.get("evidence_id"), "type": e.get("type"),
                 "summary": e.get("summary"), "confidence": e.get("confidence")}
                for e in ev_slice
            ]
        result["token_estimate"] = self._token_estimate(result)
        return result

    def get_ooda_frame(self) -> dict:
        data = self._load("ooda_frame.json")
        if "error" in data:
            return data
        return {
            "case_id": data.get("case_id"),
            "observe": data.get("observe"),
            "orient": data.get("orient"),
            "decide": data.get("decide"),
            "act": data.get("act"),
        }

    def get_root_cause_candidates(self, top_k: int = 0) -> list:
        """top_k=0 means return all."""
        data = self._load("evidence_pack.json")
        if "error" in data:
            return [data]
        candidates = data.get("root_cause_candidates", [])
        return candidates if top_k <= 0 else candidates[:top_k]

    def get_recovery_candidates(self, top_k: int = 0) -> list:
        """top_k=0 means return all."""
        data = self._load("recovery_candidates.json")
        if "error" in data:
            return [data]
        candidates = data if isinstance(data, list) else data.get("candidates", [])
        return candidates if top_k <= 0 else candidates[:top_k]

    def get_missing_evidence_request(self) -> list:
        data = self._load("evidence_pack.json")
        if "error" in data:
            return []
        return data.get("missing_evidence", [])

    def get_full_summary(self, top_k: int = 3, max_evidence: int = 5) -> dict:
        """Single call that returns everything an AI needs. Maximum token efficiency."""
        result = {
            "state": self.get_state_snapshot(),
            "ooda": self.get_ooda_frame(),
            "top_candidates": self.get_root_cause_candidates(top_k=top_k),
            "top_recovery": self.get_recovery_candidates(top_k=top_k),
            "missing_evidence": self.get_missing_evidence_request(),
            "top_evidence": self.get_evidence_pack(max_evidence=max_evidence).get("evidence_objects", []),
        }
        result["token_estimate"] = self._token_estimate(result)
        return result

    def get_experience_records(self, experience_path: str = "output/experiences.jsonl") -> list:
        p = Path(experience_path)
        if not p.exists():
            return []
        records = []
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
