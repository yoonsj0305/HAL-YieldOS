# Product Memory Rebinning Demo

**HAL YieldOS — Product Demo Sample Data**

This sample demonstrates the core value proposition of YieldOS for NAND flash memory:
a device that **binary policy would DISCARD** contains significant recoverable functional capacity
when analyzed with functional zone rebinning.

## Dataset

| File | Contents |
|------|----------|
| `block_health.csv` | 128-block MLC NAND health telemetry (32 GB total, 0.25 GB/block) |
| `device_info.json` | Device metadata, ECC policy, endurance thresholds |
| `baseline_policy.json` | Binary pass/fail policy (industry baseline for comparison) |

## Block Composition

| Zone | Blocks | Capacity | Trigger |
|------|--------|----------|---------|
| `discard` | 12 | 3.0 GB | 8× runtime_bad + 4× uncorrectable ECC |
| `approximate_cache` | 16 | 4.0 GB | corrected_errors ≥ 100, retention < 72h |
| `read_only_archive` | 12 | 3.0 GB | PE cycle ratio ≥ 0.80 |
| `safe` | 88 | 22.0 GB | No at-risk signals |
| **Total** | **128** | **32.0 GB** | |

## Binary Policy vs YieldOS

**Binary policy** (`baseline_policy.json`): Any `runtime_bad` block → device FAIL → DISCARD.
Verdict: **FAIL** — the 12 discard blocks trigger immediate device rejection.

**YieldOS analysis**: 88 safe blocks (22 GB) remain fully functional.
The device is a **functional reclassification candidate** for:
- 22 GB high-reliability safe zone
- 4 GB approximate AI cache zone
- 3 GB read-only archive zone

`reclassification_occurred = true`

## Run

```bash
yieldos memory product-demo --out output/product_memory_rebinning_demo
```

## Inspect

```bash
yieldos inspect-output output/product_memory_rebinning_demo
cat output/product_memory_rebinning_demo/baseline_vs_yieldos.json
cat output/product_memory_rebinning_demo/memory_functional_capacity.json
```

## Safety

All outputs are candidate estimates for human review only.
YieldOS does not modify firmware, remap blocks, or certify data integrity.
No recovery action is executed without explicit human authorization.
