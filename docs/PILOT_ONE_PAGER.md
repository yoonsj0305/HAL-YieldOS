# HAL YieldOS — Pilot One-Pager

*For design-partner and pilot evaluation.*

---

## One-Line

HAL YieldOS turns imperfect industrial system data into Functional Yield evidence packages for human review.

한국어: HAL YieldOS는 불완전한 산업 시스템 데이터를 기능수율 EvidencePack과 Functional Passport로 바꿔, 사람 검토와 AI 보조 의사결정에 사용할 수 있게 만드는 읽기 전용 소프트웨어입니다.

---

## Problem

Industrial systems — robots, semiconductor fab equipment, satellites, memory devices — frequently operate with partial failure, degraded function, missing telemetry, or uncertain remaining capability.

Existing dashboards show signals. But they rarely answer:

> **What can still function, what must be blocked, under what conditions, and based on what evidence?**

The result is binary: ship or scrap, pass or fail, online or offline — even when a more granular answer exists.

---

## Approach

YieldOS reads **sanitized logs** and generates:

- **EvidencePack** — sealed, checksummed evidence bundle
- **Functional Passport** — candidate remaining / blocked role assessment
- **Decision Readiness Report** — evidence completeness and confidence
- **Missing Evidence Request** — explicit next data acquisition guidance
- **Valid Conditions** — candidate operating envelopes
- **Process Confidence Report** — analysis quality score and missing metrics

Every output is **candidate evidence** for human review — not a decision, certification, or hardware command.

---

## Pilot Domains

### Semiconductor

**Purpose:** Prepare Recovery Compiler intake evidence from fab process data.

**Inputs required:**

| File | Description |
|------|-------------|
| `tool_log.csv` | Process tool step logs |
| `metrology.csv` | CD metrology measurements |
| `test_results.csv` | Functional test results |
| `wafer_map.csv` | Die pass/fail map |
| `chip_tile_map.json` | Die tile layout |
| `workload_roles.json` | Target functional roles |
| `recovery_constraints.json` | Recovery boundary constraints |

**Key outputs:**

- `semiconductor_wafer_die_summary.json`
- `semiconductor_functional_region_map.json`
- `semiconductor_role_candidate_map.json`
- `semiconductor_recovery_compiler_export.json` *(candidate-only, for offline testing)*
- `semiconductor_handoff_manifest.json`
- `functional_passport.json` with `confidence_explanation`

### Robot

**Purpose:** Reclassify remaining vs. blocked roles after telemetry-observed degradation.

**Inputs required:**

- Robot telemetry CSV
- Operator observation notes
- Maintenance notes
- Force/torque event logs
- Human intervention timeline

**Key outputs:**

- `robot_role_reclassification_report.json`
- `robot_valid_conditions_report.json`
- `robot_human_review_packet.json`
- `functional_passport.json`

---

## Safety Boundary

| Property | Value |
|----------|-------|
| Mode | `read_only` |
| Outputs | `candidate_only` |
| Decisions | `human_review_required` |
| Hardware control | `false` |
| Recipe control | `false` |
| Safety certification | Not provided |
| Yield guarantee | Not provided |
| Root-cause certification | Not provided |
| Recovery Compiler execution | Not performed |

---

## Pilot Success Criteria

A pilot is **ready** when:

1. Sanitized sample logs can be loaded.
2. Standard YieldOS output bundle is generated without errors.
3. `yieldos validate --strict` passes.
4. Missing evidence is clearly listed in `next_data_request.json`.
5. Human reviewer can evaluate the `functional_passport.json` and decide next steps.

---

## Getting Started

```bash
pip install -e .
yieldos doctor --deep
yieldos demo --all --out output/demo_all
yieldos validate --case output/demo_all/semiconductor --strict
```

For semiconductor pilot:

```bash
yieldos semiconductor pilot-pack \
  --input samples/pilot_semiconductor \
  --out output/semiconductor_pilot_pack
yieldos validate --case output/semiconductor_pilot_pack --strict
```

See [docs/DEMO_GUIDE.md](DEMO_GUIDE.md) for the full demo walkthrough.

---

*HAL YieldOS v3.0.7 — read-only | candidate-only | human-review-required*
