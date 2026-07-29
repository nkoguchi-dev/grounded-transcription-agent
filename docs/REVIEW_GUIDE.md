# 自己レビューガイド

## PR のスコープと基準ブランチ

- [ ] PR の base が想定したリモートの既定ブランチである。
- [ ] 差分に別 Issue の変更やローカル未公開コミットが混入していない。
- [ ] 変更内容が対象 Issue に対応しており、無関係な変更は別 PR に分離している。

## 責務の分離

- [ ] 依存方向が `Presentation → Application → Domain` を守り、Infrastructure は定義済みの抽象を実装している。
- [ ] Presentation は SQLAlchemy、Session、具体 Repository、DB 接続設定を直接参照していない。
- [ ] Application は SQLAlchemy の型、Session、具体 Repository に依存せず、ユースケースとトランザクション境界を表現している。
- [ ] Domain は永続化、フレームワーク、外部サービスの知識を持たない。
- [ ] Application と Infrastructure の両方を import するのは composition root に限定されている。

## トランザクション

- [ ] 更新ユースケースごとの境界、成功時の commit、例外時の rollback が明確である。
- [ ] Repository は独自に commit せず、複数の永続化操作を同じ Unit of Work で扱える。
- [ ] 外部サービス呼び出しや長時間処理を DB トランザクション内に保持していない。
- [ ] 非同期処理の状態遷移は短いトランザクションで永続化され、失敗状態を確認できる。
- [ ] DB 確定と非同期メッセージ送信が原子的でない場合、その制約と対処方針を変更内容と設計文書に明記している。
