import time

from app.celery_app import celery
from app.domain.jobs.model import JobStatus
from app.infrastructure.database import SessionLocal
from app.infrastructure.jobs import SqlAlchemyJobRepository


@celery.task(name="app.worker.execute_dummy_job")  # type: ignore[untyped-decorator]
def execute_dummy_job(job_id: str) -> None:
    session = SessionLocal()
    repository = SqlAlchemyJobRepository(session)
    job = repository.get(job_id)
    if job is None or job.status is not JobStatus.QUEUED:
        session.close()
        return
    try:
        job = job.start()
        repository.update(job)
        session.commit()
        time.sleep(job.duration_seconds)
        if job.should_fail:
            raise RuntimeError("Dummy job was configured to fail")
        repository.update(job.succeed({"message": "Dummy job completed"}))
        session.commit()
    except Exception as error:
        session.rollback()
        current = repository.get(job_id)
        if current and current.status is JobStatus.RUNNING:
            repository.update(current.fail(str(error)))
            session.commit()
        raise
    finally:
        session.close()
