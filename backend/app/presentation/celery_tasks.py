from app.composition import build_execute_dummy_job_use_case
from app.presentation.celery_app import EXECUTE_DUMMY_JOB_TASK_NAME, celery


@celery.task(name=EXECUTE_DUMMY_JOB_TASK_NAME)  # type: ignore[untyped-decorator]
def execute_dummy_job(job_id: str) -> None:
    build_execute_dummy_job_use_case().execute(job_id)
