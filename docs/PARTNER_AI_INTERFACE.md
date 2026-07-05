# Partner AI Interface

YieldOS is not an AI model.

Partner AI systems should not consume raw industrial logs directly when a YieldOS EvidencePack
is available.

---

## Preferred Flow

```
industrial logs
→ YieldOS schema validation
→ EvidencePack
→ Functional Passport
→ Decision Readiness
→ AI-readable context
→ engineer / reviewer / manager
```

Raw logs fed directly into LLMs are unstructured, verbose, and expensive.
YieldOS EvidencePacks are compact, structured, and evidence-lineage-preserved.

---

## Future Output Candidates

The following outputs are planned for a future interface release:

- `ai_context_pack.json` — machine-readable evidence summary for LLM consumption
- `ai_context_pack.md` — human-readable equivalent

These do not exist yet. Do not reference them as current outputs.

---

## Future CLI

The following command is a planned interface. It is documented for roadmap clarity and is not implemented in the current release:

```bash
yieldos export ai-context --case <case_dir> --out <out_dir>
```

---

## Claim Boundary

AI summaries must not convert candidate evidence into:

- certified root cause
- automatic equipment action
- yield guarantees
- safety certifications
- physical design signoff claims

YieldOS candidate evidence stays candidate until a human engineer reviews it.

---

## 한국어 요약

YieldOS는 AI 모델이 아니다.
파트너 AI 시스템은 원시 로그를 직접 받는 것보다 YieldOS EvidencePack을 통해 정제된 증거를 받는 것이 더 안전하고 효율적이다.
YieldOS output → LLM 요약 → 엔지니어 Q&A → 보고서 순서로 활용한다.
