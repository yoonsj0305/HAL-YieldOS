"""
yieldos/demo_runner.py

Direct Python demo runner — generates domain demo output without spawning
a subprocess.  Both the CLI (cmd_demo) and tests import from here so they
exercise the same code path.

Public API
----------
run_domain_demo_direct(*, domain, out_dir) -> Path
run_all_domain_demos_direct(*, out_dir) -> dict[str, Path]
"""
from __future__ import annotations

from pathlib import Path

SUPPORTED_DOMAINS = ("robot", "space", "semiconductor", "semiforge", "memory")


def run_domain_demo_direct(*, domain: str, out_dir: Path) -> Path:
    """Generate a demo case for a single domain without spawning a subprocess.

    Uses the same underlying analysis + report-writing logic as
    ``yieldos demo --domain <domain> --out <out_dir>``.

    Parameters
    ----------
    domain:
        Canonical domain name: robot | space | semiconductor | semiforge | memory.
        Domain aliases are resolved the same way as the CLI.
    out_dir:
        Target output directory (created if it does not exist).

    Returns
    -------
    Path
        The output directory (same as *out_dir*).
    """
    # Lazy imports keep startup cost low when only a subset of domains is needed.
    from .cli.main import (
        _memory_extra_outputs,
        _memory_source_data_paths,
        _resolve_domain,
        _robot_source_data_paths,
        _run_and_write,
        _run_memory,
        _run_robot,
        _run_semiconductor,
        _run_semiforge,
        _run_space,
        _sample_root,
        _semiconductor_extra_outputs,
        _semiconductor_source_data_paths,
        _semiforge_source_data_paths,
        _space_source_data_paths,
    )

    canonical, _ = _resolve_domain(domain)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    samples = _sample_root()
    out_str = str(out_dir)

    if canonical == "robot":
        tp = samples / "robot_ooda" / "robot_telemetry.csv"
        if not tp.exists():
            tp = samples / "robot" / "robot_telemetry.csv"
        result = _run_robot(str(tp), case_id=f"demo_{canonical}")
        extra = None
        sdp = _robot_source_data_paths(str(tp))

    elif canonical == "space":
        tp = samples / "satguard" / "satellite_telemetry.csv"
        if not tp.exists():
            tp = samples / "space" / "satellite_telemetry.csv"
        result = _run_space(str(tp), case_id=f"demo_{canonical}")
        extra = None
        sdp = _space_source_data_paths(str(tp))

    elif canonical == "semiconductor":
        dd = samples / "semfab_tel_like"
        if not dd.exists():
            dd = samples / "semiconductor"
        result = _run_semiconductor(str(dd), case_id=f"demo_{canonical}")
        extra = _semiconductor_extra_outputs(result)
        sdp = _semiconductor_source_data_paths(str(dd))

    elif canonical == "semiforge":
        cp = samples / "semiforge_crossbar" / "config.json"
        if not cp.exists():
            cp = samples / "semiforge" / "config.json"
        result = _run_semiforge(str(cp), case_id=f"demo_{canonical}", mc=30)
        extra = None
        sdp = _semiforge_source_data_paths(str(cp))

    elif canonical == "memory":
        md = Path(__file__).parent / "sample_data" / "memory_device"
        if not md.exists():
            md = samples / "memory_device"
        if not md.exists():
            md = Path(__file__).parent.parent / "samples" / "memory_device"
        result = _run_memory(str(md), case_id=f"demo_{canonical}")
        extra = _memory_extra_outputs(result)
        sdp = _memory_source_data_paths(str(md))

    else:
        raise ValueError(
            f"Unknown domain {domain!r}. "
            f"Supported: {', '.join(SUPPORTED_DOMAINS)}"
        )

    _run_and_write(result, out_str, canonical, extra_outputs=extra, source_data_paths=sdp)
    return out_dir


def run_all_domain_demos_direct(*, out_dir: Path) -> dict[str, Path]:
    """Generate all five standard domain demos without spawning subprocesses.

    Parameters
    ----------
    out_dir:
        Base output directory.  Each domain is written to ``<out_dir>/<domain>/``.

    Returns
    -------
    dict[str, Path]
        ``{"robot": Path(...), "space": Path(...), ...}``
    """
    out_dir = Path(out_dir)
    results: dict[str, Path] = {}
    for dom in SUPPORTED_DOMAINS:
        dom_out = out_dir / dom
        results[dom] = run_domain_demo_direct(domain=dom, out_dir=dom_out)
    return results
