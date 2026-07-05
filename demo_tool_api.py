"""
YieldOS AI Tool API demo.
Demonstrates Token Idiot Index: how much fewer tokens an AI needs
when using YieldOS Tool API vs reading raw logs directly.

Usage:
  python demo_tool_api.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from yieldos.api.tool_api import YieldOSToolAPI
from yieldos.core.report_writer import ReportWriter
from yieldos.domains.robot import RobotAnalyzer
from yieldos.domains.satellite import SatGuardAnalyzer
from yieldos.domains.semfab import SemFabAnalyzer


def _token_estimate(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return max(1, len(text) // 4)


def _raw_log_tokens(data_dir: str) -> int:
    total = 0
    for f in Path(data_dir).glob("*.csv"):
        total += _token_estimate(f.read_text(encoding="utf-8"))
    return total


def _api_tokens(case_dir: str) -> int:
    api = YieldOSToolAPI(case_dir)
    summary = api.get_full_summary()
    return _token_estimate(json.dumps(summary, ensure_ascii=False))


def _recovery_dict(recovery: list) -> list:
    return [r.to_dict() for r in recovery]


def run_domain(domain: str, analyzer, input_path: str, out_dir: str, is_dir: bool = True) -> dict:
    print(f"\n{'='*60}")
    print(f"  Domain: {domain}")
    print(f"{'='*60}")

    if is_dir:
        result = analyzer.analyze(data_dir=input_path, case_id=f"demo_{domain}")
        raw_tokens = _raw_log_tokens(input_path)
    else:
        result = analyzer.analyze(telemetry_path=input_path, case_id=f"demo_{domain}")
        raw_tokens = _token_estimate(Path(input_path).read_text(encoding="utf-8"))

    # Write outputs
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    writer = ReportWriter()
    writer.write_all(out_dir, result["state"], result["evidence_pack"], result["ooda_frame"],
                     recovery_candidates=result["recovery_candidates"])

    api_tokens = _api_tokens(out_dir)
    tii = raw_tokens / max(api_tokens, 1)

    state = result["state"]
    pack = result["evidence_pack"]
    ooda = result["ooda_frame"]
    mr = result.get("mission_readiness")

    print(f"\n  State:      {state.state.value}")
    print(f"  Severity:   {state.severity.value}")
    print(f"  Confidence: {state.confidence:.0%}")
    if mr is not None:
        print(f"  Mission readiness: {mr:.0%}")
    print(f"\n  Summary: {pack.summary}")
    print(f"\n  OODA Decide: {ooda.decide}")
    print("\n  Root cause candidates:")
    for r in pack.root_cause_candidates[:3]:
        print(f"    [{r['confidence']:.0%}] {r['candidate']}")
    print("\n  Recovery candidates:")
    for r in result["recovery_candidates"][:3]:
        print(f"    -> {r.action}  (risk: {r.risk})")
    print("\n  Missing evidence:")
    for m in pack.missing_evidence[:3]:
        print(f"    ? {m}")

    print("\n  --- Token Efficiency ---")
    print(f"  Raw input tokens (est.):    {raw_tokens:>8,}")
    print(f"  Tool API tokens (est.):     {api_tokens:>8,}")
    print(f"  Token Idiot Index:          {tii:>8.1f}x  (target: >=10)")
    print(f"  Checksum: {pack.checksum[:40]}...")

    return {"domain": domain, "raw_tokens": raw_tokens, "api_tokens": api_tokens, "tii": tii}


def main():
    print("\n" + "="*60)
    print("  HAL YieldOS - AI Tool API Demo")
    print("  Read-Only Industrial Evidence Engine")
    print("="*60)

    results = []

    import os

    from yieldos.domains.robot.synthetic_gen import generate_all as gen_robot
    from yieldos.domains.satellite.synthetic_gen import generate_all as gen_sat

    # SemFab: use large dataset if available, else fall back to sample
    semfab_input = "samples/semfab_large" if os.path.exists("samples/semfab_large/tool_log.csv") else "samples/semfab_tel_like"
    results.append(run_domain(
        "semiconductor_fab",
        SemFabAnalyzer(),
        semfab_input,
        "output/demo_semfab",
        is_dir=True,
    ))

    # Robot: auto-generate large dataset if not present
    robot_large = "samples/robot_large/robot_telemetry.csv"
    if not os.path.exists(robot_large):
        print("\n[YieldOS] Generating large robot dataset (500 rows)...")
        gen_robot("samples/robot_large", n_samples=500)
    results.append(run_domain(
        "robotics",
        RobotAnalyzer(),
        robot_large,
        "output/demo_robot",
        is_dir=False,
    ))

    # Satellite: auto-generate large dataset if not present
    sat_large = "samples/sat_large/satellite_telemetry.csv"
    if not os.path.exists(sat_large):
        print("\n[YieldOS] Generating large satellite dataset (500 rows)...")
        gen_sat("samples/sat_large", n_samples=500)
    results.append(run_domain(
        "satellite",
        SatGuardAnalyzer(),
        sat_large,
        "output/demo_sat",
        is_dir=False,
    ))

    print(f"\n{'='*60}")
    print("  Summary: Token Idiot Index across domains")
    print(f"{'='*60}")
    print(f"  {'Domain':25s}  {'Raw':>8}  {'API':>6}  {'TII':>6}")
    print(f"  {'-'*52}")
    total_raw = total_api = 0
    for r in results:
        print(f"  {r['domain']:25s}  {r['raw_tokens']:>8,}  {r['api_tokens']:>6,}  {r['tii']:>6.1f}x")
        total_raw += r["raw_tokens"]
        total_api += r["api_tokens"]
    total_tii = total_raw / max(total_api, 1)
    print(f"  {'-'*52}")
    print(f"  {'TOTAL':25s}  {total_raw:>8,}  {total_api:>6,}  {total_tii:>6.1f}x")
    goal_met = total_tii >= 10
    print(f"\n  Goal: Token Idiot Index >= 10x  ->  {'[ACHIEVED]' if goal_met else '[below target - use larger dataset]'}")
    print()


if __name__ == "__main__":
    main()
