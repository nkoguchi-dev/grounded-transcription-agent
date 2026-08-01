import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
