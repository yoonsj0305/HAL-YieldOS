# Pilot Sample — NAND/Flash Memory Device

Sample input data for `yieldos pilot check --domain memory`.

## Files

| File | Description |
|------|-------------|
| `bad_block_map.csv` | Block-level health (16 blocks: 2 factory bad, 3 runtime bad, 1 uncorrectable) |
| `ecc_log.csv` | ECC correction events across 15 days |
| `product_bin_rules.json` | Baseline binning policy (strict zero-tolerance) |

## Usage

```bash
# Check readiness
yieldos pilot check \
  --domain memory \
  --input samples/pilot_memory \
  --out output/pilot_check_memory
```

## Notes

- Block 7 is uncorrectable (escalating ECC errors visible in ecc_log).
- Blocks 4 and 12 are runtime bad with moderate ECC error rates.
- Full pilot requires ≥ 64 blocks; this sample is a truncated demo.
- Device serial numbers removed — block_id is sequential integer.
