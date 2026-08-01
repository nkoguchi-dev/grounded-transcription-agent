import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("MINIO_INTERNAL_ENDPOINT", "http://minio:9000")
os.environ.setdefault("MINIO_PUBLIC_ENDPOINT", "http://localhost:9002")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("MINIO_BUCKET", "gta-local-artifacts")
