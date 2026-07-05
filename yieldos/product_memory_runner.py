"""
yieldos/product_memory_runner.py

Direct Python runner for the Product Memory Rebinning demo.

Used by both the CLI (cmd_memory_product_demo) and the test suite so that
both exercise exactly the same underlying logic without spawning a subprocess.

Public API
----------
run_product_memory_rebinning_demo_direct(*, out_dir) -> Path
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def run_product_memory_rebinning_demo_direct(*, out_dir: Path) -> Path:
    """Generate the Product Memory Rebinning demo without spawning a subprocess.

    This function mirrors cmd_memory_product_demo() in yieldos/cli/main.py.
    The CLI calls this function directly; tests call it directly too.

    Parameters
    ----------
    out_dir:
        Target output directory (created if it does not exist).

    Returns
    -------
    Path
        The output directory (same as *out_dir*).
    """
    from .cli.main import (
        _memory_extra_outputs,
        _memory_source_data_paths,
        _run_and_write,
        _run_memory,
        _sample_root,
    )

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    samples = _sample_root()
    demo_dir = samples / "product_memory_rebinning_demo"
    if not demo_dir.exists():
        raise FileNotFoundError(
            f"Product memory rebinning demo sample not found at {demo_dir}"
        )

    policy_path = demo_dir / "baseline_policy.json"

    result = _run_memory(str(demo_dir), case_id="product_demo_rebinning", asset_id="NAND_DEMO_32GB_MLC")
    extra = _memory_extra_outputs(result)
    _run_and_write(result, str(out_dir), "memory", extra_outputs=extra,
                   source_data_paths=_memory_source_data_paths(str(demo_dir)))

    # Enrich baseline_vs_yieldos.json with baseline_policy data (mirrors CLI logic)
    baseline_policy: dict = {}
    if policy_path.exists():
        baseline_policy = json.loads(policy_path.read_text(encoding="utf-8"))

    baseline_path = out_dir / "baseline_vs_yieldos.json"
    if baseline_path.exists():
        bvsy = json.loads(baseline_path.read_text(encoding="utf-8"))

        state_metrics = result["state"].metrics or {}
        n_discard = state_metrics.get("discard_blocks", 0)
        rules = baseline_policy.get("rules", {})
        max_rtb = rules.get("max_runtime_bad_blocks", 0)
        fc = result.get("functional_capacity") or {}

        bvsy["baseline_policy_name"] = baseline_policy.get("policy_name", "")
        bvsy["baseline_policy_rules"] = rules
        bvsy["binary_verdict_detail"] = (
            f"{n_discard} discard blocks detected: runtime_bad and/or uncorrectable blocks "
            f"exceed max_runtime_bad_blocks={max_rtb}. Binary policy verdict: FAIL."
        )
        bvsy["recovered_functional_capacity_estimate"] = {
            "safe_gb": fc.get("safe_capacity_gb", 0.0),
            "approximate_cache_gb": fc.get("approximate_cache_capacity_gb", 0.0),
            "read_only_archive_gb": fc.get("read_only_archive_capacity_gb", 0.0),
            "discard_gb": fc.get("discarded_capacity_gb", 0.0),
            "total_raw_gb": fc.get("raw_capacity_gb", 0.0),
            "note": "Capacity estimates for human review only. Not certified safe for deployment.",
        }
        bvsy["binary_policy_action_if_verdict_fail"] = "device_discard_or_hold_for_review"
        enriched_bytes = json.dumps(bvsy, indent=2, ensure_ascii=False).encode("utf-8")
        baseline_path.write_bytes(enriched_bytes)

        # Update case_manifest.json checksum to match the enriched baseline
        manifest_path = out_dir / "case_manifest.json"
        if manifest_path.exists():
            new_sha256 = "sha256:" + hashlib.sha256(enriched_bytes).hexdigest()
            cm = json.loads(manifest_path.read_text(encoding="utf-8"))
            if "files" in cm and "baseline_vs_yieldos" in cm["files"]:
                cm["files"]["baseline_vs_yieldos"]["sha256"] = new_sha256
                cm["files"]["baseline_vs_yieldos"]["byte_size"] = len(enriched_bytes)
                manifest_path.write_text(
                    json.dumps(cm, indent=2, ensure_ascii=False), encoding="utf-8"
                )

    return out_dir
