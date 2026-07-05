"""
Failure Scenario Library — append-only JSONL persistence (v2.2.0).

Writes failure scenario records to yieldos_state/<domain>.jsonl.
Fails gracefully: if the directory is not writable, logs a warning and returns None.

Safety invariant: persistence is read-only shadow data — no hardware state is written.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

STATE_DIR = Path("yieldos_state")


def _ensure_dir() -> Optional[Path]:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        return STATE_DIR
    except OSError as exc:
        logger.warning("yieldos_state/ not writable: %s", exc)
        return None


def append_failure_scenario(record: dict) -> Optional[Path]:
    """
    Append a failure scenario record to yieldos_state/<domain>.jsonl.
    Returns the Path written, or None on failure.
    """
    d = _ensure_dir()
    if d is None:
        return None
    domain = record.get("domain_pack", record.get("domain", "unknown"))
    path = d / f"{domain}.jsonl"
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return path
    except OSError as exc:
        logger.warning("Failed to persist failure scenario: %s", exc)
        return None


def load_failure_scenarios(domain: Optional[str] = None) -> List[dict]:
    """
    Load all failure scenarios from yieldos_state/.
    If domain is specified, load only that domain's file.
    Returns an empty list on missing directory or parse errors.
    """
    if not STATE_DIR.exists():
        return []
    results: List[dict] = []
    if domain:
        files = [STATE_DIR / f"{domain}.jsonl"]
    else:
        files = list(STATE_DIR.glob("*.jsonl"))
    for path in files:
        if not path.exists():
            continue
        try:
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        results.append(json.loads(line))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load %s: %s", path, exc)
    return results
