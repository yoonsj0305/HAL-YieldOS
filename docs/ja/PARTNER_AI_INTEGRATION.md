# Partner AI Integration — パートナーAI統合ガイド

HAL YieldOSはAIではありません。

YieldOSは、パートナーAIが安全に読める証拠パックを生成します。

Raw logを直接AIに渡すのではなく、YieldOSが生成した EvidencePack、Functional Passport、Decision Readiness をAIとエンジニアが確認する流れを推奨します。

---

## 推奨フロー

```
産業ログ（CSV / JSON）
→ YieldOSスキーマ検証
→ EvidencePack生成
→ Functional Passport生成
→ Decision Readiness生成
→ パートナーAIが要約
→ エンジニアQ&A
→ 日本語報告書
→ 経営幹部ブリーフィング
```

---

## なぜRaw Logを直接AIに渡さないのか

- Raw logは非構造化で冗長
- Root cause候補が証拠なしで生成される可能性がある
- EvidencePackは証拠の連鎖（evidence lineage）を保持する
- YieldOSのcandidate-only境界が維持される

---

## 重要な制約

AIの要約は以下に変換してはなりません：

- 認証されたroot cause
- 自動装置アクション
- 歩留まり保証
- 安全認証
- 物理設計サインオフ

YieldOSの候補証拠は、人間のエンジニアがレビューするまで候補のままです。

---

## 将来のインターフェース（現在は未実装）

将来的に以下の出力が計画されています：

- `ai_context_pack.json` — LLM消費用の機械可読証拠要約
- `ai_context_pack.md` — 人間可読の同等物

これらは現在存在しません。

---

## 製品定義

AI は話す。
YieldOS は証拠を作る。
Forge は覚える。
人間が決定する。
