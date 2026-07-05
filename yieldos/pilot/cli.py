"""
yieldos/pilot/cli.py

CLI handler functions for `yieldos pilot init` and `yieldos pilot check`.
Called from yieldos/cli/main.py dispatch.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .init_pack import generate_init_pack
from .readiness import run_pilot_check


def cmd_pilot_init(args) -> int:
    """Handle: yieldos pilot init --domain <domain> --out <dir>"""
    domain = args.domain
    out_dir = Path(args.out)

    try:
        result_dir = generate_init_pack(domain=domain, out_dir=out_dir)
        print(f"[YieldOS Pilot Init] Domain: {domain}")
        print(f"[YieldOS Pilot Init] Output: {result_dir}")
        print("[YieldOS Pilot Init] Canonical files generated:")
        canonical = [
            "pilot_input_contract.json",
            "sample_file_manifest.json",
            "missing_data_request_template.json",
            "sanitization_checklist.md",
            "pilot_boundary_statement.md",
            "README.md",
        ]
        for fname in canonical:
            marker = "OK" if (result_dir / fname).exists() else "MISSING"
            print(f"  [{marker}] {fname}")
        print()
        print("Next step:")
        print("  Share missing_data_request_template.json with your data engineering team.")
        print("  Complete sanitization_checklist.md before sharing any data.")
        print(
            f"  Then run: yieldos pilot check --domain {domain} "
            f"--input <data_dir> --out <check_dir>"
        )
        return 0
    except ValueError as exc:
        print(f"[YieldOS Pilot Init] ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[YieldOS Pilot Init] Unexpected error: {exc}", file=sys.stderr)
        return 1


def cmd_pilot_check(args) -> int:
    """Handle: yieldos pilot check --domain <domain> --input <dir> --out <dir>"""
    domain = args.domain
    input_dir = Path(args.input)
    out_dir = Path(args.out)

    if not input_dir.exists():
        print(
            f"[YieldOS Pilot Check] ERROR: Input directory not found: {input_dir}",
            file=sys.stderr,
        )
        return 1

    try:
        result_dir = run_pilot_check(domain=domain, input_dir=input_dir, out_dir=out_dir)
        import json  # noqa: PLC0415

        report_path = result_dir / "pilot_readiness_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))

        status = report["status"]
        score = report["readiness_score"]
        blocking = report["blocking_issue_count"]

        print(f"[YieldOS Pilot Check] Domain: {domain}")
        print(f"[YieldOS Pilot Check] Status: {status}")
        print(f"[YieldOS Pilot Check] Readiness score: {score:.1%}")
        print(f"[YieldOS Pilot Check] Blocking issues: {blocking}")
        print(f"[YieldOS Pilot Check] Output: {result_dir}")
        print("[YieldOS Pilot Check] Canonical files generated:")
        canonical_check = [
            "pilot_readiness_report.json",
            "missing_data_request.json",
            "data_sufficiency_preview.json",
            "pilot_decision_boundary.json",
        ]
        for fname in canonical_check:
            marker = "OK" if (result_dir / fname).exists() else "MISSING"
            print(f"  [{marker}] {fname}")
        print()
        if status == "READY_FOR_FUNCTIONAL_YIELD_PILOT":
            print("Data is READY for functional yield pilot analysis.")
            print(
                f"  Run: yieldos {domain} analyze --input {input_dir} --out <output_dir>"
            )
        elif blocking > 0:
            print("Blocking issues found. Review missing_data_request.json for details.")
            print("Review pilot_decision_boundary.json for safety boundary information.")
        return 0
    except ValueError as exc:
        print(f"[YieldOS Pilot Check] ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[YieldOS Pilot Check] Unexpected error: {exc}", file=sys.stderr)
        return 1
