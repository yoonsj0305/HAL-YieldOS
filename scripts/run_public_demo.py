#!/usr/bin/env python3
"""
HAL YieldOS — Public Demo Runner

Runs the complete public demonstration:
  1. Health check (yieldos doctor --deep)
  2. All 5 domain demos
  3. Strict validation for all 5 domains
  4. Semiconductor pilot-pack + strict validation
  5. Robot pilot-pack + strict validation

Usage:
    python scripts/run_public_demo.py [--out <output_dir>]

Safety note:
    This script does NOT run the Recovery Compiler.
    This script does NOT generate recovery_profile.json.
    This script does NOT control hardware, modify recipes, or execute recovery.
    All outputs are candidate evidence for human review.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


_DEMO_DOMAINS = ["robot", "space", "semiconductor", "semiforge", "memory"]
_TIMEOUT = 300  # seconds per command


def _run(cmd: list[str], *, label: str, timeout: int = _TIMEOUT) -> None:
    print(f"\n[DEMO] {label}")
    print(f"       $ {' '.join(cmd)}")
    result = subprocess.run(cmd, timeout=timeout)
    if result.returncode != 0:
        print(f"[FAIL] {label} exited with code {result.returncode}")
        sys.exit(result.returncode)
    print(f"[PASS] {label}")


def main() -> int:
    parser = argparse.ArgumentParser(description="HAL YieldOS public demo runner")
    parser.add_argument(
        "--out",
        default="output/public_demo",
        help="Output root directory (default: output/public_demo)",
    )
    args = parser.parse_args()
    out_root = Path(args.out)

    py = sys.executable
    yieldos = [py, "-m", "yieldos.cli.main"]

    print("=" * 60)
    print("HAL YieldOS -- Public Demo")
    print("read-only | candidate-only | human-review-required")
    print("=" * 60)

    # 1. Health check
    _run(yieldos + ["doctor", "--deep"], label="Health check (doctor --deep)")

    # 2. All 5 domain demos
    demo_out = str(out_root / "demo_all")
    _run(
        yieldos + ["demo", "--all", "--out", demo_out],
        label="5-domain demo",
        timeout=600,
    )

    # 3. Strict validation for all 5 domains
    for domain in _DEMO_DOMAINS:
        case_dir = str(out_root / "demo_all" / domain)
        _run(
            yieldos + ["validate", "--case", case_dir, "--strict"],
            label=f"Strict validation: {domain}",
        )

    # 4. Semiconductor pilot-pack
    semi_pilot_out = str(out_root / "semiconductor_pilot_pack")
    semi_input = "samples/pilot_semiconductor"
    if Path(semi_input).exists():
        _run(
            yieldos + [
                "semiconductor", "pilot-pack",
                "--input", semi_input,
                "--out", semi_pilot_out,
            ],
            label="Semiconductor pilot-pack",
            timeout=300,
        )
        _run(
            yieldos + ["validate", "--case", semi_pilot_out, "--strict"],
            label="Semiconductor pilot-pack strict validation",
        )
        _check_no_recovery_profile(semi_pilot_out)
    else:
        print(f"\n[SKIP] Semiconductor pilot sample not found at {semi_input}")

    # 5. Robot pilot-pack
    robot_pilot_out = str(out_root / "robot_pilot_pack")
    robot_input = "samples/pilot_robot"
    if Path(robot_input).exists():
        _run(
            yieldos + [
                "robot", "pilot-pack",
                "--input", robot_input,
                "--out", robot_pilot_out,
            ],
            label="Robot pilot-pack",
            timeout=300,
        )
        _run(
            yieldos + ["validate", "--case", robot_pilot_out, "--strict"],
            label="Robot pilot-pack strict validation",
        )
    else:
        print(f"\n[SKIP] Robot pilot sample not found at {robot_input}")

    # Generate output index
    _write_output_index(out_root)

    # Summary
    print("\n" + "=" * 60)
    print("[DONE] HAL YieldOS public demo complete.")
    print()
    print("Key outputs:")
    _print_if_exists(out_root / "INDEX.md")
    _print_if_exists(out_root / "semiconductor_pilot_pack" / "report.html")
    _print_if_exists(out_root / "semiconductor_pilot_pack" / "functional_passport.json")
    _print_if_exists(out_root / "robot_pilot_pack" / "report.html")
    _print_if_exists(out_root / "robot_pilot_pack" / "functional_passport.json")
    print()
    print("Safety:")
    print("  read_only=true")
    print("  candidate_only=true")
    print("  human_review_required=true")
    print("  hardware_control_enabled=false")
    print("  recovery_profile_generated=false")
    print("=" * 60)
    return 0


def _write_output_index(out_root: Path) -> None:
    """Write INDEX.md summarizing demo outputs and safety boundary."""
    index_path = out_root / "INDEX.md"
    content = """\
# HAL YieldOS Public Demo Output

## Generated bundles

- output/public_demo/demo_all/
- output/public_demo/semiconductor_pilot_pack/
- output/public_demo/robot_pilot_pack/

## Key files

### Semiconductor

- semiconductor_pilot_pack/functional_passport.json
- semiconductor_pilot_pack/semiconductor_recovery_compiler_export.json
- semiconductor_pilot_pack/semiconductor_handoff_manifest.json
- semiconductor_pilot_pack/report.html

### Robot

- robot_pilot_pack/functional_passport.json
- robot_pilot_pack/robot_human_review_packet.json
- robot_pilot_pack/report.html

## Safety boundary

- read-only
- candidate-only
- human-review-required
- no hardware control
- no Recovery Compiler execution
- recovery_profile.json is not generated by YieldOS

## Next step

Open report.html files in a browser and inspect functional_passport.json.
"""
    index_path.write_text(content, encoding="utf-8")
    print(f"[INDEX] {index_path}")


def _check_no_recovery_profile(out_dir: str) -> None:
    rp = Path(out_dir) / "recovery_profile.json"
    if rp.exists():
        print(f"[ERROR] recovery_profile.json found in {out_dir} — YieldOS must not generate this file.")
        sys.exit(1)
    print(f"[CHECK] recovery_profile.json not generated in {out_dir} (correct)")


def _print_if_exists(path: Path) -> None:
    if path.exists():
        print(f"  {path}")


if __name__ == "__main__":
    raise SystemExit(main())
