"""HAL YieldOS -- Read-Only Industrial Evidence Engine."""
from pathlib import Path as _Path


def _read_version() -> str:
    _vf = _Path(__file__).parent.parent / "VERSION"
    return _vf.read_text(encoding="utf-8-sig").strip() if _vf.exists() else "2.0.0"

__version__ = _read_version()
