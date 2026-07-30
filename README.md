# Grounded Transcription Agent

原音と任意のコンテキストを根拠に、文字起こしを安全に見直す基盤です。現在は Phase 1
の最小骨組みとして、非同期ダミージョブの登録・実行・参照を提供します。

## 起動

```bash
cp backend/.env.example backend/.env.local
cp minio/.env.example minio/.env.local
docker compose up --build --wait
curl -X POST http://localhost:8010/api/jobs -H 'content-type: application/json' \
  -d '{"duration_seconds": 1, "should_fail": false}'
```

`GET /api/jobs/{job_id}` で `queued`、`running`、`succeeded` または `failed` を確認できます。
OpenAPI は <http://localhost:8010/docs>、MinIO Console は <http://localhost:9003> です。

## 責任の境界

- FastAPI はジョブを受け付け、状態を返します。
- Application 層が Unit of Work を通じてトランザクション境界を決めます。SQLAlchemy の
  Session、Repository 実装、commit/rollback は Infrastructure 層に閉じ込め、composition root
  だけが両層を組み立てます。
- PostgreSQL はジョブ状態・結果・エラーの正本です。
- Celery と Redis は非同期実行を担当します。
- MinIO は後続 Phase の音声・成果物用に初期化済みですが、本版ではアプリから書き込みません。

ジョブ登録の DB 確定と Celery への送信は原子的ではありません。送信後に task ID の保存が失敗
する可能性があります。この制約への Transactional Outbox による対処は本 Phase の対象外です。

停止は `docker compose down`、ローカルデータを破棄する場合は `database/data/` と
`minio/volume/` を削除してから再起動します。
