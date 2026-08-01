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

## 検証

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
