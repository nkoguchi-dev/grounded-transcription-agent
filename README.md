# Grounded Transcription Agent

原音と任意のコンテキストを根拠に、文字起こしを安全に見直す基盤です。現在は Phase 1
の最小骨組みとして、非同期ダミージョブとオブジェクトの直接アップロードを提供します。

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

## Pre-Signed URL によるオブジェクトの確認

次の例では、開始 API が生成した object key を含む署名済み URL へ、Backend を経由せず
ダミーファイルを PUT します。`jq` が必要です。

```bash
printf 'dummy artifact' > /tmp/gta-dummy.txt
START=$(curl -sS -X POST http://localhost:8010/api/artifacts/uploads \
  -H 'content-type: application/json' \
  -d '{"content_type":"text/plain","expected_size":14}')
ARTIFACT_ID=$(printf '%s' "$START" | jq -r .artifact_id)
UPLOAD_URL=$(printf '%s' "$START" | jq -r .upload_url)

curl -sS -X PUT "$UPLOAD_URL" -H 'content-type: text/plain' \
  --data-binary @/tmp/gta-dummy.txt
curl -sS -X POST "http://localhost:8010/api/artifacts/$ARTIFACT_ID/complete"
curl -sS "http://localhost:8010/api/artifacts/$ARTIFACT_ID"

DOWNLOAD=$(curl -sS -X POST \
  "http://localhost:8010/api/artifacts/$ARTIFACT_ID/download-url")
curl -sS "$(printf '%s' "$DOWNLOAD" | jq -r .download_url)"
```

Backend は `MINIO_INTERNAL_ENDPOINT=http://minio:9000` で HEAD を行い、Client 向け URL は
`MINIO_PUBLIC_ENDPOINT=http://localhost:9002` を署名対象として発行します。署名後の URL の
host は置換しません。両 endpoint の認証情報、bucket、URL 有効期間は
[`backend/.env.example`](backend/.env.example) で設定できます。

## 責任の境界

- FastAPI はジョブを受け付け、状態を返します。
- Application 層が Unit of Work を通じてトランザクション境界を決めます。SQLAlchemy の
  Session、Repository 実装、commit/rollback は Infrastructure 層に閉じ込め、composition root
  だけが両層を組み立てます。
- PostgreSQL はジョブ状態・結果・エラーの正本です。
- Celery と Redis は非同期実行を担当します。
- MinIO は artifact 本体を保持し、Backend は署名 URL の発行と HEAD による完了確認だけを
  行います。Application 層は MinIO SDK ではなく Object Storage ポートへ依存します。

ジョブ登録の DB 確定と Celery への送信は原子的ではありません。送信後に task ID の保存が失敗
する可能性があります。この制約への Transactional Outbox による対処は本 Phase の対象外です。

停止は `docker compose down`、ローカルデータを破棄する場合は `database/data/` と
`minio/volume/` を削除してから再起動します。
