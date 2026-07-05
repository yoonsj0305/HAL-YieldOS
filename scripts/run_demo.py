#!/usr/bin/env python3
"""Deprecated compatibility wrapper — use: yieldos demo --all"""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    print("[run_demo.py] This script is deprecated. Use: yieldos demo --all --out <dir>")
    return subprocess.call(
        [sys.executable, "-m", "yieldos.cli.main", "demo", "--all", "--out", "output/demo_all"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
