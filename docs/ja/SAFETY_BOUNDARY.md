# Safety Boundary — 安全境界仕様

HAL YieldOSは読み取り専用です。

YieldOSはハードウェアを制御しません。
YieldOSはroot causeを認証しません。
YieldOSは安全性を認証しません。
YieldOSは自動復旧を実行しません。

すべての判断は candidate-only であり、人間のレビューが必要です。

---

## システムレベル安全不変条件

| 条件 | 強制値 |
|------|--------|
| `StateSnapshot.mode` | `read_only_shadow` |
| `EvidencePack.causal_claim_boundary` | `candidate_only_not_certified_cause` |
| `OODAFrame.act` | `recommendation_only_no_hardware_action` |
| `RecoveryCandidate.hardware_execution_enabled` | `false` |
| `RecoveryCandidate.requires_human_review` | `true` |

---

## ドメイン別禁止事項

### ロボット

YieldOSはROSコマンドを送信しません。
YieldOSはトルクコマンドを送信しません。
YieldOSはキャリブレーションシーケンスをトリガーしません。

### 衛星

YieldOSはアップリンクコマンドを送信しません。
YieldOSは運用モードを切り替えません。
YieldOSはペイロードを制御しません。

### 半導体

YieldOSはプロセスレシピを変更しません。
YieldOSは装置の起動・停止コマンドを送信しません。
YieldOSはroot causeを認証しません。

### FYFab Seed

FYFab Seedはチップを製造しません。
FYFab Seedは物理設計サインオフを行いません。
FYFab Seedはタイミングクロージャを行いません。
FYFab Seedは歩留まりを保証しません。

---

## 人間レビューゲート

すべての復旧候補は `requires_human_review = true` を持ちます。

1. エンジニアが証拠パックを読む
2. エンジニアがroot cause候補を評価する
3. エンジニアが復旧候補に対して行動するかどうかを決定する
4. YieldOSは復旧アクションを自律的に実行しない
