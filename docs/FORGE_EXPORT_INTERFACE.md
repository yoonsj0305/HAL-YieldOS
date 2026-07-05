# Forge Export Interface

YieldOS does not embed full HAL Forge.

YieldOS exports Forge-compatible JSON.
Forge ingests YieldOS output.

---

## Design Principle

Good structure:
```
YieldOS exports Forge-compatible JSON.
Forge ingests YieldOS output.
```

Avoided structure:
```
YieldOS imports full HAL Forge runtime.
YieldOS depends on Forge runtime.
```

---

## Future Output Candidates

The following outputs are planned for a future interface release:

- `forge_decision_intake.json` — structured intake for Forge decision engine
- `forge_memory_event.json` — memory event for Forge fabric
- `forge_sop_candidate_seed.json` — SOP candidate seed for Forge workflow

These do not exist yet. Do not reference them as current outputs.

---

## Future CLI

The following command is a planned interface. It is documented for roadmap clarity and is not implemented in the current release:

```bash
yieldos export forge --case <case_dir> --out <out_dir>
```

---

## Boundary

- No full Forge runtime dependency
- No automatic memory promotion
- No automatic approval
- No autonomous action
- Human review required before any Forge workflow integration

---

## 한국어 요약

YieldOS는 full HAL Forge를 내장하지 않는다.
YieldOS는 Forge-compatible JSON을 export하고, Forge가 YieldOS output을 ingestion하는 방향으로 설계한다.
향후 forge_decision_intake.json, forge_memory_event.json 등의 output을 추가할 예정이다.
