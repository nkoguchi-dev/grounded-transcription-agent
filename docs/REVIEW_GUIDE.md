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
- [ ] FastAPI／Celery の import、型、設定、タスク登録・発行・Worker エントリポイントは Presentation
  層に限定され、Application／Domain に実装固有の名称がない。
- [ ] ドメインモデルを入出力とする Repository Interface は、対応する `app/domain/<domain>/` 配下に定義され、Application 層に残っていない。
- [ ] Application と Infrastructure の両方を import するのは composition root に限定されている。
- [ ] 1 つの Python モジュールが 1 つの機能だけを所有し、ユースケース、API 操作、Worker 処理が
  別モジュールに分割されている。
- [ ] 各機能に固有の入力・出力 DTO は、その機能を実装するモジュールに定義されている。
- [ ] `__init__.py`、composition root、ルーター集約などの組み立て専用モジュールに、機能の実装や
  DTO が混入していない。

## トランザクション

- [ ] 更新ユースケースごとの境界、成功時の commit、例外時の rollback が明確である。
- [ ] Repository は独自に commit せず、複数の永続化操作を同じ Unit of Work で扱える。
- [ ] 外部サービス呼び出しや長時間処理を DB トランザクション内に保持していない。
- [ ] 非同期処理の状態遷移は短いトランザクションで永続化され、失敗状態を確認できる。
- [ ] DB 確定と非同期メッセージ送信が原子的でない場合、その制約と対処方針を変更内容と設計文書に明記している。

## Application エラーと Presentation での変換

- [ ] 予期される Application 失敗が固有例外で表され、`RuntimeError`、`ValueError`、`Exception`、
  `None` などで曖昧に表現されていない。
- [ ] Application 例外が FastAPI、HTTP ステータス、Celery など Presentation 固有の型や知識を参照していない。
- [ ] Presentation は具体的な Application 例外だけを意図したレスポンスへ変換し、予期しない例外を
  包括的に catch して既知の 4xx／5xx へ誤変換していない。
- [ ] Infrastructure／外部ライブラリ固有の例外が境界で意味のある Application 例外へ変換され、
  Application／Presentation へ漏れていない。
- [ ] 公開エラーレスポンスが内部例外のメッセージ、接続先、認証情報などの内部詳細や機密情報を漏らしていない。
- [ ] 新規または変更された Application 例外と HTTP ステータスの対応が、本番と共通の composition root を
  使う Component/API Test で網羅され、公開本文、情報非漏洩、副作用も検証されている。
- [ ] HTTP 以外の Presentation についても、例外の伝播・再試行・記録方針が明確である。

## コードコメントと docstring

- [ ] コードだけから安全に判断できない意図・制約・トレードオフには、必要なコメントまたは docstring がある。
- [ ] 実装変更に伴い、既存のコメントと docstring が古くなったり実装と矛盾したりしていない。
- [ ] 名前・型・制御フローを逐語的に説明するだけの冗長なコメントを増やしていない。
