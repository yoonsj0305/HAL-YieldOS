"""Shared metadata injected into all YieldOS JSON outputs."""
from __future__ import annotations

from pathlib import Path

PACKAGE_NAME = "hal-yieldos"
FALLBACK_VERSION = "2.3.1"


def _version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version
        try:
            return version(PACKAGE_NAME)
        except PackageNotFoundError:
            pass
    except ImportError:
        pass
    # fallback: VERSION file (editable install, dev environment)
    vf = Path(__file__).parent.parent.parent / "VERSION"
    try:
        return vf.read_text().strip()
    except Exception:
        return FALLBACK_VERSION


def generated_by() -> dict:
    return {
        "product": "HAL YieldOS",
        "version": _version(),
        "mode": "read_only_shadow",
    }


SAFETY_BLOCK: dict = {
    "read_only": True,
    "shadow_only": True,
    "hardware_execution_enabled": False,
    "human_review_required": True,
    "causal_claim_boundary": "candidate_only_not_certified_cause",
}

SCHEMA_VERSION = _version()
