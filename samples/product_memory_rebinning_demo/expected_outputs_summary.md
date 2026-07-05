# Expected Outputs Summary — Product Memory Rebinning Demo

## Analysis Inputs

| Field | Value |
|-------|-------|
| Device | NAND_DEMO_32GB_MLC |
| Raw capacity | 32.0 GB |
| Block count | 128 × 0.25 GB |
| NAND type | MLC (simulated) |

## Expected Block Classification

| Classification | Blocks | Capacity (GB) | Trigger |
|---------------|--------|---------------|---------|
| discard | 12 | 3.00 | 8× `is_runtime_bad=true`, 4× `uncorrectable_error_count≥1` |
| approximate_cache | 16 | 4.00 | `corrected_error_count≥100` and `retention_hours=48<72` |
| read_only_archive | 12 | 3.00 | `pe_ratio=0.90≥0.80`, no corrected/retention issues |
| safe | 88 | 22.00 | No at-risk signals |

## Expected State Snapshot

| Field | Expected Value |
|-------|---------------|
| `state` | `functional_yield_estimated` |
| `severity` | `medium` |
| `functional_yield` | `0.6875` (22/32) |
| `discard_rate` | `0.0938` (12/128) |
| `bin_class` | `memory_bronze_cache_only` |

## Expected baseline_vs_yieldos.json

```json
{
  "binary_policy_verdict": "FAIL",
  "yieldos_functional_verdict": "memory_bronze_cache_only",
  "reclassification_occurred": true,
  "recovered_functional_capacity_estimate": {
    "safe_gb": 22.0,
    "approximate_cache_gb": 4.0,
    "read_only_archive_gb": 3.0,
    "discard_gb": 3.0,
    "total_raw_gb": 32.0
  },
  "baseline_policy_rules": {
    "max_runtime_bad_blocks": 0,
    "max_uncorrectable_error_blocks": 0,
    "max_at_risk_fraction": 0.10
  }
}
```

## Expected Remaining Roles

- `approximate_ai_cache_candidate`
- `temporary_buffer_candidate`
- `read_only_archive_candidate`

## Expected Blocked Roles

- `primary_filesystem_metadata`
- `financial_record_storage`
- `safety_critical_storage`

## Strict Validation

Expected: 59/59 STRICT PASS
