# Grounded Transcription Agent

## 対象範囲

Phase 1 では、ローカルで動く非同期ジョブ基盤を構築する。対応する Phase が開始されるまで、
フロントエンド、MCP サーバー、認証、文字起こしプロバイダーとの連携を追加しない。

## バックエンドのルール

- Python 3.14、FastAPI、Celery、PostgreSQL、Redis、MinIO をローカルスタックとして使用する。
- 依存方向は `Presentation → Application → Domain` とする。Infrastructure は Application と
  Domain のポートを実装し、Application と Infrastructure の両方を import できるのは composition
  root のみとする。
- ジョブの状態・結果の正本は PostgreSQL とする。Redis は Celery のブローカーとしてのみ使用する。
- Application のユースケースがトランザクション境界を決め、Unit of Work などの抽象のみに依存する。
  SQLAlchemy の型、Session、具象 Repository を import してはならない。
- Infrastructure は SQLAlchemy による Unit of Work と Repository の実装を提供し、commit/rollback と
  Session のライフサイクルを管理する。
- Presentation は DB、SQLAlchemy、具象 Repository、DB 接続設定を参照せず、Application の
  ユースケースを呼び出す。Application と Infrastructure を組み立てるのは composition root のみとする。
- 外部サービスの呼び出しや長時間処理を DB トランザクション内で実行しない。非同期処理の状態遷移は、
  短い独立したトランザクションとして永続化する。
- PR を作成する前に、base が想定したリモート既定ブランチであること、および比較差分が対象 Issue の
  変更だけであることを確認する。無関係な変更や未公開のローカルコミットは別 PR に分離する。
- コミット前に `poetry run black .`、`poetry run isort .`、`poetry run flake8 .`、
  `poetry run mypy .`、`poetry run pytest` を実行する。

## ローカルコマンド

```bash
cp .env.example .env.local
docker compose up --build --wait
docker compose logs -f api worker
cd backend && poetry run pytest
```
