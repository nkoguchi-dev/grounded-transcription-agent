from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.application.jobs.errors import JobDispatchError, JobNotFoundError


def register_application_error_handlers(app: FastAPI) -> None:
    """Keep public HTTP mappings explicit and separate from application errors."""

    @app.exception_handler(JobNotFoundError)
    async def handle_job_not_found(
        _request: Request, _error: JobNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Job not found"},
        )

    @app.exception_handler(JobDispatchError)
    async def handle_job_dispatch_failure(
        _request: Request, _error: JobDispatchError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Job broker is unavailable"},
        )
