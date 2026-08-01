# バックエンド開発ガイド

## アーキテクチャと依存関係

- Python 3.14、FastAPI、Celery、PostgreSQL、Redis、MinIO をローカルスタックとして使用する。
- 依存方向は `Presentation → Application → Domain` とする。Infrastructure は Application と
  Domain の抽象を実装し、Application と Infrastructure の両方を import できるのは composition
  root のみとする。
- `JobRepository` のようにドメインモデルを入出力とする Repository Interface は、対応するモデルの
  近くの `app/domain/<domain>/` に定義する。Application 層には配置しない。
- ジョブの状態・結果の正本は PostgreSQL とする。Redis は Celery のブローカーとしてのみ使用する。
- Application のユースケースがトランザクション境界を決め、Unit of Work などの抽象のみに依存する。
  SQLAlchemy の型、Session、具象 Repository を import してはならない。
- Infrastructure は SQLAlchemy による Unit of Work と Repository の実装を提供し、commit/rollback と
  Session のライフサイクルを管理する。
- Presentation は DB、SQLAlchemy、具象 Repository、DB 接続設定を参照せず、Application の
  ユースケースを呼び出す。Application と Infrastructure を組み立てるのは composition root のみとする。
- FastAPI と Celery の import、型、設定、タスク登録・発行・Worker エントリポイントは Presentation 層に
  限定する。Application はフレームワーク非依存のポートを通じてジョブを発行し、Domain は実装方式を
  示す名称を持たない不透明な task ID だけを扱う。
- 外部サービスの呼び出しや長時間処理を DB トランザクション内で実行しない。非同期処理の状態遷移は、
  短い独立したトランザクションとして永続化する。

## Application エラーと Presentation での変換

- Application 層で予期されるユースケース上の失敗は、`app/application/errors.py` の基底例外を継承した
  固有例外で表す。機能固有の例外は対応する機能モジュールの近くに定義し、`RuntimeError`、
  `ValueError`、`Exception`、`None` などで曖昧に表現しない。
- Application 例外は FastAPI、HTTP ステータス、Celery など Presentation 固有の知識を持たない。
  Presentation が具体的な Application 例外だけを、公開可能な HTTP レスポンスまたはタスク失敗へ変換する。
- 予期しない例外は原則として上位へ伝播させ、HTTP 500 や Celery のタスク失敗などフレームワーク標準の
  障害処理へ委ねる。包括的な `except Exception` で既知の 4xx／5xx に変換してはならない。
- Infrastructure や外部ライブラリの例外は境界 Adapter または Application のポート契約で、意味のある
  Application 例外へ変換する。外部ライブラリ固有の例外を Application／Presentation へ漏らさない。
- Domain の不変条件違反と Application のユースケース失敗を混同しない。公開レスポンスには内部例外の
  メッセージ、接続先、認証情報などの内部詳細や機密情報を含めない。
- HTTP 以外の Presentation では、必要な状態の記録後に例外を伝播するか、再試行するかを明示する。
  Celery Worker は失敗状態を永続化した後に元の例外を伝播し、タスク失敗として扱わせる。
- HTTP に対応付けたすべての Application 例外について、本番と共通の composition root を使う
  Component/API Test でステータス、公開本文、情報非漏洩、副作用を検証する。

## 検証

機能ごとのテストは自己完結させ、別機能のテストモジュール、fixture、Stub、Fake、テスト用ヘルパーを
import して再利用しない。対象機能に必要なテストダブルは、その機能のテストモジュールまたは対象機能用の
共通 fixture に定義する。プロダクションコード上の公開インターフェースや、機能に依存しない汎用テスト基盤は
共有してよい。

依存関係は `uv sync --frozen` で同期する。コミット前に `uv run black --check .`、
`uv run isort --check-only .`、`uv run flake8 .`、`uv run mypy .`、
`uv run pytest tests`、`uv run pytest integration_tests` を実行する。Component/API Test は
Testcontainers で PostgreSQL を起動するため、実行には Docker Engine が必要になる。

## ローカルコマンド（リポジトリルートで実行）

```bash
cp backend/.env.example backend/.env.local
cp minio/.env.example minio/.env.local
docker compose up --build --wait
docker compose logs -f api worker
cd backend && uv sync --frozen
uv run pytest tests
uv run pytest integration_tests
```
