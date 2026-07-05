#!/usr/bin/env python3
"""
YieldOS CLI
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

# Domain alias → canonical domain name
DOMAIN_ALIASES = {
    "satellite": "space",
    "satguard": "space",
    "sat": "space",
    "semfab": "semiconductor",
    "edge_ai": "semiconductor",
    "dark_cell": "semiforge",
    "robot": "robot",
    "space": "space",
    "semiconductor": "semiconductor",
    "semiforge": "semiforge",
    "memory": "memory",
    "memory_device": "memory",
    "nand": "memory",
}

# Internal analyzer dispatch key from canonical
CANONICAL_TO_ANALYZER = {
    "robot": "robot",
    "space": "satellite",       # satellite domain folder
    "semiconductor": "semfab",  # semfab domain folder
    "semiforge": "semiforge",
    "memory": "memory",
}


def _resolve_domain(raw: str) -> tuple[str, str]:
    """Return (canonical, analyzer_key) for any raw domain string."""
    canonical = DOMAIN_ALIASES.get(raw.lower(), raw.lower())
    analyzer = CANONICAL_TO_ANALYZER.get(canonical, canonical)
    return canonical, analyzer


def _get_version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version
        try:
            return version("hal-yieldos")
        except PackageNotFoundError:
            pass
    except ImportError:
        pass
    vf = Path(__file__).parent.parent.parent / "VERSION"
    try:
        return vf.read_text().strip()
    except Exception:
        return "unknown"


def _sample_root() -> Path:
    """Path to embedded sample data (or external samples/ folder as fallback)."""
    pkg_samples = Path(__file__).parent.parent / "sample_data"
    if pkg_samples.exists():
        return pkg_samples
    # fallback: development samples/ folder
    return Path(__file__).parent.parent.parent / "samples"


def _print_completion(case_id: str, paths: dict, state=None, extra: dict = None) -> None:
    print(f"\n[YieldOS] Completed: {case_id}")
    if state:
        print(f"  State:      {state.state.value}")
        print(f"  Severity:   {state.severity.value}")
        print(f"  Confidence: {state.confidence:.0%}")
    if extra:
        for k, v in extra.items():
            print(f"  {k}: {v}")
    print("\n  Generated:")
    for k, v in paths.items():
        print(f"    - {Path(v).name}")
    print("\n  Safety:")
    print("    - read_only: true")
    print("    - hardware_execution_enabled: false")
    print("    - causal_boundary: candidate_only_not_certified_cause")


def _write_result_extras(result: dict, out_dir: str) -> None:
    """Write domain-specific extra files (time_alignment_report, evidence_graph, etc.)."""
    out_path = Path(out_dir)
    for key in ("time_alignment_report", "evidence_graph", "functional_yield_result",
                "optimizer_info"):
        if key in result and result[key]:
            fname = f"{key}.json"
            out_path.mkdir(parents=True, exist_ok=True)
            (out_path / fname).write_text(
                json.dumps(result[key], ensure_ascii=False, indent=2), encoding="utf-8"
            )


def _load_policy_inputs(args: argparse.Namespace) -> dict:
    """Load optional policy JSON files specified via --cvc / --authority / --envelope / --risk-policy."""
    policy: dict = {}
    for attr, key in [("cvc", "cvc"), ("authority", "authority_matrix"),
                      ("envelope", "operating_envelope"), ("risk_policy", "risk_policy")]:
        path_str = getattr(args, attr, None)
        if path_str:
            p = Path(path_str)
            if p.exists():
                try:
                    policy[key] = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    pass
    return policy or None


def _run_and_write(result: dict, out_dir: str, domain_canonical: str,
                   extra_outputs: dict | None = None,
                   source_data_paths: list | None = None,
                   policy_inputs: dict | None = None) -> dict:
    """Run ReportWriter with all v2.1+ bundle extras."""
    from ..core.report_writer import ReportWriter
    paths = ReportWriter().write_all(
        out_dir,
        result["state"],
        result["evidence_pack"],
        result["ooda_frame"],
        recovery_candidates=result.get("recovery_candidates", []),
        remaining_roles=result.get("remaining_roles", []),
        blocked_roles=result.get("blocked_roles", []),
        bin_class=result.get("bin_class"),
        decision_readiness=result.get("decision_readiness"),
        domain_canonical=domain_canonical,
        extra_outputs=extra_outputs,
        input_validation_override=result.get("input_validation"),
        source_data_paths=source_data_paths or result.get("source_data_paths"),
        policy_inputs=policy_inputs,
        optimizer_info_override=result.get("optimizer_info"),
    )
    _write_result_extras(result, out_dir)
    return paths


# ── Domain runner helpers ───────────────────────────────────────────────────

def _run_robot(telemetry_path: str, case_id=None, asset_id="robot_arm_07") -> dict:
    from ..domains.robot import RobotAnalyzer
    return RobotAnalyzer().analyze(telemetry_path=telemetry_path, case_id=case_id, asset_id=asset_id)


def _run_space(telemetry_path: str, case_id=None, asset_id="cubesat_01") -> dict:
    from ..domains.satellite import SatGuardAnalyzer
    return SatGuardAnalyzer().analyze(telemetry_path=telemetry_path, case_id=case_id, asset_id=asset_id)


def _run_semiconductor(data_dir: str, case_id=None, asset_id="ETCH_01.CH_A") -> dict:
    from ..domains.semfab import SemFabAnalyzer
    return SemFabAnalyzer().analyze(data_dir=data_dir, case_id=case_id, asset_id=asset_id)


def _run_semiforge(config_path: str, case_id=None, mc: int = 30, optimizer: str = "greedy") -> dict:
    from ..domains.semiforge import SemiForgeSimulator
    return SemiForgeSimulator().simulate(config_path=config_path, case_id=case_id,
                                         monte_carlo_runs=mc, optimizer=optimizer)


def _run_memory(input_dir: str, case_id=None, asset_id: str = "memdev_01") -> dict:
    from ..domains.memory import MemoryAnalyzer
    return MemoryAnalyzer().analyze(input_dir=input_dir, case_id=case_id, asset_id=asset_id)


# ── CLI commands ───────────────────────────────────────────────────────────

def cmd_demo(args: argparse.Namespace) -> int:
    """Run built-in demo for one or all domains."""
    run_all = getattr(args, "all", False)
    domain_raw = (getattr(args, "demo_domain", None) or ("all" if run_all else "all"))
    out_base = Path(getattr(args, "out", "output/demo_all"))
    samples = _sample_root()

    domains_to_run = []
    if domain_raw == "all" or run_all:
        domain_raw = "all"
        domains_to_run = ["robot", "space", "semiconductor", "semiforge", "memory"]
    else:
        canonical, _ = _resolve_domain(domain_raw)
        domains_to_run = [canonical]

    alias_used = domain_raw if domain_raw not in ("all",) else None

    all_ok = True
    for dom in domains_to_run:
        out_dir = str(out_base / dom) if domain_raw == "all" else str(out_base)
        print(f"\n[YieldOS] Demo: {dom} -> {out_dir}")
        try:
            if dom == "robot":
                tp = samples / "robot_ooda" / "robot_telemetry.csv"
                if not tp.exists():
                    tp = samples / "robot" / "robot_telemetry.csv"
                result = _run_robot(str(tp), case_id=f"demo_{dom}")
            elif dom == "space":
                tp = samples / "satguard" / "satellite_telemetry.csv"
                if not tp.exists():
                    tp = samples / "space" / "satellite_telemetry.csv"
                result = _run_space(str(tp), case_id=f"demo_{dom}")
            elif dom == "semiconductor":
                dd = samples / "semfab_tel_like"
                if not dd.exists():
                    dd = samples / "semiconductor"
                result = _run_semiconductor(str(dd), case_id=f"demo_{dom}")
            elif dom == "semiforge":
                cp = samples / "semiforge_crossbar" / "config.json"
                if not cp.exists():
                    cp = samples / "semiforge" / "config.json"
                result = _run_semiforge(str(cp), case_id=f"demo_{dom}", mc=30)
            elif dom == "memory":
                # Resolution order: sample_data (packaged wheel) → dev samples → fallback
                md = Path(__file__).parent.parent / "sample_data" / "memory_device"
                if not md.exists():
                    md = samples / "memory_device"
                if not md.exists():
                    md = Path(__file__).parent.parent.parent / "samples" / "memory_device"
                result = _run_memory(str(md), case_id=f"demo_{dom}")
            else:
                print(f"  [ERROR] Unknown domain: {dom}")
                all_ok = False
                continue

            if alias_used and alias_used != dom:
                result["domain_alias_used"] = alias_used

            if dom == "memory":
                extra = _memory_extra_outputs(result)
            elif dom == "semiconductor":
                extra = _semiconductor_extra_outputs(result)
            else:
                extra = None
            # Pass domain-specific source data paths for traceability manifest
            if dom == "robot":
                sdp = _robot_source_data_paths(str(tp))
            elif dom == "space":
                sdp = _space_source_data_paths(str(tp))
            elif dom == "semiconductor":
                sdp = _semiconductor_source_data_paths(str(dd))
            elif dom == "semiforge":
                sdp = _semiforge_source_data_paths(str(cp))
            elif dom == "memory":
                sdp = _memory_source_data_paths(str(md))
            else:
                sdp = None
            paths = _run_and_write(result, out_dir, dom, extra_outputs=extra,
                                   source_data_paths=sdp)
            _print_completion(result["case_id"], paths, result["state"])
        except Exception as exc:
            print(f"  [ERROR] Demo {dom} failed: {exc}")
            all_ok = False

    return 0 if all_ok else 1


def cmd_analyze(args: argparse.Namespace) -> int:
    """Unified analyze command dispatching by --domain."""
    domain_raw = args.domain
    canonical, analyzer = _resolve_domain(domain_raw)
    inp = args.input
    out = args.out
    case_id = getattr(args, "case", None)
    alias_used = domain_raw if domain_raw != canonical else None
    policy_inputs = _load_policy_inputs(args)

    print(f"[YieldOS] analyze --domain {domain_raw} (canonical: {canonical})")
    try:
        if analyzer == "robot":
            result = _run_robot(inp, case_id=case_id,
                                asset_id=getattr(args, "asset", "robot_arm_07"))
        elif analyzer == "satellite":
            result = _run_space(inp, case_id=case_id,
                                asset_id=getattr(args, "asset", "cubesat_01"))
        elif analyzer == "semfab":
            result = _run_semiconductor(inp, case_id=case_id,
                                        asset_id=getattr(args, "asset", "ETCH_01.CH_A"))
        elif analyzer == "semiforge":
            result = _run_semiforge(inp, case_id=case_id,
                                    mc=getattr(args, "mc", 30),
                                    optimizer=getattr(args, "optimizer", "greedy"))
        elif analyzer == "memory":
            result = _run_memory(inp, case_id=case_id,
                                 asset_id=getattr(args, "asset", "memdev_01"))
        else:
            print(f"[ERROR] Unknown domain '{domain_raw}'. Use: robot, space, semiconductor, semiforge, memory")
            return 1

        if alias_used:
            result["domain_alias_used"] = alias_used

        if analyzer == "memory":
            extra = _memory_extra_outputs(result)
            sdp = _memory_source_data_paths(inp)
        elif analyzer == "robot":
            extra = None
            sdp = _robot_source_data_paths(inp)
        elif analyzer == "satellite":
            extra = None
            sdp = _space_source_data_paths(inp)
        elif analyzer == "semfab":
            extra = _semiconductor_extra_outputs(result)
            sdp = _semiconductor_source_data_paths(inp)
        elif analyzer == "semiforge":
            extra = None
            sdp = _semiforge_source_data_paths(inp)
        else:
            extra = None
            sdp = None
        paths = _run_and_write(result, out, canonical, extra_outputs=extra,
                               policy_inputs=policy_inputs, source_data_paths=sdp)
        _print_completion(result["case_id"], paths, result["state"],
                          extra={"canonical_domain": canonical, "alias_used": alias_used} if alias_used else None)
        return 0
    except FileNotFoundError as exc:
        print(f"[ERROR] Input not found: {exc}")
        return 1
    except Exception as exc:
        _write_degraded_output(out, str(exc), case_id or f"case_{domain_raw}_error", canonical)
        print(f"[ERROR] Analysis failed: {exc}")
        return 1


def _write_degraded_output(out_dir: str, error_msg: str, case_id: str, domain: str) -> None:
    """Write structured error output instead of crashing."""
    from ..contracts.meta import SAFETY_BLOCK, SCHEMA_VERSION, generated_by
    base = Path(out_dir)
    base.mkdir(parents=True, exist_ok=True)

    analysis_error = {
        "schema": "hal.yieldos.analysis_error.v1",
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "domain_pack": domain,
        "error_type": "analysis_failure",
        "error_message": str(error_msg),
        "safe_to_continue": False,
        "generated_outputs": ["input_validation.json", "next_data_request.json", "analysis_error.json"],
        "generated_by": generated_by(),
    }
    (base / "analysis_error.json").write_text(
        json.dumps(analysis_error, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    input_validation = {
        "schema": "hal.yieldos.input_validation.v1",
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "domain_pack": domain,
        "status": "FAILED",
        "data_level": "DATA_INCOMPLETE",
        "error": str(error_msg),
        "safety_boundary": SAFETY_BLOCK,
        "generated_by": generated_by(),
    }
    (base / "input_validation.json").write_text(
        json.dumps(input_validation, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    next_data = {
        "schema": "hal.yieldos.next_data_request.v1",
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "domain_pack": domain,
        "current_readiness": "DATA_INCOMPLETE",
        "required_evidence": ["telemetry data file", "configuration file"],
        "note": "Analysis failed due to missing or invalid input.",
        "generated_by": generated_by(),
    }
    (base / "next_data_request.json").write_text(
        json.dumps(next_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def cmd_semifab_gen(args: argparse.Namespace) -> int:
    from ..domains.semfab.synthetic_gen import generate_all
    print(f"[YieldOS] Generating synthetic SemFab dataset -> {args.out}")
    info = generate_all(args.out, n_lots=args.lots, wafers_per_lot=args.wafers)
    print(f"[YieldOS] Generated: {info['tool_log_rows']} tool log rows, "
          f"{info['lots']} lots, {info['wafers']} wafers")
    print(f"[YieldOS] Output: {info['data_dir']}")
    return 0


def cmd_semifab_analyze(args: argparse.Namespace) -> int:
    print(f"[YieldOS] SemFab Shadow analysis: {args.input}")
    result = _run_semiconductor(
        args.input, case_id=getattr(args, "case", None),
        asset_id=getattr(args, "asset", "ETCH_01.CH_A"),
    )
    policy_inputs = _load_policy_inputs(args)
    paths = _run_and_write(result, args.out, "semiconductor",
                           extra_outputs=_semiconductor_extra_outputs(result),
                           policy_inputs=policy_inputs,
                           source_data_paths=_semiconductor_source_data_paths(args.input))
    _print_completion(result["case_id"], paths, result["state"])
    return 0


def cmd_semiforge_simulate(args: argparse.Namespace) -> int:
    mc = getattr(args, "mc", 30)
    optimizer = getattr(args, "optimizer", "greedy")
    asset = getattr(args, "asset", None)
    case_id = f"case_semiforge_{asset}" if asset else None
    print(f"[YieldOS] SemiForge simulation: {args.config} (MC runs={mc}, optimizer={optimizer})")
    result = _run_semiforge(args.config, case_id=case_id, mc=mc, optimizer=optimizer)

    opt_info = result.get("optimizer_info", {})
    if opt_info.get("fallback"):
        print("  [optimizer] Optimizer unavailable. Falling back to deterministic heuristic scheduler.")
        print("  [optimizer] Install SQBM with: pip install hal-yieldos[sqbm]")
    else:
        print(f"  [optimizer] backend={opt_info.get('used', optimizer)}")

    policy_inputs = _load_policy_inputs(args)
    paths = _run_and_write(result, args.out, "semiforge", policy_inputs=policy_inputs,
                           source_data_paths=_semiforge_source_data_paths(args.config))
    fy = result["functional_yield_result"]
    _print_completion(
        result["case_id"], paths, result["state"],
        extra={
            "Y_func": f"{fy['y_func']:.4f}",
            "r_conn": f"{fy['r_conn']:.4f}",
            "C_eff":  f"{fy['c_eff']:.4f}",
            "optimizer": opt_info.get("used", optimizer),
        },
    )
    return 0


def cmd_robot_gen(args: argparse.Namespace) -> int:
    from ..domains.robot.synthetic_gen import generate_all
    print(f"[YieldOS] Generating synthetic robot telemetry -> {args.out}")
    info = generate_all(args.out, n_samples=args.samples)
    print(f"[YieldOS] Generated: {info['rows']} rows, joint {info['joint_id']}")
    print(f"[YieldOS] Degradation starts at row {info['degradation_start']}, "
          f"fault at row {info['fault_start']}")
    return 0


def cmd_sat_gen(args: argparse.Namespace) -> int:
    from ..domains.satellite.synthetic_gen import generate_all
    print(f"[YieldOS] Generating synthetic satellite telemetry -> {args.out}")
    info = generate_all(args.out, n_samples=args.samples)
    print(f"[YieldOS] Generated: {info['rows']} rows, asset {info['asset_id']}")
    print(f"[YieldOS] Degradation starts at row {info['degradation_start']}, "
          f"fault at row {info['fault_start']}")
    return 0


def cmd_robot_analyze(args: argparse.Namespace) -> int:
    print(f"[YieldOS] RobotOODA analysis: {args.input}")
    result = _run_robot(
        args.input, case_id=getattr(args, "case", None),
        asset_id=getattr(args, "asset", "robot_arm_07"),
    )
    extra_outputs = {}
    maint_log = getattr(args, "maintenance_log", None)
    op_log = getattr(args, "operation_log", None)
    env_log = getattr(args, "environment_log", None)
    if maint_log or op_log or env_log:
        from ..domains.robot.incident_memory import (
            build_fleet_failure_memory,
            build_incident_timeline,
            build_industrial_data_record,
            load_industrial_data,
        )
        print("[YieldOS] Loading industrial data sources...")
        data = load_industrial_data(
            telemetry_path=args.input,
            maintenance_log_path=maint_log,
            operation_log_path=op_log,
            environment_log_path=env_log,
        )
        case_id = result.get("case_id", "")
        asset_id = getattr(args, "asset", "robot_arm_07")
        snapshot_hash = result["state"].snapshot_hash if result.get("state") else ""
        timeline = build_incident_timeline(
            data["telemetry"], data["maintenance_log"], data["operation_log"],
            case_id=case_id, asset_id=asset_id,
        )
        industrial_record = build_industrial_data_record(
            data["telemetry"], data["maintenance_log"], data["operation_log"],
            data["environment_log"], case_id=case_id, asset_id=asset_id,
        )
        fleet_mem = build_fleet_failure_memory(
            industrial_record, timeline,
            state_snapshot_hash=snapshot_hash, case_id=case_id, asset_id=asset_id,
        )
        extra_outputs["incident_timeline"] = timeline
        extra_outputs["industrial_data_record"] = industrial_record
        extra_outputs["fleet_failure_memory"] = fleet_mem
        print(f"  [INFO] incident_timeline: {timeline['total_events']} events")
        print(f"  [INFO] industrial_data_record: {industrial_record['data_sources']}")
    policy_inputs = _load_policy_inputs(args)
    paths = _run_and_write(result, args.out, "robot", extra_outputs=extra_outputs or None,
                           policy_inputs=policy_inputs,
                           source_data_paths=_robot_source_data_paths(args.input))
    _print_completion(result["case_id"], paths, result["state"])
    return 0


def cmd_robot_pilot_pack(args: argparse.Namespace) -> int:
    import csv as _csv

    from ..domains.robot.field_aliases import (
        apply_aliases,
        build_field_mapping_report,
        detect_aliases,
    )
    from ..domains.robot.pilot_pack import build_pilot_case_summary_md, generate_pilot_pack
    from ..domains.robot.unit_normalization import build_unit_normalization_report

    input_dir = Path(args.input)
    out_dir = Path(args.out)
    asset_id = getattr(args, "asset", "robot_pilot_01")
    case_id_arg = getattr(args, "case", None)

    if not input_dir.exists():
        print(f"[ERROR] Input directory not found: {input_dir}")
        return 1
    telemetry_path = input_dir / "robot_telemetry.csv"
    if not telemetry_path.exists():
        print(f"[ERROR] robot_telemetry.csv not found in {input_dir}")
        return 1

    print(f"[YieldOS] Robot pilot-pack: {input_dir} -> {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load telemetry for alias detection + unit check
    with telemetry_path.open(encoding="utf-8") as _f:
        _reader = _csv.DictReader(_f)
        rows = list(_reader)
        columns = list(_reader.fieldnames or [])

    alias_map = detect_aliases(columns)
    if alias_map:
        print(f"  [INFO] field aliases detected: {alias_map}")
        rows = apply_aliases(rows, alias_map)
        # Recompute canonical columns after remapping
        canonical_cols = list(rows[0].keys()) if rows else columns

        # Write remapped telemetry for analyzer
        mapped_path = out_dir / "_mapped_telemetry_tmp.csv"
        with mapped_path.open("w", encoding="utf-8", newline="") as _mf:
            _dw = _csv.DictWriter(_mf, fieldnames=canonical_cols)
            _dw.writeheader()
            _dw.writerows(rows)
        analyzer_input = str(mapped_path)
    else:
        canonical_cols = columns
        analyzer_input = str(telemetry_path)

    # Run main robot analysis
    result = _run_robot(analyzer_input, case_id=case_id_arg, asset_id=asset_id)

    # Clean up temp file
    if alias_map:
        tmp_p = out_dir / "_mapped_telemetry_tmp.csv"
        if tmp_p.exists():
            tmp_p.unlink()

    case_id = result["case_id"]

    # Unit normalization report (always generated)
    unit_norm = build_unit_normalization_report(canonical_cols, rows, case_id, alias_map)

    # Field mapping report (only if aliases detected)
    extra_outputs: dict = {"robot_unit_normalization_report": unit_norm}
    if alias_map:
        extra_outputs["robot_field_mapping_report"] = build_field_mapping_report(
            columns, alias_map, case_id
        )

    # Generate 6 pilot-specific JSON reports
    pilot_reports = generate_pilot_pack(
        input_dir=str(input_dir),
        analysis_result=result,
        case_id=case_id,
        asset_id=asset_id,
        alias_map=alias_map,
        columns=canonical_cols,
        rows=rows,
    )
    extra_outputs.update(pilot_reports)

    # Write standard 22-file bundle + pilot extras
    source_paths = [str(input_dir / f) for f in (
        "robot_telemetry.csv", "maintenance_log.csv", "operator_notes.csv",
        "sim_expectation.csv", "intervention_log.csv", "force_torque_log.csv",
    )]
    paths = _run_and_write(result, str(out_dir), "robot",
                           extra_outputs=extra_outputs,
                           source_data_paths=source_paths)

    # Write robot_pilot_case_summary.md directly (not JSON, not via write_all)
    rpr = pilot_reports.get("robot_pilot_readiness_report", {})
    ecr = pilot_reports.get("robot_evidence_completeness_report", {})
    summary_md = build_pilot_case_summary_md(
        case_id=case_id,
        asset_id=asset_id,
        readiness_status=rpr.get("readiness_status", "UNKNOWN"),
        readiness_score=rpr.get("readiness_score", 0.0),
        remaining_roles=result.get("remaining_roles") or [],
        blocked_roles=result.get("blocked_roles") or [],
        bin_class=result.get("bin_class") or "unknown",
        slip_events=ecr.get("completeness_summary", {}).get("slip_events_detected", 0),
        contact_events=ecr.get("completeness_summary", {}).get("contact_instability_events", 0),
        interventions=ecr.get("completeness_summary", {}).get("human_interventions_recorded", 0),
        files_missing=rpr.get("required_files_missing", []),
    )
    (out_dir / "robot_pilot_case_summary.md").write_text(summary_md, encoding="utf-8")
    paths["robot_pilot_case_summary"] = str(out_dir / "robot_pilot_case_summary.md")

    print(f"  [INFO] pilot readiness:      {rpr.get('readiness_status', 'N/A')} "
          f"(score={rpr.get('readiness_score', 0.0):.2f})")
    print(f"  [INFO] evidence completeness: "
          f"{ecr.get('completeness_summary', {}).get('completeness_status', 'N/A')}")
    print(f"  [INFO] remaining roles:      {result.get('remaining_roles', [])}")
    print(f"  [INFO] blocked roles:        {result.get('blocked_roles', [])}")
    _print_completion(case_id, paths, result["state"])
    return 0


def cmd_semiconductor_pilot_pack(args: argparse.Namespace) -> int:
    import csv as _csv

    from ..domains.semfab.field_aliases import (
        apply_aliases,
        build_field_mapping_report,
        detect_aliases,
    )
    from ..domains.semfab.pilot_pack import build_pilot_case_summary_md, generate_pilot_pack
    from ..domains.semfab.unit_normalization import build_unit_normalization_report

    input_dir = Path(args.input)
    out_dir = Path(args.out)
    asset_id = getattr(args, "asset", "chip_demo_001")
    case_id_arg = getattr(args, "case", None)

    if not input_dir.exists():
        print(f"[ERROR] Input directory not found: {input_dir}")
        return 1
    tool_log_path = input_dir / "tool_log.csv"
    if not tool_log_path.exists():
        print(f"[ERROR] tool_log.csv not found in {input_dir}")
        return 1

    print(f"[YieldOS] Semiconductor pilot-pack: {input_dir} -> {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load tool_log for alias detection + unit check
    with tool_log_path.open(encoding="utf-8") as _f:
        _reader = _csv.DictReader(_f)
        tool_rows = list(_reader)
        tool_cols = list(_reader.fieldnames or [])

    alias_map = detect_aliases(tool_cols)
    if alias_map:
        print(f"  [INFO] field aliases detected: {alias_map}")
        tool_rows = apply_aliases(tool_rows, alias_map)
        tool_cols = list(tool_rows[0].keys()) if tool_rows else tool_cols

    # Load metrology and test_results
    def _load_csv_file(fname):
        p = input_dir / fname
        if not p.exists():
            return []
        with p.open(encoding="utf-8") as _f:
            return list(_csv.DictReader(_f))

    metro_rows = _load_csv_file("metrology.csv")
    test_rows = _load_csv_file("test_results.csv")

    # Run standard SemFab analyzer to get the standard bundle result
    result = _run_semiconductor(str(input_dir), case_id=case_id_arg, asset_id=asset_id)
    case_id = result["case_id"]

    # Unit normalization report
    unit_norm = build_unit_normalization_report(tool_cols, tool_rows, case_id, alias_map)

    extra_outputs: dict = {"semiconductor_unit_normalization_report": unit_norm}
    if alias_map:
        extra_outputs["semiconductor_field_mapping_report"] = build_field_mapping_report(
            tool_cols, alias_map, case_id
        )

    # Generate all 11 pilot-specific JSON reports
    pilot_reports = generate_pilot_pack(
        input_dir=str(input_dir),
        case_id=case_id,
        asset_id=asset_id,
        alias_map=alias_map,
        tool_cols=tool_cols,
        tool_rows=tool_rows,
        metro_rows=metro_rows,
        test_rows=test_rows,
    )
    extra_outputs.update(pilot_reports)

    # Source data paths for source_data_manifest (all existing input files)
    _pilot_input_files = [
        "tool_log.csv", "metrology.csv", "test_results.csv",
        "wafer_map.csv", "lot_genealogy.csv", "chamber_log.csv",
        "inspection_notes.csv", "recipe_context_redacted.json",
        "chip_tile_map.json", "workload_roles.json", "recovery_constraints.json",
    ]
    source_paths = [str(input_dir / f) for f in _pilot_input_files
                    if (input_dir / f).exists()]

    # Write standard YieldOS case bundle (22+ files) + semiconductor pilot extras
    paths = _run_and_write(result, str(out_dir), "semiconductor",
                           extra_outputs=extra_outputs,
                           source_data_paths=source_paths)

    # Write semiconductor_pilot_case_summary.md (not JSON, not via write_all)
    rpr = pilot_reports.get("semiconductor_pilot_readiness_report", {})
    rcm = pilot_reports.get("semiconductor_role_candidate_map", {})
    intake = pilot_reports.get("semiconductor_recovery_compiler_intake_preview", {})
    wds = pilot_reports.get("semiconductor_wafer_die_summary", {})
    mer = pilot_reports.get("semiconductor_missing_evidence_request", {})
    summary_md = build_pilot_case_summary_md(
        case_id=case_id,
        asset_id=asset_id,
        readiness_status=rpr.get("readiness_status", "UNKNOWN"),
        readiness_score=rpr.get("readiness_score", 0.0),
        remaining_roles=rcm.get("remaining_roles", []),
        reduced_roles=rcm.get("reduced_roles", []),
        blocked_roles=rcm.get("blocked_roles", []),
        intake_status=intake.get("handoff_status", "NOT_READY_FOR_COMPILER_HANDOFF"),
        missing_items=[m.get("item", "") for m in mer.get("missing_items", [])],
        lot_ids=wds.get("lot_ids", []),
        wafer_count=len(wds.get("wafer_ids", [])),
        die_pass=wds.get("die_count_pass", 0),
        die_fail=wds.get("die_count_fail", 0),
    )
    (out_dir / "semiconductor_pilot_case_summary.md").write_text(summary_md, encoding="utf-8")
    paths["semiconductor_pilot_case_summary"] = str(out_dir / "semiconductor_pilot_case_summary.md")

    # ── v3.0.3: Post-patch standard outputs for semiconductor pilot contract alignment ──
    intake_data = pilot_reports.get("semiconductor_recovery_compiler_intake_preview", {})
    _pilot_ctx = {
        "evidence_completeness_report_ref": "semiconductor_evidence_completeness_report.json",
        "wafer_die_summary_ref": "semiconductor_wafer_die_summary.json",
        "functional_region_map_ref": "semiconductor_functional_region_map.json",
        "role_candidate_map_ref": "semiconductor_role_candidate_map.json",
        "valid_conditions_report_ref": "semiconductor_valid_conditions_report.json",
        "process_evidence_report_ref": "semiconductor_process_evidence_report.json",
        "human_review_packet_ref": "semiconductor_human_review_packet.json",
        "missing_evidence_request_ref": "semiconductor_missing_evidence_request.json",
        "recovery_compiler_intake_preview_ref": "semiconductor_recovery_compiler_intake_preview.json",
        "recovery_compiler_handoff_boundary_ref": "semiconductor_recovery_compiler_handoff_boundary.json",
        "recovery_compiler_export_ref": "semiconductor_recovery_compiler_export.json",
        "handoff_manifest_ref": "semiconductor_handoff_manifest.json",
        "pilot_case_summary_ref": "semiconductor_pilot_case_summary.md",
    }
    fp_path = out_dir / "functional_passport.json"
    if fp_path.exists():
        fp_data = json.loads(fp_path.read_text(encoding="utf-8"))
        fp_data["semiconductor_pilot_context"] = _pilot_ctx
        fp_path.write_text(json.dumps(fp_data, ensure_ascii=False, indent=2), encoding="utf-8")

    drr_path = out_dir / "decision_readiness_report.json"
    if drr_path.exists():
        drr = json.loads(drr_path.read_text(encoding="utf-8"))
        drr["allowed_decisions"] = [
            "request_missing_data",
            "accept_for_offline_functional_yield_review",
            "allow_recovery_compiler_intake_preview",
            "allow_recovery_compiler_export_for_offline_testing",
            "reject_due_to_insufficient_evidence",
        ]
        drr["forbidden_decisions"] = [
            "modify_recipe", "control_equipment", "execute_recovery_profile",
            "claim_root_cause", "guarantee_yield", "certify_timing",
            "flash_firmware", "runtime_apply_profile",
        ]
        drr["automatic_decision_enabled"] = False
        drr["hardware_control_enabled"] = False
        drr["recipe_control_enabled"] = False
        drr["tool_control_enabled"] = False
        drr["human_review_required"] = True
        drr["claim_boundary"] = "decision_readiness_not_operational_authority"
        drr_path.write_text(json.dumps(drr, ensure_ascii=False, indent=2), encoding="utf-8")

    ss_path = out_dir / "state_snapshot.json"
    if ss_path.exists():
        ss = json.loads(ss_path.read_text(encoding="utf-8"))
        ss["snapshot_type"] = "semiconductor_pilot_candidate_state"
        ss["candidate_state"] = {
            "remaining_functions_present": len(result.get("remaining_roles", [])) > 0,
            "blocked_functions_present": len(result.get("blocked_roles", [])) > 0,
            "valid_conditions_present": True,
            "missing_evidence_present": bool(intake_data.get("handoff_inputs")),
            "human_review_required": True,
            "recovery_compiler_intake_ready": (
                intake_data.get("handoff_status") == "READY_FOR_OFFLINE_COMPILER_TEST"
            ),
        }
        ss["linked_reports"] = {
            "functional_region_map_ref": "semiconductor_functional_region_map.json",
            "role_candidate_map_ref": "semiconductor_role_candidate_map.json",
            "valid_conditions_report_ref": "semiconductor_valid_conditions_report.json",
            "recovery_compiler_intake_preview_ref": "semiconductor_recovery_compiler_intake_preview.json",
            "recovery_compiler_export_ref": "semiconductor_recovery_compiler_export.json",
        }
        _safety = ss.get("safety", {})
        _safety["recovery_profile_generated"] = False
        _safety["recipe_control_enabled"] = False
        _safety["tool_control_enabled"] = False
        _safety["claim_boundary"] = "candidate_state_snapshot_not_operational_authority"
        ss["safety"] = _safety
        ss_path.write_text(json.dumps(ss, ensure_ascii=False, indent=2), encoding="utf-8")

    ooda_path = out_dir / "ooda_frame.json"
    if ooda_path.exists():
        ooda = json.loads(ooda_path.read_text(encoding="utf-8"))
        ooda["act"] = {
            "automatic_action_enabled": False,
            "hardware_control_enabled": False,
            "recipe_control_enabled": False,
            "tool_control_enabled": False,
            "claim_boundary": "ooda_frame_not_operational_authority",
        }
        ooda["decide"] = {
            "allowed_decisions": [
                "request_missing_data",
                "accept_for_offline_functional_yield_review",
                "allow_recovery_compiler_intake_preview",
                "allow_recovery_compiler_export_for_offline_testing",
                "reject_due_to_insufficient_evidence",
            ],
            "forbidden_decisions": [
                "modify_recipe", "control_equipment", "execute_recovery_profile",
                "claim_root_cause", "guarantee_yield", "certify_timing",
            ],
            "human_review_required": True,
        }
        ooda_path.write_text(json.dumps(ooda, ensure_ascii=False, indent=2), encoding="utf-8")

    # Add pilot-pack export note to HTML (confidence section already written by write_all)
    html_path = out_dir / "report.html"
    if html_path.exists():
        _html = html_path.read_text(encoding="utf-8")
        _semi_note = (
            '<div class="semi-pilot-export-note">'
            "<p>semiconductor_recovery_compiler_export.json has been generated. "
            "This is <strong>not a recovery profile</strong>. It is a candidate-only export "
            "artifact for offline HAL Recovery Compiler testing. "
            "human review required before compiler execution. "
            "Do not apply to hardware without separate runtime authorization.</p>"
            "</div>"
        )
        if "</body>" in _html:
            _html = _html.replace("</body>", _semi_note + "</body>")
        else:
            _html += _semi_note
        html_path.write_text(_html, encoding="utf-8")

    # Update case_manifest checksums for all post-patched files
    _patched = [
        "functional_passport.json", "decision_readiness_report.json",
        "state_snapshot.json", "ooda_frame.json", "report.html", "report.md",
    ]
    _cm_path = out_dir / "case_manifest.json"
    if _cm_path.exists():
        _cm = json.loads(_cm_path.read_text(encoding="utf-8"))
        _cm_files = _cm.get("files", {})
        for _entry in _cm_files.values():
            _fname = _entry.get("path", "")
            if _fname in _patched:
                _fp2 = out_dir / _fname
                if _fp2.exists():
                    _entry["sha256"] = "sha256:" + hashlib.sha256(_fp2.read_bytes()).hexdigest()
                    _entry["byte_size"] = _fp2.stat().st_size
        _cm_path.write_text(json.dumps(_cm, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  [INFO] pilot readiness:          {rpr.get('readiness_status', 'N/A')} "
          f"(score={rpr.get('readiness_score', 0.0):.2f})")
    print(f"  [INFO] recovery compiler intake: {intake.get('handoff_status', 'N/A')}")
    print(f"  [INFO] remaining roles:          {rcm.get('remaining_roles', [])}")
    print(f"  [INFO] blocked roles:            {rcm.get('blocked_roles', [])}")
    _print_completion(case_id, paths, result["state"])
    print("[YieldOS] Semiconductor pilot-pack complete.")
    print("  Safety: read_only=true | hardware_control_enabled=false | human_review_required=true")
    print("  Boundary: candidate_only - no recipe control, no equipment control, no root-cause claim")
    return 0


def cmd_robot_import_check(args: argparse.Namespace) -> int:
    from ..domains.robot.import_check import run_import_check
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input directory not found: {input_path}")
        return 1
    out_path = Path(args.out)
    print(f"[YieldOS] Robot import-check: {input_path} -> {out_path}")
    import_report, _pilot = run_import_check(str(input_path), str(out_path))
    print(f"  [INFO] schema_status:    {import_report['schema_status']}")
    print(f"  [INFO] privacy_status:   {import_report['privacy_status']}")
    print(f"  [INFO] readiness_status: {import_report['readiness_status']}")
    if import_report["missing_required_files"]:
        print(f"  [WARN] missing files:    {import_report['missing_required_files']}")
    if import_report["detected_sensitive_fields"]:
        print(f"  [WARN] sensitive fields: {import_report['detected_sensitive_fields']}")
    print(f"  [INFO] next_step:        {import_report['recommended_next_step']}")
    print(f"[YieldOS] import-check complete -> {out_path}")
    return 0 if import_report["schema_status"] != "FAILED" else 1


def cmd_robot_skill_demo(args: argparse.Namespace) -> int:
    from ..domains.robot.skill_memory import RobotSkillMemoryLayer
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)
    input_dir = getattr(args, "input", None)
    if input_dir:
        print(f"[YieldOS] Robot Skill Memory demo (external: {input_dir}) -> {out_path}")
    else:
        print(f"[YieldOS] Robot Skill Memory demo -> {out_path}")
    layer = RobotSkillMemoryLayer()
    r = layer.run_demo(out_dir=str(out_path), input_dir=input_dir)
    print(f"  [INFO] case_id:            {r['case_id']}")
    print(f"  [INFO] operator_skill_note: {r['operator_skill_note']['note_count']} notes")
    print(f"  [INFO] interventions:       {r['human_intervention_timeline']['intervention_count']}")
    print(f"  [INFO] skill_mappings:      {r['skill_to_evidence_map']['mapping_count']}")
    print(f"  [INFO] gap_events:          {r['sim_to_real_gap_report']['summary']['sim_success_real_failure_count']}")
    print(f"  [INFO] force_events:        {r['force_compliance_event_log']['summary']['total_force_events']}")
    print("  [INFO] case_study:          robot_skill_memory_case_study.json")
    print("  [INFO] before_after:        before_after_functional_reclassification.json")
    print("[YieldOS] Robot Skill Memory demo complete")
    return 0


def cmd_sat_analyze(args: argparse.Namespace) -> int:
    print(f"[YieldOS] SatGuard analysis: {args.input}")
    result = _run_space(
        args.input, case_id=getattr(args, "case", None),
        asset_id=getattr(args, "asset", "cubesat_01"),
    )
    mr = result.get("mission_readiness", "N/A")
    policy_inputs = _load_policy_inputs(args)
    paths = _run_and_write(result, args.out, "space", policy_inputs=policy_inputs,
                           source_data_paths=_space_source_data_paths(args.input))
    _print_completion(
        result["case_id"], paths, result["state"],
        extra={"mission_readiness": f"{mr:.0%}" if isinstance(mr, float) else mr},
    )
    return 0


def cmd_sat_orbit_demo(args: argparse.Namespace) -> int:
    """Run YieldOS-Orbit demo on bundled CubeSat power degradation sample."""
    from ..domains.satellite.orbit_demo import run_orbit_demo
    asset_id = getattr(args, "asset", "cubesat_demo_01")
    out = args.out
    print(f"[YieldOS] Orbit demo analysis -> {out}")
    try:
        demo_result = run_orbit_demo(out_dir=out, asset_id=asset_id)
    except Exception as exc:
        print(f"[ERROR] Orbit demo failed: {exc}")
        return 1
    state = demo_result.get("state")
    case_id = demo_result.get("case_id", "orbit_demo")
    paths = demo_result.get("paths", {})
    orbit_rec = demo_result.get("orbit_recommendation", {})
    print(f"  case_id: {case_id}")
    print(f"  state: {state.state.value if state else 'unknown'}")
    print(f"  severity: {state.severity.value if state else 'unknown'}")
    print(f"  orbit_mode: {orbit_rec.get('orbit_mode_recommendation', 'N/A')}")
    print(f"  payload_recommendation: {orbit_rec.get('payload_recommendation', 'N/A')}")
    print(f"  outputs: {len(paths)} files -> {out}")
    print("  [PASS] Orbit demo complete. Human review required before any action.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Unified run command: dispatches by --domain."""
    domain = args.run_domain
    canonical, analyzer = _resolve_domain(domain)
    inp = args.input
    out = args.out

    if analyzer == "semfab":
        print(f"[YieldOS] run semiconductor: {inp}")
        result = _run_semiconductor(inp, case_id=getattr(args, "case", None))
    elif analyzer == "semiforge":
        print(f"[YieldOS] run semiforge: {inp}")
        result = _run_semiforge(inp)
    elif analyzer == "robot":
        print(f"[YieldOS] run robot: {inp}")
        result = _run_robot(inp, case_id=getattr(args, "case", None))
    elif analyzer == "satellite":
        print(f"[YieldOS] run space: {inp}")
        result = _run_space(inp, case_id=getattr(args, "case", None))
    elif analyzer == "memory":
        print(f"[YieldOS] run memory: {inp}")
        result = _run_memory(inp, case_id=getattr(args, "case", None))
    else:
        print(f"[ERROR] Unknown domain '{domain}'. Use: robot, space, semiconductor, semiforge, memory")
        return 1

    if analyzer == "memory":
        extra = _memory_extra_outputs(result)
        paths = _run_and_write(result, out, canonical, extra_outputs=extra,
                               source_data_paths=_memory_source_data_paths(inp))
    else:
        paths = _run_and_write(result, out, canonical)
    _print_completion(result["case_id"], paths, result["state"])
    return 0


# ── Validate ───────────────────────────────────────────────────────────────

STRICT_REQUIRED_FILES = [
    "input_validation.json",
    "decision_readiness_report.json",
    "functional_yield_scorecard.json",
    "functional_binning_result.json",
    "functional_passport.json",
    "evidence_pack.json",
    "evidence_pack.md",
    "recovery_route_report.json",
    "failure_scenario_record.json",
    "next_data_request.json",
    "case_manifest.json",
    "report.html",
]

FORBIDDEN_REPORT_TERMS = [
    "space-grade", "nasa-grade", "flight-qualified", "mission-certified",
    "jedec-qualified", "production-proven", "certified root cause",
    "autonomous recovery", "live control", "controller replacement",
    "guaranteed yield improvement",
]


def cmd_validate(args: argparse.Namespace) -> int:
    case_dir = Path(args.case)
    strict = getattr(args, "strict", False)
    mode_label = "STRICT" if strict else "STANDARD"
    print(f"[YieldOS] Validating case ({mode_label}): {case_dir}")
    passed = 0
    failed = 0

    def _check(condition: bool, msg_pass: str, msg_fail: str) -> bool:
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {msg_pass}")
            passed += 1
        else:
            print(f"  [FAIL] {msg_fail}")
            failed += 1
        return condition

    # Standard file existence checks
    for fname in ["state_snapshot.json", "evidence_pack.json", "ooda_frame.json", "report.html"]:
        _check((case_dir / fname).exists(), f"{fname} exists", f"{fname} MISSING")

    pack_path = case_dir / "evidence_pack.json"
    if not pack_path.exists():
        print(f"\n[YieldOS] Validation FAILED: {failed} check(s) failed, {passed} passed")
        return 1

    pack = json.loads(pack_path.read_text(encoding="utf-8"))

    # Checksum
    stored = pack.get("checksum", "")
    payload = {
        "schema": pack.get("schema", ""),
        "case_id": pack.get("case_id", ""),
        "domain": pack.get("domain", ""),
        "asset_id": pack.get("asset_id", ""),
        "summary": pack.get("summary", ""),
        "causal_claim_boundary": pack.get("causal_claim_boundary", ""),
        "evidence_objects": pack.get("evidence_objects", []),
        "root_cause_candidates": pack.get("root_cause_candidates", []),
        "missing_evidence": pack.get("missing_evidence", []),
        "state_snapshot_ref": pack.get("state_snapshot_ref", ""),
        "state_snapshot_hash": pack.get("state_snapshot_hash", ""),
        "created_at": pack.get("created_at", ""),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected = "sha256:" + hashlib.sha256(blob).hexdigest()
    _check(stored == expected, f"Checksum valid ({stored[:20]}...)", "Checksum MISMATCH")

    _check(
        pack.get("causal_claim_boundary") == "candidate_only_not_certified_cause",
        "causal_claim_boundary: candidate_only_not_certified_cause",
        "causal_claim_boundary violated",
    )

    # Recovery candidates safety
    rec_path = case_dir / "recovery_candidates.json"
    if rec_path.exists():
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        hw_enabled = any(r.get("hardware_execution_enabled", False) for r in rec)
        _check(not hw_enabled,
               "recovery_candidates: hardware_execution_enabled=false",
               "recovery_candidates: hardware_execution_enabled=TRUE (SAFETY VIOLATION)")

    # State snapshot
    state_path = case_dir / "state_snapshot.json"
    if state_path.exists():
        state_data = json.loads(state_path.read_text(encoding="utf-8"))
        _check(state_data.get("mode") == "read_only_shadow", "mode: read_only_shadow", "mode violated")
        _check("schema" in state_data, "state_snapshot has schema", "state_snapshot missing schema")
        _check("schema_version" in state_data, "state_snapshot has schema_version", "state_snapshot missing schema_version")
        _check("generated_by" in state_data, "state_snapshot has generated_by", "state_snapshot missing generated_by")
        safety = state_data.get("safety", {})
        _check(safety.get("read_only") is True, "safety.read_only=true", "safety.read_only not true")
        _check(safety.get("shadow_only") is True, "safety.shadow_only=true", "safety.shadow_only not true")
        _check(safety.get("hardware_execution_enabled") is False,
               "safety.hardware_execution_enabled=false", "safety.hardware_execution_enabled not false")

    # OODA frame
    ooda_path = case_dir / "ooda_frame.json"
    if ooda_path.exists():
        ooda = json.loads(ooda_path.read_text(encoding="utf-8"))
        act = ooda.get("act", "")
        if isinstance(act, str):
            _check(
                "recommendation" in act or "no_hardware" in act,
                f"act: {act}", f"act boundary violated: {act}",
            )
            if strict:
                _check(
                    act == "recommendation_only_no_hardware_action",
                    "[strict] ooda.act exact value correct",
                    f"[strict] ooda.act must be 'recommendation_only_no_hardware_action', got '{act}'",
                )
        elif isinstance(act, dict):
            _check(
                act.get("automatic_action_enabled") is False,
                "ooda.act.automatic_action_enabled=false",
                "ooda.act.automatic_action_enabled VIOLATION",
            )
            _check(
                act.get("hardware_control_enabled") is False,
                "ooda.act.hardware_control_enabled=false",
                "ooda.act.hardware_control_enabled VIOLATION",
            )
            if strict:
                _check(
                    act.get("automatic_action_enabled") is False,
                    "[strict] ooda.act.automatic_action_enabled=false",
                    "[strict] ooda.act.automatic_action_enabled VIOLATION",
                )
                _check(
                    act.get("hardware_control_enabled") is False,
                    "[strict] ooda.act.hardware_control_enabled=false",
                    "[strict] ooda.act.hardware_control_enabled VIOLATION",
                )
                _check(
                    act.get("recipe_control_enabled") is False,
                    "[strict] ooda.act.recipe_control_enabled=false",
                    "[strict] ooda.act.recipe_control_enabled VIOLATION",
                )
        _check("schema" in ooda, "ooda_frame has schema", "ooda_frame missing schema")

    _check((case_dir / "recovery_candidates.json").exists(),
           "recovery_candidates.json exists", "recovery_candidates.json MISSING")

    # Forbidden actions
    FORBIDDEN_ACTIONS = {
        "change_recipe", "modify_recipe", "send_robot_command",
        "send_satellite_command", "uplink_command", "execute_hardware",
        "hardware_command", "equipment_start", "equipment_stop",
        "auto_calibration_execute",
    }
    if rec_path.exists():
        rec_data = json.loads(rec_path.read_text(encoding="utf-8"))
        forbidden_found = [
            f"recovery.action={r.get('action', '').lower()}"
            for r in rec_data
            if str(r.get("action", "")).lower() in FORBIDDEN_ACTIONS
        ]
        _check(not forbidden_found, "no forbidden action strings in recovery_candidates",
               f"forbidden actions found: {forbidden_found}")

    # Evidence pack schema
    _check("schema" in pack, "evidence_pack has schema", "evidence_pack missing schema")
    _check("schema_version" in pack, "evidence_pack has schema_version", "evidence_pack missing schema_version")
    _check("generated_by" in pack, "evidence_pack has generated_by", "evidence_pack missing generated_by")

    # Recovery candidate metadata
    if rec_path.exists():
        rec_data2 = json.loads(rec_path.read_text(encoding="utf-8"))
        if rec_data2:
            first = rec_data2[0]
            _check("schema_version" in first, "recovery_candidates[0] has schema_version",
                   "recovery_candidates missing schema_version")
            _check("generated_by" in first, "recovery_candidates[0] has generated_by",
                   "recovery_candidates missing generated_by")
            _check("safety" in first, "recovery_candidates[0] has safety block",
                   "recovery_candidates missing safety block")

    # ── STRICT mode additional checks ──────────────────────────────────────
    if strict:
        from ..contracts.recovery_candidate import DANGEROUS_TERMS as _DANGEROUS_TERMS
        from ..contracts.recovery_candidate import SAFE_ACTION_PREFIXES
        print("\n  [STRICT] Checking Standard Output Bundle...")
        for fname in STRICT_REQUIRED_FILES:
            _check((case_dir / fname).exists(), f"[strict] {fname} exists", f"[strict] {fname} MISSING")

        # Functional passport safety
        fp_path = case_dir / "functional_passport.json"
        if fp_path.exists():
            fp = json.loads(fp_path.read_text(encoding="utf-8"))
            _check(fp.get("hardware_execution_enabled") is False,
                   "[strict] functional_passport.hardware_execution_enabled=false",
                   "[strict] functional_passport.hardware_execution_enabled VIOLATION")
            _check(fp.get("human_approval_required") is True,
                   "[strict] functional_passport.human_approval_required=true",
                   "[strict] functional_passport.human_approval_required not true")

        # Case manifest file checksums
        manifest_path = case_dir / "case_manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            files_section = manifest.get("files", {})
            checksum_mismatches = []
            for key, entry in files_section.items():
                fpath = case_dir / entry.get("path", "")
                stored_sha = entry.get("sha256", "")
                if fpath.exists() and stored_sha.startswith("sha256:"):
                    actual = "sha256:" + hashlib.sha256(fpath.read_bytes()).hexdigest()
                    if actual != stored_sha:
                        checksum_mismatches.append(entry["path"])
            _check(not checksum_mismatches,
                   "[strict] case_manifest file checksums match",
                   f"[strict] case_manifest checksum MISMATCH: {checksum_mismatches}")

        # Recovery route report safety
        rrr_path = case_dir / "recovery_route_report.json"
        if rrr_path.exists():
            rrr = json.loads(rrr_path.read_text(encoding="utf-8"))
            for route in rrr.get("routes", []):
                action = route.get("action", "")
                _check(action.lower().startswith(SAFE_ACTION_PREFIXES),
                       f"[strict] route '{action}' has safe prefix",
                       f"[strict] route '{action}' MISSING safe prefix")
                _check(not route.get("hardware_execution_enabled", False),
                       f"[strict] route '{action}' hardware_execution_enabled=false",
                       f"[strict] route '{action}' hardware_execution_enabled VIOLATION")

        # External claim guard — check report.html and report.md
        for report_fname in ["report.html", "report.md"]:
            report_path = case_dir / report_fname
            if report_path.exists():
                content = report_path.read_text(encoding="utf-8").lower()
                for term in FORBIDDEN_REPORT_TERMS:
                    if term.lower() in content:
                        _check(False, "", f"[strict] forbidden claim '{term}' found in {report_fname}")

        # Recovery candidate action prefix (strict)
        if rec_path.exists():
            rec_strict = json.loads(rec_path.read_text(encoding="utf-8"))
            for rc_item in rec_strict:
                rc_action = rc_item.get("action", "")
                _check(rc_action.lower().startswith(SAFE_ACTION_PREFIXES),
                       f"[strict] recovery action has safe prefix: {rc_action}",
                       f"[strict] recovery action missing safe prefix: {rc_action}")
                terms_text = " ".join([rc_action,
                                       rc_item.get("expected_benefit", ""),
                                       *rc_item.get("steps", [])]).lower()
                dangerous_found = [t for t in _DANGEROUS_TERMS if t in terms_text]
                _check(not dangerous_found,
                       f"[strict] recovery action '{rc_action}' has no dangerous terms",
                       f"[strict] recovery action '{rc_action}' contains: {dangerous_found}")

        # Analysis trace existence
        _check((case_dir / "analysis_trace.json").exists(),
               "[strict] analysis_trace.json exists", "[strict] analysis_trace.json MISSING")

        # Input validation check: must exist and status must be PASSED
        iv_path = case_dir / "input_validation.json"
        _check(iv_path.exists(),
               "[strict] input_validation.json exists", "[strict] input_validation.json MISSING")
        if iv_path.exists():
            iv = json.loads(iv_path.read_text(encoding="utf-8"))
            iv_status = iv.get("status", "")
            iv_data_level = iv.get("data_level", "")
            _check(iv_status == "PASSED",
                   "[strict] input_validation.status == PASSED",
                   f"[strict] input_validation.status == {iv_status!r} (expected PASSED)")
            _check(iv_data_level not in ("EMPTY", "INVALID_SCHEMA"),
                   f"[strict] input_validation.data_level acceptable: {iv_data_level}",
                   f"[strict] input_validation.data_level is {iv_data_level!r} — EMPTY or INVALID_SCHEMA not accepted in strict mode")

        # Decision readiness report category check
        dr_path = case_dir / "decision_readiness_report.json"
        if dr_path.exists():
            dr = json.loads(dr_path.read_text(encoding="utf-8"))
            valid_cats = {"DATA_INCOMPLETE", "RUNNABLE_LOW_CONFIDENCE", "PASSPORT_ELIGIBLE",
                          "ACTION_INELIGIBLE", "DECISION_READY", "RUNTIME_CANDIDATE"}
            cat = dr.get("category", "")
            _check(cat in valid_cats,
                   f"[strict] decision_readiness category: {cat}",
                   f"[strict] unknown decision_readiness category: {cat}")

        # Manifest completeness: all listed files must exist; standard outputs must be in manifest
        _MANIFEST_REQUIRED_KEYS = {
            "state_snapshot", "evidence_pack", "ooda_frame", "recovery_candidates",
            "report_md", "report_html", "input_validation", "decision_readiness_report",
            "functional_yield_scorecard", "functional_binning_result", "functional_passport",
            "evidence_pack_md", "recovery_route_report", "failure_scenario_record",
            "next_data_request", "analysis_trace",
            "source_data_manifest", "data_quality_report", "evidence_conflict_report",
            "baseline_vs_yieldos", "business_case_summary",
        }
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            files_section = manifest.get("files", {})
            # Check every listed file exists on disk
            missing_from_disk = [
                entry.get("path", key)
                for key, entry in files_section.items()
                if not (case_dir / entry.get("path", "")).exists()
            ]
            _check(not missing_from_disk,
                   "[strict] all manifest-listed files exist on disk",
                   f"[strict] manifest lists files missing on disk: {missing_from_disk[:5]}")
            # Check required standard outputs appear in manifest
            absent_keys = [k for k in _MANIFEST_REQUIRED_KEYS if k not in files_section]
            _check(not absent_keys,
                   "[strict] case_manifest covers all standard output files",
                   f"[strict] case_manifest missing standard outputs: {absent_keys[:5]}")

        # ── Robot Skill Memory auto-detection ──────────────────────────────────
        _skill_note_p = case_dir / "operator_skill_note.json"
        if _skill_note_p.exists():
            print("\n  [STRICT] Checking Robot Skill Memory outputs...")
            for _sm_fname in [
                "operator_skill_note.json",
                "human_intervention_timeline.json",
                "skill_to_evidence_map.json",
            ]:
                _check((case_dir / _sm_fname).exists(),
                       f"[strict][skill-memory] {_sm_fname} exists",
                       f"[strict][skill-memory] {_sm_fname} MISSING")
            _fp_skill_p = case_dir / "functional_passport.json"
            if _fp_skill_p.exists():
                _fp_skill = json.loads(_fp_skill_p.read_text(encoding="utf-8"))
                _check("human_skill_context" in _fp_skill,
                       "[strict][skill-memory] functional_passport has human_skill_context",
                       "[strict][skill-memory] functional_passport missing human_skill_context")

            _gap_p = case_dir / "sim_to_real_gap_report.json"
            _force_p = case_dir / "force_compliance_event_log.json"
            if _gap_p.exists() or _force_p.exists():
                print("  [STRICT] Checking Physical Reality Gap outputs...")
                _check(_gap_p.exists(),
                       "[strict][physical-gap] sim_to_real_gap_report.json exists",
                       "[strict][physical-gap] sim_to_real_gap_report.json MISSING")
                _check(_force_p.exists(),
                       "[strict][physical-gap] force_compliance_event_log.json exists",
                       "[strict][physical-gap] force_compliance_event_log.json MISSING")
                if _fp_skill_p.exists():
                    _fp_pg = json.loads(_fp_skill_p.read_text(encoding="utf-8"))
                    _check("physical_reality_context" in _fp_pg,
                           "[strict][physical-gap] functional_passport has physical_reality_context",
                           "[strict][physical-gap] functional_passport missing physical_reality_context")
                    if "physical_reality_context" in _fp_pg:
                        _prc = _fp_pg["physical_reality_context"]
                        _check(_prc.get("context_capture_status") in {"partial", "complete"},
                               "[strict][physical-gap] context_capture_status valid",
                               f"[strict][physical-gap] context_capture_status invalid: {_prc.get('context_capture_status')}")
                if _gap_p.exists():
                    _gap_data = json.loads(_gap_p.read_text(encoding="utf-8"))
                    _gap_sb = _gap_data.get("safety_boundary", {})
                    _check(_gap_sb.get("hardware_execution_enabled") is False,
                           "[strict][physical-gap] sim_to_real_gap_report safety_boundary ok",
                           "[strict][physical-gap] sim_to_real_gap_report safety VIOLATION")
                    for _ge in _gap_data.get("gap_events", []):
                        _ge_cb = _ge.get("claim_boundary", "")
                        _check(_ge_cb == "candidate_only_sim_to_real_gap",
                               f"[strict][physical-gap] gap_event {_ge.get('event_id', '?')} claim_boundary ok",
                               f"[strict][physical-gap] gap_event claim_boundary violated: {_ge_cb}")
                if _force_p.exists():
                    _force_data = json.loads(_force_p.read_text(encoding="utf-8"))
                    _force_sb = _force_data.get("safety_boundary", {})
                    _check(_force_sb.get("hardware_execution_enabled") is False,
                           "[strict][physical-gap] force_compliance_event_log safety_boundary ok",
                           "[strict][physical-gap] force_compliance_event_log safety VIOLATION")
                    _ALLOWED_FORCE_TYPES = {
                        "force_spike", "torque_anomaly", "slip_event", "grip_failure_candidate",
                        "contact_instability", "excessive_payload_resistance",
                        "position_error_deviation", "unknown_physical_event",
                    }
                    for _fe in _force_data.get("events", []):
                        _fe_et = _fe.get("event_type", "")
                        _check(_fe_et in _ALLOWED_FORCE_TYPES,
                               f"[strict][physical-gap] force_event {_fe.get('event_id', '?')} event_type ok: {_fe_et}",
                               f"[strict][physical-gap] force_event forbidden event_type: {_fe_et}")
                        _fe_cb = _fe.get("claim_boundary", "")
                        _check(_fe_cb == "candidate_physical_event_only",
                               f"[strict][physical-gap] force_event {_fe.get('event_id', '?')} claim_boundary ok",
                               f"[strict][physical-gap] force_event claim_boundary violated: {_fe_cb}")

            _cs_p = case_dir / "robot_skill_memory_case_study.json"
            _ba_p = case_dir / "before_after_functional_reclassification.json"
            if _cs_p.exists() or _ba_p.exists():
                print("  [STRICT] Checking Robot Skill Memory Case Study outputs...")
                _check(_cs_p.exists(),
                       "[strict][case-study] robot_skill_memory_case_study.json exists",
                       "[strict][case-study] robot_skill_memory_case_study.json MISSING")
                _check(_ba_p.exists(),
                       "[strict][case-study] before_after_functional_reclassification.json exists",
                       "[strict][case-study] before_after_functional_reclassification.json MISSING")
                if _fp_skill_p.exists():
                    _fp_cs = json.loads(_fp_skill_p.read_text(encoding="utf-8"))
                    _check("case_study_ref" in _fp_cs,
                           "[strict][case-study] functional_passport has case_study_ref",
                           "[strict][case-study] functional_passport missing case_study_ref")
                    _check("before_after_ref" in _fp_cs,
                           "[strict][case-study] functional_passport has before_after_ref",
                           "[strict][case-study] functional_passport missing before_after_ref")
                _ooda_p = case_dir / "ooda_frame.json"
                if _ooda_p.exists():
                    _ooda = json.loads(_ooda_p.read_text(encoding="utf-8"))
                    _check("case_study_ref" in _ooda,
                           "[strict][case-study] ooda_frame has case_study_ref",
                           "[strict][case-study] ooda_frame missing case_study_ref")
                if _ba_p.exists():
                    _ba = json.loads(_ba_p.read_text(encoding="utf-8"))
                    _ba_yv = _ba.get("yieldos_view", {})
                    _check(len(_ba_yv.get("remaining_roles", [])) >= 1,
                           "[strict][case-study] before_after has remaining_roles",
                           "[strict][case-study] before_after missing remaining_roles")
                    _check(len(_ba_yv.get("blocked_roles", [])) >= 1,
                           "[strict][case-study] before_after has blocked_roles",
                           "[strict][case-study] before_after missing blocked_roles")
                if _cs_p.exists():
                    _cs = json.loads(_cs_p.read_text(encoding="utf-8"))
                    _cs_sb = _cs.get("safety_boundary", {})
                    _check(_cs_sb.get("hardware_execution_enabled") is False,
                           "[strict][case-study] case_study safety_boundary ok",
                           "[strict][case-study] case_study safety VIOLATION")
                    _check(_cs_sb.get("human_review_required") is True,
                           "[strict][case-study] case_study human_review_required ok",
                           "[strict][case-study] case_study human_review_required VIOLATION")
                    _check(_cs_sb.get("candidate_only") is True,
                           "[strict][case-study] case_study candidate_only ok",
                           "[strict][case-study] case_study candidate_only VIOLATION")

        # ── FYFab Seed auto-detection ───────────────────────────────────────────
        _fyfab_passport_p = case_dir / "functional_yield_chip_passport.json"
        if _fyfab_passport_p.exists():
            _fyfab_data = json.loads(_fyfab_passport_p.read_text(encoding="utf-8"))
            if _fyfab_data.get("schema", "").startswith("hal.yieldos.fyfab"):
                print("\n  [STRICT] Checking FYFab Seed outputs...")
                _FYFAB_FILES = [
                    "fabricated_structure_map.json",
                    "defect_map_summary.json",
                    "usable_cell_classification.json",
                    "candidate_functional_regions.json",
                    "reconfiguration_candidate_map.json",
                    "functional_yield_chip_passport.json",
                    "fyfab_case_study.json",
                ]
                for _ff in _FYFAB_FILES:
                    _check((case_dir / _ff).exists(),
                           f"[strict][fyfab] {_ff} exists",
                           f"[strict][fyfab] {_ff} MISSING")

                # functional_passport links chip passport
                _fp_fyfab_p = case_dir / "functional_passport.json"
                if _fp_fyfab_p.exists():
                    _fp_fyfab = json.loads(_fp_fyfab_p.read_text(encoding="utf-8"))
                    _check("fyfab_chip_passport_ref" in _fp_fyfab,
                           "[strict][fyfab] functional_passport has fyfab_chip_passport_ref",
                           "[strict][fyfab] functional_passport missing fyfab_chip_passport_ref")

                # ooda_frame links fyfab case study
                _ooda_fyfab_p = case_dir / "ooda_frame.json"
                if _ooda_fyfab_p.exists():
                    _ooda_fyfab = json.loads(_ooda_fyfab_p.read_text(encoding="utf-8"))
                    _check("fyfab_case_study_ref" in _ooda_fyfab,
                           "[strict][fyfab] ooda_frame has fyfab_case_study_ref",
                           "[strict][fyfab] ooda_frame missing fyfab_case_study_ref")

                # source_data_manifest includes FYFab inputs
                _sdm_fyfab_p = case_dir / "source_data_manifest.json"
                if _sdm_fyfab_p.exists():
                    _sdm_fyfab = json.loads(_sdm_fyfab_p.read_text(encoding="utf-8"))
                    _sdm_files = (
                        _sdm_fyfab.get("input_files")
                        or _sdm_fyfab.get("source_files")
                        or []
                    )
                    _sdm_names = {
                        Path(f.get("path", f.get("file_path", ""))).name
                        for f in _sdm_files
                    }
                    for _fi in ["fabricated_structure_grid.csv", "defect_map.csv", "material_regions.csv"]:
                        _check(_fi in _sdm_names,
                               f"[strict][fyfab] source_data_manifest includes {_fi}",
                               f"[strict][fyfab] source_data_manifest missing {_fi}")

                # Safety invariants
                _check(_fyfab_data.get("hardware_execution_enabled") is False,
                       "[strict][fyfab] chip_passport hardware_execution_enabled=false",
                       "[strict][fyfab] chip_passport hardware_execution_enabled VIOLATION")
                _check(_fyfab_data.get("human_review_required") is True,
                       "[strict][fyfab] chip_passport human_review_required=true",
                       "[strict][fyfab] chip_passport human_review_required VIOLATION")

                # Forbidden control terms in all FYFab JSON outputs
                _FYFAB_FORBIDDEN = [
                    "execute_recipe", "modify_recipe", "control_deposition",
                    "control_etch", "control_lithography",
                    "physical_design_signoff_certified", "timing_closure_certified",
                    "yield_guarantee", "certified_root_cause", "confirmed_root_cause",
                ]
                for _ff2 in _FYFAB_FILES:
                    _ffp = case_dir / _ff2
                    if _ffp.exists():
                        _fft = _ffp.read_text(encoding="utf-8").lower()
                        for _term in _FYFAB_FORBIDDEN:
                            if _term.lower() in _fft:
                                _check(False, "",
                                       f"[strict][fyfab] forbidden term '{_term}' in {_ff2}")

        # ── Semiconductor Report auto-detection ────────────────────────────────
        _pdr_p = case_dir / "process_drift_report.json"
        _scr_p = case_dir / "semiconductor_confidence_report.json"
        if _pdr_p.exists() or _scr_p.exists():
            print("\n  [STRICT] Checking Semiconductor Calibration outputs...")
            _check(_pdr_p.exists(),
                   "[strict][semiconductor] process_drift_report.json exists",
                   "[strict][semiconductor] process_drift_report.json MISSING")
            _check(_scr_p.exists(),
                   "[strict][semiconductor] semiconductor_confidence_report.json exists",
                   "[strict][semiconductor] semiconductor_confidence_report.json MISSING")

            # Safety boundary checks
            if _pdr_p.exists():
                _pdr = json.loads(_pdr_p.read_text(encoding="utf-8"))
                _pdr_sb = _pdr.get("safety_boundary", {})
                _check(_pdr_sb.get("hardware_execution_enabled") is False,
                       "[strict][semiconductor] process_drift_report safety_boundary.hardware_execution_enabled=false",
                       "[strict][semiconductor] process_drift_report safety VIOLATION")
                _check(_pdr_sb.get("human_review_required") is True,
                       "[strict][semiconductor] process_drift_report safety_boundary.human_review_required=true",
                       "[strict][semiconductor] process_drift_report human_review_required VIOLATION")
                _check(_pdr_sb.get("candidate_only") is True,
                       "[strict][semiconductor] process_drift_report safety_boundary.candidate_only=true",
                       "[strict][semiconductor] process_drift_report candidate_only VIOLATION")

            # Confidence report checks
            if _scr_p.exists():
                _scr = json.loads(_scr_p.read_text(encoding="utf-8"))
                _scr_cr = _scr.get("confidence_report", {})
                _check(_scr_cr.get("confidence_kind") == "analysis_confidence",
                       "[strict][semiconductor] confidence_report.confidence_kind == analysis_confidence",
                       f"[strict][semiconductor] confidence_report.confidence_kind WRONG: {_scr_cr.get('confidence_kind')}")
                _scr_sb = _scr.get("safety_boundary", {})
                _check(_scr_sb.get("hardware_execution_enabled") is False,
                       "[strict][semiconductor] confidence_report safety_boundary.hardware_execution_enabled=false",
                       "[strict][semiconductor] confidence_report safety VIOLATION")

            # functional_passport refs
            _fp_semi_p = case_dir / "functional_passport.json"
            if _fp_semi_p.exists():
                _fp_semi = json.loads(_fp_semi_p.read_text(encoding="utf-8"))
                _check("process_drift_report_ref" in _fp_semi,
                       "[strict][semiconductor] functional_passport has process_drift_report_ref",
                       "[strict][semiconductor] functional_passport missing process_drift_report_ref")
                _check("semiconductor_confidence_report_ref" in _fp_semi,
                       "[strict][semiconductor] functional_passport has semiconductor_confidence_report_ref",
                       "[strict][semiconductor] functional_passport missing semiconductor_confidence_report_ref")

            # case_manifest optional_outputs includes both files
            _cm_semi_p = case_dir / "case_manifest.json"
            if _cm_semi_p.exists():
                _cm_semi = json.loads(_cm_semi_p.read_text(encoding="utf-8"))
                _opt_semi = _cm_semi.get("optional_outputs", {})
                _opt_paths = (
                    [v.get("path") for v in _opt_semi.values()]
                    if isinstance(_opt_semi, dict)
                    else [item.get("path") for item in _opt_semi]
                )
                _check("process_drift_report.json" in _opt_paths,
                       "[strict][semiconductor] case_manifest optional_outputs includes process_drift_report.json",
                       "[strict][semiconductor] case_manifest optional_outputs missing process_drift_report.json")
                _check("semiconductor_confidence_report.json" in _opt_paths,
                       "[strict][semiconductor] case_manifest optional_outputs includes semiconductor_confidence_report.json",
                       "[strict][semiconductor] case_manifest optional_outputs missing semiconductor_confidence_report.json")

            # Forbidden terms in semiconductor report files
            _SEMI_FORBIDDEN = [
                "execute_recipe", "modify_recipe", "control_deposition",
                "control_etch", "control_lithography", "recipe_change_command",
                "robot_command", "satellite_command", "uplink_command",
                "automatic_recovery_execution", "physical_design_signoff_certified",
                "timing_closure_certified", "yield_guarantee",
                "certified_root_cause", "confirmed_root_cause", "safety_certified",
            ]
            for _semi_f, _semi_p in [("process_drift_report.json", _pdr_p),
                                      ("semiconductor_confidence_report.json", _scr_p)]:
                if _semi_p.exists():
                    _semi_text = _semi_p.read_text(encoding="utf-8").lower()
                    for _term in _SEMI_FORBIDDEN:
                        if _term.lower() in _semi_text:
                            _check(False, "",
                                   f"[strict][semiconductor] forbidden term '{_term}' in {_semi_f}")

        # ── Robot Pilot-Pack auto-detection (v3.0.0) ──────────────────────────
        _rpr_p = case_dir / "robot_pilot_readiness_report.json"
        if _rpr_p.exists():
            print("\n  [STRICT] Checking Robot Pilot-Pack outputs...")
            _PILOT_PACK_FILES = [
                "robot_pilot_readiness_report.json",
                "robot_evidence_completeness_report.json",
                "robot_role_reclassification_report.json",
                "robot_valid_conditions_report.json",
                "robot_human_review_packet.json",
                "robot_missing_evidence_request.json",
                "robot_unit_normalization_report.json",
                "robot_pilot_case_summary.md",
            ]
            for _pp_fname in _PILOT_PACK_FILES:
                _check((case_dir / _pp_fname).exists(),
                       f"[strict][pilot-pack] {_pp_fname} exists",
                       f"[strict][pilot-pack] {_pp_fname} MISSING")

            # Readiness report safety
            _rpr = json.loads(_rpr_p.read_text(encoding="utf-8"))
            _rpr_sb = _rpr.get("safety_boundary", {})
            _check(_rpr_sb.get("hardware_execution_enabled") is False,
                   "[strict][pilot-pack] readiness_report hardware_execution_enabled=false",
                   "[strict][pilot-pack] readiness_report safety VIOLATION")
            _check(_rpr_sb.get("human_review_required") is True,
                   "[strict][pilot-pack] readiness_report human_review_required=true",
                   "[strict][pilot-pack] readiness_report human_review_required VIOLATION")
            _check(_rpr.get("hardware_control_enabled") is False,
                   "[strict][pilot-pack] readiness_report hardware_control_enabled=false",
                   "[strict][pilot-pack] readiness_report hardware_control_enabled VIOLATION")
            _check(_rpr.get("readiness_status") in {
                "PILOT_READY", "PARTIAL_PILOT_READY", "NOT_PILOT_READY"
            },
                   f"[strict][pilot-pack] readiness_status valid: {_rpr.get('readiness_status')}",
                   f"[strict][pilot-pack] readiness_status invalid: {_rpr.get('readiness_status')}")

            # Role reclassification report
            _rrr_pp = case_dir / "robot_role_reclassification_report.json"
            if _rrr_pp.exists():
                _rrr_pp_data = json.loads(_rrr_pp.read_text(encoding="utf-8"))
                _rr_sb = _rrr_pp_data.get("safety_boundary", {})
                _check(_rr_sb.get("hardware_execution_enabled") is False,
                       "[strict][pilot-pack] role_reclassification safety_boundary ok",
                       "[strict][pilot-pack] role_reclassification safety VIOLATION")
                _check(isinstance(_rrr_pp_data.get("canonical_roles_assessed"), list),
                       "[strict][pilot-pack] role_reclassification canonical_roles_assessed present",
                       "[strict][pilot-pack] role_reclassification missing canonical_roles_assessed")

            # Evidence completeness report
            _ecr_pp = case_dir / "robot_evidence_completeness_report.json"
            if _ecr_pp.exists():
                _ecr_pp_data = json.loads(_ecr_pp.read_text(encoding="utf-8"))
                _ec_sb = _ecr_pp_data.get("safety_boundary", {})
                _check(_ec_sb.get("hardware_execution_enabled") is False,
                       "[strict][pilot-pack] evidence_completeness safety_boundary ok",
                       "[strict][pilot-pack] evidence_completeness safety VIOLATION")
                _check("completeness_summary" in _ecr_pp_data,
                       "[strict][pilot-pack] evidence_completeness has completeness_summary",
                       "[strict][pilot-pack] evidence_completeness missing completeness_summary")

            # Human review packet
            _hrp_pp = case_dir / "robot_human_review_packet.json"
            if _hrp_pp.exists():
                _hrp_pp_data = json.loads(_hrp_pp.read_text(encoding="utf-8"))
                _hrp_sa = _hrp_pp_data.get("safety_assertions", {})
                _check(_hrp_sa.get("hardware_control_enabled") is False,
                       "[strict][pilot-pack] human_review_packet hardware_control_enabled=false",
                       "[strict][pilot-pack] human_review_packet hardware_control_enabled VIOLATION")
                _check(isinstance(_hrp_pp_data.get("review_checklist"), list)
                       and len(_hrp_pp_data["review_checklist"]) > 0,
                       "[strict][pilot-pack] human_review_packet review_checklist non-empty",
                       "[strict][pilot-pack] human_review_packet review_checklist empty or missing")

            # Unit normalization report
            _unr_pp = case_dir / "robot_unit_normalization_report.json"
            if _unr_pp.exists():
                _unr_pp_data = json.loads(_unr_pp.read_text(encoding="utf-8"))
                _un_sb = _unr_pp_data.get("safety_boundary", {})
                _check(_un_sb.get("hardware_execution_enabled") is False,
                       "[strict][pilot-pack] unit_normalization safety_boundary ok",
                       "[strict][pilot-pack] unit_normalization safety VIOLATION")

            # Forbidden control terms in pilot-pack JSON outputs
            # Negative-context keys: values under these keys are boundary statements, not active claims
            _PP_NEGATIVE_KEYS = {
                "not_sufficient_for", "forbidden_decisions", "what_not_to_do",
                "yieldos_does_not", "forbidden_handoff", "claim_boundary",
                "not_certification", "invalid_or_unknown_conditions", "warnings",
                "forbidden_control", "blocked_claims", "safety_boundary",
                "limitations", "disallowed_actions",
            }
            _PP_FORBIDDEN = [
                "send_robot_command", "execute_hardware", "hardware_command",
                "auto_calibration_execute", "autonomous_recovery_execution",
                "yield_guarantee", "certified_root_cause", "safety_certified",
                "robot_command", "uplink_command",
            ]
            for _pp_json in _PILOT_PACK_FILES:
                if not _pp_json.endswith(".json"):
                    continue
                _pp_path = case_dir / _pp_json
                if _pp_path.exists():
                    import re as _re
                    _pp_text_raw = _pp_path.read_text(encoding="utf-8").lower()
                    _pp_safe_text = _pp_text_raw
                    for _nck in _PP_NEGATIVE_KEYS:
                        _pp_safe_text = _re.sub(
                            r'"' + _nck + r'"\s*:\s*(?:\[[\s\S]*?\]|"[^"]*")',
                            f'"{_nck}": "__BOUNDARY__"',
                            _pp_safe_text,
                        )
                    for _term in _PP_FORBIDDEN:
                        if _term.lower() in _pp_safe_text:
                            _check(False, "",
                                   f"[strict][pilot-pack] forbidden term '{_term}' in {_pp_json}")

        # ── Semiconductor Pilot-Pack auto-detection (v3.0.1) ─────────────────
        _spr_p = case_dir / "semiconductor_pilot_readiness_report.json"
        if _spr_p.exists():
            print("\n  [STRICT] Checking Semiconductor Pilot-Pack outputs...")
            _SEMI_PP_FILES = [
                "semiconductor_pilot_readiness_report.json",
                "semiconductor_evidence_completeness_report.json",
                "semiconductor_wafer_die_summary.json",
                "semiconductor_functional_region_map.json",
                "semiconductor_role_candidate_map.json",
                "semiconductor_valid_conditions_report.json",
                "semiconductor_process_evidence_report.json",
                "semiconductor_human_review_packet.json",
                "semiconductor_missing_evidence_request.json",
                "semiconductor_recovery_compiler_intake_preview.json",
                "semiconductor_recovery_compiler_handoff_boundary.json",
                "semiconductor_recovery_compiler_export.json",
                "semiconductor_handoff_manifest.json",
                "semiconductor_pilot_case_summary.md",
            ]
            for _spp_fname in _SEMI_PP_FILES:
                _check((case_dir / _spp_fname).exists(),
                       f"[strict][semi-pilot] {_spp_fname} exists",
                       f"[strict][semi-pilot] {_spp_fname} MISSING")

            # Readiness report safety
            _spr = json.loads(_spr_p.read_text(encoding="utf-8"))
            _check(_spr.get("hardware_control_enabled") is False,
                   "[strict][semi-pilot] readiness_report hardware_control_enabled=false",
                   "[strict][semi-pilot] readiness_report hardware_control_enabled VIOLATION")
            _check(_spr.get("human_review_required") is True,
                   "[strict][semi-pilot] readiness_report human_review_required=true",
                   "[strict][semi-pilot] readiness_report human_review_required VIOLATION")
            _check(_spr.get("readiness_status") in {
                "PILOT_READY", "PARTIAL_PILOT_READY", "NOT_PILOT_READY"
            },
                   f"[strict][semi-pilot] readiness_status valid: {_spr.get('readiness_status')}",
                   f"[strict][semi-pilot] readiness_status invalid: {_spr.get('readiness_status')}")

            # Recovery compiler intake preview
            _rci_p = case_dir / "semiconductor_recovery_compiler_intake_preview.json"
            if _rci_p.exists():
                _rci = json.loads(_rci_p.read_text(encoding="utf-8"))
                _check(_rci.get("hardware_control_enabled") is False,
                       "[strict][semi-pilot] intake_preview hardware_control_enabled=false",
                       "[strict][semi-pilot] intake_preview hardware_control_enabled VIOLATION")
                _check(_rci.get("human_review_required") is True,
                       "[strict][semi-pilot] intake_preview human_review_required=true",
                       "[strict][semi-pilot] intake_preview human_review_required VIOLATION")
                _check(_rci.get("handoff_status") in {
                    "READY_FOR_OFFLINE_COMPILER_TEST",
                    "PARTIAL_FOR_OFFLINE_COMPILER_TEST",
                    "NOT_READY_FOR_COMPILER_HANDOFF",
                    "INVALID_COMPILER_INTAKE",
                },
                       f"[strict][semi-pilot] handoff_status valid: {_rci.get('handoff_status')}",
                       f"[strict][semi-pilot] handoff_status invalid: {_rci.get('handoff_status')}")
                _check("recovery_profile" not in _rci,
                       "[strict][semi-pilot] intake_preview does not have recovery_profile key",
                       "[strict][semi-pilot] intake_preview MUST NOT have recovery_profile key")

            # Handoff boundary
            _hb_p = case_dir / "semiconductor_recovery_compiler_handoff_boundary.json"
            if _hb_p.exists():
                _hb = json.loads(_hb_p.read_text(encoding="utf-8"))
                _check(_hb.get("hardware_control_enabled") is False,
                       "[strict][semi-pilot] handoff_boundary hardware_control_enabled=false",
                       "[strict][semi-pilot] handoff_boundary hardware_control_enabled VIOLATION")
                _check(isinstance(_hb.get("forbidden_handoff"), list)
                       and len(_hb["forbidden_handoff"]) > 0,
                       "[strict][semi-pilot] handoff_boundary forbidden_handoff non-empty",
                       "[strict][semi-pilot] handoff_boundary forbidden_handoff empty or missing")

            # Human review packet
            _shr_p = case_dir / "semiconductor_human_review_packet.json"
            if _shr_p.exists():
                _shr = json.loads(_shr_p.read_text(encoding="utf-8"))
                _check(_shr.get("hardware_control_enabled") is False,
                       "[strict][semi-pilot] human_review_packet hardware_control_enabled=false",
                       "[strict][semi-pilot] human_review_packet hardware_control_enabled VIOLATION")
                _check(isinstance(_shr.get("review_questions"), list)
                       and len(_shr["review_questions"]) > 0,
                       "[strict][semi-pilot] human_review_packet review_questions non-empty",
                       "[strict][semi-pilot] human_review_packet review_questions empty or missing")
                _check("execute_recovery_profile" in _shr.get("forbidden_decisions", [])
                       or any("execute" in fd for fd in _shr.get("forbidden_decisions", [])),
                       "[strict][semi-pilot] human_review_packet has execute forbidden decision",
                       "[strict][semi-pilot] human_review_packet missing execute forbidden decision")

            # Forbidden control terms — skip terms in negative-context boundary keys
            _SEMI_PP_FORBIDDEN = [
                "execute_recipe", "modify_recipe", "control_deposition",
                "control_etch", "control_lithography", "recipe_change_command",
                "equipment_control_command", "firmware_flash_payload",
                "runtime_apply_instruction", "hardware_control_enabled.*true",
                "yield_guarantee", "certified_root_cause", "confirmed_root_cause",
                "safety_certified", "recovery_profile",
            ]
            # Negative-context keys: terms in values under these keys are boundary statements,
            # not active claims. Also includes keys that describe OTHER systems' roles/outputs.
            _NEGATIVE_CONTEXT_KEYS = {
                "not_sufficient_for", "forbidden_decisions", "what_not_to_do",
                "yieldos_does_not", "forbidden_handoff", "claim_boundary",
                "not_certification", "invalid_or_unknown_conditions", "warnings",
                "forbidden_control", "blocked_claims", "safety_boundary",
                "limitations", "disallowed_actions", "recovery_compiler_role",
                "external_system_role", "not_to_do", "boundary",
                "forbidden_files", "handoff_conditions", "recovery_profile_generated",
            }
            for _spp_json in _SEMI_PP_FILES:
                if not _spp_json.endswith(".json"):
                    continue
                _spp_path = case_dir / _spp_json
                if not _spp_path.exists():
                    continue
                try:
                    _spp_data = json.loads(_spp_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                _spp_text_full = _spp_path.read_text(encoding="utf-8").lower()
                # Build a safe text by removing negative-context key values
                import re as _re
                _safe_text = _spp_text_full
                for _nck in _NEGATIVE_CONTEXT_KEYS:
                    # Replace value AND key for keys whose name contains a forbidden term
                    _safe_text = _re.sub(
                        r'"' + _nck + r'"\s*:\s*(?:\[[\s\S]*?\]|"[^"]*"|true|false|null)',
                        '"__safe_key__": "__BOUNDARY_STATEMENT__"',
                        _safe_text,
                    )
                for _term in _SEMI_PP_FORBIDDEN:
                    if _term in _safe_text:
                        _check(False, "",
                               f"[strict][semi-pilot] forbidden term '{_term}' in {_spp_json}")

            # ── v3.0.3: New contract alignment checks ─────────────────────────
            # functional_passport semiconductor_pilot_context
            _fp_sp_p = case_dir / "functional_passport.json"
            if _fp_sp_p.exists():
                _fp_sp = json.loads(_fp_sp_p.read_text(encoding="utf-8"))
                _check("semiconductor_pilot_context" in _fp_sp,
                       "[strict][semi-pilot] functional_passport has semiconductor_pilot_context",
                       "[strict][semi-pilot] functional_passport missing semiconductor_pilot_context")
                _spc = _fp_sp.get("semiconductor_pilot_context", {})
                if _spc:
                    _check("recovery_compiler_export_ref" in _spc,
                           "[strict][semi-pilot] semiconductor_pilot_context has recovery_compiler_export_ref",
                           "[strict][semi-pilot] semiconductor_pilot_context missing recovery_compiler_export_ref")
                    _check("handoff_manifest_ref" in _spc,
                           "[strict][semi-pilot] semiconductor_pilot_context has handoff_manifest_ref",
                           "[strict][semi-pilot] semiconductor_pilot_context missing handoff_manifest_ref")

            # decision_readiness allowed/forbidden
            _dr_sp_p = case_dir / "decision_readiness_report.json"
            if _dr_sp_p.exists():
                _dr_sp = json.loads(_dr_sp_p.read_text(encoding="utf-8"))
                _check(
                    isinstance(_dr_sp.get("allowed_decisions"), list)
                    and len(_dr_sp["allowed_decisions"]) > 0,
                    "[strict][semi-pilot] decision_readiness has allowed_decisions",
                    "[strict][semi-pilot] decision_readiness missing allowed_decisions",
                )
                _check(
                    isinstance(_dr_sp.get("forbidden_decisions"), list)
                    and len(_dr_sp["forbidden_decisions"]) > 0,
                    "[strict][semi-pilot] decision_readiness has forbidden_decisions",
                    "[strict][semi-pilot] decision_readiness missing forbidden_decisions",
                )
                _check(_dr_sp.get("hardware_control_enabled") is False,
                       "[strict][semi-pilot] decision_readiness hardware_control_enabled=false",
                       "[strict][semi-pilot] decision_readiness hardware_control_enabled VIOLATION")
                _check(_dr_sp.get("human_review_required") is True,
                       "[strict][semi-pilot] decision_readiness human_review_required=true",
                       "[strict][semi-pilot] decision_readiness human_review_required VIOLATION")
                _check(_dr_sp.get("automatic_decision_enabled") is False,
                       "[strict][semi-pilot] decision_readiness automatic_decision_enabled=false",
                       "[strict][semi-pilot] decision_readiness automatic_decision_enabled VIOLATION")

            # state_snapshot snapshot_type
            _ss_sp_p = case_dir / "state_snapshot.json"
            if _ss_sp_p.exists():
                _ss_sp = json.loads(_ss_sp_p.read_text(encoding="utf-8"))
                _check(
                    _ss_sp.get("snapshot_type") == "semiconductor_pilot_candidate_state",
                    "[strict][semi-pilot] state_snapshot.snapshot_type=semiconductor_pilot_candidate_state",
                    f"[strict][semi-pilot] state_snapshot.snapshot_type wrong: {_ss_sp.get('snapshot_type')}",
                )
                _ss_safety2 = _ss_sp.get("safety", {})
                _check(_ss_safety2.get("recovery_profile_generated") is False,
                       "[strict][semi-pilot] state_snapshot.safety.recovery_profile_generated=false",
                       "[strict][semi-pilot] state_snapshot.safety.recovery_profile_generated VIOLATION")

            # recovery compiler export
            _rce_p = case_dir / "semiconductor_recovery_compiler_export.json"
            _check(_rce_p.exists(),
                   "[strict][semi-pilot] semiconductor_recovery_compiler_export.json exists",
                   "[strict][semi-pilot] semiconductor_recovery_compiler_export.json MISSING")
            if _rce_p.exists():
                _rce = json.loads(_rce_p.read_text(encoding="utf-8"))
                _check(_rce.get("recovery_profile_generated") is False,
                       "[strict][semi-pilot] export recovery_profile_generated=false",
                       "[strict][semi-pilot] export recovery_profile_generated VIOLATION")
                _check(_rce.get("hardware_control_enabled") is False,
                       "[strict][semi-pilot] export hardware_control_enabled=false",
                       "[strict][semi-pilot] export hardware_control_enabled VIOLATION")
                _check(_rce.get("export_status") in {
                    "READY_FOR_OFFLINE_COMPILER_TEST",
                    "PARTIAL_FOR_OFFLINE_COMPILER_TEST",
                    "NOT_READY_FOR_COMPILER_HANDOFF",
                    "INVALID_COMPILER_EXPORT",
                },
                       f"[strict][semi-pilot] export status valid: {_rce.get('export_status')}",
                       f"[strict][semi-pilot] export status invalid: {_rce.get('export_status')}")
                _check(_rce.get("compiler_project") == "hal-recovery-compiler",
                       "[strict][semi-pilot] export compiler_project=hal-recovery-compiler",
                       "[strict][semi-pilot] export compiler_project WRONG")

            # handoff manifest
            _hm_p = case_dir / "semiconductor_handoff_manifest.json"
            _check(_hm_p.exists(),
                   "[strict][semi-pilot] semiconductor_handoff_manifest.json exists",
                   "[strict][semi-pilot] semiconductor_handoff_manifest.json MISSING")
            if _hm_p.exists():
                _hm = json.loads(_hm_p.read_text(encoding="utf-8"))
                _check(_hm.get("hardware_control_enabled") is False,
                       "[strict][semi-pilot] handoff_manifest hardware_control_enabled=false",
                       "[strict][semi-pilot] handoff_manifest hardware_control_enabled VIOLATION")
                _check(_hm.get("human_review_required") is True,
                       "[strict][semi-pilot] handoff_manifest human_review_required=true",
                       "[strict][semi-pilot] handoff_manifest human_review_required VIOLATION")
                _check("semiconductor_recovery_compiler_export.json" in _hm.get("allowed_files", []),
                       "[strict][semi-pilot] handoff_manifest allowed_files includes export",
                       "[strict][semi-pilot] handoff_manifest allowed_files missing export")
                _check("recovery_profile.json" in _hm.get("forbidden_files", []),
                       "[strict][semi-pilot] handoff_manifest forbidden_files includes recovery_profile.json",
                       "[strict][semi-pilot] handoff_manifest forbidden_files missing recovery_profile.json")

            # no recovery_profile.json
            _check(not (case_dir / "recovery_profile.json").exists(),
                   "[strict][semi-pilot] recovery_profile.json not generated",
                   "[strict][semi-pilot] recovery_profile.json exists (VIOLATION)")

        # ── Functional Yield Essence auto-detection (v2.8.7) ──────────────────
        print("\n  [STRICT] Checking Functional Yield Essence fields...")

        def _safe_load_json(path: "Path") -> "dict | None":
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                _check(False, "",
                       f"[strict][essence] {path.name} is not valid JSON (tampered or corrupt)")
                return None

        _fp_ess_p = case_dir / "functional_passport.json"
        if _fp_ess_p.exists():
            _fp_ess = _safe_load_json(_fp_ess_p)
            if _fp_ess is not None:
                _fyop = _fp_ess.get("functional_yield_organizing_principle", {})
                _check(bool(_fyop),
                       "[strict][essence] functional_passport has functional_yield_organizing_principle",
                       "[strict][essence] functional_passport missing functional_yield_organizing_principle")
                if _fyop:
                    _check("core_question" in _fyop,
                           "[strict][essence] functional_yield_organizing_principle has core_question",
                           "[strict][essence] functional_yield_organizing_principle missing core_question")
                    _check(_fyop.get("human_review_required") is True,
                           "[strict][essence] functional_yield_organizing_principle human_review_required=true",
                           "[strict][essence] functional_yield_organizing_principle human_review_required VIOLATION")
                    _check("not_certification" in _fyop.get("claim_boundary", ""),
                           "[strict][essence] functional_yield_organizing_principle claim_boundary ok",
                           f"[strict][essence] claim_boundary missing not_certification: {_fyop.get('claim_boundary')}")

        _dqr_ess_p = case_dir / "data_quality_report.json"
        if _dqr_ess_p.exists():
            _dqr_ess = _safe_load_json(_dqr_ess_p)
            if _dqr_ess is not None:
                _ds = _dqr_ess.get("data_sufficiency", {})
                _check(bool(_ds),
                       "[strict][essence] data_quality_report has data_sufficiency",
                       "[strict][essence] data_quality_report missing data_sufficiency")
                if _ds:
                    _check("sufficiency_status" in _ds,
                           "[strict][essence] data_sufficiency has sufficiency_status",
                           "[strict][essence] data_sufficiency missing sufficiency_status")
                    _check(_ds.get("sufficiency_status") in {
                        "SUFFICIENT_FOR_CANDIDATE_REVIEW", "PARTIAL_FOR_CANDIDATE_REVIEW",
                        "INSUFFICIENT_FOR_CANDIDATE_REVIEW", "UNKNOWN",
                    },
                           f"[strict][essence] data_sufficiency.sufficiency_status valid: {_ds.get('sufficiency_status')}",
                           f"[strict][essence] data_sufficiency.sufficiency_status invalid: {_ds.get('sufficiency_status')}")
                    _check(bool(_ds.get("not_sufficient_for")),
                           "[strict][essence] data_sufficiency has not_sufficient_for",
                           "[strict][essence] data_sufficiency missing not_sufficient_for")
                    _check("claim_boundary" in _ds,
                           "[strict][essence] data_sufficiency has claim_boundary",
                           "[strict][essence] data_sufficiency missing claim_boundary")

        _cm_ess_p = case_dir / "case_manifest.json"
        if _cm_ess_p.exists():
            _cm_ess = _safe_load_json(_cm_ess_p)
            if _cm_ess is not None:
                _fyl = _cm_ess.get("functional_yield_lineage_summary", {})
                _check(bool(_fyl),
                       "[strict][essence] case_manifest has functional_yield_lineage_summary",
                       "[strict][essence] case_manifest missing functional_yield_lineage_summary")
                if _fyl:
                    for _ref_key in ("source_manifest_ref", "evidence_pack_ref",
                                     "functional_passport_ref", "decision_readiness_ref"):
                        _check(_ref_key in _fyl,
                               f"[strict][essence] lineage_summary has {_ref_key}",
                               f"[strict][essence] lineage_summary missing {_ref_key}")

        _dr_ess_p = case_dir / "decision_readiness_report.json"
        if _dr_ess_p.exists():
            _dr_ess = _safe_load_json(_dr_ess_p)
            if _dr_ess is not None:
                _hrp = _dr_ess.get("human_review_preparation", {})
                _check(bool(_hrp),
                       "[strict][essence] decision_readiness_report has human_review_preparation",
                       "[strict][essence] decision_readiness_report missing human_review_preparation")
                if _hrp:
                    _check(_hrp.get("automatic_decision_enabled") is False,
                           "[strict][essence] human_review_preparation.automatic_decision_enabled=false",
                           "[strict][essence] human_review_preparation.automatic_decision_enabled VIOLATION")
                    _check(_hrp.get("approval_gate_required") is True,
                           "[strict][essence] human_review_preparation.approval_gate_required=true",
                           "[strict][essence] human_review_preparation.approval_gate_required VIOLATION")

    status = "PASSED" if failed == 0 else "FAILED"
    print(f"\n[YieldOS] Validation {status} ({mode_label}): {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


# ── Version / Doctor ───────────────────────────────────────────────────────

def cmd_version(args: argparse.Namespace) -> int:
    import platform
    version = _get_version()
    try:
        from ..optimizers.sqbm_optional import SQBMOptimizer
        sqbm_status = "installed" if SQBMOptimizer().is_available() else "optional (not installed)"
    except Exception:
        sqbm_status = "optional (not installed)"
    print(f"HAL YieldOS {version}")
    print("Release type: PoC/MVP")
    print(f"Python: {platform.python_version()}")
    print(f"SQBM: {sqbm_status}")
    print("Hardware execution: disabled")
    print("Domain packs: robot, space, semiconductor, semiforge, memory")
    print("Domain aliases: satguard->space, semfab->semiconductor, satellite->space")
    return 0


# ── Doctor helpers (mode detection + deep checks) ──────────────────────────

def _find_project_root() -> "Path | None":
    """Return project root Path if running from source tree, else None."""
    candidate = Path(__file__).parent.parent.parent
    if (
        (candidate / "VERSION").exists()
        and (candidate / "pyproject.toml").exists()
        and (candidate / "MANIFEST.json").exists()
    ):
        return candidate
    return None


def _detect_runtime_mode() -> str:
    """Return 'source' if running from source tree, 'installed' if wheel-installed."""
    return "source" if _find_project_root() is not None else "installed"


def _installed_package_version() -> "str | None":
    """Return installed package version via importlib.metadata, or None."""
    try:
        from importlib.metadata import version as _meta_ver
        return _meta_ver("hal-yieldos")
    except Exception:
        return None


def _bundled_manifest_data() -> "dict | None":
    """Read bundled yieldos/MANIFEST.json via importlib.resources."""
    try:
        import json as _j
        from importlib import resources as _res
        pkg_root = _res.files("yieldos")
        for rel in ("MANIFEST.json", "resources/MANIFEST.json"):
            target = pkg_root
            for part in rel.split("/"):
                target = target / part
            try:
                if target.is_file():
                    return _j.loads(target.read_text(encoding="utf-8"))
            except Exception:
                pass
    except Exception:
        pass
    return None


def _bundled_version_str() -> "str | None":
    """Read yieldos/VERSION via importlib.resources."""
    try:
        from importlib import resources as _res
        pkg_root = _res.files("yieldos")
        vpath = pkg_root / "VERSION"
        if vpath.is_file():
            return vpath.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return None


class _DoctorDeepResult:
    def __init__(self) -> None:
        self.runtime_mode: str = ""
        self.checks: list = []
        self.info_lines: list = []

    @property
    def overall_pass(self) -> bool:
        return all(ok for ok, _, _ in self.checks)

    @property
    def overall_status(self) -> str:
        return "PASS" if self.overall_pass else "FAIL"


def _run_deep_checks(runtime_mode: "str | None" = None) -> _DoctorDeepResult:
    """
    Run deep integrity checks and return a _DoctorDeepResult.
    Detects source vs installed mode automatically unless runtime_mode is forced.
    """
    import json as _json

    result = _DoctorDeepResult()
    mode = runtime_mode if runtime_mode is not None else _detect_runtime_mode()
    result.runtime_mode = mode

    if mode == "source":
        # ── source mode: check root project files ─────────────────────────
        root = _find_project_root()
        version_file = root / "VERSION"
        pyproject_file = root / "pyproject.toml"
        manifest_file = root / "MANIFEST.json"

        file_version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "MISSING"
        pkg_version = None
        if pyproject_file.exists():
            for line in pyproject_file.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("version") and "=" in line:
                    pkg_version = line.split("=", 1)[1].strip().strip('"')
                    break
        manifest_version = None
        manifest_data = None
        if manifest_file.exists():
            manifest_data = _json.loads(manifest_file.read_text(encoding="utf-8"))
            manifest_version = manifest_data.get("version")

        version_consistent = (file_version == pkg_version == manifest_version)
        result.checks.append((version_consistent,
            f"Version consistency: VERSION={file_version} pyproject={pkg_version} MANIFEST={manifest_version}",
            "All three must match"))

        if manifest_data:
            bundle = manifest_data.get("standard_output_bundle", [])
            ok = len(bundle) == 22
            result.checks.append((ok,
                f"standard_output_bundle: {len(bundle)} files declared ({'PASS' if ok else 'must be 22'})",
                "Update MANIFEST.json standard_output_bundle to list 22 files"))
        else:
            result.checks.append((False, "standard_output_bundle: MANIFEST.json missing", ""))

        sample_data_root = Path(__file__).parent.parent / "sample_data"
        for domain_dir, sentinel in [
            ("memory_device", "block_health.csv"),
            ("robot", "robot_telemetry.csv"),
            ("space", "satellite_telemetry.csv"),
            ("semiconductor", "lot_genealogy.csv"),
            ("semiforge", "config.json"),
        ]:
            sd = sample_data_root / domain_dir
            ok = sd.exists() and (sd / sentinel).exists()
            result.checks.append((ok,
                f"sample_data/{domain_dir}: {'PASS' if ok else 'MISSING'}",
                f"Restore yieldos/sample_data/{domain_dir}/{sentinel}"))

        demo_sd = sample_data_root / "product_memory_rebinning_demo"
        ok = demo_sd.exists() and (demo_sd / "block_health.csv").exists()
        result.checks.append((ok,
            f"sample_data/product_memory_rebinning_demo: {'PASS' if ok else 'MISSING'}",
            "Copy samples/product_memory_rebinning_demo/ into yieldos/sample_data/"))

        erp = sample_data_root / "external_robot_log_package"
        erp_ok = erp.exists() and (erp / "robot_telemetry.csv").exists()
        result.checks.append((erp_ok,
            f"sample_data/external_robot_log_package: {'PASS' if erp_ok else 'MISSING'}",
            "Restore yieldos/sample_data/external_robot_log_package/"))

        fyfab = sample_data_root / "fyfab_seed"
        fyfab_ok = fyfab.exists() and (fyfab / "fabricated_structure_grid.csv").exists()
        result.checks.append((fyfab_ok,
            f"sample_data/fyfab_seed: {'PASS' if fyfab_ok else 'MISSING'}",
            "Restore yieldos/sample_data/fyfab_seed/"))

        scripts_dir = root / "scripts"
        run_demo = scripts_dir / "run_demo.py"
        if run_demo.exists():
            _rd = run_demo.read_text(encoding="utf-8")
            is_wrapper = "deprecated" in _rd.lower() and "RobotAnalyzer" not in _rd
            result.checks.append((is_wrapper,
                f"scripts/run_demo.py: {'clean wrapper (PASS)' if is_wrapper else 'still contains domain imports (FAIL)'}",
                "Replace run_demo.py with thin CLI wrapper"))
        else:
            result.checks.append((True, "scripts/run_demo.py: not present (OK)", ""))

        make_zip = scripts_dir / "make_release_zip.py"
        if make_zip.exists():
            _mz = make_zip.read_text(encoding="utf-8")
            is_disabled = "raise SystemExit" in _mz or "DEPRECATED" in _mz
            result.checks.append((is_disabled,
                f"scripts/make_release_zip.py: {'disabled (PASS)' if is_disabled else 'still executable (FAIL)'}",
                "Add raise SystemExit guard to make_release_zip.py"))
        else:
            result.checks.append((True, "scripts/make_release_zip.py: not present (OK)", ""))

        dist_dir = root / "dist"
        stale_files = list(dist_dir.glob("*2.1.0*")) if dist_dir.exists() else []
        result.checks.append((len(stale_files) == 0,
            f"dist/ stale artifacts: {'none found (PASS)' if not stale_files else [f.name for f in stale_files]}",
            "Remove v2.1.0 artifacts from dist/ before release"))

    else:
        # ── installed mode: package metadata + bundled resources ──────────
        meta_ver = _installed_package_version()
        bundled_ver = _bundled_version_str()
        bundled_manifest_data_for_ver = _bundled_manifest_data()

        if meta_ver:
            result.checks.append((True, f"Package version: {meta_ver}", ""))
        elif bundled_ver:
            result.checks.append((True, f"Package version: {bundled_ver} (via bundled VERSION)", ""))
        elif bundled_manifest_data_for_ver and bundled_manifest_data_for_ver.get("version"):
            result.checks.append((True,
                f"Package version: {bundled_manifest_data_for_ver['version']} (via bundled MANIFEST)", ""))
        else:
            result.checks.append((False,
                "Package version: not found via metadata, bundled VERSION, or bundled MANIFEST",
                "Package not installed or package name mismatch"))

        if bundled_ver:
            result.info_lines.append(f"Bundled VERSION: {bundled_ver}")
        else:
            result.info_lines.append("Bundled VERSION not found, using package metadata")

        result.info_lines.append(
            "pyproject.toml not available in installed mode, using package metadata"
        )

        manifest_data = bundled_manifest_data_for_ver or _bundled_manifest_data()
        if manifest_data:
            result.checks.append((True, "Bundled MANIFEST.json: found", ""))
            bundle = manifest_data.get("standard_output_bundle", [])
            ok = len(bundle) == 22
            result.checks.append((ok,
                f"standard_output_bundle: {len(bundle)} files declared ({'PASS' if ok else 'must be 22'})",
                "Bundled MANIFEST.json standard_output_bundle must have 22 files"))
            domains = manifest_data.get("domains", [])
            expected_domains = {"robot", "space", "semiconductor", "semiforge", "memory"}
            ok = expected_domains.issubset(set(domains))
            result.checks.append((ok,
                f"domains: {', '.join(domains)}", "Missing required domains"))
        else:
            result.checks.append((False,
                "Bundled MANIFEST.json: MISSING (package data not installed?)", ""))

        try:
            from importlib import resources as _res
            _pkg_root = _res.files("yieldos")
            for domain_rel, sentinel in [
                ("sample_data/memory_device", "block_health.csv"),
                ("sample_data/robot", "robot_telemetry.csv"),
                ("sample_data/space", "satellite_telemetry.csv"),
                ("sample_data/semiconductor", "lot_genealogy.csv"),
                ("sample_data/semiforge", "config.json"),
            ]:
                target = _pkg_root
                for part in domain_rel.split("/"):
                    target = target / part
                sentinel_path = target / sentinel
                try:
                    ok = sentinel_path.is_file()
                except Exception:
                    ok = False
                result.checks.append((ok,
                    f"package {domain_rel}: {'PASS' if ok else 'MISSING'}",
                    f"Package data missing: {domain_rel}/{sentinel}"))

            erp_path = _pkg_root / "sample_data" / "external_robot_log_package"
            erp_sentinel = erp_path / "robot_telemetry.csv"
            try:
                erp_ok = erp_sentinel.is_file()
            except Exception:
                erp_ok = False
            result.checks.append((erp_ok,
                f"package sample_data/external_robot_log_package: {'PASS' if erp_ok else 'MISSING'}",
                "Package data missing: external_robot_log_package/"))
        except Exception as exc:
            result.checks.append((False, f"Package sample data: ERROR ({exc})", ""))

    # ── Shared checks (both modes) ─────────────────────────────────────────
    try:
        from ..contracts.recovery_candidate import FORBIDDEN_ACTION_PREFIXES
        ok = "schedule_" in FORBIDDEN_ACTION_PREFIXES and "flag_" in FORBIDDEN_ACTION_PREFIXES
        result.checks.append((ok,
            f"FORBIDDEN_ACTION_PREFIXES includes schedule_ and flag_: {'PASS' if ok else 'FAIL'}", ""))
    except Exception as exc:
        result.checks.append((False, f"FORBIDDEN_ACTION_PREFIXES check: FAIL ({exc})", ""))

    return result


def cmd_doctor(args: argparse.Namespace) -> int:
    import sys as _sys
    print("HAL YieldOS Doctor\n")
    runtime_mode = _detect_runtime_mode()
    print(f"Runtime mode: {runtime_mode}\n")
    checks = []

    vi = _sys.version_info
    ok = vi >= (3, 10)
    checks.append((ok, f"Python version: {vi.major}.{vi.minor}.{vi.micro}", "requires >= 3.10"))

    try:
        import yieldos  # noqa
        checks.append((True, "Package import: PASS", ""))
    except Exception as e:
        checks.append((False, f"Package import: FAIL ({e})", ""))

    try:
        from . import main  # noqa
        checks.append((True, "CLI entrypoint: PASS", ""))
    except Exception as e:
        checks.append((False, f"CLI entrypoint: FAIL ({e})", ""))

    samples = _sample_root()
    ok = samples.exists()
    checks.append((ok, f"Sample files: {'PASS (' + str(samples) + ')' if ok else 'MISSING (' + str(samples) + ')'}", ""))

    demo_script = Path(__file__).parent.parent.parent / "scripts" / "run_demo.py"
    if demo_script.exists():
        print("  [INFO] scripts/run_demo.py: found (development helper)")
    else:
        print("  [INFO] scripts/run_demo.py: not found (optional development helper -- use 'yieldos demo' instead)")

    try:
        test_path = Path("output") / ".doctor_write_test"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("ok")
        test_path.unlink()
        checks.append((True, "Write permission: PASS", ""))
    except Exception as e:
        checks.append((False, f"Write permission: FAIL ({e})", ""))

    try:
        from ..optimizers.sqbm_optional import SQBMOptimizer
        if SQBMOptimizer().is_available():
            checks.append((True, "SQBM backend: installed", ""))
        else:
            print("  [INFO] SQBM backend: optional, not installed")
    except Exception:
        print("  [INFO] SQBM backend: optional, not installed")

    # Safety default check — use a valid safe-prefix action
    try:
        from ..contracts import RecoveryCandidate
        rc = RecoveryCandidate(action="recommend_test", expected_benefit="doctor safety check")
        ok = not rc.hardware_execution_enabled
        checks.append((ok, "Safety default (hardware=false): PASS", "hardware_execution_enabled defaulted to True!"))
    except Exception as e:
        checks.append((False, f"Safety default: FAIL ({e})", ""))

    # Safety prefix enforcement
    try:
        from ..contracts import RecoveryCandidate
        try:
            RecoveryCandidate(action="execute_command", expected_benefit="x")
            checks.append((False, "Safety prefix guard: FAIL (accepted unsafe action)", ""))
        except ValueError:
            checks.append((True, "Safety prefix guard: PASS (rejects unsafe actions)", ""))
    except Exception as e:
        checks.append((False, f"Safety prefix guard: ERROR ({e})", ""))

    all_pass = True
    for ok, msg, hint in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {msg}")
        if not ok:
            all_pass = False
            if hint:
                print(f"         hint: {hint}")

    # Deep checks
    if getattr(args, "deep", False):
        print("\n[Deep Checks]")
        deep_result = _run_deep_checks(runtime_mode=runtime_mode)
        for line in deep_result.info_lines:
            print(f"  [INFO] {line}")
        for ok, msg, hint in deep_result.checks:
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {msg}")
            if not ok:
                all_pass = False
                if hint:
                    print(f"         hint: {hint}")

    print(f"\n  Overall: {'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


# ── Inspect / Generate / Record / Experience ──────────────────────────────

def cmd_inspect_output(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir)
    if not case_dir.exists():
        print(f"[ERROR] Directory not found: {case_dir}")
        return 1

    def _load(fname: str):
        p = case_dir / fname
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return None

    # Check for FYFab Seed output (v2.8.0)
    fyfab_passport = _load("functional_yield_chip_passport.json")
    if fyfab_passport and fyfab_passport.get("schema", "").startswith("hal.yieldos.fyfab"):
        cs_data = _load("fyfab_case_study.json") or {}
        cls_data = _load("usable_cell_classification.json") or {}
        dm_data = _load("defect_map_summary.json") or {}
        class_counts = cls_data.get("class_counts", {})
        remaining = fyfab_passport.get("remaining_functions", [])
        blocked = fyfab_passport.get("blocked_functions", [])
        print("FYFab Case:")
        print(f"  title:                {cs_data.get('title', 'Functional Yield Fab Seed Demo')}")
        print(f"  cells:                {sum(class_counts.values())}")
        print(f"  defects:              {dm_data.get('total_defects', 0)}")
        print(f"  functional yield score: {fyfab_passport.get('functional_yield_score', 0.0)}")
        print(f"  chip bin candidate:   {fyfab_passport.get('chip_bin_candidate', 'N/A')}")
        print(f"  remaining functions:  {len(remaining)}")
        print(f"  blocked functions:    {len(blocked)}")
        print("  boundary:             simulation-only, read-only, candidate-only")
        hw_ok = fyfab_passport.get("hardware_execution_enabled") is False
        hr_ok = fyfab_passport.get("human_review_required") is True
        print(f"  safety:               {'PASS' if hw_ok and hr_ok else 'FAIL'}")
        return 0

    # Check for import-check output (v2.7.0)
    ic_report = _load("robot_import_check_report.json")
    if ic_report:
        rf = ic_report.get("required_files", {})
        rf_count = sum(1 for v in rf.values() if v)
        rf_total = len(rf)
        opt_files = ic_report.get("optional_files", {})
        opt_present = [k for k, v in opt_files.items() if v]
        print("Robot Import Check Report:")
        print(f"  schema_status:    {ic_report.get('schema_status', 'N/A')}")
        print(f"  privacy_status:   {ic_report.get('privacy_status', 'N/A')}")
        print(f"  readiness_status: {ic_report.get('readiness_status', 'N/A')}")
        print(f"  required_files:   {rf_count}/{rf_total} present")
        if opt_present:
            print(f"  optional_files:   {', '.join(opt_present)} present")
        if ic_report.get("missing_required_files"):
            print(f"  missing files:    {ic_report['missing_required_files']}")
        if ic_report.get("detected_sensitive_fields"):
            print(f"  sensitive fields: {ic_report['detected_sensitive_fields']}")
        print(f"  next_step:        {ic_report.get('recommended_next_step', 'N/A')}")
        return 0

    state = _load("state_snapshot.json")
    pack = _load("evidence_pack.json")
    rec_raw = _load("recovery_candidates.json")
    fp = _load("functional_passport.json")
    dr = _load("decision_readiness_report.json")
    iv = _load("input_validation.json")

    if state is None and pack is None:
        # Check for error output
        err = _load("analysis_error.json")
        if err:
            print("Case status: ANALYSIS_ERROR")
            print(f"Error: {err.get('error_message', 'unknown')}")
            return 0
        print(f"[ERROR] No recognizable output files in: {case_dir}")
        return 1

    case_id = (state or pack or {}).get("case_id", "unknown")
    domain = (state or pack or {}).get("domain", "unknown")

    # Show INVALID_INPUT warning first if input validation failed
    iv_status = iv.get("status") if iv else None
    if iv_status == "FAILED":
        print("Case status: INVALID_INPUT")
        print(f"Input Validation: FAILED — {iv.get('blocking_reasons', [])}")
        print(f"Data level:       {iv.get('data_level', 'N/A')}")
        print()

    print(f"Case:         {case_id}")
    print(f"Domain:       {domain}")

    if iv:
        print(f"Input Valid:  {iv_status} (data_level: {iv.get('data_level', 'N/A')})")

    if state:
        print(f"State:        {state.get('state', 'N/A')}")
        print(f"Severity:     {state.get('severity', 'N/A')}")
        conf = state.get('confidence', 0)
        print(f"Confidence:   {conf:.0%}" if isinstance(conf, float) else f"Confidence:   {conf}")

    if pack:
        print(f"Evidence:     {len(pack.get('evidence_objects', []))} objects")
        print(f"RCA:          {len(pack.get('root_cause_candidates', []))} candidates")
        print(f"Missing:      {len(pack.get('missing_evidence', []))} evidence items")

    if fp:
        print(f"Passport:     {fp.get('bin_class', 'N/A')}")
        print(f"Remaining:    {fp.get('remaining_roles', [])}")
        print(f"Blocked:      {fp.get('blocked_roles', [])}")

    if dr:
        print(f"Readiness:    {dr.get('category', 'N/A')} (score: {dr.get('readiness_score', 'N/A')})")

    if rec_raw:
        print(f"Recovery:     {len(rec_raw)} candidates")

    hw_ok = True
    if rec_raw:
        hw_ok = not any(r.get("hardware_execution_enabled", False) for r in rec_raw)
    cb_ok = pack.get("causal_claim_boundary") == "candidate_only_not_certified_cause" if pack else True
    print(f"Safety:       {'PASS' if hw_ok and cb_ok else 'FAIL'}")

    html = case_dir / "report.html"
    if html.exists():
        print(f"Report:       {html}")

    cs = _load("robot_skill_memory_case_study.json")
    if cs:
        fb = cs.get("functional_reclassification", {})
        print()
        print("Case Study:")
        print(f"  title:           {cs.get('title', 'N/A')}")
        print(f"  baseline:        {cs.get('case_summary', {}).get('baseline_interpretation', 'N/A')}")
        print(f"  YieldOS:         {cs.get('case_summary', {}).get('yieldos_interpretation', 'N/A')}")
        print(f"  remaining roles: {len(fb.get('remaining_roles', []))}")
        print(f"  blocked roles:   {len(fb.get('blocked_roles', []))}")
        print("  evidence chain:  operator note + intervention + force/slip event + sim-to-real gap")
        print("  boundary:        read-only, candidate-only, human-review-only")

    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    gen_type = getattr(args, "gen_type", None)
    if gen_type == "semfab":
        from ..domains.semfab.synthetic_gen import generate_all_with_fault
        print(f"[YieldOS] Generating synthetic SemFab dataset (fault={args.fault}) -> {args.out}")
        info = generate_all_with_fault(args.out, n_rows=args.rows, fault=args.fault)
        print(f"[YieldOS] Generated: {info.get('tool_log_rows', 0)} tool log rows")
        print(f"[YieldOS] Output: {info['data_dir']}")
    elif gen_type == "robot":
        from ..domains.robot.synthetic_gen import generate_all_with_fault
        print(f"[YieldOS] Generating synthetic robot telemetry (fault={args.fault}) -> {args.out}")
        info = generate_all_with_fault(args.out, n_samples=args.rows, fault=args.fault)
        print(f"[YieldOS] Generated: {info['rows']} rows")
    elif gen_type == "satellite":
        from ..domains.satellite.synthetic_gen import generate_all_with_fault
        print(f"[YieldOS] Generating synthetic satellite telemetry (fault={args.fault}) -> {args.out}")
        info = generate_all_with_fault(args.out, n_samples=args.rows, fault=args.fault)
        print(f"[YieldOS] Generated: {info['rows']} rows")
    elif gen_type == "semiforge-config":
        out_path = Path(args.out) if args.out.endswith(".json") else Path(args.out + ".json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        start, end = args.defect_rate_start, args.defect_rate_end
        rates = [round(start + (end - start) * i / max(args.points - 1, 1), 4) for i in range(args.points)]
        configs = [{"defect_rate": r, "array_rows": 64, "array_cols": 64,
                    "defect_distribution": "iid", "baseline_accuracy": 0.92} for r in rates]
        out_path.write_text(json.dumps(configs, indent=2), encoding="utf-8")
        print(f"[YieldOS] Generated {len(configs)} SemiForge configs -> {out_path}")
    else:
        print("[ERROR] Unknown generate type. Use: semfab, robot, satellite, semiforge-config")
        return 1
    return 0


def cmd_semiforge_compare(args: argparse.Namespace) -> int:
    from ..domains.semiforge.sweep import run_sweep, write_sweep_csv, write_sweep_json

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    config = {}
    if args.config:
        p = Path(args.config)
        if p.exists():
            config = json.loads(p.read_text(encoding="utf-8"))

    distributions = args.distributions
    print(f"[YieldOS] SemiForge compare: distributions={distributions}, runs={args.runs}")

    all_results = {}
    for dist in distributions:
        print(f"  Sweeping distribution={dist}...")
        results = run_sweep(
            array_rows=config.get("array_rows", 64),
            array_cols=config.get("array_cols", 64),
            distribution=dist,
            clustering_factor=config.get("clustering_factor", 3.0),
            baseline_accuracy=config.get("baseline_accuracy", 0.92),
            monte_carlo_runs=args.runs,
        )
        all_results[dist] = results
        write_sweep_csv(results, str(out / f"{dist}_sweep.csv"))
        write_sweep_json(results, str(out / f"{dist}_sweep.json"))

    comparison = {
        "schema": "yieldos.semiforge.compare.v1",
        "distributions_compared": distributions,
        "monte_carlo_runs": args.runs,
        "note": (
            "Clustered defects may reduce functional yield earlier than iid random defects. "
            "This is a simulation-based sensitivity comparison, not calibrated device data."
        ),
        "results": {
            dist: {
                "mean_y_func": round(sum(r["y_func"] for r in res) / len(res), 4) if res else 0,
                "mean_r_conn": round(sum(r["r_conn"] for r in res) / len(res), 4) if res else 0,
                "point_count": len(res),
            }
            for dist, res in all_results.items()
        },
    }
    (out / "iid_vs_clustered.json").write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    html = _compare_html(comparison, all_results)
    (out / "report.html").write_text(html, encoding="utf-8")
    print(f"[YieldOS] Compare complete -> {out}")
    return 0


def _compare_html(comparison: dict, all_results: dict) -> str:
    import html as _html
    rows = []
    dists = comparison.get("distributions_compared", [])
    for dist in dists:
        for r in all_results.get(dist, []):
            rows.append(
                f"<tr><td>{_html.escape(dist)}</td>"
                f"<td>{r.get('defect_rate', 0):.3f}</td>"
                f"<td>{r.get('r_conn', 0):.3f}</td>"
                f"<td>{r.get('y_func', 0):.3f}</td></tr>"
            )
    note = _html.escape(comparison.get("note", ""))
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<title>SemiForge Distribution Compare</title>'
        '<style>body{font-family:monospace;padding:20px} table{border-collapse:collapse}'
        ' td,th{border:1px solid #ccc;padding:4px 8px}'
        ' .safety{background:#ffe0e0;padding:10px;margin:10px 0}'
        ' .note{background:#fff3cd;padding:10px;margin:10px 0}</style>'
        '</head><body>'
        f'<h1>SemiForge: {_html.escape(" vs ".join(dists))}</h1>'
        '<div class="safety">'
        '<b>Safety:</b> read_only=true | hardware_execution_enabled=false | recommendation_only'
        '</div>'
        f'<div class="note"><b>Note:</b> {note}</div>'
        '<table><tr><th>Distribution</th><th>Defect Rate</th><th>r_conn</th><th>Y_func</th></tr>'
        + "".join(rows)
        + "</table></body></html>"
    )


def cmd_semiforge_sweep(args: argparse.Namespace) -> int:
    from ..domains.semiforge.sweep import ascii_plot, run_sweep, write_sweep_csv, write_sweep_json

    config = {}
    if getattr(args, "config", None):
        cfg_path = Path(args.config)
        if cfg_path.exists():
            config = json.loads(cfg_path.read_text(encoding="utf-8"))

    rows = args.rows if args.rows is not None else config.get("array_rows", 64)
    cols = args.cols if args.cols is not None else config.get("array_cols", 64)
    cluster_factor = args.cluster_factor if args.cluster_factor is not None else config.get("clustering_factor", 3.0)
    baseline_acc = args.baseline_acc if args.baseline_acc is not None else config.get("baseline_accuracy", 0.92)
    seed = getattr(args, "seed", None)

    distributions = ["iid", "clustered"] if args.dist == "both" else [args.dist]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for dist in distributions:
        print(f"\n[YieldOS] SemiForge sweep: {rows}x{cols}, dist={dist}, MC={args.mc}"
              + (f", seed={seed}" if seed is not None else ""))
        results = run_sweep(
            array_rows=rows, array_cols=cols, distribution=dist,
            clustering_factor=cluster_factor, baseline_accuracy=baseline_acc,
            monte_carlo_runs=args.mc, seed=seed,
        )
        write_sweep_csv(results, str(out / f"sweep_{dist}.csv"))
        write_sweep_json(results, str(out / f"sweep_{dist}.json"))
        print(ascii_plot(results, "y_func"))
        print(ascii_plot(results, "r_conn"))
        print(f"[YieldOS] CSV: {out / f'sweep_{dist}.csv'}")
        print(f"[YieldOS] JSON: {out / f'sweep_{dist}.json'}")
    return 0


def cmd_fyfab_demo(args: argparse.Namespace) -> int:
    from ..domains.semiforge.fyfab import run_fyfab_demo
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)
    input_dir = getattr(args, "input", None)
    if input_dir:
        print(f"[YieldOS] FYFab Seed demo (input: {input_dir}) -> {out_path}")
    else:
        print(f"[YieldOS] FYFab Seed demo -> {out_path}")
    r = run_fyfab_demo(out_dir=str(out_path), input_dir=input_dir)
    cp = r["chip_passport"]
    cs = r["classification"].get("class_counts", {})
    dm = r["defect_summary"]
    print(f"  [INFO] case_id:               {r['case_id']}")
    print(f"  [INFO] total_cells:            {sum(cs.values())}")
    print(f"  [INFO] total_defects:          {dm.get('total_defects', 0)}")
    print(f"  [INFO] functional_yield_score: {cp.get('functional_yield_score', 0.0)}")
    print(f"  [INFO] chip_bin_candidate:     {cp.get('chip_bin_candidate', 'N/A')}")
    print(f"  [INFO] remaining_functions:    {cp.get('remaining_functions', [])}")
    print(f"  [INFO] blocked_functions:      {cp.get('blocked_functions', [])}")
    print("[YieldOS] FYFab Seed demo complete")
    return 0


def _memory_source_data_paths(input_dir: str) -> list:
    """Return all expected memory input paths for source_data_manifest (existing or not)."""
    d = Path(input_dir)
    return [str(d / "block_health.csv"), str(d / "device_info.json")]


def _robot_source_data_paths(telemetry_path: str) -> list:
    """Return robot input paths for source_data_manifest."""
    p = Path(telemetry_path)
    paths = [str(p)]
    base = p.parent
    for optional in ("maintenance_log.csv", "operation_log.csv", "environment_log.csv"):
        op = base / optional
        paths.append(str(op))
    return paths


def _space_source_data_paths(telemetry_path: str) -> list:
    """Return space input paths for source_data_manifest."""
    p = Path(telemetry_path)
    paths = [str(p)]
    op = p.parent / "mission_profile.json"
    paths.append(str(op))
    return paths


def _semiconductor_source_data_paths(data_dir: str) -> list:
    """Return semiconductor input paths for source_data_manifest."""
    d = Path(data_dir)
    return [str(d / f) for f in (
        "tool_log.csv", "wafer_map.csv", "metrology.csv",
        "test_result.csv", "lot_genealogy.csv",
    )]


def _semiforge_source_data_paths(config_path: str) -> list:
    """Return semiforge input paths for source_data_manifest."""
    return [str(config_path)]


def _memory_extra_outputs(result: dict) -> dict:
    """Extract memory-specific extra outputs for write_all()."""
    extras = {}
    if result.get("functional_capacity"):
        extras["memory_functional_capacity"] = result["functional_capacity"]
    if result.get("placement_recommendation"):
        extras["memory_data_placement_recommendation"] = result["placement_recommendation"]
    if result.get("bad_block_evidence_map"):
        extras["memory_bad_block_evidence_map"] = result["bad_block_evidence_map"]
    return extras or None


def _semiconductor_extra_outputs(result: dict) -> dict:
    """Build semiconductor-specific extra output files for write_all().

    Converts internal analyzer drift/confidence data to release-grade evidence reports.
    """
    extras = {}
    case_id = result.get("case_id", "semiconductor_case")
    raw_drift = result.get("process_drift_report")
    raw_conf = result.get("confidence_report")

    if raw_drift:
        # Map internal metric_trends to the v1 signal schema
        metric_trends = raw_drift.get("metric_trends", [])
        signals = []
        unavailable = []
        for t in metric_trends:
            status = t.get("status", "UNKNOWN")
            if status == "INSUFFICIENT_DATA":
                unavailable.append(t.get("metric", "unknown"))
                continue
            early_mean = t.get("early_mean")
            recent_mean = t.get("recent_mean")
            if early_mean is None or recent_mean is None:
                unavailable.append(t.get("metric", "unknown"))
                continue
            delta = round(recent_mean - early_mean, 6) if recent_mean is not None and early_mean is not None else None
            relative_delta = t.get("relative_delta")
            direction = "upward" if (delta is not None and delta > 0) else ("downward" if (delta is not None and delta < 0) else "stable")
            signals.append({
                "status": status,
                "metric": t.get("metric", "unknown"),
                "old_mean": early_mean,
                "recent_mean": recent_mean,
                "delta": delta,
                "relative_delta": relative_delta,
                "direction": direction,
                "recent_fraction": t.get("recent_fraction", 0.3),
                "threshold": t.get("threshold", 0.08),
                "sample_count": t.get("sample_count", 0),
                "claim_boundary": "candidate_trend_not_root_cause",
            })

        # Determine summary_status
        statuses = {t.get("status") for t in metric_trends}
        if "DRIFT_CANDIDATE" in statuses:
            summary_status = "DRIFT_CANDIDATE"
        elif statuses == {"STABLE_NORMAL"}:
            summary_status = "STABLE_NORMAL"
        elif statuses == {"INSUFFICIENT_DATA"}:
            summary_status = "INSUFFICIENT_DATA"
        elif statuses and all(s in ("STABLE_NORMAL", "INSUFFICIENT_DATA") for s in statuses):
            summary_status = "STABLE_NORMAL"
        elif statuses:
            summary_status = "MIXED_SIGNALS"
        else:
            summary_status = "UNKNOWN"

        extras["process_drift_report"] = {
            "schema": "hal.yieldos.semiconductor.process_drift_report.v1",
            "case_id": case_id,
            "domain": "semiconductor",
            "recent_trend_detection": {
                "signals": signals,
                "unavailable_metrics": unavailable,
                "summary_status": summary_status,
            },
            "claim_boundary": "candidate_drift_not_root_cause",
            "safety_boundary": {
                "hardware_execution_enabled": False,
                "human_review_required": True,
                "candidate_only": True,
            },
        }

    if raw_conf:
        extras["semiconductor_confidence_report"] = {
            "schema": "hal.yieldos.semiconductor.confidence_report.v1",
            "case_id": case_id,
            "domain": "semiconductor",
            "confidence_report": {
                "confidence_kind": "analysis_confidence",
                "score": raw_conf.get("score", 0.0),
                "data_status": raw_conf.get("data_status", "UNKNOWN"),
                "signal_status": raw_conf.get("signal_status", "UNKNOWN"),
                "reasons": raw_conf.get("reasons", []),
                "claim_boundary": "confidence_is_analysis_quality_not_safety_certification",
                "missing_metrics": raw_conf.get("missing_metrics", []),
                "available_metrics_summary": raw_conf.get("available_metrics_summary", {}),
            },
            "interpretation_boundary": {
                "confidence_is_not": [
                    "risk severity",
                    "safety certification",
                    "root-cause certification",
                    "yield guarantee",
                ],
                "confidence_means": "analysis_quality_given_available_inputs",
            },
            "safety_boundary": {
                "hardware_execution_enabled": False,
                "human_review_required": True,
                "candidate_only": True,
            },
        }

    return extras or None


def cmd_memory_analyze(args: argparse.Namespace) -> int:
    inp = args.input
    out = args.out
    asset = getattr(args, "asset", "memdev_01")
    case_id = getattr(args, "case", None)
    print(f"[YieldOS] Memory analysis: {inp}")
    result = _run_memory(inp, case_id=case_id, asset_id=asset)
    extra = _memory_extra_outputs(result)
    policy_inputs = _load_policy_inputs(args)
    paths = _run_and_write(result, out, "memory", extra_outputs=extra, policy_inputs=policy_inputs,
                           source_data_paths=_memory_source_data_paths(inp))
    fy = result["state"].metrics.get("functional_yield", "N/A")
    _print_completion(
        result["case_id"], paths, result["state"],
        extra={"functional_yield": f"{fy:.1%}" if isinstance(fy, float) else fy,
               "bin_class": result.get("bin_class", "N/A")},
    )
    return 0


def cmd_memory_gen(args: argparse.Namespace) -> int:
    from ..domains.memory.synthetic_gen import generate_all
    n_blocks = getattr(args, "blocks", 128)
    out = args.out
    print(f"[YieldOS] Generating synthetic memory block health data -> {out} ({n_blocks} blocks)")
    info = generate_all(out, n_blocks=n_blocks)
    print(f"[YieldOS] Generated: {info['blocks']} blocks, device={info['device_id']}")
    print(f"[YieldOS] factory_bad={info['factory_bad']}, runtime_bad={info['runtime_bad']}")
    return 0


def cmd_memory_product_demo(args: argparse.Namespace) -> int:
    """Run the Product Memory Rebinning Killer Demo."""
    out = args.out

    samples = _sample_root()
    demo_dir = samples / "product_memory_rebinning_demo"
    if not demo_dir.exists():
        print(f"[YieldOS] ERROR: demo sample not found at {demo_dir}", file=sys.stderr)
        return 1

    policy_path = demo_dir / "baseline_policy.json"
    print(f"[YieldOS] Product Memory Rebinning Demo: {demo_dir}")
    if policy_path.exists():
        print(f"[YieldOS] Loading baseline_policy: {policy_path}")

    result = _run_memory(str(demo_dir), case_id="product_demo_rebinning", asset_id="NAND_DEMO_32GB_MLC")
    extra = _memory_extra_outputs(result)
    paths = _run_and_write(result, out, "memory", extra_outputs=extra,
                           source_data_paths=_memory_source_data_paths(str(demo_dir)))

    # Enrich baseline_vs_yieldos.json with baseline_policy data
    baseline_policy = {}
    if policy_path.exists():
        baseline_policy = json.loads(policy_path.read_text(encoding="utf-8"))

    baseline_path = Path(out) / "baseline_vs_yieldos.json"
    bvsy = {}
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
        print("[YieldOS] Enriched baseline_vs_yieldos.json with baseline_policy data")

        # Update case_manifest.json checksum to match the enriched file
        manifest_path = Path(out) / "case_manifest.json"
        if manifest_path.exists():
            import hashlib as _hl
            new_sha256 = "sha256:" + _hl.sha256(enriched_bytes).hexdigest()
            cm = json.loads(manifest_path.read_text(encoding="utf-8"))
            if "files" in cm and "baseline_vs_yieldos" in cm["files"]:
                cm["files"]["baseline_vs_yieldos"]["sha256"] = new_sha256
                cm["files"]["baseline_vs_yieldos"]["byte_size"] = len(enriched_bytes)
                manifest_path.write_text(
                    json.dumps(cm, indent=2, ensure_ascii=False), encoding="utf-8"
                )

    fy = result["state"].metrics.get("functional_yield", 0.0)
    reclassified = bvsy.get("reclassification_occurred", False)
    _print_completion(
        result["case_id"], paths, result["state"],
        extra={
            "functional_yield": f"{fy:.1%}" if isinstance(fy, float) else fy,
            "bin_class": result.get("bin_class", "N/A"),
            "reclassification_occurred": reclassified,
        },
    )
    return 0


def cmd_record_outcome(args: argparse.Namespace) -> int:
    from ..contracts import OutcomeRecord
    from ..core.experience_graph import ExperienceGraph

    record = OutcomeRecord(
        case_id=args.case,
        domain=args.rec_domain,
        asset_id=args.asset,
        selected_action=args.action_taken,
        outcome=args.outcome,
        before_score=args.before,
        after_score=args.after,
        notes=args.notes,
        recorded_by="engineer",
    )
    graph = ExperienceGraph(store_path=args.exp_file)
    graph.record(record)
    print(f"[YieldOS] Outcome recorded: {args.case} -> {args.outcome}")
    print(f"[YieldOS] Score delta: {record.before_score:.2f} -> {record.after_score:.2f} ({record.delta():+.2f})")
    return 0


def cmd_experience(args: argparse.Namespace) -> int:
    from ..core.experience_graph import ExperienceGraph

    graph = ExperienceGraph(store_path=args.file)
    filter_asset = getattr(args, "filter_asset", None)
    filter_domain = getattr(args, "filter_domain", None)
    if filter_asset:
        records = graph.load_by_asset(filter_asset)
    elif filter_domain:
        records = graph.load_by_domain(filter_domain)
    else:
        records = graph.load_all()

    summary = graph.summary()
    print(f"[YieldOS] Experience Graph: {summary['total']} total records")
    print(f"[YieldOS] By domain: {summary['by_domain']}")
    for r in records[-10:]:
        delta = r.get("delta", 0)
        sign = "+" if delta >= 0 else ""
        print(f"  {r['case_id']:30s}  {r['domain']:20s}  {r['selected_action']:30s}  "
              f"{r['outcome']:25s}  delta={sign}{delta:.2f}")
    return 0


# ── Parser ────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    version = _get_version()
    parser = argparse.ArgumentParser(
        prog="yieldos",
        description=f"HAL YieldOS v{version} - Read-Only Industrial Evidence Engine",
    )
    sub = parser.add_subparsers(dest="command")

    # ── demo ─────────────────────────────────────────────────────────────
    demo_p = sub.add_parser("demo", help="Run built-in demo for one or all domain packs")
    demo_p.add_argument("--demo-domain", dest="demo_domain", default=None,
                        help="Domain to demo: robot, space, semiconductor, semiforge, satguard, semfab, all")
    demo_p.add_argument("--domain", dest="demo_domain", default=None,
                        help="Alias for --demo-domain")
    demo_p.add_argument("--all", action="store_true", default=False, help="Run all domains")
    demo_p.add_argument("--out", required=True, help="Output directory")

    # ── analyze (unified) ────────────────────────────────────────────────
    analyze_p = sub.add_parser("analyze", help="Analyze with any domain pack")
    analyze_p.add_argument("--domain", dest="domain", required=True,
                           help="Domain: robot, space, semiconductor, semiforge (aliases: satguard, semfab, satellite)")
    analyze_p.add_argument("--input", required=True, help="Input file or directory")
    analyze_p.add_argument("--out", required=True, help="Output directory")
    analyze_p.add_argument("--asset", default=None)
    analyze_p.add_argument("--case", default=None)
    analyze_p.add_argument("--mc", type=int, default=30)
    analyze_p.add_argument("--optimizer", default="greedy", choices=["greedy", "sqbm"])
    analyze_p.add_argument("--cvc", default=None, help="Path to cvc.json (constraint & value priority)")
    analyze_p.add_argument("--authority", default=None, help="Path to action_authority_matrix.json")
    analyze_p.add_argument("--envelope", default=None, help="Path to operating_envelope.json")
    analyze_p.add_argument("--risk-policy", dest="risk_policy", default=None, help="Path to risk_policy.json")

    # ── run (backward compat) ─────────────────────────────────────────────
    run_p = sub.add_parser("run", help="Analyze any domain with a single command")
    run_p.add_argument("--input", required=True)
    run_p.add_argument("--domain", required=True, dest="run_domain",
                       choices=list(DOMAIN_ALIASES.keys()) + ["semfab", "semiforge", "robot", "sat", "nand"])
    run_p.add_argument("--out", required=True)
    run_p.add_argument("--case", default=None)

    # ── semifab ──────────────────────────────────────────────────────────
    sf = sub.add_parser("semifab")
    sf_sub = sf.add_subparsers(dest="action")
    sf_a = sf_sub.add_parser("analyze")
    sf_a.add_argument("--input", required=True)
    sf_a.add_argument("--out", required=True)
    sf_a.add_argument("--asset", default="ETCH_01.CH_A")
    sf_a.add_argument("--case", default=None)
    sf_a.add_argument("--cvc", default=None)
    sf_a.add_argument("--authority", default=None)
    sf_a.add_argument("--envelope", default=None)
    sf_a.add_argument("--risk-policy", dest="risk_policy", default=None)
    sf_g = sf_sub.add_parser("gen")
    sf_g.add_argument("--out", required=True)
    sf_g.add_argument("--lots", type=int, default=20)
    sf_g.add_argument("--wafers", type=int, default=5)

    # ── semiforge ────────────────────────────────────────────────────────
    forge = sub.add_parser("semiforge")
    forge_sub = forge.add_subparsers(dest="action")
    forge_sim = forge_sub.add_parser("simulate")
    forge_sim.add_argument("--config", required=True)
    forge_sim.add_argument("--out", required=True)
    forge_sim.add_argument("--asset", default=None, help="Asset identifier for case output")
    forge_sim.add_argument("--mc", type=int, default=30)
    forge_sim.add_argument("--optimizer", default="greedy", choices=["greedy", "sqbm"])
    forge_sim.add_argument("--cvc", default=None)
    forge_sim.add_argument("--authority", default=None)
    forge_sim.add_argument("--envelope", default=None)
    forge_sim.add_argument("--risk-policy", dest="risk_policy", default=None)
    forge_sweep = forge_sub.add_parser("sweep")
    forge_sweep.add_argument("--config", default=None)
    forge_sweep.add_argument("--out", required=True)
    forge_sweep.add_argument("--rows", type=int, default=None)
    forge_sweep.add_argument("--cols", type=int, default=None)
    forge_sweep.add_argument("--dist", default="both", choices=["iid", "clustered", "both"])
    forge_sweep.add_argument("--mc", type=int, default=30)
    forge_sweep.add_argument("--cluster-factor", type=float, default=None)
    forge_sweep.add_argument("--baseline-acc", type=float, default=None)
    forge_sweep.add_argument("--seed", type=int, default=None)
    forge_compare = forge_sub.add_parser("compare")
    forge_compare.add_argument("--config", required=True)
    forge_compare.add_argument("--distributions", nargs="+", default=["iid", "clustered"])
    forge_compare.add_argument("--out", required=True)
    forge_compare.add_argument("--runs", type=int, default=30)
    forge_fyfab = forge_sub.add_parser("fyfab-demo")
    forge_fyfab.add_argument("--out", required=True, help="Output directory for FYFab Seed demo")
    forge_fyfab.add_argument("--input", default=None, help="Optional input folder with FYFab seed data")

    # ── robot ─────────────────────────────────────────────────────────────
    robot = sub.add_parser("robot")
    robot_sub = robot.add_subparsers(dest="action")
    robot_a = robot_sub.add_parser("analyze")
    robot_a.add_argument("--input", required=True)
    robot_a.add_argument("--out", required=True)
    robot_a.add_argument("--asset", default="robot_arm_07")
    robot_a.add_argument("--case", default=None)
    robot_a.add_argument("--maintenance-log", dest="maintenance_log", default=None,
                         help="Optional maintenance log CSV for industrial data layer")
    robot_a.add_argument("--operation-log", dest="operation_log", default=None,
                         help="Optional operation log CSV for industrial data layer")
    robot_a.add_argument("--environment-log", dest="environment_log", default=None,
                         help="Optional environment log CSV for industrial data layer")
    robot_a.add_argument("--cvc", default=None)
    robot_a.add_argument("--authority", default=None)
    robot_a.add_argument("--envelope", default=None)
    robot_a.add_argument("--risk-policy", dest="risk_policy", default=None)
    robot_g = robot_sub.add_parser("gen")
    robot_g.add_argument("--out", required=True)
    robot_g.add_argument("--samples", type=int, default=500)
    robot_sd = robot_sub.add_parser("skill-demo")
    robot_sd.add_argument("--out", required=True, help="Output directory for Robot Skill Memory demo")
    robot_sd.add_argument("--input", default=None, help="Optional external robot log package folder")
    robot_ic = robot_sub.add_parser("import-check")
    robot_ic.add_argument("--input", required=True, help="External robot log package folder to check")
    robot_ic.add_argument("--out", required=True, help="Output directory for import-check reports")
    robot_pp = robot_sub.add_parser("pilot-pack")
    robot_pp.add_argument("--input", required=True, help="Directory with 6 required pilot CSV files")
    robot_pp.add_argument("--out", required=True, help="Output directory for pilot-pack outputs")
    robot_pp.add_argument("--asset", default="robot_pilot_01", help="Asset identifier")
    robot_pp.add_argument("--case", default=None, help="Optional case ID override")

    # ── semiconductor ────────────────────────────────────────────────────
    semicon = sub.add_parser("semiconductor")
    semicon_sub = semicon.add_subparsers(dest="action")
    semicon_pp = semicon_sub.add_parser("pilot-pack")
    semicon_pp.add_argument("--input", required=True,
                            help="Directory with pilot semiconductor input files")
    semicon_pp.add_argument("--out", required=True,
                            help="Output directory for semiconductor pilot-pack outputs")
    semicon_pp.add_argument("--asset", default="chip_demo_001", help="Asset/chip identifier")
    semicon_pp.add_argument("--case", default=None, help="Optional case ID override")

    # ── sat ───────────────────────────────────────────────────────────────
    sat = sub.add_parser("sat")
    sat_sub = sat.add_subparsers(dest="action")
    sat_a = sat_sub.add_parser("analyze")
    sat_a.add_argument("--input", required=True)
    sat_a.add_argument("--out", required=True)
    sat_a.add_argument("--asset", default="cubesat_01")
    sat_a.add_argument("--case", default=None)
    sat_a.add_argument("--cvc", default=None)
    sat_a.add_argument("--authority", default=None)
    sat_a.add_argument("--envelope", default=None)
    sat_a.add_argument("--risk-policy", dest="risk_policy", default=None)
    sat_g = sat_sub.add_parser("gen")
    sat_g.add_argument("--out", required=True)
    sat_g.add_argument("--samples", type=int, default=500)
    sat_od = sat_sub.add_parser("orbit-demo")
    sat_od.add_argument("--out", required=True)
    sat_od.add_argument("--asset", default="cubesat_demo_01")

    # ── memory ─────────────────────────────────────────────────────────────
    mem = sub.add_parser("memory")
    mem_sub = mem.add_subparsers(dest="action")
    mem_a = mem_sub.add_parser("analyze")
    mem_a.add_argument("--input", required=True, help="Directory containing block_health.csv and device_info.json")
    mem_a.add_argument("--out", required=True, help="Output directory")
    mem_a.add_argument("--asset", default="memdev_01", help="Asset identifier")
    mem_a.add_argument("--case", default=None, help="Optional case ID")
    mem_a.add_argument("--cvc", default=None)
    mem_a.add_argument("--authority", default=None)
    mem_a.add_argument("--envelope", default=None)
    mem_a.add_argument("--risk-policy", dest="risk_policy", default=None)
    mem_g = mem_sub.add_parser("gen")
    mem_g.add_argument("--out", required=True, help="Output directory for generated sample data")
    mem_g.add_argument("--blocks", type=int, default=128, help="Number of blocks to generate")
    mem_pd = mem_sub.add_parser("product-demo")
    mem_pd.add_argument("--out", required=True, help="Output directory for product demo outputs")

    # ── validate ──────────────────────────────────────────────────────────
    val = sub.add_parser("validate")
    val.add_argument("--case", required=True)
    val.add_argument("--strict", action="store_true", default=False,
                     help="Strict mode: check all v2.1 Standard Output Bundle files")

    # ── version / doctor / inspect-output ─────────────────────────────────
    sub.add_parser("version")
    doctor_p = sub.add_parser("doctor")
    doctor_p.add_argument("--deep", action="store_true", default=False,
                          help="Run deep consistency checks (version, sample_data, dist artifacts)")
    insp = sub.add_parser("inspect-output")
    insp.add_argument("case_dir")

    # ── generate ──────────────────────────────────────────────────────────
    gen = sub.add_parser("generate")
    gen_sub = gen.add_subparsers(dest="gen_type")
    gen_sf = gen_sub.add_parser("semfab")
    gen_sf.add_argument("--rows", type=int, default=1000)
    gen_sf.add_argument("--fault", default="none",
                        choices=["none","chamber_drift","incoming_wafer_variation",
                                 "recipe_step_instability","metrology_shift","yield_drop"])
    gen_sf.add_argument("--out", required=True)
    gen_ro = gen_sub.add_parser("robot")
    gen_ro.add_argument("--rows", type=int, default=1000)
    gen_ro.add_argument("--fault", default="none",
                        choices=["none","joint_degradation","vibration_increase",
                                 "position_error_growth","latency_spike","battery_drop"])
    gen_ro.add_argument("--out", required=True)
    gen_sa = gen_sub.add_parser("satellite")
    gen_sa.add_argument("--rows", type=int, default=1000)
    gen_sa.add_argument("--fault", default="none",
                        choices=["none","power_margin_drop","thermal_rise",
                                 "attitude_error_growth","comms_snr_drop","fault_flag_event"])
    gen_sa.add_argument("--out", required=True)
    gen_fo = gen_sub.add_parser("semiforge-config")
    gen_fo.add_argument("--defect-rate-start", type=float, default=0.0)
    gen_fo.add_argument("--defect-rate-end", type=float, default=0.4)
    gen_fo.add_argument("--points", type=int, default=10)
    gen_fo.add_argument("--out", required=True)

    # ── record / experience ───────────────────────────────────────────────
    rec = sub.add_parser("record")
    rec.add_argument("--case", required=True)
    rec.add_argument("--rec-domain", required=True, dest="rec_domain")
    rec.add_argument("--asset", required=True)
    rec.add_argument("--action", required=True, dest="action_taken")
    rec.add_argument("--outcome", required=True)
    rec.add_argument("--before", type=float, default=0.0)
    rec.add_argument("--after", type=float, default=0.0)
    rec.add_argument("--notes", default="")
    rec.add_argument("--exp-file", default="output/experiences.jsonl")

    exp = sub.add_parser("experience")
    exp.add_argument("--file", default="output/experiences.jsonl")
    exp.add_argument("--filter-domain", dest="filter_domain", default=None)
    exp.add_argument("--filter-asset", dest="filter_asset", default=None)

    # ── pilot ─────────────────────────────────────────────────────────────
    _PILOT_DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]
    pilot = sub.add_parser("pilot")
    pilot_sub = pilot.add_subparsers(dest="action")
    pilot_init = pilot_sub.add_parser("init")
    pilot_init.add_argument(
        "--domain", required=True, choices=_PILOT_DOMAINS,
        help="Domain to generate pilot readiness pack for",
    )
    pilot_init.add_argument("--out", required=True, help="Output directory for pilot init pack")
    pilot_check = pilot_sub.add_parser("check")
    pilot_check.add_argument(
        "--domain", required=True, choices=_PILOT_DOMAINS,
        help="Domain to check readiness for",
    )
    pilot_check.add_argument("--input", required=True, help="Directory containing pilot input data")
    pilot_check.add_argument("--out", required=True, help="Output directory for readiness report")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = getattr(args, "command", None)
    action = getattr(args, "action", None)

    dispatch = {
        "demo": cmd_demo,
        "analyze": cmd_analyze,
        "run": cmd_run,
        "version": cmd_version,
        "doctor": cmd_doctor,
        "inspect-output": cmd_inspect_output,
        "generate": cmd_generate,
        "validate": cmd_validate,
        "record": cmd_record_outcome,
        "experience": cmd_experience,
    }
    if command in dispatch:
        return dispatch[command](args)

    # Sub-subcommand dispatch
    if command == "semifab":
        if action == "gen":
            return cmd_semifab_gen(args)
        if action == "analyze":
            return cmd_semifab_analyze(args)
    elif command == "semiforge":
        if action == "simulate":
            return cmd_semiforge_simulate(args)
        if action == "sweep":
            return cmd_semiforge_sweep(args)
        if action == "compare":
            return cmd_semiforge_compare(args)
        if action == "fyfab-demo":
            return cmd_fyfab_demo(args)
    elif command == "robot":
        if action == "gen":
            return cmd_robot_gen(args)
        if action == "analyze":
            return cmd_robot_analyze(args)
        if action == "skill-demo":
            return cmd_robot_skill_demo(args)
        if action == "import-check":
            return cmd_robot_import_check(args)
        if action == "pilot-pack":
            return cmd_robot_pilot_pack(args)
    elif command == "semiconductor":
        if action == "pilot-pack":
            return cmd_semiconductor_pilot_pack(args)
    elif command == "sat":
        if action == "gen":
            return cmd_sat_gen(args)
        if action == "analyze":
            return cmd_sat_analyze(args)
        if action == "orbit-demo":
            return cmd_sat_orbit_demo(args)
    elif command == "memory":
        if action == "analyze":
            return cmd_memory_analyze(args)
        if action == "gen":
            return cmd_memory_gen(args)
        if action == "product-demo":
            return cmd_memory_product_demo(args)
    elif command == "pilot":
        from ..pilot.cli import cmd_pilot_check, cmd_pilot_init
        if action == "init":
            return cmd_pilot_init(args)
        if action == "check":
            return cmd_pilot_check(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
