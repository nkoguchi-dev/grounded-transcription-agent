from app.celery_app import celery
from app.composition import build_execute_dummy_job_use_case


@celery.task(name="app.worker.execute_dummy_job")  # type: ignore[untyped-decorator]
def execute_dummy_job(job_id: str) -> None:
    build_execute_dummy_job_use_case().execute(job_id)
